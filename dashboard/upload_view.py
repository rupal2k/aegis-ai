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
from dashboard.illustrations import EMPLOYEE_HEALTH, _render_illus as _illus
from dashboard.design_helpers import (
    section_header, apply_chart_theme, empty_state, inline_note,
    divider as nm_divider, ICON_UPLOAD,
)
from dashboard.data_normalizer import detect_format, to_feature_records

PLOT_BG  = "#111c30"
GRID_CLR = "rgba(255,255,255,0.05)"
FONT_CLR = "#94a3b8"
ACCENT   = "#84cc16"

COLOR_MAP = {
    "Low":      "#22c55e",
    "Moderate": "#eab308",
    "High":     "#f97316",
    "Critical": "#ef4444",
}

FORMAT_LABELS = {
    "roster":   "Employee roster",
    "lab":      "LAB markers (long-format)",
    "activity": "Activity / wellness records",
    "unknown":  "Unrecognized",
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


def _run_analysis(records: list[dict], company_name: str, base_premium: float) -> dict:
    """`records` is the output of `to_feature_records` — each item has
    `employee_id` and `_features` (a fully-defaulted feature dict)."""
    results: list[dict] = []
    total = len(records)
    bar = st.progress(0, text=f"Scoring employees... 0 / {total}")

    for i, rec in enumerate(records):
        features = rec["_features"]
        try:
            pred = predict_employee(features)
            results.append({
                "employee_id": rec["employee_id"],
                "age":         features["age"],
                "gender":      features["gender"],
                "bmi":         features["bmi"],
                "smoker":      features["smoker"],
                "diabetic":    features["diabetic"],
                "hypertension":features["hypertension"],
                "job_category":features["job_category"],
                "hrs":         pred["health_risk_score"],
                "loss_ratio":  pred["predicted_loss_ratio"],
                "risk_band":   pred["risk_band"],
            })
        except Exception as exc:
            st.warning(f"Skipped {rec['employee_id']}: {exc}")

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
    inline_note(f"Analysis complete — <b>{res['company_name']}</b>", level="ok")

    code = active_code()
    rate = CURRENCIES[code]["rate"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Employees", res["employee_count"],
        help="Total employees scored in this analysis.",
    )
    c2.metric(
        "Mean HRS", f"{res['mean_hrs']:.1f}", res["risk_band"],
        delta_color="inverse",
        help="Average Health Risk Score — lower is healthier. Bands: Low <30 · Moderate 30–59 · High 60–79 · Critical 80+.",
    )
    c3.metric(
        "Adjusted premium", fmt(res["premium"]["adjusted_premium"] * rate),
        help="Estimated premium based on your workforce HRS in the selected currency.",
    )
    c4.metric(
        "Premium change", f"{res['premium']['adjustment_pct']:+.2f}%",
        delta_color="inverse" if res["premium"]["adjustment_pct"] > 0 else "normal",
        help="Premium change vs the base premium you entered.",
    )

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
        )
        apply_chart_theme(
            dist_fig, height=220, show_legend=False,
            x_title="% of workforce",
        )
        st.plotly_chart(dist_fig, use_container_width=True)

    with col_gauge:
        st.subheader("Health Risk Score")
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=res["mean_hrs"],
            number={"font": {"color": FONT_CLR, "size": 36}},
            gauge={
                "axis":    {"range": [0, 100], "tickcolor": "#333333", "tickfont": {"color": "#333333"}},
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
            template={},
            height=230,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=FONT_CLR, size=12),
        )
        st.plotly_chart(gauge, use_container_width=True)

    st.info(
        f"**Recommendation:** {res['premium']['recommendation']}  \n"
        f"Adjusted premium: **{fmt(res['premium']['adjusted_premium'] * rate)}** "
        f"({res['premium']['adjustment_pct']:+.2f}% vs base {fmt(res['base_premium'] * rate)})"
    )

    st.subheader("Employee risk scores")

    # Filter pills
    _PILL_COLORS = {
        "All":      ("#94a3b8", "#162036"),
        "High":     ("#0d1424", "#f97316"),
        "Moderate": ("#0d1424", "#eab308"),
        "Low":      ("#0d1424", "#22c55e"),
    }
    filter_opts = list(_PILL_COLORS.keys())
    if "upload_risk_filter" not in st.session_state:
        st.session_state["upload_risk_filter"] = "All"

    cols = st.columns(len(filter_opts))
    for col, opt in zip(cols, filter_opts):
        txt_c, bg_c = _PILL_COLORS[opt]
        active = st.session_state["upload_risk_filter"] == opt
        border = f"2px solid {bg_c}" if active else "2px solid transparent"
        opacity = "1" if active else "0.45"
        with col:
            st.markdown(
                f'<div style="text-align:center;padding:5px 0 6px;">'
                f'<span style="display:inline-block;padding:4px 14px;border-radius:20px;'
                f'background:{bg_c};color:{txt_c};font-size:11px;font-weight:600;'
                f'letter-spacing:0.06em;border:{border};opacity:{opacity};'
                f'font-family:Inter,system-ui,sans-serif;">{opt.upper()}</span></div>',
                unsafe_allow_html=True,
            )
            if st.button(opt, key=f"pill_{opt}", use_container_width=True,
                         help=f"Show {opt} risk employees"):
                st.session_state["upload_risk_filter"] = opt
                st.rerun()

    active_filter = st.session_state["upload_risk_filter"]
    raw_df = res["df"][[
        "employee_id", "age", "gender", "bmi", "smoker",
        "diabetic", "hypertension", "job_category", "hrs", "risk_band",
    ]]
    if active_filter != "All":
        raw_df = raw_df[raw_df["risk_band"] == active_filter]

    display_df = raw_df.rename(columns={
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

    if display_df.empty:
        st.info(f"No {active_filter.lower()} risk employees in this dataset.")
    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "HRS": st.column_config.ProgressColumn(
                    "HRS", min_value=0, max_value=100, format="%.1f",
                    help="Individual Health Risk Score — 0 (healthiest) to 100 (critical risk)"),
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
    section_header(
        "Ad-hoc Scoring",
        "Analyse your own workforce data",
        "Upload a CSV of employee records for instant HRS scoring using the production model. "
        "No data is stored on the server. When wearable data is absent, national-average telemetry defaults are applied.",
    )
    with st.expander("Accepted CSV formats", expanded=False):
        st.markdown(
            "The uploader **auto-detects** the dataset shape and normalizes it before scoring. "
            "Three formats are supported:\n\n"
            "**1. Employee roster (wide)** — `employee_id, age, gender, bmi, smoker, diabetic, hypertension, job_category`. "
            "Best fidelity — all features come from your data.\n\n"
            "**2. LAB markers (long-format)** — `unique_id, gender, marker_code, value, status, risk_level, ...`. "
            "Marker codes are mapped to health domains (heart, diabetes, kidney, liver, iron, thyroid, bone, vitamin, inflammation). "
            "Demographics not provided in the file are filled with population medians from the training dataset.\n\n"
            "**3. Activity / wellness records (wide)** — `user_id, year, Bone Health, Diabetes, Heart Health, "
            "Inflammation, Iron, Kidney Health, Liver Health, Thyroid Health, Vitamin Deficiency, "
            "step_count, total_active_minutes, ...`. Domain status maps directly to lab flags; "
            "step count and active minutes feed wearable telemetry features.\n\n"
            "_Tip: download the roster template below for the highest-fidelity scoring._"
        )

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
        "Upload CSV — roster, LAB markers, or activity records",
        type=["csv"],
        help="Auto-detects employee roster, LAB long-format, or activity wide-format. "
             "Missing demographics are filled with training-set medians.",
    )

    if not uploaded:
        _eu, _ei = st.columns([1, 1])
        with _eu:
            empty_state(
                title="Upload a CSV to begin",
                hint="Drop an employee roster above. The same underwriting model that powers the portfolio "
                     "scores each row in seconds. Nothing is persisted server-side.",
                icon_svg=ICON_UPLOAD,
                cta="Need the format? Download the template above.",
            )
        with _ei:
            _illus(EMPLOYEE_HEALTH, "220px", height_px=230, align="center", opacity=0.88)
        return

    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as exc:
        inline_note(f"Could not read CSV: {exc}", level="error")
        return

    fmt = detect_format(df_raw)
    if fmt == "unknown":
        inline_note(
            "Could not recognize this CSV format. Expected one of: "
            "<b>Employee roster</b> (employee_id+age+bmi), "
            "<b>LAB markers</b> (unique_id+marker_code+value), or "
            "<b>Activity records</b> (user_id+step_count+health domains).",
            level="error",
        )
        return

    try:
        records, report = to_feature_records(df_raw, fmt)
    except Exception as exc:
        inline_note(f"Normalization failed: {exc}", level="error")
        return

    if not records:
        inline_note("No usable rows after normalization — please check the file.", level="warning")
        return

    # Format-detection summary banner
    inline_note(
        f"Detected <b>{FORMAT_LABELS[fmt]}</b> · {len(records):,} unique subjects ready to score.",
        level="ok",
    )
    if report["filled_with_defaults"]:
        filled = ", ".join(f"<code>{c}</code>" for c in report["filled_with_defaults"])
        inline_note(
            f"Filled missing fields from training-set medians: {filled}. "
            "Predictions reflect typical-population demographics for those fields.",
            level="info",
        )

    st.markdown("**Preview (first 5 rows of upload):**")
    st.dataframe(df_raw.head(5), use_container_width=True, hide_index=True)

    if not company_name.strip():
        inline_note("Enter a company name above before running the analysis.", level="warning")
        return

    if st.button(
        f"Run risk analysis for {len(records):,} subjects",
        type="primary",
        use_container_width=True,
    ):
        results = _run_analysis(records, company_name.strip(), float(base_premium))
        if results:
            st.session_state["upload_results"] = results
            st.rerun()
        else:
            inline_note("Analysis failed — no results returned from the API.", level="error")
