"""
Aegis AI — Reusable design helpers — Particle Dark edition.

Canonical building blocks every view/tab/module should use:

    page_header(eyebrow, title, subtitle)   — top-of-page identity strip
    section_header(eyebrow, title, subtitle) — sub-section identity
    hrs_gauge_html(score, size, animated)   — animated SVG arc gauge
    hrs_badge_html(score)                   — traffic-light HRS pill
    metric_card_dark(label, value, ...)     — dark metric card w/ gradient border
    shap_waterfall_html(features)           — bidirectional SHAP bar chart
    apply_chart_theme(fig, **opts)          — single Plotly dark config source
    empty_state(title, hint, ...)           — branded empty state
    status_pill(level, text)               — colored status pill
    risk_band_pill(band)                   — traffic-light risk badge
    inline_note(text, level)               — slim left-bordered note strip
    card(...)                              — dark-themed card component
"""
from __future__ import annotations
import math

import streamlit as st

from dashboard.design_tokens import NM, RISK_BAND_COLORS

# ── Severity → badge palette (bg, border, text) ─────────────────────────────
_SEVERITY_PALETTE = {
    "ok":      ("rgba(34,197,94,0.10)",  "rgba(34,197,94,0.30)",   NM["success"]),
    "info":    ("rgba(96,165,250,0.10)", "rgba(96,165,250,0.28)",  NM["info"]),
    "warning": ("rgba(234,179,8,0.10)",  "rgba(234,179,8,0.28)",   NM["warning"]),
    "error":   ("rgba(239,68,68,0.10)",  "rgba(239,68,68,0.28)",   NM["error"]),
    "neutral": ("rgba(255,255,255,0.05)","rgba(255,255,255,0.10)", NM["text_secondary"]),
}


# ── Internal risk-band helper ────────────────────────────────────────────────
def _hrs_band(score: float) -> str:
    if score < 30:  return "Low"
    if score < 60:  return "Moderate"
    if score < 80:  return "High"
    return "Critical"


# ── HRS Gauge (animated SVG arc) ─────────────────────────────────────────────
def hrs_gauge_html(
    score: float,
    *,
    size: int = 180,
    animated: bool = True,
    show_label: bool = True,
) -> str:
    """Return HTML containing an animated SVG arc gauge for the given HRS score.

    The gauge uses a 270° sweep with four color-zone backgrounds (Low/Moderate/
    High/Critical) and a glowing value arc that animates from 0 → score.
    Include the result in st.markdown(unsafe_allow_html=True).
    """
    band  = _hrs_band(score)
    color = RISK_BAND_COLORS.get(band, "#22c55e")

    r    = 54.0
    circ = 2 * math.pi * r          # ≈ 339.3
    arc  = circ * 0.75               # 270° of the full circle
    # Offset for the filled arc: dashoffset = track_start + (arc - filled_portion)
    track_start = circ * 0.125
    filled      = (score / 100.0) * arc
    offset      = track_start + (arc - filled)

    # Unique ID to avoid CSS collision when multiple gauges on same page
    uid = f"g{int(score * 10)}"

    anim_css = ""
    if animated:
        anim_css = (
            f"<style>"
            f"@keyframes sweep_{uid} {{"
            f"  from {{ stroke-dashoffset: {track_start + arc:.2f}; }}"
            f"  to   {{ stroke-dashoffset: {offset:.2f}; }}"
            f"}}"
            f".arc_{uid} {{"
            f"  animation: sweep_{uid} 1.2s cubic-bezier(.4,0,.2,1) both;"
            f"}}"
            f"</style>"
        )

    # Color-zone backgrounds (Low/Moderate/High/Critical as semi-transparent arcs)
    zones = [
        ("#22c55e", 0.00, 0.30),
        ("#eab308", 0.30, 0.60),
        ("#f97316", 0.60, 0.80),
        ("#ef4444", 0.80, 1.00),
    ]
    zone_arcs = ""
    for c, s, e in zones:
        za   = arc * (e - s)
        zoff = track_start - arc * s
        zone_arcs += (
            f'<circle cx="60" cy="65" r="{r}" fill="none" stroke="{c}"'
            f' stroke-width="8" opacity=".18"'
            f' stroke-dasharray="{za:.2f} {circ - za:.2f}"'
            f' stroke-dashoffset="{zoff:.2f}"'
            f' transform="rotate(135,60,65)"/>'
        )

    w = size
    h = int(size * 100 / 120 * 0.90)

    center_text = ""
    if show_label:
        center_text = (
            f'<text x="60" y="62" text-anchor="middle" fill="{color}" font-size="26"'
            f' font-weight="700" font-family="\'Space Grotesk\',system-ui,sans-serif">'
            f'{int(score)}</text>'
            f'<text x="60" y="74" text-anchor="middle"'
            f' fill="rgba(255,255,255,.30)" font-size="7.5"'
            f' font-family="\'Inter\',system-ui,sans-serif" letter-spacing="1">'
            f'HEALTH RISK SCORE</text>'
            f'<text x="60" y="85" text-anchor="middle" fill="{color}" font-size="8.5"'
            f' font-weight="600" font-family="\'Inter\',system-ui,sans-serif"'
            f' letter-spacing="1.5">{band.upper()}</text>'
        )

    return (
        f"{anim_css}"
        f'<svg width="{w}" height="{h}" viewBox="0 0 120 100" style="overflow:visible;">'
        # Track ring
        f'<circle cx="60" cy="65" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)"'
        f' stroke-width="8"'
        f' stroke-dasharray="{arc:.2f} {circ - arc:.2f}"'
        f' stroke-dashoffset="{track_start:.2f}"'
        f' stroke-linecap="round" transform="rotate(135,60,65)"/>'
        # Zone backgrounds
        f"{zone_arcs}"
        # Value arc (animated)
        f'<circle cx="60" cy="65" r="{r}" fill="none" stroke="{color}"'
        f' stroke-width="8" class="arc_{uid}"'
        f' stroke-dasharray="{arc:.2f} {circ - arc:.2f}"'
        f' stroke-dashoffset="{offset:.2f}"'
        f' stroke-linecap="round" transform="rotate(135,60,65)"'
        f' style="filter:drop-shadow(0 0 7px {color}99);"/>'
        # Center labels
        f"{center_text}"
        f"</svg>"
    )


def render_hrs_gauge(score: float, **kwargs) -> None:
    """Streamlit wrapper — renders the HRS gauge via st.markdown."""
    st.markdown(hrs_gauge_html(score, **kwargs), unsafe_allow_html=True)


# ── HRS Traffic-light Badge ──────────────────────────────────────────────────
def hrs_badge_html(score: float) -> str:
    """Return HTML for a traffic-light HRS badge pill.

    Colored dot · score · band label, all in the band's risk color.
    """
    band  = _hrs_band(score)
    color = RISK_BAND_COLORS.get(band, "#22c55e")
    is_critical = band == "Critical"
    pulse = (
        f"animation:nm-criticalPulse 2s infinite;"
        if is_critical else
        f"animation:nm-pulseRing 2.5s infinite;"
    )
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:3px 10px;border-radius:9999px;'
        f'background:{color}18;border:1px solid {color}44;'
        f'font-size:12px;font-weight:700;color:{color};'
        f'font-family:Inter,system-ui,sans-serif;">'
        f'<span style="width:6px;height:6px;border-radius:50%;background:{color};'
        f'display:inline-block;flex-shrink:0;{pulse}"></span>'
        f'{int(score)}&nbsp;·&nbsp;{band.upper()}</span>'
    )


# ── Dark Metric Card ─────────────────────────────────────────────────────────
def metric_card_dark(
    label: str,
    value: str,
    sub: str | None = None,
    trend_up: bool | None = None,   # True = risk up (orange), False = risk down (green)
    delay: float = 0,
    accent: str | None = None,
) -> str:
    """Return HTML for a dark-theme metric card with gradient top border + fadeIn animation."""
    ac       = accent or NM["accent"]
    sub_color = (NM["risk_high"] if trend_up else NM["risk_low"]) if trend_up is not None else NM["text_secondary"]
    arrow    = ("↑ " if trend_up else "↓ ") if trend_up is not None else ""
    sub_html = (
        f'<div style="font-size:12px;color:{sub_color};margin-top:6px;'
        f'display:flex;align-items:center;gap:3px;">'
        f'<span>{arrow}</span><span>{sub}</span></div>'
    ) if sub else ""
    return (
        f'<div style="padding:20px 22px;border-radius:12px;'
        f'background:{NM["bg_raised"]};border:1px solid {NM["border_default"]};'
        f'position:relative;overflow:hidden;'
        f'animation:nm-countUp 0.5s ease {delay}s both;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        f'background:linear-gradient(to right,{ac}80,transparent);"></div>'
        f'<div style="font-size:11px;color:{NM["text_tertiary"]};letter-spacing:0.08em;'
        f'text-transform:uppercase;margin-bottom:10px;'
        f'font-family:Inter,system-ui,sans-serif;">{label}</div>'
        f'<div style="font-size:28px;font-weight:700;color:{NM["text_primary"]};'
        f'font-family:\'Space Grotesk\',system-ui,sans-serif;line-height:1;">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def render_metric_card_dark(**kwargs) -> None:
    st.markdown(metric_card_dark(**kwargs), unsafe_allow_html=True)


# ── SHAP Bidirectional Waterfall ─────────────────────────────────────────────
def shap_waterfall_html(
    features: list[dict],
    *,
    max_val: float = 20.0,
    show_n: int = 8,
) -> str:
    """Return HTML for a bidirectional SHAP waterfall chart.

    Each feature dict must have:
        name      (str)   — feature label
        value     (float) — SHAP contribution (positive = increases HRS = bad)
        direction (str)   — "negative" (bad, bar goes right) | "positive" (good, left)

    Renders green bars left of center for HRS-reducing features,
    orange→red bars right of center for HRS-increasing features.
    """
    rows = ""
    for f in features[:show_n]:
        pct   = min(abs(f["value"]) / max_val * 100, 100)
        bad   = f["direction"] == "negative"
        color = f"#f97316" if bad else "#22c55e"
        label_color = f"#f97316" if bad else "#22c55e"
        sign  = "+" if bad else "−"

        left_bar = right_bar = ""
        if bad:
            right_bar = (
                f'<div style="width:{pct}%;height:6px;'
                f'background:linear-gradient(to right,#f97316,#ef4444);'
                f'border-radius:0 3px 3px 0;"></div>'
            )
        else:
            left_bar = (
                f'<div style="width:{pct}%;height:6px;'
                f'background:linear-gradient(to left,#22c55e,#16a34a);'
                f'border-radius:3px 0 0 3px;margin-left:auto;"></div>'
            )

        rows += (
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:12px;color:{NM["text_secondary"]};margin-bottom:5px;">'
            f'<span>{f["name"]}</span>'
            f'<span style="font-weight:600;color:{label_color};">'
            f'{sign}{abs(f["value"]):.1f} HRS</span>'
            f'</div>'
            f'<div style="display:flex;gap:4px;align-items:center;">'
            f'<div style="width:50%;display:flex;justify-content:flex-end;">{left_bar}</div>'
            f'<div style="width:1px;height:10px;background:{NM["border_default"]};flex-shrink:0;"></div>'
            f'<div style="width:50%;display:flex;">{right_bar}</div>'
            f'</div>'
            f'</div>'
        )

    legend = (
        f'<div style="display:flex;justify-content:space-between;'
        f'margin-top:16px;font-size:10px;">'
        f'<span style="color:#22c55e;">← HRS Reduction (positive)</span>'
        f'<span style="color:#f97316;">HRS Increase (negative) →</span>'
        f'</div>'
    )
    return (
        f'<div style="background:{NM["bg_raised"]};border:1px solid {NM["border_default"]};'
        f'border-radius:12px;padding:20px 24px;">'
        f'{rows}{legend}'
        f'</div>'
    )


def render_shap_waterfall(features: list[dict], **kwargs) -> None:
    st.markdown(shap_waterfall_html(features, **kwargs), unsafe_allow_html=True)


# ── Page / Section Headers ───────────────────────────────────────────────────
def page_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Render a consistent top-of-page header (dark theme)."""
    sub = (
        f'<div style="font-size:13px;color:{NM["text_secondary"]};margin-top:6px;'
        f'font-family:Inter,system-ui,sans-serif;line-height:1.55;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin:4px 0 6px;animation:nm-fadeIn 0.4s ease both;">'
        f'<div style="font-size:10px;color:{NM["text_tertiary"]};text-transform:uppercase;'
        f'letter-spacing:0.14em;font-weight:600;margin-bottom:6px;'
        f'font-family:Inter,system-ui,sans-serif;">{eyebrow}</div>'
        f'<div style="font-size:28px;font-weight:700;color:{NM["text_primary"]};line-height:1.15;'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;letter-spacing:-0.03em;">'
        f'{title}</div>'
        f'{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Render a consistent sub-section header (dark theme)."""
    sub = (
        f'<div style="font-size:12px;color:{NM["text_secondary"]};margin-top:4px;'
        f'font-family:Inter,system-ui,sans-serif;line-height:1.5;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin:4px 0 10px;">'
        f'<div style="font-size:10px;color:{NM["text_tertiary"]};text-transform:uppercase;'
        f'letter-spacing:0.12em;font-weight:600;margin-bottom:4px;'
        f'font-family:Inter,system-ui,sans-serif;">{eyebrow}</div>'
        f'<div style="font-size:18px;font-weight:700;color:{NM["text_primary"]};'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;letter-spacing:-0.02em;'
        f'line-height:1.25;">{title}</div>'
        f'{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Chart Theme (dark bg) ────────────────────────────────────────────────────
def apply_chart_theme(
    fig,
    *,
    height: int | None = None,
    show_legend: bool = True,
    legend_horizontal: bool = True,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
):
    """Apply the canonical Aegis dark Plotly theme to a figure.

    Every chart in the dashboard MUST go through this helper. Returns the fig
    so it can be chained: `st.plotly_chart(apply_chart_theme(fig), ...)`.
    """
    fig.update_layout(template={})

    layout = dict(
        plot_bgcolor=NM["bg_raised"],
        paper_bgcolor=NM["bg_raised"],
        font=dict(color=NM["text_primary"], family=NM["font_body"], size=12),
        margin=dict(l=0, r=20, t=24, b=40),
        xaxis=dict(
            gridcolor=NM["grid"],
            zeroline=False,
            tickfont=dict(color=NM["text_secondary"], size=12, family=NM["font_body"]),
            tickcolor=NM["text_secondary"],
            color=NM["text_secondary"],
            linecolor=NM["border_default"],
            title_font=dict(color=NM["text_tertiary"], size=12),
            title_standoff=10,
        ),
        yaxis=dict(
            gridcolor=NM["grid"],
            zeroline=False,
            automargin=True,
            tickfont=dict(color=NM["text_secondary"], size=12, family=NM["font_body"]),
            tickcolor=NM["text_secondary"],
            color=NM["text_secondary"],
            linecolor=NM["border_default"],
            title_font=dict(color=NM["text_tertiary"], size=12),
        ),
    )

    if x_range is not None:
        layout["xaxis"]["range"] = list(x_range)
    if y_range is not None:
        layout["yaxis"]["range"] = list(y_range)
    if x_title is not None:
        layout["xaxis"]["title"] = dict(
            text=x_title, font=dict(color=NM["text_tertiary"], size=12)
        )
    if y_title is not None:
        layout["yaxis"]["title"] = dict(
            text=y_title, font=dict(color=NM["text_tertiary"], size=12)
        )
    if height is not None:
        layout["height"] = height

    if not show_legend:
        layout["showlegend"] = False
    else:
        legend = dict(
            font=dict(color=NM["text_secondary"], size=12, family=NM["font_body"]),
            bgcolor="rgba(255,255,255,0.05)",
            bordercolor=NM["border_default"],
            borderwidth=1,
        )
        if legend_horizontal:
            legend.update(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        layout["legend"] = legend

    fig.update_layout(**layout)

    _tick_font   = dict(color=NM["text_secondary"], size=12, family=NM["font_body"])
    _title_font  = dict(color=NM["text_tertiary"], size=12)
    fig.update_xaxes(
        tickfont=_tick_font, tickcolor=NM["text_secondary"],
        color=NM["text_secondary"], title_font=_title_font,
    )
    fig.update_yaxes(
        tickfont=_tick_font, tickcolor=NM["text_secondary"],
        color=NM["text_secondary"], title_font=_title_font,
        automargin=True,
    )

    return fig


# ── Empty State ──────────────────────────────────────────────────────────────
def empty_state(
    title: str,
    hint: str,
    icon_svg: str | None = None,
    cta: str | None = None,
) -> None:
    """Branded empty-state card (dark theme)."""
    icon_html = (
        f'<div style="margin-bottom:14px;opacity:0.60;">{icon_svg}</div>' if icon_svg else ""
    )
    cta_html = (
        f'<div style="font-size:11px;color:{NM["accent_text"]};font-weight:600;'
        f'letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;'
        f'font-family:Inter,system-ui,sans-serif;">{cta}</div>'
        if cta else ""
    )
    st.markdown(
        f'<div style="background:{NM["bg_raised"]};border:1px dashed {NM["border_strong"]};'
        f'border-radius:12px;padding:32px 28px;text-align:center;margin:6px 0;">'
        f'{icon_html}'
        f'<div style="font-size:15px;font-weight:600;color:{NM["text_primary"]};'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;margin-bottom:6px;">'
        f'{title}</div>'
        f'<div style="font-size:13px;color:{NM["text_secondary"]};line-height:1.55;'
        f'max-width:520px;margin:0 auto;font-family:Inter,system-ui,sans-serif;">'
        f'{hint}</div>'
        f'{cta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Status Pill ──────────────────────────────────────────────────────────────
def status_pill(level: str, text: str) -> str:
    """Return HTML for a single status pill (dark theme).

    level ∈ {ok, info, warning, error, neutral}.
    """
    bg, border, color = _SEVERITY_PALETTE.get(level, _SEVERITY_PALETTE["neutral"])
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'background:{bg};border:1px solid {border};color:{color};'
        f'border-radius:9999px;padding:3px 10px;font-size:11px;font-weight:600;'
        f'letter-spacing:0.04em;font-family:LetteraMonoLL,\'Space Mono\',monospace;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{color};"></span>'
        f'{text}</span>'
    )


# ── Risk Band Pill ───────────────────────────────────────────────────────────
def risk_band_pill(band: str) -> str:
    """Traffic-light risk band pill for Low / Moderate / High / Critical."""
    color = RISK_BAND_COLORS.get(band, NM["text_secondary"])
    is_critical = band == "Critical"
    pulse = " animation:nm-criticalPulse 2s infinite;" if is_critical else ""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'background:{color}18;border:1px solid {color}44;color:{color};'
        f'border-radius:9999px;padding:3px 10px;font-size:11px;font-weight:700;'
        f'letter-spacing:0.06em;font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;'
        f'text-transform:uppercase;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{color};{pulse}"></span>'
        f'{band}</span>'
    )


# ── Inline Note ──────────────────────────────────────────────────────────────
def inline_note(text: str, level: str = "info") -> None:
    """Slim left-bordered note strip (dark theme)."""
    bg, border, color = _SEVERITY_PALETTE.get(level, _SEVERITY_PALETTE["info"])
    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};'
        f'border-left:3px solid {color};border-radius:8px;'
        f'padding:10px 14px;margin:4px 0 12px;'
        f'font-size:12.5px;color:{NM["text_secondary"]};line-height:1.55;'
        f'font-family:Inter,system-ui,sans-serif;">{text}</div>',
        unsafe_allow_html=True,
    )


# ── Tag Chip ─────────────────────────────────────────────────────────────────
def tag(text: str, *, mono: bool = False) -> str:
    """Compact dark tag chip for short identifiers."""
    family = (
        "LetteraMonoLL,'Space Mono',monospace" if mono
        else "Inter,system-ui,sans-serif"
    )
    return (
        f'<span style="background:{NM["bg_card_hover"]};color:{NM["text_secondary"]};'
        f'border:1px solid {NM["border_default"]};padding:4px 10px;border-radius:6px;'
        f'font-size:11px;font-family:{family};'
        f'display:inline-block;margin-right:4px;">{text}</span>'
    )


def render_tags(tags: list[str], *, mono: bool = False) -> None:
    st.markdown(
        "".join(tag(t, mono=mono) for t in tags),
        unsafe_allow_html=True,
    )


# ── Divider ──────────────────────────────────────────────────────────────────
def divider(top: int = 18, bottom: int = 18) -> None:
    """A brand-consistent divider with controllable spacing (dark theme)."""
    st.markdown(
        f'<div style="height:1px;background:{NM["border_default"]};'
        f'margin:{top}px 0 {bottom}px;"></div>',
        unsafe_allow_html=True,
    )


# ── Brand Logo ───────────────────────────────────────────────────────────────
def brand_mark_svg(
    width: int = 80,
    *,
    body: str = "#111111",
    accent: str = "#84cc16",
    stroke: float = 2.5,
    show_inner: bool = True,
) -> str:
    """Return the canonical shield+ECG+brackets SVG (dark edition uses lime accent)."""
    height = int(width * 90 / 80)
    inner = (
        f'<path d="M 40,14 L 66,14 Q 72,14 72,20 L 72,44 C 72,62 56,73 40,79 '
        f'C 24,73 8,62 8,44 L 8,20 Q 8,14 14,14 Z" fill="none" '
        f'stroke="{accent}" stroke-width="1.5" opacity="0.25"/>'
        if show_inner else ""
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 80 94" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<g transform="translate(0,4)">'
        f'<path d="M 40,4 L 72,4 Q 80,4 80,12 L 80,46 C 80,68 60,82 40,90 '
        f'C 20,82 0,68 0,46 L 0,12 Q 0,4 8,4 Z" fill="{body}"/>'
        f'{inner}'
        f'<polyline points="10,46 20,46 25,32 30,60 35,42 40,50 46,46 70,46" '
        f'stroke="{accent}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" fill="none"/>'
        f'<path d="M 8,4 L 0,4 L 0,12" stroke="{accent}" stroke-width="2" '
        f'fill="none" stroke-linecap="round"/>'
        f'<path d="M 72,4 L 80,4 L 80,12" stroke="{accent}" stroke-width="2" '
        f'fill="none" stroke-linecap="round"/>'
        f'</g></svg>'
    )


_LOGO_VARIANTS = {
    "primary": {
        "bg": "transparent", "body": "#111111", "accent": "#84cc16",
        "wordmark": "#f0f4f8", "subtitle": "#94a3b8",
        "subtitle_text": "UNDERWRITING INTELLIGENCE",
    },
    "dark": {
        "bg": "#0d1424", "body": "#84cc16", "accent": "#0d1424",
        "wordmark": "#f0f4f8", "subtitle": "#64748b",
        "subtitle_text": "UNDERWRITING INTELLIGENCE",
    },
    "accent": {
        "bg": "#84cc16", "body": "#111111", "accent": "#84cc16",
        "wordmark": "#111111", "subtitle": "rgba(0,0,0,0.55)",
        "subtitle_text": "GROUP INSURANCE",
    },
    "compact": {
        "bg": "#111c30", "body": "#111111", "accent": "#84cc16",
        "wordmark": "#f0f4f8", "subtitle": "#94a3b8",
        "subtitle_text": "GROUP INSURANCE",
    },
}


def brand_logo_html(
    *,
    variant: str = "primary",
    width: int = 64,
    show_wordmark: bool = True,
    show_subtitle: bool = True,
    subtitle: str | None = None,
    stacked: bool = False,
    bordered: bool = False,
) -> str:
    """Return HTML for an Aegis AI brand lockup (dark edition)."""
    if variant == "icon":
        return brand_mark_svg(width=width)

    if variant == "stacked":
        return brand_logo_html(
            variant="dark", width=width, show_wordmark=show_wordmark,
            show_subtitle=show_subtitle, subtitle=subtitle, stacked=True,
            bordered=bordered,
        )

    cfg       = _LOGO_VARIANTS.get(variant, _LOGO_VARIANTS["primary"])
    word_size = max(int(width * 0.50), 16)
    sub_size  = max(int(width * 0.16), 9)
    sub_text  = subtitle if subtitle is not None else cfg["subtitle_text"]

    mark = brand_mark_svg(width=width, body=cfg["body"], accent=cfg["accent"])

    word_block = ""
    if show_wordmark:
        sub = (
            f'<div style="font-family:Inter,system-ui,sans-serif;font-weight:500;'
            f'font-size:{sub_size}px;color:{cfg["subtitle"]};letter-spacing:0.20em;'
            f'text-transform:uppercase;margin-top:4px;">{sub_text}</div>'
            if show_subtitle and sub_text else ""
        )
        rule = (
            f'<div style="height:1.5px;background:#84cc16;border-radius:1px;'
            f'width:60%;margin:6px 0 4px;"></div>'
            if variant == "compact" else ""
        )
        align = "center" if stacked else "flex-start"
        word_block = (
            f'<div style="display:flex;flex-direction:column;align-items:{align};'
            f'line-height:1;">'
            f'<div style="font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;'
            f'font-weight:700;font-size:{word_size}px;color:{cfg["wordmark"]};'
            f'letter-spacing:-0.025em;text-transform:uppercase;line-height:1;">'
            f'AEGIS&nbsp;AI</div>'
            f'{rule}{sub}'
            f'</div>'
        )

    direction  = "column" if stacked else "row"
    gap        = 14 if stacked else max(int(width * 0.22), 12)
    wrap_pad   = "16px 22px" if bordered else "0"
    wrap_border = (
        f"1px solid {NM['border_default']}" if bordered else "none"
    )
    wrap_radius = "14px" if bordered else "0"
    wrap_shadow = "0 1px 4px rgba(0,0,0,0.30)" if bordered else "none"

    return (
        f'<div style="display:inline-flex;flex-direction:{direction};align-items:center;'
        f'gap:{gap}px;background:{cfg["bg"]};padding:{wrap_pad};'
        f'border:{wrap_border};border-radius:{wrap_radius};box-shadow:{wrap_shadow};">'
        f'{mark}{word_block}'
        f'</div>'
    )


def render_brand_logo(**kwargs) -> None:
    """Streamlit-side wrapper — renders the brand logo via st.markdown."""
    st.markdown(brand_logo_html(**kwargs), unsafe_allow_html=True)


# ── Cards ────────────────────────────────────────────────────────────────────
def card(
    *,
    eyebrow: str | None = None,
    title: str | None = None,
    body: str | None = None,
    mono_footer: str | None = None,
    badge: str | None = None,
    variant: str = "default",      # default | accent | inverse
    stat: str | None = None,
    stat_color: str | None = None,
) -> str:
    """Return HTML for a dark-theme Aegis card. Supports default/accent/inverse."""
    if variant == "accent":
        bg, border, shadow, eyebrow_color, body_color = (
            NM["bg_raised"],
            NM["accent_border"],
            "0 4px 20px rgba(132,204,22,0.18)",
            NM["accent_text"],
            NM["text_secondary"],
        )
    elif variant == "inverse":
        bg, border, shadow, eyebrow_color, body_color = (
            "#FFFFFF",
            "rgba(0,0,0,0.10)",
            "0 4px 16px rgba(0,0,0,0.30)",
            "#555555",
            "#333333",
        )
    else:
        bg, border, shadow, eyebrow_color, body_color = (
            NM["bg_raised"],
            NM["border_default"],
            "0 1px 4px rgba(0,0,0,0.25)",
            NM["text_tertiary"],
            NM["text_secondary"],
        )

    title_color = NM["text_inverse"] if variant == "inverse" else NM["text_primary"]

    badge_html = (
        f'<div style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{NM["accent_ghost"]};color:{NM["accent_text"]};'
        f'border:1px solid {NM["accent_border"]};border-radius:9999px;'
        f'padding:2px 9px;font-size:10px;font-weight:600;'
        f'letter-spacing:0.05em;text-transform:uppercase;'
        f'font-family:LetteraMonoLL,\'Space Mono\',monospace;margin-bottom:10px;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{NM["accent_dim"]};"></span>'
        f'{badge}</div>'
        if badge else ""
    )
    eyebrow_html = (
        f'<div style="font-size:10px;color:{eyebrow_color};text-transform:uppercase;'
        f'letter-spacing:0.12em;font-weight:600;margin-bottom:8px;'
        f'font-family:Inter,system-ui,sans-serif;">{eyebrow}</div>'
        if eyebrow else ""
    )
    title_html = (
        f'<div style="font-size:15px;font-weight:600;color:{title_color};'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;'
        f'margin-bottom:4px;line-height:1.25;letter-spacing:-0.01em;">'
        f'{title}</div>'
        if title else ""
    )
    _sc = stat_color or (NM["accent_text"] if variant == "accent" else title_color)
    stat_html = (
        f'<div style="font-size:28px;font-weight:700;color:{_sc};'
        f'line-height:1;margin-bottom:6px;letter-spacing:-0.02em;'
        f'font-family:LetteraMonoLL,\'Space Mono\',monospace;">{stat}</div>'
        if stat else ""
    )
    body_html = (
        f'<div style="font-size:12.5px;color:{body_color};line-height:1.55;'
        f'font-family:Inter,system-ui,sans-serif;">{body}</div>'
        if body else ""
    )
    mono_html = (
        f'<div style="font-family:LetteraMonoLL,\'Space Mono\',monospace;'
        f'font-size:11px;color:{NM["accent_text"]};background:{NM["accent_ghost"]};'
        f'padding:6px 10px;border-radius:6px;margin-top:10px;'
        f'border:1px solid {NM["accent_border"]};">{mono_footer}</div>'
        if mono_footer else ""
    )

    return (
        f'<div style="background:{bg};border:1px solid {border};border-radius:12px;'
        f'padding:18px 20px;box-shadow:{shadow};">'
        f'{badge_html}{eyebrow_html}{stat_html}{title_html}{body_html}{mono_html}'
        f'</div>'
    )


def render_card(**kwargs) -> None:
    st.markdown(card(**kwargs), unsafe_allow_html=True)


def card_grid(cards: list[dict], cols: int = 3) -> None:
    """Render a horizontal grid of cards."""
    columns = st.columns(cols)
    for i, c in enumerate(cards):
        with columns[i % cols]:
            st.markdown(card(**c), unsafe_allow_html=True)


# ── SVG Icons ────────────────────────────────────────────────────────────────
ICON_UPLOAD = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'
)
ICON_DATA = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
    '<path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>'
)
ICON_CHART = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="3" y1="20" x2="21" y2="20"/>'
    '<rect x="6" y="10" width="3" height="10"/>'
    '<rect x="11" y="6" width="3" height="14"/>'
    '<rect x="16" y="13" width="3" height="7"/></svg>'
)
