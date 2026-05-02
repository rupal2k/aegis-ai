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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&display=swap');

/* ═══════════════════════════════════════════════════════════════════
   AEGIS AI — Particle Dark Theme
   Base colours pulled from design_tokens.py NM dict.
   ═══════════════════════════════════════════════════════════════════ */

/* ── Base ──────────────────────────────────────────────────────── */
.stApp { background-color: #070b14 !important; }
body, .stApp, p, li, span, div {
    font-family: 'Inter', system-ui, sans-serif;
    color: #f0f4f8;
}

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0d1424 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] > div:first-child {
    background-color: #0d1424 !important;
}

/* ── Typography ───────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    color: #f0f4f8 !important;
    letter-spacing: -0.025em;
}
h1 { font-size: 1.65rem !important; font-weight: 700 !important; }
h2 { font-size: 1.3rem  !important; font-weight: 700 !important; }
h3 { font-size: 1.05rem !important; font-weight: 400 !important; letter-spacing: -0.01em; }

p, .stMarkdown p { font-family: 'Inter', system-ui, sans-serif !important; color: #94a3b8 !important; }

/* Form labels */
.stTextInput label,
.stSelectbox label,
.stTextArea label,
.stNumberInput label,
[data-testid="stWidgetLabel"] {
    color: #94a3b8 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* ── Metric cards ─────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: #111c30 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-top: 2px solid #84cc16 !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35) !important;
    animation: nm-countUp 0.5s ease both !important;
}
[data-testid="stMetricValue"] {
    color: #f0f4f8 !important;
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 1.75rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
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

/* ── Tabs ─────────────────────────────────────────────────────── */
[data-testid="stTabs"] button {
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    letter-spacing: -0.01em !important;
    transition: color 0.15s !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f0f4f8 !important;
    font-weight: 700 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #84cc16 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Divider ──────────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* ── Bordered containers / cards ──────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #111c30 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.30) !important;
}

/* ── Dataframe ────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stDataFrame"] thead tr th {
    background: #162036 !important;
    color: #64748b !important;
}

/* ── Download buttons ─────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background-color: #162036 !important;
    color: #f0f4f8 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px;
    font-family: 'Inter', system-ui, sans-serif;
    font-weight: 500;
    transition: background 0.15s;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #1e2d4a !important;
}

/* ── Primary buttons — lime accent ───────────────────────────── */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg,#84cc16,#65a30d) !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: -0.01em;
    height: 40px !important;
    transition: opacity 0.15s, transform 0.10s !important;
}
[data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stButton"] > button[kind="primary"] span,
[data-testid="stButton"] > button[kind="primary"] *,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primary"] span,
[data-testid="stBaseButton-primary"] * {
    color: #000000 !important;
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 700 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    opacity: 0.90 !important;
}
/* ── Secondary / default buttons ──────────────────────────────── */
[data-testid="stButton"] > button,
[data-testid="stBaseButton-secondary"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 13px !important;
    background-color: #111c30 !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    height: 40px !important;
    font-weight: 500 !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stButton"] > button p,
[data-testid="stButton"] > button span,
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondary"] span {
    color: #94a3b8 !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background-color: #162036 !important;
    border-color: rgba(132,204,22,0.35) !important;
    color: #f0f4f8 !important;
}
[data-testid="stButton"] > button:hover *,
[data-testid="stBaseButton-secondary"]:hover * {
    color: #f0f4f8 !important;
}
/* Restore primary over base */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg,#84cc16,#65a30d) !important;
    border: none !important;
}
[data-testid="stButton"] > button[kind="primary"] *,
[data-testid="stBaseButton-primary"] * {
    color: #000000 !important;
}

/* ── Captions ─────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Glow metric card ─────────────────────────────────────────── */
[data-testid="stMetric"].nm-glow {
    border-color: rgba(132,204,22,0.45) !important;
    box-shadow: 0 0 24px rgba(132,204,22,0.15), 0 4px 12px rgba(0,0,0,0.30) !important;
}

/* ── Text inputs — compact height ─────────────────────────────── */
[data-baseweb="input"],
[data-baseweb="base-input"] {
    min-height: unset !important;
    height: 40px !important;
    background-color: #162036 !important;
    border-color: rgba(255,255,255,0.12) !important;
    color: #f0f4f8 !important;
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
    color: #f0f4f8 !important;
    background-color: #162036 !important;
}
[data-testid="stTextInput"] [data-testid="stTextInputRootElement"] {
    height: 40px !important;
    min-height: unset !important;
    align-items: center !important;
}

/* ── Form submit button ───────────────────────────────────────── */
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
[data-testid="stFormSubmitButton"] button {
    height: 42px !important;
    min-height: unset !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    font-size: 14px !important;
    line-height: 42px !important;
    background: linear-gradient(135deg,#84cc16,#65a30d) !important;
    color: #000000 !important;
    border: none !important;
    font-family: 'NType82', 'Space Grotesk', system-ui, sans-serif !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 0.90 !important;
}

/* ── Focus rings — accessibility ──────────────────────────────── */
input:focus-visible,
button:focus-visible,
[data-baseweb="input"]:focus-within {
    outline: 2px solid #84cc16 !important;
    outline-offset: 2px !important;
    border-radius: 6px;
}

/* ── Progress bars — lime accent ──────────────────────────────── */
[data-testid="stProgress"] [role="progressbar"] {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 4px !important;
    height: 6px !important;
}
[data-testid="stProgress"] [role="progressbar"] > div {
    background: linear-gradient(90deg, #65a30d, #84cc16) !important;
    border-radius: 4px !important;
}

/* ── Expanders — dark card ────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    background: #111c30 !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.30);
}
[data-testid="stExpander"] summary {
    padding: 10px 16px !important;
    font-size: 13px !important;
    color: #94a3b8 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
[data-testid="stExpander"] summary:hover { color: #f0f4f8 !important; }
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] .stMarkdown p {
    color: #94a3b8 !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
    color: #f0f4f8 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid rgba(132,204,22,0.40) !important;
    padding-left: 12px !important;
    color: #94a3b8 !important;
}

/* ── Alert boxes ──────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Selectbox ────────────────────────────────────────────────── */
[data-baseweb="select"] > div:first-child {
    background-color: #162036 !important;
    border-color: rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    min-height: unset !important;
    height: 40px !important;
}

/* ── Spinner text ─────────────────────────────────────────────── */
[data-testid="stSpinner"] p {
    font-size: 13px !important;
    color: #64748b !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Alert hyperlink buttons ──────────────────────────────────── */
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
    border-radius: 0 !important;
}
.alert-link-btn button:hover { opacity: 0.75 !important; background: transparent !important; }
.alert-link-high button { color: #ef4444 !important; }
.alert-link-med  button { color: #f97316 !important; }
.alert-link-info button { color: #60a5fa !important; }
.alert-link-ok   button { color: #22c55e !important; }

/* ── Selectbox value text ─────────────────────────────────────── */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span { color: #94a3b8 !important; font-size: 13px !important; }

/* ── Text input placeholder + value ──────────────────────────── */
[data-testid="stTextInput"] input::placeholder { color: #475569 !important; }
[data-testid="stTextInput"] input { color: #f0f4f8 !important; }

/* ── Code / mono inline ───────────────────────────────────────── */
code {
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 0.88em !important;
    background: rgba(132,204,22,0.12) !important;
    color: #84cc16 !important;
    padding: 0.15em 0.4em !important;
    border-radius: 4px !important;
    border: 1px solid rgba(132,204,22,0.25) !important;
}

/* ── Scrollbar ────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(132,204,22,0.20); border-radius: 2px; }

/* ── Main block container ─────────────────────────────────────── */
.main .block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
}

/* ── Tab spacing ──────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    height: 2.5px !important;
    border-radius: 2px;
}
[data-testid="stTabs"] button { padding: 10px 18px !important; }

/* ── Number input height ──────────────────────────────────────── */
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="base-input"] { height: 40px !important; }

/* ── Slider — lime accent ─────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #84cc16 !important;
    border: 1.5px solid #65a30d !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div:first-child {
    background: linear-gradient(90deg, #65a30d, #84cc16) !important;
}

/* ── Checkbox ─────────────────────────────────────────────────── */
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div {
    background-color: #84cc16 !important;
    border-color: #65a30d !important;
}

/* ── File uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] section {
    background: #111c30 !important;
    border: 1.5px dashed rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    transition: border-color 0.15s, background 0.15s;
}
[data-testid="stFileUploader"] section:hover {
    border-color: rgba(132,204,22,0.45) !important;
    background: rgba(132,204,22,0.04) !important;
}
[data-testid="stFileUploader"] section button {
    background: linear-gradient(135deg,#84cc16,#65a30d) !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    height: 38px !important;
    font-weight: 700 !important;
}

/* ── Spinner ──────────────────────────────────────────────────── */
[data-testid="stSpinner"] svg circle { stroke: #84cc16 !important; }

/* ── Streamlit alert boxes ────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}
[data-testid="stAlertContainer"][kind="success"],
[data-baseweb="notification"][role="status"] {
    background: rgba(34,197,94,0.08) !important;
    border-left: 3px solid #22c55e !important;
}
[data-testid="stAlertContainer"][kind="info"] {
    background: rgba(96,165,250,0.08) !important;
    border-left: 3px solid #60a5fa !important;
}
[data-testid="stAlertContainer"][kind="warning"] {
    background: rgba(234,179,8,0.08) !important;
    border-left: 3px solid #eab308 !important;
}
[data-testid="stAlertContainer"][kind="error"] {
    background: rgba(239,68,68,0.08) !important;
    border-left: 3px solid #ef4444 !important;
}

/* ── Plotly modebar ───────────────────────────────────────────── */
.modebar-btn:hover svg path { fill: #84cc16 !important; }

/* ── Dataframe cells ──────────────────────────────────────────── */
[data-testid="stDataFrame"] [data-testid="stDataFrameCell"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #94a3b8 !important;
}

/* ── Code block ───────────────────────────────────────────────── */
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] pre {
    background: #0d1424 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-family: 'LetteraMonoLL', 'Space Mono', monospace !important;
    font-size: 12.5px !important;
}

/* ══ LIGHT-TEXT GUARD-RAIL ═══════════════════════════════════════
   Every visible text element on the dark theme must be light.
   !important throughout — Streamlit's own !important defaults
   are overridden by specificity + !important stacking.            */

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] span,
.stCaption, .stCaption p {
    color: #64748b !important;
    font-size: 12.5px !important;
    line-height: 1.55 !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] div,
[data-testid="stMetricLabel"] label {
    color: #64748b !important;
    font-size: 11px !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div { color: #f0f4f8 !important; }
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] div { color: #94a3b8 !important; }

[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] details summary { color: #94a3b8 !important; }

[data-testid="stHeadingWithActionElements"] *,
.stSubheader, .stSubheader * { color: #f0f4f8 !important; }

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
}

/* Plotly tick / legend / annotation */
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text,
.js-plotly-plot .plotly .legendtext,
.js-plotly-plot .plotly .annotation-text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle { fill: #94a3b8 !important; }

/* Form labels everywhere */
.stTextInput label, .stSelectbox label, .stTextArea label,
.stNumberInput label, .stCheckbox label, .stRadio label,
.stSlider label, .stMultiSelect label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    color: #94a3b8 !important;
}

/* Markdown body */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span { color: #94a3b8 !important; }
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 { color: #f0f4f8 !important; }

/* Selectbox */
[data-baseweb="select"] [role="combobox"] *,
[data-baseweb="select"] div[aria-selected],
[data-baseweb="select"] span { color: #94a3b8 !important; }
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
        "width:24px;height:24px;min-width:24px;background:#0d1424;border-radius:6px;"
        "color:#84cc16;font-size:10px;font-weight:700;flex-shrink:0;margin-top:1px;"
        "font-family:'LetteraMonoLL','Space Mono',monospace;"
    )
    st.markdown(f"""
<div style="padding:4px 0 0;">

  <!-- Capability strip -->
  <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:14px;
              font-family:'Inter',system-ui,sans-serif;">PLATFORM CAPABILITIES</div>
  <div style="display:flex;flex-direction:column;gap:14px;margin-bottom:32px;">
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">01</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#f0f4f8;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Predict risk before renewal</div>
        <div style="font-size:13px;color:#94a3b8;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          XGBoost + SHAP score workforce health from claims and HR data, surfacing high-risk segments weeks ahead.</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">02</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#f0f4f8;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Price with confidence</div>
        <div style="font-size:13px;color:#94a3b8;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          Dynamic premium recommendations adjust to risk tier, reducing manual overrides and pricing errors.</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:14px;">
      <span style="{_NUMBER}">03</span>
      <div>
        <div style="font-size:14px;font-weight:700;color:#f0f4f8;
                    font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    letter-spacing:-0.015em;line-height:1.2;margin-bottom:3px;">Prove wellness ROI</div>
        <div style="font-size:13px;color:#94a3b8;line-height:1.55;
                    font-family:'Inter',system-ui,sans-serif;">
          HR managers quantify intervention impact and share renewal-ready reports directly with underwriters.</div>
      </div>
    </div>
  </div>

  <!-- Workspace preview cards -->
  <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:12px;
              font-family:'Inter',system-ui,sans-serif;">YOUR WORKSPACE AFTER SIGN-IN</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:30px;">
    <div style="background:#111c30;border:1px solid rgba(255,255,255,0.07);border-radius:12px;
                padding:16px 18px;box-shadow:0 4px 12px rgba(0,0,0,0.35);">
      <div style="display:inline-flex;align-items:center;gap:6px;
                  background:rgba(132,204,22,0.12);border:1px solid rgba(132,204,22,0.25);
                  border-radius:9999px;padding:2px 9px;margin-bottom:10px;">
        <span style="width:5px;height:5px;border-radius:50%;background:#84cc16;"></span>
        <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:9.5px;
                     font-weight:600;color:#84cc16;letter-spacing:0.08em;text-transform:uppercase;">UNDERWRITER</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:#f0f4f8;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  letter-spacing:-0.015em;margin-bottom:6px;">Full underwriting book</div>
      <div style="font-size:12px;color:#94a3b8;line-height:1.55;
                  font-family:'Inter',system-ui,sans-serif;">
        Portfolio risk · Account review · Premium movement · PDF reports</div>
    </div>
    <div style="background:#111c30;border:1px solid rgba(255,255,255,0.07);border-radius:12px;
                padding:16px 18px;box-shadow:0 4px 12px rgba(0,0,0,0.35);">
      <div style="display:inline-flex;align-items:center;gap:6px;
                  background:rgba(132,204,22,0.12);border:1px solid rgba(132,204,22,0.25);
                  border-radius:9999px;padding:2px 9px;margin-bottom:10px;">
        <span style="width:5px;height:5px;border-radius:50%;background:#84cc16;"></span>
        <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:9.5px;
                     font-weight:600;color:#84cc16;letter-spacing:0.08em;text-transform:uppercase;">HR&nbsp;MANAGER</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:#f0f4f8;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  letter-spacing:-0.015em;margin-bottom:6px;">Single-company scope</div>
      <div style="font-size:12px;color:#94a3b8;line-height:1.55;
                  font-family:'Inter',system-ui,sans-serif;">
        Workforce trends · Key drivers · Wellness ROI · Renewal prep</div>
    </div>
  </div>

  <!-- HRS scale -->
  <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:12px;
              font-family:'Inter',system-ui,sans-serif;">HEALTH RISK SCORE (HRS) SCALE</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <div style="background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.35);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#22c55e;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">0–29 · LOW</div>
    <div style="background:rgba(234,179,8,0.10);border:1px solid rgba(234,179,8,0.35);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#eab308;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">30–59 · MODERATE</div>
    <div style="background:rgba(249,115,22,0.10);border:1px solid rgba(249,115,22,0.35);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#f97316;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;">60–79 · HIGH</div>
    <div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.40);
                border-radius:9999px;padding:4px 12px;font-size:11px;color:#ef4444;
                font-weight:700;white-space:nowrap;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                letter-spacing:0.04em;text-transform:uppercase;animation:nm-criticalPulse 2s infinite;">80+ · CRITICAL</div>
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
<div style="background:#111c30;border:1px solid rgba(255,255,255,0.07);border-radius:10px;
            padding:12px 14px;margin-top:4px;">
    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;
                margin-bottom:6px;font-weight:500;">Session Notes</div>
    <div style="font-size:12px;color:#94a3b8;line-height:1.55;margin-bottom:8px;">
        {role_copy}
    </div>
    <div style="font-size:11px;color:#94a3b8;line-height:1.5;">
        <strong style="color:#f0f4f8;">Currency:</strong> changing the selector updates displayed premium values only.<br>
        <strong style="color:#f0f4f8;">Session:</strong> sign out clears the current dashboard session.
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

  <!-- Logo — Primary on light (design system: Aegis AI Logo - Standalone.html, variant 01) -->
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:30px;">
    <svg width="56" height="64" viewBox="0 0 68 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g transform="translate(0, 4)">
        <path d="M 34,4 L 62,4 Q 68,4 68,10 L 68,40 C 68,58 51,70 34,76 C 17,70 0,58 0,40 L 0,10 Q 0,4 6,4 Z" fill="#111111"/>
        <path d="M 34,12 L 56,12 Q 60,12 60,16 L 60,38 C 60,52 46,62 34,67 C 22,62 8,52 8,38 L 8,16 Q 8,12 12,12 Z" fill="none" stroke="#84cc16" stroke-width="1.5" opacity="0.3"/>
        <polyline points="10,40 18,40 22,28 26,52 30,36 34,44 38,40 58,40" stroke="#84cc16" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M 6,4 L 0,4 L 0,10" stroke="#84cc16" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        <path d="M 62,4 L 68,4 L 68,10" stroke="#84cc16" stroke-width="1.5" fill="none" stroke-linecap="round"/>
      </g>
    </svg>
    <div>
      <div style="font-size:26px;font-weight:700;
                  font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                  color:#f0f4f8;letter-spacing:-0.025em;line-height:1;text-transform:uppercase;">AEGIS&nbsp;AI</div>
      <div style="font-size:10px;color:#84cc16;letter-spacing:0.20em;text-transform:uppercase;
                  font-family:'Inter',system-ui,sans-serif;font-weight:600;margin-top:5px;">
        UNDERWRITING&nbsp;INTELLIGENCE</div>
    </div>
  </div>

  <!-- Brand tagline pill -->
  <div style="display:inline-flex;align-items:center;gap:7px;
              background:rgba(132,204,22,0.12);
              border:1px solid rgba(132,204,22,0.25);
              border-radius:9999px;padding:4px 12px;margin-bottom:18px;">
    <span style="width:6px;height:6px;border-radius:50%;background:#84cc16;
                 animation:nm-pulseRing 2.5s infinite;"></span>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;
                 font-size:10.5px;font-weight:600;color:#84cc16;
                 letter-spacing:0.10em;text-transform:uppercase;">
      AI-POWERED · GROUP INSURANCE</span>
  </div>

  <!-- Hero — brand tagline + sign-in cue -->
  <div style="margin-bottom:8px;">
    <div style="font-size:38px;font-weight:700;
                font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                color:#f0f4f8;letter-spacing:-0.03em;line-height:1.0;">
      Predict.<br>Protect.<br>Perform.</div>
  </div>
  <div style="font-size:14px;color:#94a3b8;margin-top:14px;line-height:1.55;
              font-family:'Inter',system-ui,sans-serif;max-width:380px;
              margin-bottom:26px;">
    AI-powered group insurance underwriting. Score workforce risk, adjust premiums dynamically, and prove wellness ROI — all from one workspace.
  </div>

  <!-- Sign-in eyebrow -->
  <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.14em;
              font-weight:600;margin-bottom:8px;
              font-family:'Inter',system-ui,sans-serif;">SIGN IN TO CONTINUE</div>

</div>
""", unsafe_allow_html=True)

            login_form()

            # Trust signals — security & enterprise compliance row
            st.markdown("""
<div style="display:flex;align-items:center;gap:14px;margin-top:22px;max-width:400px;
            padding-top:14px;border-top:1px solid rgba(255,255,255,0.07);">
  <div style="display:inline-flex;align-items:center;gap:6px;">
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
      <path d="M6.5 1L2 3.2v3.8C2 9.8 4 11.8 6.5 12.5 9 11.8 11 9.8 11 7V3.2L6.5 1z"
            stroke="#84cc16" stroke-width="1.4" fill="none"/>
    </svg>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
                 color:#84cc16;letter-spacing:0.06em;font-weight:500;">SOC 2 · TYPE II</span>
  </div>
  <div style="width:1px;height:14px;background:rgba(255,255,255,0.10);"></div>
  <div style="display:inline-flex;align-items:center;gap:6px;">
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
      <rect x="2" y="5" width="9" height="6.5" rx="1" stroke="#84cc16" stroke-width="1.4" fill="none"/>
      <path d="M4 5V3.5a2.5 2.5 0 0 1 5 0V5" stroke="#84cc16" stroke-width="1.4" fill="none"/>
    </svg>
    <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
                 color:#84cc16;letter-spacing:0.06em;font-weight:500;">HIPAA SAFE</span>
  </div>
  <div style="width:1px;height:14px;background:rgba(255,255,255,0.10);"></div>
  <span style="font-family:'LetteraMonoLL','Space Mono',monospace;font-size:10px;
               color:#64748b;letter-spacing:0.06em;font-weight:500;">ENTERPRISE READY</span>
</div>
""", unsafe_allow_html=True)

        with _rc:
            _render_right_panel()

        return

    # ── Authenticated sidebar ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px;
            border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:12px;">
    <svg width="34" height="40" viewBox="0 0 68 80" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(0, 4)">
            <path d="M 34,4 L 62,4 Q 68,4 68,10 L 68,40 C 68,58 51,70 34,76 C 17,70 0,58 0,40 L 0,10 Q 0,4 6,4 Z" fill="#111111"/>
            <path d="M 34,12 L 56,12 Q 60,12 60,16 L 60,38 C 60,52 46,62 34,67 C 22,62 8,52 8,38 L 8,16 Q 8,12 12,12 Z" fill="none" stroke="#84cc16" stroke-width="1.5" opacity="0.30"/>
            <polyline points="10,40 18,40 22,28 26,52 30,36 34,44 38,40 58,40" stroke="#84cc16" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M 6,4 L 0,4 L 0,10" stroke="#84cc16" stroke-width="1.5" fill="none" stroke-linecap="round"/>
            <path d="M 62,4 L 68,4 L 68,10" stroke="#84cc16" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </g>
    </svg>
    <div>
        <div style="font-size:15px;font-weight:700;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                    color:#f0f4f8;line-height:1.05;letter-spacing:-0.02em;text-transform:uppercase;">AEGIS&nbsp;AI</div>
        <div style="font-size:9px;color:#84cc16;letter-spacing:0.18em;text-transform:uppercase;
                    font-family:'Inter',system-ui,sans-serif;font-weight:600;margin-top:3px;">
            UNDERWRITING&nbsp;INTELLIGENCE</div>
    </div>
</div>
""", unsafe_allow_html=True)
        _name = user.get("name") or user.get("email", "?")
        _parts = _name.split("@")[0].replace(".", " ").split() if "@" in _name else _name.split()
        _initials = "".join(p[0].upper() for p in _parts if p)[:2] or "??"
        _role_label = {"underwriter": "Underwriter", "hr_admin": "HR Manager"}.get(user["role"], user["role"])
        # Role-specific pulse color
        _pulse_css = (
            "animation:nm-criticalPulse 2s infinite;"
            if user["role"] == "hr_admin" else
            "animation:nm-pulseRing 2.5s infinite;"
        )
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
  <div style="width:34px;height:34px;border-radius:50%;
              background:rgba(132,204,22,0.14);border:1px solid rgba(132,204,22,0.30);
              display:flex;align-items:center;justify-content:center;
              font-size:12px;font-weight:700;color:#84cc16;
              font-family:'NType82','Space Grotesk',system-ui,sans-serif;flex-shrink:0;">{_initials}</div>
  <div style="min-width:0;">
    <div style="font-size:13px;font-weight:600;font-family:'NType82','Space Grotesk',system-ui,sans-serif;
                color:#f0f4f8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_name}</div>
    <div style="font-size:10px;color:#64748b;letter-spacing:0.08em;text-transform:uppercase;margin-top:1px;">{_role_label}</div>
  </div>
</div>
<!-- Role badge with live pulse dot -->
<div style="display:inline-flex;align-items:center;gap:6px;
            padding:4px 10px;border-radius:12px;
            background:rgba(132,204,22,0.10);border:1px solid rgba(132,204,22,0.22);
            margin-bottom:8px;">
  <div style="width:5px;height:5px;border-radius:50%;background:#84cc16;flex-shrink:0;{_pulse_css}"></div>
  <span style="font-size:10px;font-weight:600;letter-spacing:0.10em;text-transform:uppercase;color:#84cc16;
               font-family:'NType82','Space Grotesk',system-ui,sans-serif;">{_role_label}</span>
</div>
""", unsafe_allow_html=True)
        if user["role"] == "hr_admin":
            _company = user.get("org", "Your Company")
            st.markdown(f"""
<div style="background:#162036;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:8px 12px;margin-top:4px;margin-bottom:2px;">
  <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.10em;font-weight:500;margin-bottom:3px;">Active Client</div>
  <div style="font-size:13px;font-weight:600;font-family:'NType82','Space Grotesk',system-ui,sans-serif;color:#f0f4f8;">{_company}</div>
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
<div style="background:#111c30;border:1px solid rgba(255,255,255,0.07);border-radius:10px;
            padding:12px 14px;margin-top:4px;box-shadow:0 4px 16px rgba(0,0,0,0.30);">
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#84cc16;
                     display:inline-block;flex-shrink:0;
                     box-shadow:0 0 0 4px rgba(132,204,22,0.20);
                     animation:nm-pulseRing 2s infinite;"></span>
        <span style="font-size:10px;color:#84cc16;font-weight:600;
                     letter-spacing:0.10em;text-transform:uppercase;
                     font-family:'NType82','Space Grotesk',system-ui,sans-serif;">Model Active</span>
    </div>
    <div style="font-family:'LetteraMonoLL','Space Mono',monospace;
                font-size:11px;color:#84cc16;background:rgba(132,204,22,0.08);
                padding:5px 8px;border-radius:5px;border:1px solid rgba(132,204,22,0.20);
                margin-bottom:6px;">XGBOOST v2.1 · SHAP</div>
    <div style="font-size:11px;color:#94a3b8;line-height:1.4;">
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
