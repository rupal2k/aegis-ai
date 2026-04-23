"""HR Manager dashboard — single company, wellness ROI projection."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.api_client import (
    list_companies, get_company_prediction,
    get_company_employees, calculate_premium,
    calculate_wellness_roi,
)
from dashboard.currency import fmt, active_code, CURRENCIES

COLOR_MAP = {
    "Low":      "#22C55E",
    "Moderate": "#F59E0B",
    "High":     "#EF4444",
    "Critical": "#991B1B",
}
PLOT_BG  = "#FFFFFF"
GRID_CLR = "rgba(0,0,0,0.06)"
FONT_CLR = "#111111"
ACCENT   = "#9BC800"


def _chart_defaults():
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="system-ui, -apple-system, sans-serif"),
        margin=dict(l=0, r=20, t=24, b=40),
    )


def render():
    user = st.session_state["user"]
    company_id = user["company_id"]

    st.title(f"{user['org']} — Workforce Health Dashboard")
    st.caption(f"Signed in as {user['name']}")

    companies = list_companies()
    company = next((c for c in companies if c["company_id"] == company_id), None)
    if not company:
        st.error("Your company was not found in the database.")
        return

    with st.spinner("Loading health analytics..."):
        pred      = get_company_prediction(company_id)
        prem      = calculate_premium(float(company["base_premium"]), pred["mean_hrs"])
        employees = get_company_employees(company_id)
    emp_df = pd.DataFrame(employees)

    c1, c2, c3, c4 = st.columns(4)
    claims_inr = pred["mean_loss_ratio"] * prem["adjusted_premium"]
    c1.metric("Employees",          pred["employee_count"])
    c2.metric("Health risk score",  f"{pred['mean_hrs']:.1f}", pred["risk_band"])
    c3.metric("Current premium",    fmt(prem["adjusted_premium"]),
              f"{prem['adjustment_pct']:+.2f}% vs book rate")
    c4.metric("Annual claims est.", fmt(claims_inr))

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Workforce overview", "Top risk drivers", "Wellness ROI simulator"])

    with tab1:
        st.subheader("Risk band distribution")
        dist_df = pd.DataFrame({
            "band": ["Low", "Moderate", "High", "Critical"],
            "pct":  [pred["low_risk_pct"], pred["moderate_risk_pct"],
                     pred["high_risk_pct"], pred["critical_risk_pct"]],
        })
        fig = px.pie(
            dist_df, names="band", values="pct", hole=0.55,
            color="band", color_discrete_map=COLOR_MAP,
        )
        fig.update_layout(
            **_chart_defaults(),
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        fig.update_traces(textinfo="percent+label", textfont_size=13)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Key workforce metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg daily steps",    f"{emp_df['avg_daily_steps'].mean():,.0f}")
        m2.metric("Avg resting HR",     f"{emp_df['avg_resting_hr'].mean():.0f} bpm")
        m3.metric("Smokers",            f"{emp_df['smoker'].sum() / len(emp_df) * 100:.1f}%")
        m4.metric("Chronic conditions", f"{(emp_df['chronic_count'] > 0).sum() / len(emp_df) * 100:.1f}%")

        st.subheader("Age vs claims")
        scatter = px.scatter(
            emp_df, x="age", y="loss_ratio", color="chronic_count",
            labels={"age": "Age", "loss_ratio": "Loss ratio",
                    "chronic_count": "Chronic conditions"},
            color_continuous_scale=["#22C55E", "#F59E0B", "#EF4444"],
        )
        scatter.update_layout(**_chart_defaults(), height=340)
        scatter.update_traces(marker=dict(size=6, opacity=0.7))
        st.plotly_chart(scatter, use_container_width=True)

    with tab2:
        st.subheader("What's driving your risk score?")
        st.caption("SHAP importance — higher = bigger contribution to risk")

        drivers = pred.get("top_risk_drivers", [])
        if drivers:
            driver_df = pd.DataFrame(drivers)
            fig = px.bar(
                driver_df.sort_values("importance"),
                x="importance", y="feature", orientation="h",
                color_discrete_sequence=[ACCENT],
                labels={"importance": "Importance", "feature": ""},
            )
            fig.update_layout(**_chart_defaults(), height=380)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recommended interventions")
        recs = {
            "avg_daily_steps":  ("Step-count challenge",           "Expected HRS drop: 5-12 pts"),
            "smoker":           ("Smoking cessation program",       "Expected HRS drop: 8-15 pts"),
            "avg_sleep_hours":  ("Sleep hygiene workshops",         "Expected HRS drop: 3-6 pts"),
            "hypertension":     ("BP screening camps",              "Expected HRS drop: 6-10 pts"),
            "diabetic":         ("Diabetes management program",     "Expected HRS drop: 10-18 pts"),
            "bmi":              ("Nutrition counseling + gym",      "Expected HRS drop: 4-8 pts"),
            "visit_count":      ("Preventive care incentives",      "Expected HRS drop: 5-9 pts"),
            "avg_resting_hr":   ("Cardio fitness program",          "Expected HRS drop: 4-7 pts"),
            "health_composite": ("Comprehensive wellness bundle",   "Expected HRS drop: 10-20 pts"),
            "activity_score":   ("Workplace activity program",      "Expected HRS drop: 6-10 pts"),
            "clinical_burden":  ("Case management for high-users",  "Expected HRS drop: 8-14 pts"),
            "chronic_count":    ("Chronic disease management",      "Expected HRS drop: 10-18 pts"),
        }
        for d in drivers[:3]:
            rec = recs.get(d["feature"])
            if rec:
                with st.container(border=True):
                    st.markdown(f"**{rec[0]}** — {rec[1]}")
                    st.caption(f"Driver: `{d['feature']}` (importance {d['importance']:.3f})")

    with tab3:
        st.subheader("Wellness program ROI simulator")
        st.caption("Model the financial impact of reducing your workforce HRS.")

        col1, col2 = st.columns(2)
        with col1:
            current = st.number_input(
                "Current HRS", value=float(pred["mean_hrs"]),
                min_value=0.0, max_value=100.0, step=0.5,
            )
        with col2:
            improvement = st.slider(
                "HRS improvement target", 0, 40, 15,
                help="Points you expect the program to reduce HRS by",
            )
        projected = max(0.0, current - improvement)

        roi = calculate_wellness_roi(float(company["base_premium"]), current, projected)

        m1, m2, m3 = st.columns(3)
        m1.metric("Current premium",   fmt(roi["current_premium"]),
                  roi["current_zone"].title())
        m2.metric("Projected premium", fmt(roi["projected_premium"]),
                  roi["projected_zone"].title())
        m3.metric("Annual savings",    fmt(roi["annual_savings"]),
                  f"{roi['hrs_improvement']:.1f} HRS points")

        code = active_code()
        rate = CURRENCIES[code]["rate"]
        sym  = CURRENCIES[code]["symbol"]
        wf = go.Figure(go.Waterfall(
            x=["Current premium", "Wellness savings", "Projected premium"],
            y=[roi["current_premium"] * rate,
               -roi["annual_savings"] * rate,
               roi["projected_premium"] * rate],
            measure=["absolute", "relative", "total"],
            decreasing={"marker": {"color": "#22C55E"}},
            increasing={"marker": {"color": "#EF4444"}},
            totals={"marker":    {"color": ACCENT}},
            connector={"line": {"color": GRID_CLR}},
        ))
        wf.update_layout(
            **_chart_defaults(),
            height=320,
            title=dict(text=f"Premium savings breakdown ({code})", font=dict(size=14)),
            yaxis=dict(gridcolor=GRID_CLR, tickprefix=sym),
        )
        st.plotly_chart(wf, use_container_width=True)

        if roi["annual_savings"] > 0:
            st.success(
                f"A {improvement}-point HRS improvement could save "
                f"**{fmt(roi['annual_savings'])}** annually. "
                f"Use this projection when renewing with your insurer."
            )
