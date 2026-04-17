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


def render():
    user = st.session_state["user"]
    company_id = user["company_id"]

    st.title(f"{user['org']} — Workforce Health Dashboard")
    st.caption(f"Signed in as {user['name']}")

    companies = list_companies()
    company = next((c for c in companies if c["company_id"]==company_id), None)
    if not company:
        st.error("Your company was not found in the database.")
        return

    with st.spinner("Loading health analytics..."):
        pred = get_company_prediction(company_id)
        prem = calculate_premium(float(company["base_premium"]), pred["mean_hrs"])
        employees = get_company_employees(company_id)
    emp_df = pd.DataFrame(employees)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Employees",         pred["employee_count"])
    c2.metric("Health risk score", f"{pred['mean_hrs']:.1f}", pred["risk_band"])
    c3.metric("Current premium",   f"Rs. {prem['adjusted_premium']:,.0f}",
              f"{prem['adjustment_pct']:+.2f}% vs book rate")
    c4.metric("Annual claims est.", f"Rs. {pred['mean_loss_ratio']*prem['adjusted_premium']/1e5:.1f} L")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Workforce overview",
                                 "Top risk drivers",
                                 "Wellness ROI simulator"])

    with tab1:
        st.subheader("Risk band distribution")
        dist_df = pd.DataFrame({
            "band":["Low","Moderate","High","Critical"],
            "pct":[pred["low_risk_pct"], pred["moderate_risk_pct"],
                   pred["high_risk_pct"], pred["critical_risk_pct"]],
        })
        fig = px.pie(dist_df, names="band", values="pct", hole=0.55,
                     color="band",
                     color_discrete_map={"Low":"#1D9E75","Moderate":"#EF9F27",
                                         "High":"#E24B4A","Critical":"#791F1F"})
        fig.update_layout(height=340, margin=dict(l=0,r=0,t=20,b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Key workforce metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg daily steps",   f"{emp_df['avg_daily_steps'].mean():,.0f}")
        m2.metric("Avg resting HR",    f"{emp_df['avg_resting_hr'].mean():.0f} bpm")
        m3.metric("Smokers",           f"{(emp_df['smoker'].sum()/len(emp_df)*100):.1f}%")
        m4.metric("Chronic conditions",f"{(emp_df['chronic_count']>0).sum()/len(emp_df)*100:.1f}%")

        st.subheader("Age vs claims scatter")
        scatter = px.scatter(emp_df, x="age", y="loss_ratio", color="chronic_count",
                             labels={"age":"Age","loss_ratio":"Loss ratio",
                                     "chronic_count":"Chronic conditions"},
                             color_continuous_scale=["#1D9E75","#EF9F27","#E24B4A"])
        scatter.update_layout(height=360, margin=dict(l=0,r=0,t=20,b=40))
        st.plotly_chart(scatter, use_container_width=True)

    with tab2:
        st.subheader("What's driving your company's risk score?")
        st.caption("SHAP importance — higher = bigger contribution to risk")

        drivers = pred.get("top_risk_drivers", [])
        if drivers:
            driver_df = pd.DataFrame(drivers)
            fig = px.bar(driver_df.sort_values("importance"),
                         x="importance", y="feature", orientation="h",
                         color_discrete_sequence=["#534AB7"])
            fig.update_layout(height=400, margin=dict(l=0,r=0,t=20,b=40),
                              xaxis_title="Importance", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recommended wellness interventions")
        recs = {
            "avg_daily_steps":   ("Launch step-count challenge",     "Expected HRS drop: 5–12 points"),
            "smoker":            ("Smoking cessation program",       "Expected HRS drop: 8–15 points"),
            "avg_sleep_hours":   ("Sleep hygiene workshops",         "Expected HRS drop: 3–6 points"),
            "hypertension":      ("BP screening camps quarterly",    "Expected HRS drop: 6–10 points"),
            "diabetic":          ("Diabetes management program",     "Expected HRS drop: 10–18 points"),
            "bmi":               ("Nutrition counseling + subsidized gym","Expected HRS drop: 4–8 points"),
            "visit_count":       ("Preventive care incentives",      "Expected HRS drop: 5–9 points"),
            "avg_resting_hr":    ("Cardio fitness program",          "Expected HRS drop: 4–7 points"),
            "health_composite":  ("Comprehensive wellness bundle",   "Expected HRS drop: 10–20 points"),
            "activity_score":    ("Workplace activity program",      "Expected HRS drop: 6–10 points"),
        }
        for d in drivers[:3]:
            rec = recs.get(d["feature"])
            if rec:
                with st.container(border=True):
                    st.markdown(f"**{rec[0]}** — {rec[1]}")
                    st.caption(f"Top driver: `{d['feature']}` (importance {d['importance']:.3f})")

    with tab3:
        st.subheader("Wellness program ROI simulator")
        st.caption("Model the financial impact of reducing your workforce's HRS.")

        col1, col2 = st.columns(2)
        with col1:
            current = st.number_input("Current HRS",
                                       value=float(pred["mean_hrs"]),
                                       min_value=0.0, max_value=100.0, step=0.5)
        with col2:
            improvement = st.slider("HRS improvement target", 0, 40, 15,
                                     help="How many points you expect your program to reduce HRS by")
        projected = max(0.0, current - improvement)

        roi = calculate_wellness_roi(float(company["base_premium"]),
                                      current, projected)

        m1, m2, m3 = st.columns(3)
        m1.metric("Current premium",
                  f"Rs. {roi['current_premium']:,.0f}",
                  roi["current_zone"].title())
        m2.metric("Projected premium",
                  f"Rs. {roi['projected_premium']:,.0f}",
                  roi["projected_zone"].title())
        m3.metric("Annual savings",
                  f"Rs. {roi['annual_savings']:,.0f}",
                  f"{roi['hrs_improvement']:.1f} HRS points")

        wf = go.Figure(go.Waterfall(
            x=["Current premium", "Wellness impact", "Projected premium"],
            y=[roi["current_premium"], -roi["annual_savings"], roi["projected_premium"]],
            measure=["absolute", "relative", "total"],
            decreasing={"marker":{"color":"#1D9E75"}},
            totals={"marker":{"color":"#185FA5"}},
        ))
        wf.update_layout(height=340, margin=dict(l=0,r=0,t=20,b=40),
                          title="Premium savings breakdown")
        st.plotly_chart(wf, use_container_width=True)

        if roi["annual_savings"] > 0:
            st.success(
                f"**Negotiation insight:** a {improvement}-point HRS improvement could "
                f"save Rs. {roi['annual_savings']:,.0f} annually. Use this projection "
                f"when renewing with your insurer."
            )
