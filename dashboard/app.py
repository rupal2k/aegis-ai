"""Aegis AI — B2B Dashboard entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from dashboard.auth import login_form, logout_button
from dashboard import underwriter_view, hr_view
from dashboard.currency import sidebar_selector
from dashboard.illustrations import SOC2_COMPLIANCE, BRAND_FONT_CSS, _render_illus as _illus

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
h1, h2, h3, h4, h5, h6 {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    color: #111111 !important;
    letter-spacing: -0.025em;
}
h1 { font-size: 1.65rem !important; font-weight: 700 !important; }
h2 { font-size: 1.3rem  !important; font-weight: 700 !important; }
h3 { font-size: 1.05rem !important; font-weight: 400 !important; letter-spacing: -0.01em; }

p, .stMarkdown p { font-family: 'Inter', system-ui, sans-serif !important; }

/* Form labels */
.stTextInput label,
.stSelectbox label,
.stTextArea label,
.stNumberInput label,
[data-testid="stWidgetLabel"] {
    color: #111111 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* ── Metric cards ─────────────────── */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.07);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
[data-testid="stMetricValue"] {
    color: #111111 !important;
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 1.75rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
    color: #444444 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}
[data-testid="stMetricDelta"] {
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Tabs ─────────────────────────── */
[data-testid="stTabs"] button {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 500;
    color: #666666;
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
[data-testid="stDataFrame"] thead tr th {
    background: #F2F2EC !important;
}

/* ── Download buttons ─────────────── */
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

/* ── Primary buttons — dark brand ─── */
[data-testid="stButton"] > button[kind="primary"] {
    background-color: #111111 !important;
    color: #C4FF00 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: -0.01em;
    height: 40px !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background-color: #1e1e1e !important;
    color: #DEFF6E !important;
}
/* ── Secondary / default buttons ─── */
[data-testid="stButton"] > button {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 13px !important;
    background-color: #FFFFFF !important;
    color: #333333 !important;
    border: 1px solid rgba(0,0,0,0.15) !important;
    border-radius: 8px !important;
    height: 40px !important;
    font-weight: 500 !important;
}
[data-testid="stButton"] > button:hover {
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border-color: #111111 !important;
}
/* Restore primary override after base rule */
[data-testid="stButton"] > button[kind="primary"] {
    background-color: #111111 !important;
    color: #C4FF00 !important;
    border: none !important;
}

/* ── Captions ─────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #666666 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Glow metric card ─────────────── */
[data-testid="stMetric"].nm-glow {
    border-color: rgba(150,200,0,0.45) !important;
    box-shadow: 0 0 24px rgba(196,255,0,0.10), 0 1px 3px rgba(0,0,0,0.06) !important;
}

/* ── Text inputs — compact height ─── */
[data-baseweb="input"],
[data-baseweb="base-input"] {
    min-height: unset !important;
    height: 40px !important;
}
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] > div > div > div {
    min-height: unset !important;
    height: auto !important;
}
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
[data-testid="stTextInput"] input {
    height: 40px !important;
    min-height: unset !important;
    padding: 0 12px !important;
    font-size: 14px !important;
    line-height: 40px !important;
    box-sizing: border-box !important;
}
[data-testid="stTextInput"] [data-testid="stTextInputRootElement"] {
    height: 40px !important;
    min-height: unset !important;
    align-items: center !important;
}

/* ── Form submit button ───────────── */
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
[data-testid="stFormSubmitButton"] button {
    height: 42px !important;
    min-height: unset !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    font-size: 14px !important;
    line-height: 42px !important;
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border: 1px solid #111111 !important;
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    border-radius: 8px !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #2a2a2a !important;
    border-color: #2a2a2a !important;
}

/* ── Focus rings — accessibility ──── */
input:focus-visible,
button:focus-visible,
[data-baseweb="input"]:focus-within {
    outline: 2px solid #C4FF00 !important;
    outline-offset: 2px !important;
    border-radius: 6px;
}

/* ── Progress bars — brand accent ─── */
[data-testid="stProgress"] [role="progressbar"] {
    background: rgba(0,0,0,0.06) !important;
    border-radius: 4px !important;
    height: 6px !important;
}
[data-testid="stProgress"] [role="progressbar"] > div {
    background: linear-gradient(90deg, #9BC800, #C4FF00) !important;
    border-radius: 4px !important;
}

/* ── Expanders — white card ───────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
[data-testid="stExpander"] summary {
    padding: 10px 16px !important;
    font-size: 13px !important;
    color: #333333 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
[data-testid="stExpander"] summary:hover { color: #111111 !important; }
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] .stMarkdown p {
    color: #222222 !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
    color: #111111 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid rgba(0,0,0,0.15) !important;
    padding-left: 12px !important;
    color: #444444 !important;
}

/* ── Alert boxes — softer corners ─── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ── Selectbox — compact + border ─── */
[data-baseweb="select"] > div:first-child {
    border-color: rgba(0,0,0,0.14) !important;
    border-radius: 8px !important;
    min-height: unset !important;
    height: 40px !important;
}

/* ── Spinner text ─────────────────── */
[data-testid="stSpinner"] p {
    font-size: 13px !important;
    color: #777 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Alert hyperlink buttons ─────── */
.alert-link-btn button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 2px 0 !important;
    height: auto !important;
    min-height: unset !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
    letter-spacing: 0.01em !important;
    border-radius: 0 !important;
}
.alert-link-btn button:hover {
    background: transparent !important;
    border: none !important;
    opacity: 0.75 !important;
}
.alert-link-high button { color: #8B0000 !important; }
.alert-link-med  button { color: #B06000 !important; }
.alert-link-info button { color: #0060B0 !important; }
.alert-link-ok   button { color: #5A8A00 !important; }

/* ── Selectbox value text ─────────── */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span {
    color: #222222 !important;
    font-size: 13px !important;
}

/* ── Text input placeholder + value ─ */
[data-testid="stTextInput"] input::placeholder { color: #aaaaaa !important; }
[data-testid="stTextInput"] input { color: #111111 !important; }

/* ── Code / mono inline ───────────── */
code {
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 0.88em !important;
    background: rgba(196,255,0,0.14) !important;
    color: #5A7A00 !important;
    padding: 0.15em 0.4em !important;
    border-radius: 4px !important;
    border: 1px solid rgba(150,200,0,0.40) !important;
}

/* ── Scrollbar ────────────────────── */
::-webkit-scrollbar { width: 4px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ── Login page helpers ────────────────────────────────────────────────────────

def _render_right_panel():
    """Right column content for the login page: benefits, role previews, HRS scale, illustration."""
    # No blank lines inside the HTML — CommonMark ends an HTML block at the first blank line,
    # causing everything after it to render as raw text.
    _BULLET = (
        "display:inline-flex;align-items:center;justify-content:center;"
        "width:20px;height:20px;min-width:20px;background:#111111;border-radius:50%;"
        "color:#C4FF00;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;"
    )
    st.markdown(f"""
<div style="padding:4px 0 0;">
  <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:12px;">What you get</div>
  <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:28px;">
    <div style="display:flex;align-items:flex-start;gap:10px;">
      <span style="{_BULLET}">&#10003;</span>
      <div style="font-size:13px;color:#333;line-height:1.5;"><strong style="color:#111;">Predict risk before renewal</strong> — AI scores workforce health from claims and HR data, surfacing high-risk segments weeks ahead.</div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:10px;">
      <span style="{_BULLET}">&#10003;</span>
      <div style="font-size:13px;color:#333;line-height:1.5;"><strong style="color:#111;">Price with confidence</strong> — dynamic premium recommendations adjust to risk tier, reducing manual overrides and pricing errors.</div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:10px;">
      <span style="{_BULLET}">&#10003;</span>
      <div style="font-size:13px;color:#333;line-height:1.5;"><strong style="color:#111;">Prove wellness ROI</strong> — HR managers quantify intervention impact and share renewal-ready reports directly with underwriters.</div>
    </div>
  </div>
  <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:10px;">Your workspace after sign-in</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:26px;">
    <div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.08);border-radius:10px;padding:14px 16px;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <div style="width:6px;height:6px;border-radius:50%;background:#C4FF00;flex-shrink:0;"></div>
        <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">Underwriter</div>
      </div>
      <div style="font-size:12px;color:#444;line-height:1.55;">Portfolio risk · Premium movement · Company drivers · PDF reports</div>
    </div>
    <div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.08);border-radius:10px;padding:14px 16px;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <div style="width:6px;height:6px;border-radius:50%;background:#C4FF00;flex-shrink:0;"></div>
        <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">HR Manager</div>
      </div>
      <div style="font-size:12px;color:#444;line-height:1.55;">Workforce trends · Key drivers · Wellness ROI · Renewal prep</div>
    </div>
  </div>
  <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:10px;">Health Risk Score (HRS) scale</div>
  <div style="display:flex;gap:7px;flex-wrap:wrap;">
    <div style="background:#F0FFF0;border:1px solid rgba(0,140,0,0.20);border-radius:20px;padding:4px 13px;font-size:11px;color:#276227;font-weight:500;white-space:nowrap;">0–29 · Low</div>
    <div style="background:#FFFBF0;border:1px solid rgba(180,110,0,0.25);border-radius:20px;padding:4px 13px;font-size:11px;color:#8B5E00;font-weight:500;white-space:nowrap;">30–59 · Moderate</div>
    <div style="background:#FFF5F0;border:1px solid rgba(190,70,0,0.25);border-radius:20px;padding:4px 13px;font-size:11px;color:#A63200;font-weight:500;white-space:nowrap;">60–79 · High</div>
    <div style="background:#FFF0F0;border:1px solid rgba(160,0,0,0.20);border-radius:20px;padding:4px 13px;font-size:11px;color:#8B0000;font-weight:500;white-space:nowrap;">80+ · Critical</div>
  </div>
</div>
""", unsafe_allow_html=True)

    _illus(SOC2_COMPLIANCE, "200px", height_px=230, align="right", opacity=0.88)


def _render_sidebar_reference(role: str):
    role_copy = {
        "underwriter": (
            "Portfolio figures reflect live company-level predictions across the current underwriting book."
        ),
        "hr_admin": (
            "Workforce analytics are limited to your company scope and update from the latest scored employee data."
        ),
    }.get(
        role, "Dashboard values update from the active API session and current model outputs."
    )
    st.markdown(
        f"""
<div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.07);border-radius:10px;
            padding:12px 14px;margin-top:4px;">
    <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.08em;
                margin-bottom:6px;font-weight:500;">Session Notes</div>
    <div style="font-size:12px;color:#444;line-height:1.55;margin-bottom:8px;">
        {role_copy}
    </div>
    <div style="font-size:11px;color:#666;line-height:1.5;">
        <strong style="color:#111;">Currency:</strong> changing the selector updates displayed premium values only.<br>
        <strong style="color:#111;">Session:</strong> sign out clears the current dashboard session.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def main():
    user = st.session_state.get("user")

    if not user:
        st.markdown("""
<style>
.main .block-container { padding-top: 7vh !important; padding-bottom: 4vh !important; }
[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }


</style>
""", unsafe_allow_html=True)

        _lc, _rc = st.columns([5, 7], gap="large")

        with _lc:
            st.markdown("""
<div style="max-width:400px;">

  <!-- Logo -->
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:30px;">
    <div style="width:40px;height:40px;background:#111;border-radius:10px;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;
                box-shadow:0 4px 16px rgba(0,0,0,0.15);">
      <svg width="24" height="24" viewBox="0 0 28 30" fill="none">
        <path d="M 14,1 L 26,1 Q 28,1 28,3 L 28,17 C 28,24 21,28 14,30 C 7,28 0,24 0,17 L 0,3 Q 0,1 2,1 Z" fill="#111"/>
        <path d="M 14,6 L 23,6 Q 25,6 25,8 L 25,16 C 25,21 20,24 14,26 C 8,24 3,21 3,16 L 3,8 Q 3,6 5,6 Z" fill="none" stroke="#C4FF00" stroke-width="1" opacity="0.25"/>
        <polyline points="3,17 8,17 10,11 13,23 15,15 17,19 20,17 25,17" stroke="#C4FF00" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M 2,1 L 0,1 L 0,3" stroke="#C4FF00" stroke-width="1.3" fill="none" stroke-linecap="round"/>
        <path d="M 26,1 L 28,1 L 28,3" stroke="#C4FF00" stroke-width="1.3" fill="none" stroke-linecap="round"/>
      </svg>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  color:#111;letter-spacing:-0.02em;line-height:1.1;">Aegis AI</div>
      <div style="font-size:10px;color:#999;letter-spacing:0.08em;text-transform:uppercase;margin-top:2px;">
        Underwriting Platform</div>
    </div>
  </div>

  <!-- Title + value prop -->
  <div style="margin-bottom:24px;">
    <div style="font-size:26px;font-weight:700;
                font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                color:#111;letter-spacing:-0.025em;line-height:1.15;">Sign in</div>
    <div style="font-size:13px;color:#555;margin-top:8px;line-height:1.55;">
      Predict workforce risk. Price accurately. Renew with confidence.
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

            login_form()

            # Trust signals
            st.markdown("""
<div style="display:flex;align-items:center;gap:7px;margin-top:18px;max-width:400px;">
  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
    <path d="M6.5 1L2 3.2v3.8C2 9.8 4 11.8 6.5 12.5 9 11.8 11 9.8 11 7V3.2L6.5 1z"
          stroke="#999" stroke-width="1.1" fill="none"/>
  </svg>
  <span style="font-size:11px;color:#999;font-family:'Inter',system-ui,sans-serif;
               letter-spacing:0.01em;">
    Secure login &nbsp;·&nbsp; SOC 2 Type II &nbsp;·&nbsp; Enterprise ready
  </span>
</div>
""", unsafe_allow_html=True)

        with _rc:
            _render_right_panel()

        return

    # ── Authenticated sidebar ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px;
            border-bottom:1px solid rgba(0,0,0,0.07);margin-bottom:12px;">
    <div style="width:30px;height:30px;background:#111;border-radius:8px;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <svg width="18" height="18" viewBox="0 0 28 30" fill="none">
            <path d="M 14,1 L 26,1 Q 28,1 28,3 L 28,17 C 28,24 21,28 14,30 C 7,28 0,24 0,17 L 0,3 Q 0,1 2,1 Z" fill="#111"/>
            <path d="M 14,6 L 23,6 Q 25,6 25,8 L 25,16 C 25,21 20,24 14,26 C 8,24 3,21 3,16 L 3,8 Q 3,6 5,6 Z" fill="none" stroke="#C4FF00" stroke-width="1" opacity="0.25"/>
            <polyline points="3,17 8,17 10,11 13,23 15,15 17,19 20,17 25,17" stroke="#C4FF00" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M 2,1 L 0,1 L 0,3" stroke="#C4FF00" stroke-width="1.3" fill="none" stroke-linecap="round"/>
            <path d="M 26,1 L 28,1 L 28,3" stroke="#C4FF00" stroke-width="1.3" fill="none" stroke-linecap="round"/>
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
        if user["role"] == "hr_admin":
            _company = user.get("org", "Your Company")
            st.markdown(f"""
<div style="background:#F2F2EC;border:1px solid rgba(0,0,0,0.07);border-radius:8px;padding:8px 12px;margin-top:4px;margin-bottom:2px;">
  <div style="font-size:10px;color:#999;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:3px;">Active Client</div>
  <div style="font-size:13px;font-weight:600;font-family:'NType82','Space Grotesk',system-ui,sans-serif;color:#111;">{_company}</div>
</div>
""", unsafe_allow_html=True)
        st.divider()
        sidebar_selector()
        st.divider()
        _render_sidebar_reference(user["role"])
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
