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
from dashboard.illustrations import HIPAA_PRIVACY, _render_illus as _illus
from dashboard.design_helpers import (
    page_header, section_header, apply_chart_theme, empty_state,
    inline_note, divider as nm_divider, ICON_DATA, ICON_CHART,
    card, render_card,
)

COLOR_MAP = {
    "Low":      "#5A8A00",
    "Moderate": "#B06000",
    "High":     "#C42020",
    "Critical": "#8B0000",
}
PLOT_BG  = "#FFFFFF"
GRID_CLR = "rgba(0,0,0,0.06)"
FONT_CLR = "#111111"
ACCENT   = "#9BC800"


def _chart_defaults():
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="Inter, system-ui, sans-serif"),
        margin=dict(l=0, r=20, t=24, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color=FONT_CLR),
            title=dict(font=dict(color=FONT_CLR)),
        ),
    )


def render():
    user = st.session_state["user"]
    company_id = user["company_id"]

    page_header(
        eyebrow="HR Workspace",
        title=f"{user['org']} — Workforce Health",
        subtitle=f"Signed in as {user['name']} · scope limited to your company",
    )

    # Collapsed help — doesn't compete with KPIs on load
    with st.expander("How this workspace works", expanded=False):
        st.markdown(
            "**HRS (Health Risk Score)** runs 0–100; lower is healthier. "
            "A lower company HRS supports better underwriting outcomes and lower renewal pressure.\n\n"
            "Use this workspace to monitor workforce risk, understand what is driving HRS, "
            "and estimate how health improvements could change your renewal terms.\n\n"
            "> **Currency note:** the sidebar selector updates displayed premium values only — "
            "model scores and risk bands are always computed in INR."
        )

    companies = list_companies()
    company = next((c for c in companies if c["company_id"] == company_id), None)
    if not company:
        st.error("Your company was not found in the database. Contact your Aegis administrator.")
        return

    with st.spinner("Loading health analytics..."):
        pred      = get_company_prediction(company_id)
        prem      = calculate_premium(float(company["base_premium"]), pred["mean_hrs"])
        employees = get_company_employees(company_id)
    emp_df = pd.DataFrame(employees)

    # ── KPI strip with delta context ──────────────────────────────────────────
    claims_inr = pred["mean_loss_ratio"] * prem["adjusted_premium"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Employees", pred["employee_count"],
        help="Total employees in your workforce health record.",
    )
    c2.metric(
        "Health risk score", f"{pred['mean_hrs']:.1f}",
        delta=f"{pred['mean_hrs'] - 50:+.1f} vs 50pt benchmark",
        delta_color="inverse" if pred["mean_hrs"] > 50 else "normal",
        help="Average Health Risk Score across your workforce. Lower is healthier. Industry benchmark is 50.",
    )
    c3.metric(
        "Current premium", fmt(prem["adjusted_premium"]),
        delta=f"{prem['adjustment_pct']:+.2f}% vs book rate",
        delta_color="inverse" if prem["adjustment_pct"] > 0 else "normal",
        help="Adjusted premium based on your current workforce HRS.",
    )
    c4.metric(
        "Annual claims est.", fmt(claims_inr),
        delta=f"Loss ratio {pred['mean_loss_ratio']:.3f}",
        delta_color="off",
        help="Estimated annual claims — loss ratio × adjusted premium.",
    )

    # Primary CTA — guide toward the ROI simulator when HRS is high
    if pred["mean_hrs"] > 50:
        _cta, _ = st.columns([2, 5])
        with _cta:
            if st.button("Model wellness impact →", type="primary", use_container_width=True):
                st.info("Switch to the **ROI Simulator** tab to model your renewal savings.")

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "Workforce Overview",
        "Risk Drivers",
        "ROI Simulator",
    ])

    # ── Tab 1: Workforce Overview ─────────────────────────────────────────────
    with tab1:
        _th, _ti = st.columns([3, 1])
        with _th:
            st.subheader("Risk band distribution")
            st.caption("Current workforce risk mix, core health metrics, and where claims pressure is concentrated.")
        with _ti:
            _illus(HIPAA_PRIVACY, "130px", height_px=140, align="right", opacity=0.85)

        dist_df = pd.DataFrame({
            "band": ["Low", "Moderate", "High", "Critical"],
            "pct":  [pred["low_risk_pct"], pred["moderate_risk_pct"],
                     pred["high_risk_pct"], pred["critical_risk_pct"]],
        })
        dist_df = dist_df[dist_df["pct"] > 0]
        if dist_df.empty:
            empty_state(
                title="No risk-band data yet",
                hint="Once your workforce is scored, the band mix will appear here.",
                icon_svg=ICON_DATA,
            )
        else:
            fig = px.pie(
                dist_df, names="band", values="pct", hole=0.58,
                color="band", color_discrete_map=COLOR_MAP,
            )
            apply_chart_theme(fig, height=320, show_legend=True, legend_horizontal=True)
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                annotations=[dict(
                    text=f"<b>{pred['mean_hrs']:.1f}</b><br><span style='font-size:10px'>HRS</span>",
                    x=0.5, y=0.5, font_size=18, showarrow=False,
                    font=dict(color="#111111", family="LetteraMonoLL, Space Mono, monospace"),
                )],
            )
            fig.update_traces(textinfo="percent+label", textfont_size=12, textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        nm_divider()
        section_header("Health Metrics", "Key workforce indicators")
        if emp_df.empty:
            empty_state(
                title="No employee-level data yet",
                hint="Individual telemetry and clinical fields appear here once the ingestion pipeline runs.",
                icon_svg=ICON_DATA,
            )
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Avg daily steps", f"{emp_df['avg_daily_steps'].mean():,.0f}",
                help="Average step count across your workforce. Low activity is a key HRS driver.",
            )
            m2.metric(
                "Avg resting HR", f"{emp_df['avg_resting_hr'].mean():.0f} bpm",
                help="Average resting heart rate. Elevated values can indicate cardiovascular risk.",
            )
            m3.metric(
                "Smokers", f"{emp_df['smoker'].sum() / len(emp_df) * 100:.1f}%",
                help="Percentage of employees who are smokers — one of the strongest HRS drivers.",
            )
            m4.metric(
                "Chronic conditions", f"{(emp_df['chronic_count'] > 0).sum() / len(emp_df) * 100:.1f}%",
                help="Percentage of employees with one or more chronic conditions.",
            )

            nm_divider()
            section_header("Cohort Lens", "Age vs predicted claims",
                           "Each point is one employee. Color shades denote chronic-condition count.")
            scatter = px.scatter(
                emp_df, x="age", y="loss_ratio", color="chronic_count",
                labels={"age": "Age", "loss_ratio": "Loss ratio",
                        "chronic_count": "Chronic conditions"},
                color_continuous_scale=["#5A8A00", "#B06000", "#C42020"],
            )
            apply_chart_theme(scatter, height=340, x_title="Age", y_title="Loss ratio")
            scatter.update_traces(marker=dict(size=6, opacity=0.75))
            st.plotly_chart(scatter, use_container_width=True)

    # ── Tab 2: Risk Drivers ───────────────────────────────────────────────────
    with tab2:
        section_header(
            "Explainability",
            "What's driving your risk score?",
            "SHAP importance — higher value = bigger contribution to HRS. Use these to prioritise wellness investments.",
        )

        drivers = pred.get("top_risk_drivers", [])
        if not drivers:
            empty_state(
                title="No risk-driver data yet",
                hint="Once SHAP explanations are generated for your workforce, the top drivers will surface here.",
                icon_svg=ICON_CHART,
            )
        else:
            driver_df = pd.DataFrame(drivers)
            fig = px.bar(
                driver_df.sort_values("importance"),
                x="importance", y="feature", orientation="h",
                color_discrete_sequence=[ACCENT],
                labels={"importance": "SHAP importance", "feature": ""},
            )
            apply_chart_theme(fig, height=380, show_legend=False, x_title="SHAP importance")
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        recs = {
            "avg_daily_steps":  ("Step-count challenge",          "Expected HRS drop: 5–12 pts",  8.5),
            "smoker":           ("Smoking cessation program",      "Expected HRS drop: 8–15 pts", 11.5),
            "avg_sleep_hours":  ("Sleep hygiene workshops",        "Expected HRS drop: 3–6 pts",   4.5),
            "hypertension":     ("BP screening camps",             "Expected HRS drop: 6–10 pts",  8.0),
            "diabetic":         ("Diabetes management program",    "Expected HRS drop: 10–18 pts",14.0),
            "bmi":              ("Nutrition counseling + gym",     "Expected HRS drop: 4–8 pts",   6.0),
            "visit_count":      ("Preventive care incentives",     "Expected HRS drop: 5–9 pts",   7.0),
            "avg_resting_hr":   ("Cardio fitness program",         "Expected HRS drop: 4–7 pts",   5.5),
            "health_composite": ("Comprehensive wellness bundle",  "Expected HRS drop: 10–20 pts",15.0),
            "activity_score":   ("Workplace activity program",     "Expected HRS drop: 6–10 pts",  8.0),
            "clinical_burden":  ("Case management for high-users", "Expected HRS drop: 8–14 pts", 11.0),
            "chronic_count":    ("Chronic disease management",     "Expected HRS drop: 10–18 pts",14.0),
        }
        matched = [
            (i + 1, d, recs[d["feature"]])
            for i, d in enumerate(drivers[:4])
            if d["feature"] in recs
        ]
        if matched:
            nm_divider(top=20, bottom=8)
            section_header("Action Plan", "AI recommendations",
                           "Top-priority interventions ranked by SHAP impact and modelled savings.")
            rec_cards = []
            for rank, d, (action, impact, hrs_mid) in matched:
                est = (hrs_mid / 100) * prem["adjusted_premium"] * 0.8
                rec_cards.append(card(
                    eyebrow=f"PRIORITY · {rank:02d}",
                    title=action,
                    body=impact,
                    stat=fmt(est),
                    stat_color="#5A7A00",
                    mono_footer="EST. ANNUAL SAVINGS",
                    variant="accent" if rank == 1 else "default",
                ))
            cols = st.columns(min(len(rec_cards), 2))
            for i, ch in enumerate(rec_cards):
                with cols[i % len(cols)]:
                    st.markdown(ch, unsafe_allow_html=True)

    # ── Tab 3: ROI Simulator ──────────────────────────────────────────────────
    with tab3:
        section_header(
            "Forecasting",
            "Wellness program ROI simulator",
            "Model the financial impact of reducing your workforce HRS before renewal.",
        )

        col1, col2 = st.columns(2)
        with col1:
            current = st.number_input(
                "Current HRS", value=float(pred["mean_hrs"]),
                min_value=0.0, max_value=100.0, step=0.5,
                help="Your current average Health Risk Score.",
            )
        with col2:
            improvement = st.slider(
                "HRS improvement target", 0, 40, 15,
                help="Points you expect a wellness program to reduce HRS by.",
            )
        projected = max(0.0, current - improvement)

        roi = calculate_wellness_roi(float(company["base_premium"]), current, projected)

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Current premium", fmt(roi["current_premium"]),
            roi["current_zone"].title(),
            help="Premium at your current HRS.",
        )
        m2.metric(
            "Projected premium", fmt(roi["projected_premium"]),
            roi["projected_zone"].title(),
            help="Estimated premium after the wellness-driven HRS improvement.",
        )
        m3.metric(
            "Annual savings", fmt(roi["annual_savings"]),
            f"{roi['hrs_improvement']:.1f} HRS points",
            help="Estimated annual premium reduction from the wellness program.",
        )

        code = active_code()
        rate = CURRENCIES[code]["rate"]
        sym  = CURRENCIES[code]["symbol"]
        cur_y  = roi["current_premium"]   * rate
        sav_y  = roi["annual_savings"]    * rate
        proj_y = roi["projected_premium"] * rate
        wf = go.Figure(go.Waterfall(
            x=["Current premium", "Wellness savings", "Projected premium"],
            y=[cur_y, -sav_y, proj_y],
            measure=["absolute", "relative", "total"],
            decreasing={"marker": {"color": "#22C55E"}},
            totals={"marker": {"color": "#9BC800"}},
            increasing={"marker": {"color": "#374151"}},
            connector={"line": {"color": GRID_CLR, "width": 1, "dash": "dot"}},
            textposition="outside",
            text=[f"{sym}{cur_y:,.0f}", f"-{sym}{sav_y:,.0f}", f"{sym}{proj_y:,.0f}"],
            textfont={"family": "LetteraMonoLL, Space Mono, monospace", "size": 12, "color": "#111111"},
        ))
        apply_chart_theme(wf, height=340, show_legend=False)
        wf.update_layout(
            title=dict(text=f"Premium savings breakdown ({code})",
                       font=dict(color="#111111", size=14)),
            yaxis=dict(gridcolor=GRID_CLR, tickprefix=sym, showgrid=True,
                       tickfont=dict(color="#111111", family="Inter, system-ui, sans-serif")),
        )
        st.plotly_chart(wf, use_container_width=True)

        if roi["annual_savings"] > 0:
            inline_note(
                f"A <b>{improvement}-point</b> HRS improvement could save "
                f"<b>{fmt(roi['annual_savings'])}</b> annually. "
                f"Use this projection when renewing with your insurer.",
                level="ok",
            )
        else:
            inline_note(
                "Adjust the improvement target above to see potential savings.",
                level="info",
            )
