"""Aegis AI — B2B Dashboard entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from dashboard.auth import login_form, logout_button
from dashboard import underwriter_view, hr_view
from dashboard.currency import sidebar_selector
from dashboard.illustrations import SOC2_COMPLIANCE, BRAND_FONT_CSS, _svg_img as _illus

st.set_page_config(
    page_title="Aegis AI — Underwriting Platform",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject NType82 + LetteraMonoLL brand fonts (base64 embedded, no server needed)
st.markdown(f"<style>{BRAND_FONT_CSS}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Base ─────────────────────────── */
.stApp { background-color: #E3E3DC !important; }
body, .stApp, p, li, span, div {
    font-family: 'Inter', system-ui, sans-serif;
}

/* ── Sidebar ──────────────────────── */
[data-testid="stSidebar"] {
    background-color: #EAEAE4;
    border-right: 1px solid rgba(0,0,0,0.07);
}
[data-testid="stSidebar"] > div:first-child {
    background-color: #EAEAE4;
}

/* ── Typography ───────────────────── */
/* NType82 for all headings — the NullMask display face */
h1, h2, h3, h4, h5, h6 {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    color: #111111 !important;
    letter-spacing: -0.025em;
}
h1 { font-size: 1.65rem !important; font-weight: 700 !important; }
h2 { font-size: 1.3rem  !important; font-weight: 700 !important; }
h3 { font-size: 1.05rem !important; font-weight: 400 !important; letter-spacing: -0.01em; }

/* Inter for body copy, captions, labels */
p, .stMarkdown p { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── Metric cards ─────────────────── */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.07);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
/* LetteraMonoLL for metric values — brand mono face */
[data-testid="stMetricValue"] {
    color: #111111 !important;
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 1.75rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.02em;
}
/* Inter uppercase for metric labels */
[data-testid="stMetricLabel"] {
    color: #999999 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    font-weight: 500;
}
/* LetteraMonoLL for delta figures */
[data-testid="stMetricDelta"] {
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 0.83rem !important;
}

/* ── Tabs — NType82 ───────────────── */
[data-testid="stTabs"] button {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 400;
    color: #999999;
    letter-spacing: -0.01em;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #111111 !important;
    font-weight: 700;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #C4FF00 !important;
}

/* ── Divider ──────────────────────── */
hr { border-color: rgba(0,0,0,0.08) !important; }

/* ── Bordered containers / cards ──── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.07) !important;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* ── Dataframe ────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.07);
}

/* ── Download buttons — dark + Inter ─ */
[data-testid="stDownloadButton"] > button {
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px;
    font-family: 'Inter', system-ui, sans-serif;
    font-weight: 500;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #222222 !important;
}

/* ── Primary buttons — accent + NType82 */
[data-testid="stButton"] > button[kind="primary"] {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
[data-testid="stButton"] > button {
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Captions — Inter muted ───────── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #999999 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Glow metric card (accent) ────── */
[data-testid="stMetric"].nm-glow {
    border-color: rgba(150,200,0,0.40) !important;
    box-shadow: 0 0 24px rgba(196,255,0,0.10) !important;
}

/* ── Scrollbar ────────────────────── */
::-webkit-scrollbar { width: 4px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


def main():
    user = st.session_state.get("user")

    if not user:
        _lc, _rc = st.columns([1, 1], gap="large")
        with _lc:
            st.markdown("""
<div style="padding-top:60px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
    <div style="width:44px;height:44px;background:#111;border-radius:11px;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;
                box-shadow:0 4px 20px rgba(0,0,0,0.15);">
        <svg width="24" height="24" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="5.5" stroke="#C4FF00" stroke-width="1.8"/>
            <line x1="5" y1="13" x2="13" y2="5" stroke="#C4FF00" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
    </div>
    <div>
        <div style="font-size:22px;font-weight:700;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    color:#111;letter-spacing:-0.02em;line-height:1.1;">Aegis AI</div>
        <div style="font-size:11px;color:#999;letter-spacing:0.06em;text-transform:uppercase;margin-top:2px;">
            Underwriting Platform</div>
    </div>
</div>
<div style="font-size:13px;color:#555;margin-bottom:32px;line-height:1.6;max-width:340px;">
    AI-powered group insurance underwriting. Predict workforce health risk, adjust premiums
    dynamically, and surface wellness ROI — in one platform.</div>
</div>
""", unsafe_allow_html=True)
            login_form()
        with _rc:
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:center;'
                f'padding-top:40px;opacity:0.92;">'
                f'{_illus(SOC2_COMPLIANCE, "100%", "max-width:380px;")}</div>',
                unsafe_allow_html=True,
            )
        return

    with st.sidebar:
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px;
            border-bottom:1px solid rgba(0,0,0,0.07);margin-bottom:12px;">
    <div style="width:32px;height:32px;background:#111;border-radius:8px;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="5.5" stroke="#C4FF00" stroke-width="1.8"/>
            <line x1="5" y1="13" x2="13" y2="5" stroke="#C4FF00" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
    </div>
    <div>
        <div style="font-size:14px;font-weight:700;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    color:#111;line-height:1.15;">Aegis AI</div>
        <div style="font-size:10px;color:#999;letter-spacing:0.06em;text-transform:uppercase;margin-top:1px;">
            Underwriting Platform</div>
    </div>
</div>
""", unsafe_allow_html=True)
        _name = user.get("name") or user.get("email", "?")
        _parts = _name.split("@")[0].replace(".", " ").split() if "@" in _name else _name.split()
        _initials = "".join(p[0].upper() for p in _parts if p)[:2] or "??"
        _role_label = {"underwriter": "Underwriter", "hr_admin": "HR Manager"}.get(user["role"], user["role"])
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
  <div style="width:34px;height:34px;border-radius:50%;
              background:rgba(196,255,0,0.14);border:1px solid rgba(150,200,0,0.40);
              display:flex;align-items:center;justify-content:center;
              font-size:12px;font-weight:600;color:#C4FF00;
              font-family:'NType82','Space Grotesk',system-ui,sans-serif;flex-shrink:0;">{_initials}</div>
  <div style="min-width:0;">
    <div style="font-size:13px;font-weight:600;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                color:#111;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_name}</div>
    <div style="font-size:10px;color:#999;letter-spacing:0.08em;text-transform:uppercase;margin-top:1px;">{_role_label}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.divider()
        sidebar_selector()
        st.divider()
        logout_button()
        st.divider()
        st.markdown("""
<div style="background:#111;border:1px solid #1e1e1e;border-radius:8px;
            padding:10px 12px;margin-top:4px;">
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#C4FF00;
                     display:inline-block;flex-shrink:0;"></span>
        <span style="font-size:10px;color:#C4FF00;font-weight:500;
                     letter-spacing:0.08em;text-transform:uppercase;
                     font-family:'NType82','Space Grotesk',system-ui,sans-serif;">Model Active</span>
    </div>
    <div style="font-size:11px;color:#888;line-height:1.4;">XGBoost v2.1 · SHAP enabled</div>
</div>
""", unsafe_allow_html=True)

    if user["role"] == "underwriter":
        underwriter_view.render()
    elif user["role"] == "hr_admin":
        hr_view.render()
    else:
        st.error(f"Unknown role: {user['role']}")


if __name__ == "__main__":
    main()
