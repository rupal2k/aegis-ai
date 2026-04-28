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
import dashboard.training_data_view as training_data_view
from dashboard.illustrations import GROUP_INSURANCE, _render_illus as _illus
from dashboard.design_helpers import (
    page_header, section_header, apply_chart_theme, empty_state,
    inline_note, divider as nm_divider, ICON_DATA, ICON_UPLOAD,
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

# Severity badge config: (label, text color, border color, bg color)
_ALERT_BADGE = {
    "high": ("CRITICAL",  "#8B0000", "rgba(139,0,0,0.25)",    "rgba(139,0,0,0.05)"),
    "med":  ("HIGH RISK", "#B06000", "rgba(176,96,0,0.25)",   "rgba(176,96,0,0.05)"),
    "info": ("WATCH",     "#0060B0", "rgba(0,96,176,0.25)",   "rgba(0,96,176,0.05)"),
    "ok":   ("FAVORABLE", "#5A8A00", "rgba(90,138,0,0.25)",   "rgba(90,138,0,0.05)"),
}


def _render_alerts(df):
    """Render alert cards in a 2-column grid with severity badges and hyperlink CTAs."""
    alerts = []
    critical = df[df["risk_band"] == "Critical"]
    high     = df[df["risk_band"] == "High"]
    big_adj  = df[df["adjustment_pct"] > 10]
    low      = df[df["risk_band"] == "Low"]
    avg_hrs  = df["mean_hrs"].mean()

    if len(critical) > 0:
        names  = ", ".join(critical["company_name"].head(2).tolist())
        suffix = f" +{len(critical) - 2} more" if len(critical) > 2 else ""
        alerts.append(("high", f"{names}{suffix} — immediate underwriting review required", "Critical"))
    if len(high) > 1:
        alerts.append(("med",  f"{len(high)} companies in High risk band — elevated claims exposure", "High"))
    if len(big_adj) > 0:
        alerts.append(("info", f"{len(big_adj)} companies flagged for >10% premium adjustment at renewal", "Moderate"))
    if avg_hrs > 50:
        alerts.append(("info", f"Portfolio avg HRS {avg_hrs:.1f} — exceeds 50-point industry benchmark", "Moderate"))
    if len(low) > 0:
        alerts.append(("ok",   f"{len(low)} companies in Low risk band — favourable renewal terms available", "Low"))

    if not alerts:
        return

    st.markdown(
        '<div style="font-size:11px;color:#222;text-transform:uppercase;letter-spacing:0.10em;'
        'font-weight:600;margin-bottom:10px;">Portfolio alerts</div>',
        unsafe_allow_html=True,
    )

    alert_list = alerts[:4]
    for i in range(0, len(alert_list), 2):
        row_alerts = alert_list[i:i + 2]
        grid_cols  = st.columns(len(row_alerts))
        for col, (level, text, filter_band) in zip(grid_cols, row_alerts):
            badge_label, color, border, bg = _ALERT_BADGE[level]
            with col:
                st.markdown(
                    f'<div style="background:{bg};border:1px solid {border};border-left:3px solid {color};'
                    f'border-radius:8px;padding:12px 14px;margin-bottom:2px;">'
                    f'<span style="background:{color};color:#fff;font-size:9px;font-weight:700;'
                    f'letter-spacing:0.08em;text-transform:uppercase;padding:2px 8px;border-radius:20px;">'
                    f'{badge_label}</span>'
                    f'<div style="font-size:12px;color:#222;line-height:1.45;margin-top:8px;">{text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="alert-link-btn alert-link-{level}">',
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Filter to {filter_band} accounts →",
                    key=f"alert_btn_{i}_{level}",
                    use_container_width=False,
                ):
                    st.session_state["uw_filter_band"] = filter_band
                st.markdown('</div>', unsafe_allow_html=True)


def _chart_defaults():
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR, family="Inter, system-ui, sans-serif", size=12),
        margin=dict(l=0, r=20, t=24, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#111111", size=12, family="Inter, system-ui, sans-serif"),
            title=dict(
                text="Risk band",
                font=dict(color="#111111", size=11, family="Inter, system-ui, sans-serif"),
            ),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.10)",
            borderwidth=1,
        ),
    )


_DECISION_BORDER = {
    "Low":      "#5A8A00",
    "Moderate": "#B06000",
    "High":     "#C42020",
    "Critical": "#8B0000",
}


def _render_risk_drivers(drivers: list) -> None:
    """Branded HRS driver bars — green gradient, LetteraMonoLL values."""
    if not drivers:
        st.caption("No risk driver data available for this account.")
        return
    max_imp = drivers[0]["importance"]
    rows_html = ""
    for i, d in enumerate(drivers[:5], 1):
        pct = round((d["importance"] / max_imp) * 100) if max_imp else 0
        rows_html += (
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
            f'<span style="font-size:12px;color:#222;font-family:\'Inter\',system-ui,sans-serif;">'
            f'<span style="font-size:10px;color:#222222;margin-right:6px;">{i:02d}</span>{d["feature"]}</span>'
            f'<span style="font-size:12px;font-weight:600;color:#111;'
            f'font-family:\'LetteraMonoLL\',\'Space Mono\',monospace;">{d["importance"]:.3f}</span>'
            f'</div>'
            f'<div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;">'
            f'<div style="height:100%;width:{pct}%;'
            f'background:linear-gradient(90deg,#9BC800,#C4FF00);border-radius:3px;"></div>'
            f'</div>'
            f'</div>'
        )
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);border-radius:12px;'
        f'padding:20px 22px;">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def _render_decision_card(prem: dict, base_premium: float, risk_band: str) -> None:
    """Branded underwriting decision card with risk-band accent border."""
    border_color = _DECISION_BORDER.get(risk_band, "#9BC800")
    rec = prem.get("recommendation", "N/A")
    adj = fmt(prem["adjusted_premium"])
    adj_pct = prem["adjustment_pct"]
    base_fmt = fmt(base_premium)
    sign = "▲" if adj_pct > 0 else ("▼" if adj_pct < 0 else "—")
    sign_color = "#EF4444" if adj_pct > 0 else ("#22C55E" if adj_pct < 0 else "#222222")
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);'
        f'border-left:4px solid {border_color};border-radius:10px;padding:20px 24px;margin-bottom:16px;">'
        f'<div style="font-size:10px;color:#333333;text-transform:uppercase;letter-spacing:0.12em;'
        f'font-weight:600;margin-bottom:10px;">Underwriting Decision</div>'
        f'<div style="font-size:14px;color:#111;font-weight:600;'
        f'font-family:\'NType82\',\'Space Grotesk\',system-ui,sans-serif;margin-bottom:14px;'
        f'line-height:1.4;">{rec}</div>'
        f'<div style="display:flex;gap:32px;">'
        f'<div><div style="font-size:10px;color:#222222;margin-bottom:2px;">Adjusted premium</div>'
        f'<div style="font-size:18px;font-weight:700;color:#111;'
        f'font-family:\'LetteraMonoLL\',\'Space Mono\',monospace;">{adj}</div></div>'
        f'<div><div style="font-size:10px;color:#222222;margin-bottom:2px;">vs base premium</div>'
        f'<div style="font-size:18px;font-weight:700;color:{sign_color};'
        f'font-family:\'LetteraMonoLL\',\'Space Mono\',monospace;">'
        f'{sign} {abs(adj_pct):.2f}%</div></div>'
        f'<div><div style="font-size:10px;color:#222222;margin-bottom:2px;">Base premium</div>'
        f'<div style="font-size:16px;font-weight:500;color:#222;'
        f'font-family:\'LetteraMonoLL\',\'Space Mono\',monospace;">{base_fmt}</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render():
    user = st.session_state["user"]
    page_header(
        eyebrow="Underwriting Console",
        title="Portfolio Risk Intelligence",
        subtitle=f"{user['name']} · {user['org']} · scope: full underwriting book",
    )

    # Collapsed help — doesn't compete with KPIs on load
    with st.expander("How this workspace works", expanded=False):
        st.markdown(
            "**HRS (Health Risk Score)** runs 0–100; lower is healthier. "
            "Bands: **Low (0–29)** · **Moderate (30–59)** · **High (60–79)** · **Critical (80–100)**.\n\n"
            "Move from portfolio screening → account review → pricing analysis → CSV scoring without "
            "changing stored company data.\n\n"
            "> **Currency note:** the sidebar selector updates displayed premium values only — "
            "model scores and risk bands are always computed in INR."
        )

    # ── Load portfolio data ───────────────────────────────────────────────────
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

    if not rows:
        empty_state(
            title="No portfolio data yet",
            hint="Upload an employee CSV in the CSV Scoring tab, or ingest your first company "
                 "via the API. Predictions will appear here once data exists.",
            icon_svg=ICON_UPLOAD,
            cta="Try the CSV Scoring tab →",
        )
        return

    df = pd.DataFrame(rows)

    # ── KPI strip with delta context ──────────────────────────────────────────
    n_risk        = len(df[df["risk_band"].isin(["High", "Critical"])])
    avg_hrs       = df["mean_hrs"].mean()
    adj_total     = df["adjusted"].sum()
    base_total    = df["base_premium"].apply(float).sum()
    premium_delta = adj_total - base_total

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Companies", len(df),
        delta=f"{n_risk} need review" if n_risk > 0 else "All clear",
        delta_color="inverse" if n_risk > 0 else "normal",
        help="Total employer groups in the current underwriting book.",
    )
    col2.metric(
        "Total employees", f"{int(df['employees'].sum()):,}",
        help="Total headcount across all employer groups.",
    )
    col3.metric(
        "Avg portfolio HRS", f"{avg_hrs:.1f}",
        delta=f"{avg_hrs - 50:+.1f} vs 50pt benchmark",
        delta_color="inverse" if avg_hrs > 50 else "normal",
        help="Mean Health Risk Score. Industry benchmark is 50.",
    )
    col4.metric(
        "Portfolio premium", fmt_crore(adj_total),
        delta=fmt_crore(premium_delta),
        delta_color="inverse" if premium_delta > 0 else "normal",
        help="Total adjusted premium. Delta = adjustment vs base premium.",
    )

    # Spotlight — highest-risk company surfaced as an accent card
    df_sorted = df.sort_values("mean_hrs", ascending=False)
    spotlight = df_sorted.iloc[0]
    sp_col, cta_col = st.columns([3, 2])
    with sp_col:
        render_card(
            variant="accent",
            badge=f"{spotlight['risk_band'].upper()} RISK · TOP OF BOOK",
            stat=f"{spotlight['mean_hrs']:.1f}",
            stat_color={"Critical": "#8B0000", "High": "#C42020",
                        "Moderate": "#B06000", "Low": "#5A8A00"}.get(
                            spotlight["risk_band"], "#5A7A00"),
            title=spotlight["company_name"],
            body=(f"{int(spotlight['employees']):,} employees · {spotlight['industry']} · "
                  f"premium adjustment {spotlight['adjustment_pct']:+.2f}%"),
            mono_footer=f"COMPANY ID · {spotlight['company_id']}",
        )
    with cta_col:
        # Primary CTA — guide the next decision
        if n_risk > 0:
            st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
            if st.button(
                f"Review {n_risk} high-risk account{'s' if n_risk != 1 else ''} →",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["uw_filter_band"] = "High"
            st.caption("Filters Portfolio Overview to the high-risk slice.")

    nm_divider(top=8, bottom=14)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Portfolio Overview",
        "Account Review",
        "Risk Distribution",
        "CSV Scoring",
        "Training Data",
    ])

    # ── Tab 1: Portfolio Overview ─────────────────────────────────────────────
    with tab1:
        _h1, _h2 = st.columns([3, 1])
        with _h1:
            section_header("Portfolio", "All companies — ranked by risk")
        with _h2:
            _illus(GROUP_INSURANCE, "160px", height_px=170, align="right", opacity=0.85)

        fig = px.bar(
            df.sort_values("mean_hrs"),
            x="mean_hrs", y="company_name",
            color="risk_band", color_discrete_map=COLOR_MAP,
            orientation="h",
            labels={"mean_hrs": "Health Risk Score (HRS)", "company_name": ""},
            height=max(400, len(df) * 28),
        )
        apply_chart_theme(
            fig,
            x_range=(0, 100),
            x_title="Health Risk Score (HRS)",
        )
        fig.add_vline(
            x=50, line_width=1.5, line_dash="dot", line_color="rgba(0,0,0,0.30)",
            annotation_text="Benchmark 50", annotation_position="top right",
            annotation_font=dict(size=11, color="#333333"),
        )
        st.plotly_chart(fig, use_container_width=True)

        _render_alerts(df)
        st.divider()

        # ── Filter bar ────────────────────────────────────────────────────
        st.subheader("Ranked portfolio")

        _f1, _f2, _f3 = st.columns([3, 2, 1])
        with _f1:
            search_val = st.text_input(
                "Search companies",
                value=st.session_state.get("uw_search", ""),
                placeholder="Filter by company name…",
                label_visibility="collapsed",
            )
        with _f2:
            band_options = ["All", "Critical", "High", "Moderate", "Low"]
            current_band = st.session_state.get("uw_filter_band", "All")
            if current_band not in band_options:
                current_band = "All"
            band_filter = st.selectbox(
                "Risk band",
                options=band_options,
                index=band_options.index(current_band),
                label_visibility="collapsed",
            )
        with _f3:
            if st.button("Clear", use_container_width=True):
                st.session_state["uw_filter_band"] = "All"
                st.session_state["uw_search"]      = ""
                st.rerun()

        # Sync filter state so buttons elsewhere can write to it
        st.session_state["uw_filter_band"] = band_filter
        st.session_state["uw_search"]      = search_val

        # ── Active filter state pills ─────────────────────────────────────
        code = active_code()
        sym  = CURRENCIES[code]["symbol"]
        active_parts = []
        if band_filter != "All":
            active_parts.append(f"Risk band: {band_filter}")
        if search_val.strip():
            active_parts.append(f'Search: "{search_val.strip()}"')
        active_parts.append(f"Currency: {code}")
        pill_style = (
            "background:rgba(0,0,0,0.06);padding:2px 10px;"
            "border-radius:20px;font-size:11px;color:#222;"
        )
        pills_html = " &nbsp;·&nbsp; ".join(
            f'<span style="{pill_style}">{p}</span>' for p in active_parts
        )
        st.markdown(
            f'<div style="margin-bottom:8px;line-height:2.2;">{pills_html}</div>',
            unsafe_allow_html=True,
        )

        # ── Build filtered display frame ──────────────────────────────────
        display_df = df.copy()
        if band_filter != "All":
            display_df = display_df[display_df["risk_band"] == band_filter]
        if search_val.strip():
            display_df = display_df[
                display_df["company_name"].str.contains(
                    search_val.strip(), case=False, na=False
                )
            ]

        display_df["base_premium_fx"] = display_df["base_premium"].apply(
            lambda v: float(v) * CURRENCIES[code]["rate"])
        display_df["adjusted_fx"] = display_df["adjusted"].apply(
            lambda v: v * CURRENCIES[code]["rate"])
        display_df = (
            display_df[[
                "company_id", "company_name", "industry", "employees",
                "mean_hrs", "risk_band", "base_premium_fx", "adjusted_fx",
                "adjustment_pct", "zone",
            ]]
            .rename(columns={
                "company_name":    "Company",
                "industry":        "Industry",
                "employees":       "Employees",
                "mean_hrs":        "HRS",
                "risk_band":       "Band",
                "base_premium_fx": f"Base ({code})",
                "adjusted_fx":     f"Adjusted ({code})",
                "adjustment_pct":  "Change %",
                "zone":            "Zone",
            })
            .sort_values("HRS", ascending=False)
        )

        if display_df.empty:
            st.info("No companies match the current filters. Try clearing the filters above.")
        else:
            event = st.dataframe(
                display_df.drop(columns=["company_id"]),
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                column_config={
                    "HRS": st.column_config.ProgressColumn(
                        "HRS", min_value=0, max_value=100, format="%.1f",
                        help="Health Risk Score — 0 (healthiest) to 100 (critical risk)"),
                    f"Base ({code})":     st.column_config.NumberColumn(format=f"{sym}%,.0f"),
                    f"Adjusted ({code})": st.column_config.NumberColumn(format=f"{sym}%,.0f"),
                    "Change %": st.column_config.NumberColumn(
                        format="%+.2f%%",
                        help="Premium adjustment vs base — driven by HRS and risk band"),
                },
            )

            # ── Row-level actions ─────────────────────────────────────────
            if event.selection and event.selection.rows:
                sel_idx = event.selection.rows[0]
                sel_cid = display_df.iloc[sel_idx]["company_id"]
                sel_name = display_df.iloc[sel_idx]["Company"]

                st.markdown(
                    f'<div style="background:#F5F5EF;border:1px solid rgba(0,0,0,0.08);'
                    f'border-radius:8px;padding:10px 16px;margin-top:4px;">'
                    f'<span style="font-size:12px;font-weight:600;color:#111;">{sel_name}</span>'
                    f'<span style="font-size:12px;color:#333333;margin-left:8px;">— row selected</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                _ra, _rb, _rc = st.columns([2, 2, 4])
                with _ra:
                    if st.button("Open account review →", use_container_width=True, type="primary"):
                        st.session_state["uw_deep_dive_company"] = sel_cid
                        st.info("Switch to the **Account Review** tab to see the full analysis.")
                with _rb:
                    try:
                        sel_pred = get_company_prediction(sel_cid)
                        sel_base = df[df["company_id"] == sel_cid]["base_premium"].iloc[0]
                        sel_prem = calculate_premium(float(sel_base), sel_pred["mean_hrs"])
                        pdf_bytes = generate_underwriting_report(
                            {**sel_pred, "company_name": sel_name, "company_id": sel_cid},
                            sel_prem,
                            currency=active_code(),
                        )
                        st.download_button(
                            "Export PDF report",
                            data=pdf_bytes,
                            file_name=f"aegis_report_{sel_cid}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception:
                        st.caption("PDF unavailable for this account.")

    # ── Tab 2: Account Review ─────────────────────────────────────────────────
    with tab2:
        section_header(
            "Single Account",
            "Account review",
            "Inspect one employer in detail, understand what drives its HRS, and export the underwriting report.",
        )

        default_cid = st.session_state.get("uw_deep_dive_company", df["company_id"].iloc[0])
        if default_cid not in df["company_id"].values:
            default_cid = df["company_id"].iloc[0]

        company_choice = st.selectbox(
            "Select a company",
            options=df["company_id"].tolist(),
            format_func=lambda c: df[df["company_id"] == c]["company_name"].iloc[0],
            index=df["company_id"].tolist().index(default_cid),
        )
        row  = df[df["company_id"] == company_choice].iloc[0]
        pred = get_company_prediction(company_choice)
        prem = calculate_premium(float(row["base_premium"]), pred["mean_hrs"])

        # Side-by-side: gauge (left) + metrics & band summary (right)
        _g_col, _m_col = st.columns([2, 3])
        with _g_col:
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pred["mean_hrs"],
                number={"font": {"color": FONT_CLR, "size": 40}},
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
                title={"text": "Health Risk Score", "font": {"color": FONT_CLR, "size": 14}},
            ))
            gauge.update_layout(
                height=260, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor=PLOT_BG,
            )
            st.plotly_chart(gauge, use_container_width=True)

        with _m_col:
            c1, c2, c3 = st.columns(3)
            c1.metric("Mean HRS",     f"{pred['mean_hrs']:.1f}", pred["risk_band"],
                      help="Company's average Health Risk Score across all employees.")
            c2.metric("Loss ratio",   f"{pred['mean_loss_ratio']:.3f}",
                      help="Predicted claims-to-premium ratio. Values above 1.0 indicate underwriting loss.")
            delta_inr = prem["adjusted_premium"] - float(row["base_premium"])
            c3.metric("Premium adj.", f"{prem['adjustment_pct']:+.2f}%", fmt(delta_inr),
                      help="Recommended premium change vs base, driven by this company's HRS.")

            band_data = [
                ("Low",      pred["low_risk_pct"],
                 int(pred["employee_count"] * pred["low_risk_pct"]      / 100)),
                ("Moderate", pred["moderate_risk_pct"],
                 int(pred["employee_count"] * pred["moderate_risk_pct"] / 100)),
                ("High",     pred["high_risk_pct"],
                 int(pred["employee_count"] * pred["high_risk_pct"]     / 100)),
                ("Critical", pred["critical_risk_pct"],
                 int(pred["employee_count"] * pred["critical_risk_pct"] / 100)),
            ]
            mini_cards = "".join(
                card(
                    eyebrow=label,
                    stat=f"{pct:.0f}%",
                    stat_color=COLOR_MAP[label],
                    body=f"{count} employees",
                )
                for label, pct, count in band_data
            )
            st.markdown(
                f'<div style="margin-top:10px;">'
                f'<div style="font-size:10px;color:#333333;text-transform:uppercase;letter-spacing:0.12em;'
                f'margin-bottom:10px;font-weight:600;font-family:Inter,system-ui,sans-serif;">'
                f'Risk Band Breakdown</div>'
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">'
                f'{mini_cards}</div></div>',
                unsafe_allow_html=True,
            )

        st.divider()

        nm_divider()
        section_header("Explainability", "Top risk drivers")
        _render_risk_drivers(pred.get("top_risk_drivers", []))

        nm_divider()
        section_header("Decision", "Underwriting decision")
        _render_decision_card(prem, float(row["base_premium"]), pred["risk_band"])

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

    # ── Tab 3: Risk Distribution ──────────────────────────────────────────────
    with tab3:
        section_header(
            "Portfolio Lens",
            "Risk distribution",
            "How company HRS values are distributed and which industries carry the most risk.",
        )

        hist = px.histogram(
            df, x="mean_hrs", nbins=20,
            labels={"mean_hrs": "Company Health Risk Score (HRS)", "count": "Companies"},
            color_discrete_sequence=[ACCENT],
        )
        apply_chart_theme(
            hist, height=320, show_legend=False, x_range=(0, 100),
            x_title="Company Health Risk Score (HRS)", y_title="Companies",
        )
        hist.add_vrect(x0=0,  x1=30,  fillcolor="rgba(34,197,94,0.05)",  layer="below", line_width=0)
        hist.add_vrect(x0=30, x1=60,  fillcolor="rgba(245,158,11,0.07)", layer="below", line_width=0)
        hist.add_vrect(x0=60, x1=80,  fillcolor="rgba(239,68,68,0.07)",  layer="below", line_width=0)
        hist.add_vrect(x0=80, x1=100, fillcolor="rgba(153,27,27,0.09)",  layer="below", line_width=0)
        for x, label in [(30, "Moderate"), (60, "High"), (80, "Critical")]:
            hist.add_vline(
                x=x, line_width=1, line_dash="dot", line_color="rgba(0,0,0,0.20)",
                annotation_text=label, annotation_position="top left",
                annotation_font=dict(size=10, color="#222222"),
            )
        st.plotly_chart(hist, use_container_width=True)

        nm_divider()
        section_header("Industry Cut", "Industry risk profile")
        ind = df.groupby("industry").agg(
            avg_hrs=("mean_hrs", "mean"),
            employees=("employees", "sum"),
            companies=("company_id", "count"),
        ).reset_index().sort_values("avg_hrs", ascending=False)

        if ind.empty:
            empty_state(title="No industry data", hint="Industry rollups appear here once companies are loaded.", icon_svg=ICON_DATA)
        else:
            st.dataframe(
                ind, use_container_width=True, hide_index=True,
                column_config={
                    "avg_hrs": st.column_config.ProgressColumn(
                        "Avg HRS", min_value=0, max_value=100, format="%.1f",
                        help="Average Health Risk Score across all companies in this industry"),
                    "employees": st.column_config.NumberColumn("Total employees", format="%,d"),
                    "companies": st.column_config.NumberColumn("Companies"),
                },
            )

    # ── Tab 4: CSV Scoring ────────────────────────────────────────────────────
    with tab4:
        upload_view.render_tab()

    # ── Tab 5: Training Data ──────────────────────────────────────────────────
    with tab5:
        training_data_view.render_tab()
