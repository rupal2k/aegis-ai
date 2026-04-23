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
from dashboard.illustrations import GROUP_INSURANCE, _svg_img as _illus

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


def _render_help_banner():
    """Render a compact explainer for HRS and underwriter tab usage."""
    st.markdown(
        """
<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);border-radius:12px;
            padding:16px 18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.1em;
                margin-bottom:8px;font-weight:500;">Quick Guide</div>
    <div style="font-size:13px;color:#444;line-height:1.55;margin-bottom:10px;">
        <span style="color:#111;font-weight:600;">HRS</span> means
        <span style="color:#111;font-weight:600;">Health Risk Score</span>.
        It runs from <span style="color:#111;font-weight:600;">0-100</span>, where lower is healthier.
        Aegis groups scores into <span style="color:#111;font-weight:600;">Low (0-29)</span>,
        <span style="color:#111;font-weight:600;">Moderate (30-59)</span>,
        <span style="color:#111;font-weight:600;">High (60-79)</span>, and
        <span style="color:#111;font-weight:600;">Critical (80-100)</span>.
    </div>
    <div style="font-size:12px;color:#666;line-height:1.65;">
        Use this workspace to move from portfolio screening into account review, pricing analysis,
        and one-off CSV scoring without changing stored company data.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_alerts(df):
    """Render a NullMask-styled alerts panel driven by real portfolio data."""
    LEVEL_COLORS = {
        "high": "#D63030",
        "med":  "#D07000",
        "info": "#0070C8",
        "ok":   "#5A8A00",
    }
    alerts = []
    critical = df[df["risk_band"] == "Critical"]
    high     = df[df["risk_band"] == "High"]
    big_adj  = df[df["adjustment_pct"] > 10]
    low      = df[df["risk_band"] == "Low"]
    avg_hrs  = df["mean_hrs"].mean()

    if len(critical) > 0:
        names  = ", ".join(critical["company_name"].head(2).tolist())
        suffix = f" +{len(critical) - 2} more" if len(critical) > 2 else ""
        alerts.append(("high", f"Critical risk: {names}{suffix} — immediate underwriting review required"))
    if len(high) > 1:
        alerts.append(("med", f"{len(high)} companies in High risk band — elevated claims exposure across portfolio"))
    if len(big_adj) > 0:
        alerts.append(("info", f"{len(big_adj)} companies flagged for >10% premium adjustment at next renewal"))
    if avg_hrs > 50:
        alerts.append(("info", f"Portfolio avg HRS {avg_hrs:.1f} — exceeds 50-point industry benchmark"))
    if len(low) > 0:
        alerts.append(("ok", f"{len(low)} companies in Low risk band — favourable renewal terms available"))

    rows_html = ""
    for level, text in alerts[:4]:
        col = LEVEL_COLORS[level]
        rows_html += (
            f'<div style="display:flex;align-items:flex-start;gap:10px;'
            f'padding:10px 0;border-bottom:1px solid rgba(0,0,0,0.06);">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{col};'
            f'flex-shrink:0;margin-top:5px;display:inline-block;"></span>'
            f'<div style="flex:1;font-size:13px;color:#444;line-height:1.4;">{text}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);'
        f'border-radius:12px;padding:18px 22px;margin-bottom:8px;">'
        f'<div style="font-size:11px;color:#999;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px;font-weight:500;">Alerts</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _chart_defaults():
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="Inter, system-ui, sans-serif"),
        margin=dict(l=0, r=20, t=24, b=40),
    )


def render():
    user = st.session_state["user"]
    st.title("Underwriter Console")
    st.caption(f"Signed in as {user['name']} — {user['org']}")
    _render_help_banner()

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
        _h1, _h2 = st.columns([3, 1])
        with _h1:
            st.subheader("All companies — ranked by risk")
            st.caption("Use this tab to compare the full book of business, spot outliers quickly, and review how risk affects pricing.")
        with _h2:
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end;opacity:0.85;">'
                f'{_illus(GROUP_INSURANCE, "160px")}</div>',
                unsafe_allow_html=True,
            )

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

        _render_alerts(df)

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
        st.caption("Use this tab to inspect one employer in detail, understand what drives its HRS, and export the underwriting report.")

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
                "axis":  {"range": [0, 100], "tickcolor": "#999999"},
                "bar":   {"color": ACCENT},
                "bgcolor": PLOT_BG,
                "steps": [
                    {"range": [0,  30],  "color": "rgba(34,197,94,0.10)"},
                    {"range": [30, 60],  "color": "rgba(245,158,11,0.10)"},
                    {"range": [60, 80],  "color": "rgba(239,68,68,0.10)"},
                    {"range": [80, 100], "color": "rgba(153,27,27,0.15)"},
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

        # ── Risk band mini-cards (NullMask design) ──────────────────────────
        band_data = [
            ("Low",      pred["low_risk_pct"],      "#22C55E", int(pred["employee_count"] * pred["low_risk_pct"]      / 100)),
            ("Moderate", pred["moderate_risk_pct"],  "#F59E0B", int(pred["employee_count"] * pred["moderate_risk_pct"] / 100)),
            ("High",     pred["high_risk_pct"],      "#EF4444", int(pred["employee_count"] * pred["high_risk_pct"]     / 100)),
            ("Critical", pred["critical_risk_pct"],  "#991B1B", int(pred["employee_count"] * pred["critical_risk_pct"] / 100)),
        ]
        cards_html = "".join(
            f'<div style="flex:1;background:#F5F5EF;border-radius:8px;padding:12px 14px;">'
            f'<div style="font-size:12px;font-weight:600;font-family:\'NType82\',\'Space Grotesk\',system-ui,sans-serif;color:#111;margin-bottom:6px;">{label}</div>'
            f'<div style="font-size:20px;font-weight:700;color:{color};font-family:\'NType82\',\'Space Grotesk\',system-ui,sans-serif;letter-spacing:-0.02em;">{pct:.0f}%</div>'
            f'<div style="font-size:10px;color:#999;margin-top:2px;">{count} employees</div>'
            f'<div style="height:3px;background:rgba(0,0,0,0.07);border-radius:2px;margin-top:8px;">'
            f'<div style="height:100%;width:{pct}%;background:{color};border-radius:2px;opacity:0.7;"></div>'
            f'</div></div>'
            for label, pct, color, count in band_data
        )
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);border-radius:12px;'
            f'padding:18px 22px;margin-bottom:16px;">'
            f'<div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.1em;'
            f'margin-bottom:12px;font-weight:500;">Risk Band Breakdown</div>'
            f'<div style="display:flex;gap:12px;">{cards_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

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
        st.caption("Use this tab to understand how company HRS values are distributed across the portfolio and which industries are carrying more risk.")
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
