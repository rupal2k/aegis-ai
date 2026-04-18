"""Underwriter dashboard — see all companies ranked by risk."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.api_client import (
    list_companies, get_company_prediction, calculate_premium,
)
from dashboard.pdf_report import generate_underwriting_report
from dashboard.currency import fmt, fmt_crore, active_code, CURRENCIES
import dashboard.upload_view as upload_view

# Apple-style neutral palette
COLOR_MAP = {
    "Low":      "#34c759",
    "Moderate": "#ff9f0a",
    "High":     "#ff3b30",
    "Critical": "#8e0000",
}
PLOT_BG   = "#1c1c1e"
GRID_CLR  = "#3a3a3c"
FONT_CLR  = "#f5f5f7"
ACCENT    = "#0a84ff"


def _chart_defaults():
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="system-ui, -apple-system, sans-serif"),
        margin=dict(l=0, r=20, t=24, b=40),
    )


def render():
    user = st.session_state["user"]
    st.title("Underwriter Console")
    st.caption(f"Signed in as {user['name']} — {user['org']}")

    with st.spinner("Loading portfolio..."):
        companies = list_companies()
        rows = []
        for c in companies:
            try:
                pred = get_company_prediction(c["company_id"])
                prem = calculate_premium(float(c["base_premium"]), pred["mean_hrs"])
                rows.append({
                    "company_id":     c["company_id"],
                    "company_name":   c["company_name"],
                    "industry":       c["industry"],
                    "employees":      pred["employee_count"],
                    "mean_hrs":       pred["mean_hrs"],
                    "risk_band":      pred["risk_band"],
                    "base_premium":   c["base_premium"],
                    "adjusted":       prem["adjusted_premium"],
                    "adjustment_pct": prem["adjustment_pct"],
                    "zone":           prem["zone"],
                })
            except Exception as e:
                st.warning(f"Skipping {c['company_name']}: {e}")

    df = pd.DataFrame(rows)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total companies",   len(df))
    col2.metric("Total employees",   int(df["employees"].sum()))
    col3.metric("Average HRS",       f"{df['mean_hrs'].mean():.1f}")
    col4.metric("Portfolio premium", fmt_crore(df["adjusted"].sum()))

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Portfolio overview", "Company deep dive", "Risk distribution", "Upload dataset",
    ])

    with tab1:
        st.subheader("All companies — ranked by risk")

        fig = px.bar(
            df.sort_values("mean_hrs"),
            x="mean_hrs", y="company_name",
            color="risk_band", color_discrete_map=COLOR_MAP,
            orientation="h",
            labels={"mean_hrs": "Health Risk Score", "company_name": ""},
            height=580,
        )
        fig.update_layout(
            **_chart_defaults(),
            showlegend=True,
            xaxis=dict(range=[0, 100], gridcolor=GRID_CLR, zeroline=False),
            yaxis=dict(gridcolor=GRID_CLR),
            legend_title_text="Risk band",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Ranked portfolio")
        code = active_code()
        sym  = CURRENCIES[code]["symbol"]
        display_df = df.copy()
        display_df["base_premium_fx"] = display_df["base_premium"].apply(
            lambda v: float(v) * CURRENCIES[code]["rate"])
        display_df["adjusted_fx"] = display_df["adjusted"].apply(
            lambda v: v * CURRENCIES[code]["rate"])
        display_df = display_df[[
            "company_name", "industry", "employees", "mean_hrs",
            "risk_band", "base_premium_fx", "adjusted_fx", "adjustment_pct", "zone",
        ]].rename(columns={
            "company_name":    "Company",
            "industry":        "Industry",
            "employees":       "Employees",
            "mean_hrs":        "HRS",
            "risk_band":       "Band",
            "base_premium_fx": f"Base ({code})",
            "adjusted_fx":     f"Adjusted ({code})",
            "adjustment_pct":  "Change %",
            "zone":            "Zone",
        }).sort_values("HRS", ascending=False)

        st.dataframe(
            display_df,
            use_container_width=True, hide_index=True,
            column_config={
                "HRS":              st.column_config.ProgressColumn(
                                        "HRS", min_value=0, max_value=100, format="%.1f"),
                f"Base ({code})":   st.column_config.NumberColumn(format=f"{sym}%,.0f"),
                f"Adjusted ({code})": st.column_config.NumberColumn(format=f"{sym}%,.0f"),
                "Change %":         st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )

    with tab2:
        st.subheader("Company deep dive")

        company_choice = st.selectbox(
            "Select a company",
            options=df["company_id"].tolist(),
            format_func=lambda c: df[df["company_id"] == c]["company_name"].iloc[0],
        )
        row  = df[df["company_id"] == company_choice].iloc[0]
        pred = get_company_prediction(company_choice)
        prem = calculate_premium(float(row["base_premium"]), pred["mean_hrs"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Mean HRS",     f"{pred['mean_hrs']:.1f}", pred["risk_band"])
        c2.metric("Loss ratio",   f"{pred['mean_loss_ratio']:.3f}")
        delta_inr = prem["adjusted_premium"] - float(row["base_premium"])
        c3.metric("Premium adj.", f"{prem['adjustment_pct']:+.2f}%",
                  fmt(delta_inr))

        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pred["mean_hrs"],
            number={"font": {"color": FONT_CLR, "size": 40}},
            gauge={
                "axis":  {"range": [0, 100], "tickcolor": FONT_CLR},
                "bar":   {"color": ACCENT},
                "bgcolor": PLOT_BG,
                "steps": [
                    {"range": [0,  30],  "color": "#1a3a2a"},
                    {"range": [30, 60],  "color": "#3a2e0a"},
                    {"range": [60, 80],  "color": "#3a1a18"},
                    {"range": [80, 100], "color": "#2e0d0c"},
                ],
            },
            title={"text": "Health Risk Score", "font": {"color": FONT_CLR, "size": 14}},
        ))
        gauge.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=40, b=10),
            paper_bgcolor=PLOT_BG,
        )
        st.plotly_chart(gauge, use_container_width=True)

        st.subheader("Risk breakdown")
        dist_df = pd.DataFrame({
            "band": ["Low", "Moderate", "High", "Critical"],
            "pct":  [pred["low_risk_pct"], pred["moderate_risk_pct"],
                     pred["high_risk_pct"], pred["critical_risk_pct"]],
        })
        dist_fig = px.bar(
            dist_df, x="pct", y="band", orientation="h",
            color="band", color_discrete_map=COLOR_MAP,
            labels={"pct": "% of workforce", "band": ""},
        )
        dist_fig.update_layout(
            **_chart_defaults(),
            showlegend=False, height=200,
            xaxis=dict(gridcolor=GRID_CLR, zeroline=False),
            yaxis=dict(gridcolor=GRID_CLR),
        )
        st.plotly_chart(dist_fig, use_container_width=True)

        st.subheader("Top risk drivers")
        if pred.get("top_risk_drivers"):
            for i, d in enumerate(pred["top_risk_drivers"][:5], 1):
                pct = (d["importance"] / pred["top_risk_drivers"][0]["importance"]) * 100
                st.progress(
                    pct / 100,
                    text=f"**{i}. {d['feature']}** — importance {d['importance']:.3f}",
                )

        st.divider()
        st.subheader("Underwriting decision")
        st.info(
            f"**Recommendation:** {prem['recommendation']}  \n"
            f"Adjusted premium: **{fmt(prem['adjusted_premium'])}** "
            f"({prem['adjustment_pct']:+.2f}% vs base {fmt(float(row['base_premium']))})"
        )

        pdf_bytes = generate_underwriting_report(
            {**pred, "company_name": row["company_name"], "company_id": row["company_id"]},
            prem,
            currency=active_code(),
        )
        st.download_button(
            "Download underwriting report (PDF)",
            data=pdf_bytes,
            file_name=f"aegis_report_{company_choice}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with tab3:
        st.subheader("Portfolio risk distribution")
        hist = px.histogram(
            df, x="mean_hrs", nbins=20,
            labels={"mean_hrs": "Company Health Risk Score"},
            color_discrete_sequence=[ACCENT],
        )
        hist.update_layout(**_chart_defaults(), height=320,
                           xaxis=dict(gridcolor=GRID_CLR),
                           yaxis=dict(gridcolor=GRID_CLR))
        st.plotly_chart(hist, use_container_width=True)

        st.subheader("Industry risk profile")
        ind = df.groupby("industry").agg(
            avg_hrs=("mean_hrs", "mean"),
            employees=("employees", "sum"),
            companies=("company_id", "count"),
        ).reset_index().sort_values("avg_hrs", ascending=False)
        st.dataframe(
            ind, use_container_width=True, hide_index=True,
            column_config={
                "avg_hrs": st.column_config.ProgressColumn(
                    "Avg HRS", min_value=0, max_value=100, format="%.1f"),
            },
        )

    with tab4:
        upload_view.render_tab()
