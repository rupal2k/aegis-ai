"""Aegis AI — B2B Dashboard entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from dashboard.auth import login_form, logout_button
from dashboard import underwriter_view, hr_view
from dashboard.currency import sidebar_selector
from dashboard.illustrations import SOC2_COMPLIANCE, BRAND_FONT_CSS, _render_illus as _illus
from dashboard.design_tokens import DESIGN_TOKENS_CSS

st.set_page_config(
    page_title="Aegis AI — Underwriting Platform",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject NType82 + LetteraMonoLL brand fonts (base64 embedded, no server needed)
st.markdown(f"<style>{BRAND_FONT_CSS}</style>", unsafe_allow_html=True)

# Inject design system CSS custom properties (--nm-*). Additive only — does not
# override existing inline colors in already-built views. New modules should
# reference var(--nm-*) tokens; see design.md at repo root for the full contract.
st.markdown(DESIGN_TOKENS_CSS, unsafe_allow_html=True)

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
    color: #222222 !important;
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
    color: #222222;
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
    color: #222222 !important;
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
    color: #222222 !important;
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
    color: #333333 !important;
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

/* ── Enterprise polish — main block container spacing ────── */
.main .block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
}

/* ── Tab headers — bigger active underline + spacing ────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid rgba(0,0,0,0.07);
    margin-bottom: 6px;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    height: 2.5px !important;
    border-radius: 2px;
}
[data-testid="stTabs"] button {
    padding: 10px 18px !important;
}

/* ── Number input — match text input height ────────────── */
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="base-input"] {
    height: 40px !important;
}

/* ── Slider track — brand accent ───────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #C4FF00 !important;
    border: 1.5px solid #9BC800 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div:first-child {
    background: linear-gradient(90deg, #9BC800, #C4FF00) !important;
}

/* ── Checkbox — accent fill when checked ───────────────── */
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div {
    background-color: #C4FF00 !important;
    border-color: #9BC800 !important;
}

/* ── File uploader dropzone — subtle dashed border ───── */
[data-testid="stFileUploader"] section {
    background: #FFFFFF !important;
    border: 1.5px dashed rgba(0,0,0,0.16) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    transition: border-color 0.15s, background 0.15s;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #9BC800 !important;
    background: rgba(196,255,0,0.04) !important;
}
[data-testid="stFileUploader"] section button {
    background: #111111 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    height: 38px !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 500 !important;
}

/* ── Spinner — accent stroke ───────────────────────────── */
[data-testid="stSpinner"] svg circle { stroke: #C4FF00 !important; }

/* ── Streamlit alert boxes (st.success/info/warning/error) — brand-tone ─ */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid rgba(0,0,0,0.07) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    font-family: 'Inter', system-ui, sans-serif !important;
}
/* Success — chartreuse left border */
[data-testid="stAlertContainer"][kind="success"],
[data-baseweb="notification"][role="status"] {
    background: rgba(90,138,0,0.06) !important;
    border-left: 3px solid #5A8A00 !important;
}
/* Info — blue left border */
[data-testid="stAlertContainer"][kind="info"] {
    background: rgba(0,96,176,0.06) !important;
    border-left: 3px solid #0060B0 !important;
}
/* Warning — orange left border */
[data-testid="stAlertContainer"][kind="warning"] {
    background: rgba(176,96,0,0.06) !important;
    border-left: 3px solid #B06000 !important;
}
/* Error — red left border */
[data-testid="stAlertContainer"][kind="error"] {
    background: rgba(196,32,32,0.06) !important;
    border-left: 3px solid #C42020 !important;
}

/* ── Plotly modebar — match brand on hover ───────────── */
.modebar-btn:hover svg path { fill: #C4FF00 !important; }

/* ── Status / data badges in tables — pill chips ─────── */
[data-testid="stDataFrame"] [data-testid="stDataFrameCell"] {
    font-family: 'Inter', system-ui, sans-serif !important;
}
[data-testid="stDataFrame"] [data-testid="stDataFrameCell"] [data-testid="stDataFrameCell"] {
    color: #111 !important;
}

/* ── Code block (st.code) — brand mono background ────── */
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] pre {
    background: #F5F5EF !important;
    border: 1px solid rgba(0,0,0,0.07) !important;
    border-radius: 8px !important;
    color: #111 !important;
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 12.5px !important;
}

/* ── Captions — slightly darker than default ─────────── */
[data-testid="stCaptionContainer"], .stCaption {
    color: #222222 !important;
    font-size: 12.5px !important;
    line-height: 1.55 !important;
}

/* ── DARK-TEXT GUARD-RAIL ──────────────────────────────
   Project rule: any user-facing text on the light theme must be #333 or
   darker. This block defensively darkens a curated list of Streamlit
   primitives plus Plotly tick labels so visible text never washes out,
   even when a 3rd-party widget defaults to pale grey. */

/* Sidebar text — every label, paragraph, mono digit */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #111111 !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #222222 !important;
}

/* Plotly tick / legend / annotation text — dark by default */
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text,
.js-plotly-plot .plotly .legendtext,
.js-plotly-plot .plotly .annotation-text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle {
    fill: #111111 !important;
}

/* Form labels everywhere */
.stTextInput label, .stSelectbox label, .stTextArea label,
.stNumberInput label, .stCheckbox label, .stRadio label,
.stSlider label, .stMultiSelect label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    color: #111111 !important;
}

/* Tab labels — non-active state */
[data-testid="stTabs"] button {
    color: #222222 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #111111 !important;
}

/* Markdown body — paragraphs and list items */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #222222;
}
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: #111111 !important;
}

/* Selectbox value — make sure picked options stay readable */
[data-baseweb="select"] [role="combobox"] *,
[data-baseweb="select"] div[aria-selected],
[data-baseweb="select"] span {
    color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Login page helpers ────────────────────────────────────────────────────────

def _render_right_panel():
    """Right column content for the login page: capability strip, role previews,
    HRS scale, compliance illustration. Aligned with the brand voice and
    component styles from the design package."""
    # No blank lines inside the HTML — CommonMark ends an HTML block at the first blank line.
    _NUMBER = (
        "display:inline-flex;align-items:center;justify-content:center;"
        "width:24px;height:24px;min-width:24px;background:#111111;border-radius:6px;"
        "color:#C4FF00;font-size:10px;font-weight:700;flex-shrink:0;margin-top:1px;"
        "font-family:'LetteraMonoLL','Space Mono',monospace;"
    )
    st.markdown(f"""
<div style="padding:4px 0 0;">

  <!-- Capability strip -->
  <div style="font-size:10px;color:#222;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:14px;
              font-family:'Inter',system-ui,sans-serif;">PLATFORM CAPABILITIES</div>
  <div style="display:flex;flex-direction:column;gap:14px;margin-bottom:32px;">
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">01</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#111;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Predict risk before renewal</div>
        <div style="font-size:13px;color:#222;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          XGBoost + SHAP score workforce health from claims and HR data, surfacing high-risk segments weeks ahead.</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">02</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#111;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Price with confidence</div>
        <div style="font-size:13px;color:#222;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          Dynamic premium recommendations adjust to risk tier, reducing manual overrides and pricing errors.</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">03</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#111;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Prove wellness ROI</div>
        <div style="font-size:13px;color:#222;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          HR managers quantify intervention impact and share renewal-ready reports directly with underwriters.</div>
      </div>
    </div>
  </div>

  <!-- Workspace preview cards -->
  <div style="font-size:10px;color:#222;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:12px;
              font-family:'Inter',system-ui,sans-serif;">YOUR WORKSPACE AFTER SIGN-IN</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:30px;">
    <div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.08);border-radius:12px;
                padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <div style="display:inline-flex;align-items:center;gap:6px;
                  background:rgba(196,255,0,0.14);border:1px solid rgba(150,200,0,0.40);
                  border-radius:9999px;padding:2px 9px;margin-bottom:10px;">
        <span style="width:5px;height:5px;border-radius:50%;background:#9BC800;"></span>
        <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:9.5px;
                     font-weight:600;color:#5A7A00;letter-spacing:0.08em;text-transform:uppercase;">UNDERWRITER</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:#111;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  letter-spacing:-0.015em;margin-bottom:6px;">Full underwriting book</div>
      <div style="font-size:12px;color:#222;line-height:1.55;
                  font-family:'Inter',system-ui,sans-serif;">
        Portfolio risk · Account review · Premium movement · PDF reports</div>
    </div>
    <div style="background:#FFFFFF;border:1px solid rgba(0,0,0,0.08);border-radius:12px;
                padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <div style="display:inline-flex;align-items:center;gap:6px;
                  background:rgba(196,255,0,0.14);border:1px solid rgba(150,200,0,0.40);
                  border-radius:9999px;padding:2px 9px;margin-bottom:10px;">
        <span style="width:5px;height:5px;border-radius:50%;background:#9BC800;"></span>
        <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:9.5px;
                     font-weight:600;color:#5A7A00;letter-spacing:0.08em;text-transform:uppercase;">HR&nbsp;MANAGER</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:#111;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  letter-spacing:-0.015em;margin-bottom:6px;">Single-company scope</div>
      <div style="font-size:12px;color:#222;line-height:1.55;
                  font-family:'Inter',system-ui,sans-serif;">
        Workforce trends · Key drivers · Wellness ROI · Renewal prep</div>
    </div>
  </div>

  <!-- HRS scale -->
  <div style="font-size:10px;color:#222;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:12px;
              font-family:'Inter',system-ui,sans-serif;">HEALTH RISK SCORE (HRS) SCALE</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <div style="background:rgba(90,138,0,0.08);border:1px solid rgba(90,138,0,0.30);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#5A8A00;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">0–29 · LOW</div>
    <div style="background:rgba(176,96,0,0.08);border:1px solid rgba(176,96,0,0.30);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#B06000;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">30–59 · MODERATE</div>
    <div style="background:rgba(196,32,32,0.08);border:1px solid rgba(196,32,32,0.30);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#C42020;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">60–79 · HIGH</div>
    <div style="background:rgba(139,0,0,0.10);border:1px solid rgba(139,0,0,0.35);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#8B0000;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">80+ · CRITICAL</div>
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
    <div style="font-size:10px;color:#333333;text-transform:uppercase;letter-spacing:0.08em;
                margin-bottom:6px;font-weight:500;">Session Notes</div>
    <div style="font-size:12px;color:#222;line-height:1.55;margin-bottom:8px;">
        {role_copy}
    </div>
    <div style="font-size:11px;color:#222222;line-height:1.5;">
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

  <!-- Logo — canonical squared shield + ECG pulse + corner brackets
       Source: .design-package/.../Aegis AI Logo.html · variant 01 "Primary on light" -->
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:30px;">
    <svg width="56" height="63" viewBox="0 0 80 94" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g transform="translate(0,4)">
        <path d="M 40,4 L 72,4 Q 80,4 80,12 L 80,46 C 80,68 60,82 40,90 C 20,82 0,68 0,46 L 0,12 Q 0,4 8,4 Z" fill="#111111"/>
        <path d="M 40,14 L 66,14 Q 72,14 72,20 L 72,44 C 72,62 56,73 40,79 C 24,73 8,62 8,44 L 8,20 Q 8,14 14,14 Z" fill="none" stroke="#C4FF00" stroke-width="1.5" opacity="0.25"/>
        <polyline points="10,46 20,46 25,32 30,60 35,42 40,50 46,46 70,46" stroke="#C4FF00" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M 8,4 L 0,4 L 0,12" stroke="#C4FF00" stroke-width="2" fill="none" stroke-linecap="round"/>
        <path d="M 72,4 L 80,4 L 80,12" stroke="#C4FF00" stroke-width="2" fill="none" stroke-linecap="round"/>
      </g>
    </svg>
    <div>
      <div style="font-size:26px;font-weight:700;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  color:#111;letter-spacing:-0.025em;line-height:1;text-transform:uppercase;">AEGIS&nbsp;AI</div>
      <div style="font-size:10px;color:#222;letter-spacing:0.20em;text-transform:uppercase;
                  font-family:'Inter',system-ui,sans-serif;font-weight:500;margin-top:5px;">
        UNDERWRITING&nbsp;INTELLIGENCE</div>
    </div>
  </div>

  <!-- Brand tagline pill -->
  <div style="display:inline-flex;align-items:center;gap:7px;
              background:rgba(196,255,0,0.14);
              border:1px solid rgba(150,200,0,0.40);
              border-radius:9999px;padding:4px 12px;margin-bottom:18px;">
    <span style="width:6px;height:6px;border-radius:50%;background:#9BC800;"></span>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;
                 font-size:10.5px;font-weight:600;color:#5A7A00;
                 letter-spacing:0.10em;text-transform:uppercase;">
      AI-POWERED · GROUP INSURANCE</span>
  </div>

  <!-- Hero — brand tagline + sign-in cue -->
  <div style="margin-bottom:8px;">
    <div style="font-size:38px;font-weight:700;
                font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                color:#111;letter-spacing:-0.03em;line-height:1.0;">
      Predict.<br>Protect.<br>Perform.</div>
  </div>
  <div style="font-size:14px;color:#222;margin-top:14px;line-height:1.55;
              font-family:'Inter',system-ui,sans-serif;max-width:380px;
              margin-bottom:26px;">
    AI-powered group insurance underwriting. Score workforce risk, adjust premiums dynamically, and prove wellness ROI — all from one workspace.
  </div>

  <!-- Sign-in eyebrow -->
  <div style="font-size:10px;color:#222;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:8px;
              font-family:'Inter',system-ui,sans-serif;">SIGN IN TO CONTINUE</div>

</div>
""", unsafe_allow_html=True)

            login_form()

            # Trust signals — security & enterprise compliance row
            st.markdown("""
<div style="display:flex;align-items:center;gap:14px;margin-top:22px;max-width:400px;
            padding-top:14px;border-top:1px solid rgba(0,0,0,0.07);">
  <div style="display:inline-flex;align-items:center;gap:6px;">
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
      <path d="M6.5 1L2 3.2v3.8C2 9.8 4 11.8 6.5 12.5 9 11.8 11 9.8 11 7V3.2L6.5 1z"
            stroke="#5A7A00" stroke-width="1.4" fill="none"/>
    </svg>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
                 color:#5A7A00;letter-spacing:0.06em;font-weight:500;">SOC 2 · TYPE II</span>
  </div>
  <div style="width:1px;height:14px;background:rgba(0,0,0,0.10);"></div>
  <div style="display:inline-flex;align-items:center;gap:6px;">
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
      <rect x="2" y="5" width="9" height="6.5" rx="1" stroke="#5A7A00" stroke-width="1.4" fill="none"/>
      <path d="M4 5V3.5a2.5 2.5 0 0 1 5 0V5" stroke="#5A7A00" stroke-width="1.4" fill="none"/>
    </svg>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
                 color:#5A7A00;letter-spacing:0.06em;font-weight:500;">HIPAA SAFE</span>
  </div>
  <div style="width:1px;height:14px;background:rgba(0,0,0,0.10);"></div>
  <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
               color:#222;letter-spacing:0.06em;font-weight:500;">ENTERPRISE READY</span>
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
    <svg width="32" height="36" viewBox="0 0 80 94" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(0,4)">
            <path d="M 40,4 L 72,4 Q 80,4 80,12 L 80,46 C 80,68 60,82 40,90 C 20,82 0,68 0,46 L 0,12 Q 0,4 8,4 Z" fill="#111111"/>
            <polyline points="10,46 20,46 25,32 30,60 35,42 40,50 46,46 70,46" stroke="#C4FF00" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M 8,4 L 0,4 L 0,12" stroke="#C4FF00" stroke-width="2" fill="none" stroke-linecap="round"/>
            <path d="M 72,4 L 80,4 L 80,12" stroke="#C4FF00" stroke-width="2" fill="none" stroke-linecap="round"/>
        </g>
    </svg>
    <div>
        <div style="font-size:15px;font-weight:700;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    color:#111;line-height:1.05;letter-spacing:-0.02em;text-transform:uppercase;">AEGIS&nbsp;AI</div>
        <div style="font-size:9px;color:#222;letter-spacing:0.18em;text-transform:uppercase;
                    font-family:'Inter',system-ui,sans-serif;font-weight:500;margin-top:3px;">
            UNDERWRITING&nbsp;INTELLIGENCE</div>
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
    <div style="font-size:10px;color:#333333;letter-spacing:0.08em;text-transform:uppercase;margin-top:1px;">{_role_label}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        if user["role"] == "hr_admin":
            _company = user.get("org", "Your Company")
            st.markdown(f"""
<div style="background:#F2F2EC;border:1px solid rgba(0,0,0,0.07);border-radius:8px;padding:8px 12px;margin-top:4px;margin-bottom:2px;">
  <div style="font-size:10px;color:#333333;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:3px;">Active Client</div>
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
<div style="background:#111;border:1px solid #1e1e1e;border-radius:10px;
            padding:12px 14px;margin-top:4px;box-shadow:0 4px 16px rgba(0,0,0,0.30);">
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#C4FF00;
                     display:inline-block;flex-shrink:0;
                     box-shadow:0 0 0 4px rgba(196,255,0,0.18);"></span>
        <span style="font-size:10px;color:#C4FF00;font-weight:600;
                     letter-spacing:0.10em;text-transform:uppercase;
                     font-family:'NType82','Space Grotesk',system-ui,sans-serif;">Model Active</span>
    </div>
    <div style="font-family:'LetteraMonoLL','Space Mono',monospace;
                font-size:11px;color:#C4FF00;background:rgba(196,255,0,0.08);
                padding:5px 8px;border-radius:5px;border:1px solid rgba(196,255,0,0.15);
                margin-bottom:6px;">XGBOOST v2.1 · SHAP</div>
    <div style="font-size:11px;color:#AAAAAA;line-height:1.4;">
        Last trained · live underwriting</div>
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
