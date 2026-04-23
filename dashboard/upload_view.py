"""Upload & analyse tab — lets underwriters analyse their own workforce data."""
import io
import csv

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.api_client import predict_employee, calculate_premium
from dashboard.currency import fmt, active_code, CURRENCIES
from dashboard.pdf_report import generate_underwriting_report
from dashboard.illustrations import EMPLOYEE_HEALTH, _svg_img as _illus

PLOT_BG  = "#FFFFFF"
GRID_CLR = "rgba(0,0,0,0.06)"
FONT_CLR = "#111111"
ACCENT   = "#9BC800"

COLOR_MAP = {
    "Low":      "#22C55E",
    "Moderate": "#F59E0B",
    "High":     "#EF4444",
    "Critical": "#991B1B",
}

REQUIRED_COLS = {
    "employee_id", "age", "gender", "bmi",
    "smoker", "diabetic", "hypertension", "job_category",
}

INDUSTRIES = [
    "Technology", "Healthcare", "Manufacturing", "Retail",
    "Finance", "Energy", "Education", "Other",
]

# National-average telemetry defaults used when no wearable data is supplied
_TELEMETRY_DEFAULTS = {
    "avg_daily_steps":    6000,
    "step_volatility":    500.0,
    "avg_resting_hr":     72.0,
    "hr_trend":           0.0,
    "avg_active_mins":    30.0,
    "avg_sleep_hours":    7.0,
    "avg_spo2":           97.0,
    "visit_count":        0,
    "hospitalized_count": 0,
}


def _csv_template() -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["employee_id", "age", "gender", "bmi",
                "smoker", "diabetic", "hypertension", "job_category"])
    w.writerow(["EMP001", 34, "M", 24.5, "false", "false", "false", "desk"])
    w.writerow(["EMP002", 45, "F", 29.1, "false", "true",  "true",  "field"])
    w.writerow(["EMP003", 28, "M", 22.0, "true",  "false", "false", "manual"])
    w.writerow(["EMP004", 52, "F", 31.8, "false", "true",  "false", "desk"])
    w.writerow(["EMP005", 39, "O", 26.3, "false", "false", "false", "field"])
    return buf.getvalue().encode()


def _parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def _validate_and_parse(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    records: list[dict] = []

    missing = REQUIRED_COLS - set(df.columns.str.lower())
    if missing:
        return [], [f"Missing columns: {', '.join(sorted(missing))}"]

    df = df.copy()
    df.columns = df.columns.str.lower()

    for i, row in df.iterrows():
        row_errors: list[str] = []

        try:
            age = int(row["age"])
            if not 18 <= age <= 70:
                row_errors.append(f"age {age} must be 18-70")
        except (ValueError, TypeError):
            row_errors.append("age must be an integer")
            age = None

        try:
            bmi = float(row["bmi"])
            if not 10.0 <= bmi <= 60.0:
                row_errors.append(f"bmi {bmi:.1f} must be 10-60")
        except (ValueError, TypeError):
            row_errors.append("bmi must be a number")
            bmi = None

        gender = str(row["gender"]).strip().upper()
        if gender not in ("M", "F", "O"):
            row_errors.append(f"gender '{gender}' must be M, F, or O")

        job = str(row["job_category"]).strip().lower()
        if job not in ("desk", "field", "manual"):
            row_errors.append(f"job_category '{job}' must be desk, field, or manual")

        if row_errors:
            errors.append(f"Row {i + 2} ({row.get('employee_id', '?')}): {'; '.join(row_errors)}")
        else:
            records.append({
                "employee_id": str(row["employee_id"]),
                "age":         age,
                "gender":      gender,
                "bmi":         bmi,
                "smoker":      _parse_bool(row["smoker"]),
                "diabetic":    _parse_bool(row["diabetic"]),
                "hypertension":_parse_bool(row["hypertension"]),
                "job_category":job,
            })

    return records, errors


def _run_analysis(employees: list[dict], company_name: str, base_premium: float) -> dict:
    results: list[dict] = []
    total = len(employees)
    bar = st.progress(0, text=f"Scoring employees... 0 / {total}")

    for i, emp in enumerate(employees):
        features = {
            **{k: v for k, v in emp.items() if k != "employee_id"},
            "chronic_count": int(emp["diabetic"]) + int(emp["hypertension"]),
            **_TELEMETRY_DEFAULTS,
        }
        try:
            pred = predict_employee(features)
            results.append({
                "employee_id": emp["employee_id"],
                "age":         emp["age"],
                "gender":      emp["gender"],
                "bmi":         emp["bmi"],
                "smoker":      emp["smoker"],
                "diabetic":    emp["diabetic"],
                "hypertension":emp["hypertension"],
                "job_category":emp["job_category"],
                "hrs":         pred["health_risk_score"],
                "loss_ratio":  pred["predicted_loss_ratio"],
                "risk_band":   pred["risk_band"],
            })
        except Exception as exc:
            st.warning(f"Skipped {emp['employee_id']}: {exc}")

        bar.progress((i + 1) / total, text=f"Scoring employees... {i + 1} / {total}")

    bar.empty()

    if not results:
        return {}

    df = pd.DataFrame(results)
    mean_hrs  = float(df["hrs"].mean())
    mean_loss = float(df["loss_ratio"].mean())

    low_pct      = float((df["risk_band"] == "Low").mean()      * 100)
    moderate_pct = float((df["risk_band"] == "Moderate").mean() * 100)
    high_pct     = float((df["risk_band"] == "High").mean()     * 100)
    critical_pct = float((df["risk_band"] == "Critical").mean() * 100)

    if mean_hrs < 30:
        risk_band = "Low"
    elif mean_hrs < 60:
        risk_band = "Moderate"
    elif mean_hrs < 80:
        risk_band = "High"
    else:
        risk_band = "Critical"

    try:
        prem = calculate_premium(base_premium, mean_hrs)
    except Exception:
        prem = {
            "adjusted_premium": base_premium,
            "adjustment_pct":   0.0,
            "zone":             "unknown",
            "recommendation":   "N/A",
        }

    return {
        "company_name":      company_name,
        "employee_count":    len(df),
        "mean_hrs":          round(mean_hrs, 1),
        "mean_loss_ratio":   round(mean_loss, 4),
        "risk_band":         risk_band,
        "low_risk_pct":      round(low_pct, 1),
        "moderate_risk_pct": round(moderate_pct, 1),
        "high_risk_pct":     round(high_pct, 1),
        "critical_risk_pct": round(critical_pct, 1),
        "premium":           prem,
        "base_premium":      base_premium,
        "df":                df,
    }


def _chart_defaults() -> dict:
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="Inter, system-ui, sans-serif"),
        margin=dict(l=0, r=20, t=24, b=40),
    )


def _render_results(res: dict) -> None:
    st.success(f"Analysis complete — {res['company_name']}")

    code = active_code()
    rate = CURRENCIES[code]["rate"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees",        res["employee_count"])
    c2.metric("Mean HRS",         f"{res['mean_hrs']:.1f}", res["risk_band"])
    c3.metric("Adjusted premium", fmt(res["premium"]["adjusted_premium"] * rate))
    c4.metric("Premium change",   f"{res['premium']['adjustment_pct']:+.2f}%")

    st.divider()

    col_chart, col_gauge = st.columns([3, 2])

    with col_chart:
        st.subheader("Risk band breakdown")
        dist_df = pd.DataFrame({
            "band": ["Low", "Moderate", "High", "Critical"],
            "pct":  [res["low_risk_pct"], res["moderate_risk_pct"],
                     res["high_risk_pct"], res["critical_risk_pct"]],
        })
        dist_fig = px.bar(
            dist_df, x="pct", y="band", orientation="h",
            color="band", color_discrete_map=COLOR_MAP,
            labels={"pct": "% of workforce", "band": ""},
            height=220,
        )
        dist_fig.update_layout(
            **_chart_defaults(), showlegend=False,
            xaxis=dict(gridcolor=GRID_CLR, zeroline=False),
            yaxis=dict(gridcolor=GRID_CLR),
        )
        st.plotly_chart(dist_fig, use_container_width=True)

    with col_gauge:
        st.subheader("Health Risk Score")
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=res["mean_hrs"],
            number={"font": {"color": FONT_CLR, "size": 36}},
            gauge={
                "axis":    {"range": [0, 100], "tickcolor": "#999999"},
                "bar":     {"color": ACCENT},
                "bgcolor": PLOT_BG,
                "steps": [
                    {"range": [0,  30],  "color": "rgba(34,197,94,0.10)"},
                    {"range": [30, 60],  "color": "rgba(245,158,11,0.10)"},
                    {"range": [60, 80],  "color": "rgba(239,68,68,0.10)"},
                    {"range": [80, 100], "color": "rgba(153,27,27,0.15)"},
                ],
            },
            title={"text": "Mean HRS", "font": {"color": FONT_CLR, "size": 13}},
        ))
        gauge.update_layout(
            height=230,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor=PLOT_BG,
        )
        st.plotly_chart(gauge, use_container_width=True)

    st.info(
        f"**Recommendation:** {res['premium']['recommendation']}  \n"
        f"Adjusted premium: **{fmt(res['premium']['adjusted_premium'] * rate)}** "
        f"({res['premium']['adjustment_pct']:+.2f}% vs base {fmt(res['base_premium'] * rate)})"
    )

    st.subheader("Employee risk scores")
    display_df = res["df"][[
        "employee_id", "age", "gender", "bmi", "smoker",
        "diabetic", "hypertension", "job_category", "hrs", "risk_band",
    ]].rename(columns={
        "employee_id": "ID",
        "age":         "Age",
        "gender":      "Gender",
        "bmi":         "BMI",
        "smoker":      "Smoker",
        "diabetic":    "Diabetic",
        "hypertension":"Hypertension",
        "job_category":"Job",
        "hrs":         "HRS",
        "risk_band":   "Band",
    }).sort_values("HRS", ascending=False)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "HRS": st.column_config.ProgressColumn("HRS", min_value=0, max_value=100, format="%.1f"),
        },
    )

    pred_for_pdf = {
        "company_name":      res["company_name"],
        "company_id":        "UPLOAD",
        "employee_count":    res["employee_count"],
        "mean_hrs":          res["mean_hrs"],
        "mean_loss_ratio":   res["mean_loss_ratio"],
        "risk_band":         res["risk_band"],
        "low_risk_pct":      res["low_risk_pct"],
        "moderate_risk_pct": res["moderate_risk_pct"],
        "high_risk_pct":     res["high_risk_pct"],
        "critical_risk_pct": res["critical_risk_pct"],
        "top_risk_drivers":  [],
    }
    try:
        pdf_bytes = generate_underwriting_report(pred_for_pdf, res["premium"], currency=active_code())
        st.download_button(
            "Download underwriting report (PDF)",
            data=pdf_bytes,
            file_name="aegis_upload_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:
        st.warning(f"PDF generation failed: {exc}")


def render_tab() -> None:
    st.subheader("Analyse your own workforce data")
    st.caption("Upload a CSV of employee records for instant risk scoring — no data is stored on the server.")

    res = st.session_state.get("upload_results")

    if res:
        _render_results(res)
        st.divider()
        if st.button("Start new analysis", use_container_width=True):
            del st.session_state["upload_results"]
            st.rerun()
        return

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company name", placeholder="e.g. Acme Corp")
        st.selectbox("Industry", INDUSTRIES)
    with col2:
        base_premium = st.number_input(
            "Annual base premium (INR)",
            min_value=100_000, max_value=100_000_000,
            value=5_000_000, step=100_000,
            format="%d",
        )
        st.write("")
        st.download_button(
            "Download CSV template",
            data=_csv_template(),
            file_name="aegis_employee_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    uploaded = st.file_uploader(
        "Upload employee roster (CSV)",
        type=["csv"],
        help="Required columns: employee_id, age, gender (M/F/O), bmi, smoker, diabetic, hypertension, job_category (desk/field/manual)",
    )

    if not uploaded:
        _eu, _ei = st.columns([1, 1])
        with _eu:
            st.info("Upload a CSV to get started. Use the template above for the correct format.")
        with _ei:
            st.markdown(
                f'<div style="display:flex;justify-content:center;opacity:0.88;">'
                f'{_illus(EMPLOYEE_HEALTH, "220px")}</div>',
                unsafe_allow_html=True,
            )
        return

    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        return

    employees, errors = _validate_and_parse(df_raw)

    if errors:
        st.error(f"{len(errors)} validation error(s) found:")
        for err in errors[:10]:
            st.caption(f"- {err}")
        if len(errors) > 10:
            st.caption(f"... and {len(errors) - 10} more")
        if employees:
            st.warning(f"{len(employees)} valid row(s) found. Fix errors to include all rows.")
        return

    st.success(f"{len(employees)} employees loaded successfully. Preview (first 5 rows):")
    st.dataframe(df_raw.head(5), use_container_width=True, hide_index=True)

    if not company_name.strip():
        st.warning("Enter a company name above before running the analysis.")
        return

    if st.button(
        f"Run risk analysis for {len(employees)} employees",
        type="primary",
        use_container_width=True,
    ):
        results = _run_analysis(employees, company_name.strip(), float(base_premium))
        if results:
            st.session_state["upload_results"] = results
            st.rerun()
        else:
            st.error("Analysis failed — no results returned from the API.")
