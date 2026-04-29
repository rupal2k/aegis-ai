"""
Aegis AI — Reusable design helpers built on top of `design_tokens.py`.

These are the canonical building blocks every new view/tab/module should use:

    page_header(eyebrow, title, subtitle=None)   — top-of-page identity strip
    section_header(eyebrow, title, subtitle=None) — sub-section identity strip
    apply_chart_theme(fig, **opts)               — single Plotly config source
    empty_state(icon_svg, title, hint, cta=None) — branded empty state
    status_pill(level, text)                     — colored pill for inline status
    inline_note(text, level="info")              — slim non-blocking note strip

Anything visible to the user that isn't a Streamlit native widget should go
through one of these helpers. See `design.md` at repo root for the full contract.
"""
from __future__ import annotations

import streamlit as st

from dashboard.design_tokens import NM, RISK_BAND_COLORS

# ── Severity → badge palette (background, border, text) ─────────────────────
_SEVERITY_PALETTE = {
    "ok":      ("rgba(90,138,0,0.08)",  "rgba(90,138,0,0.30)",  NM["success"]),
    "info":    ("rgba(0,96,176,0.08)",  "rgba(0,96,176,0.25)",  NM["info"]),
    "warning": ("rgba(176,96,0,0.08)",  "rgba(176,96,0,0.25)",  NM["warning"]),
    "error":   ("rgba(196,32,32,0.08)", "rgba(196,32,32,0.25)", NM["error"]),
    "neutral": ("rgba(0,0,0,0.05)",     "rgba(0,0,0,0.10)",     NM["text_secondary"]),
}


def page_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Render a consistent top-of-page header.

    Used at the top of `render()` for every primary view (Underwriter, HR).
    The eyebrow line establishes context; the title is the page identity.
    """
    sub = (
        f'<div style="font-size:13px;color:#222222;margin-top:6px;'
        f'font-family:Inter,system-ui,sans-serif;line-height:1.55;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin:4px 0 6px;">'
        f'<div style="font-size:10px;color:#333333;text-transform:uppercase;'
        f'letter-spacing:0.14em;font-weight:600;margin-bottom:6px;'
        f'font-family:Inter,system-ui,sans-serif;">{eyebrow}</div>'
        f'<div style="font-size:28px;font-weight:700;color:#111111;line-height:1.15;'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;letter-spacing:-0.03em;">'
        f'{title}</div>'
        f'{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Render a consistent sub-section header (one level under page_header)."""
    sub = (
        f'<div style="font-size:12px;color:#222222;margin-top:4px;'
        f'font-family:Inter,system-ui,sans-serif;line-height:1.5;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin:4px 0 10px;">'
        f'<div style="font-size:10px;color:#333333;text-transform:uppercase;'
        f'letter-spacing:0.12em;font-weight:600;margin-bottom:4px;'
        f'font-family:Inter,system-ui,sans-serif;">{eyebrow}</div>'
        f'<div style="font-size:18px;font-weight:700;color:#111111;'
        f'font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;letter-spacing:-0.02em;'
        f'line-height:1.25;">{title}</div>'
        f'{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


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
    """Apply the canonical Aegis Plotly theme to a figure.

    Every chart in the dashboard MUST go through this helper so that text
    colors, gridlines, fonts, and margins stay consistent. Returns the fig so
    it can be chained: `st.plotly_chart(apply_chart_theme(fig), ...)`.
    """
    # Strip the Plotly default template first so its color defaults can't bleed
    # through — Plotly charts render inside an iframe and CSS overrides don't reach.
    fig.update_layout(template={})

    layout = dict(
        plot_bgcolor=NM["bg_card"],
        paper_bgcolor=NM["bg_card"],
        font=dict(color=NM["text_primary"], family=NM["font_body"], size=12),
        margin=dict(l=0, r=20, t=24, b=40),
        xaxis=dict(
            gridcolor=NM["grid"],
            zeroline=False,
            tickfont=dict(color=NM["text_primary"], size=12, family=NM["font_body"]),
            tickcolor=NM["text_primary"],
            color=NM["text_primary"],
            linecolor=NM["border_strong"],
            title_font=dict(color=NM["text_secondary"], size=12),
            title_standoff=10,
        ),
        yaxis=dict(
            gridcolor=NM["grid"],
            zeroline=False,
            automargin=True,
            tickfont=dict(color=NM["text_primary"], size=12, family=NM["font_body"]),
            tickcolor=NM["text_primary"],
            color=NM["text_primary"],
            linecolor=NM["border_strong"],
            title_font=dict(color=NM["text_secondary"], size=12),
        ),
    )

    if x_range is not None:
        layout["xaxis"]["range"] = list(x_range)
    if y_range is not None:
        layout["yaxis"]["range"] = list(y_range)
    if x_title is not None:
        layout["xaxis"]["title"] = dict(
            text=x_title, font=dict(color=NM["text_secondary"], size=12)
        )
    if y_title is not None:
        layout["yaxis"]["title"] = dict(
            text=y_title, font=dict(color=NM["text_secondary"], size=12)
        )
    if height is not None:
        layout["height"] = height

    if not show_legend:
        layout["showlegend"] = False
    else:
        legend = dict(
            font=dict(color=NM["text_primary"], size=12, family=NM["font_body"]),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.10)",
            borderwidth=1,
        )
        if legend_horizontal:
            legend.update(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        layout["legend"] = legend

    fig.update_layout(**layout)

    # Explicit per-axis overrides — these take precedence over both template and
    # update_layout when Plotly resolves the final render tree.
    _tick_font = dict(color=NM["text_primary"], size=12, family=NM["font_body"])
    _title_font = dict(color=NM["text_secondary"], size=12)
    fig.update_xaxes(
        tickfont=_tick_font, tickcolor=NM["text_primary"],
        color=NM["text_primary"], title_font=_title_font,
    )
    fig.update_yaxes(
        tickfont=_tick_font, tickcolor=NM["text_primary"],
        color=NM["text_primary"], title_font=_title_font,
        automargin=True,
    )

    return fig


def empty_state(
    title: str,
    hint: str,
    icon_svg: str | None = None,
    cta: str | None = None,
) -> None:
    """Branded empty-state card. Use instead of plain `st.info` for primary
    "no data yet" or "upload to begin" moments."""
    icon_html = (
        f'<div style="margin-bottom:14px;opacity:0.85;">{icon_svg}</div>' if icon_svg else ""
    )
    cta_html = (
        f'<div style="font-size:11px;color:{NM["accent_text"]};font-weight:600;'
        f'letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;'
        f'font-family:Inter,system-ui,sans-serif;">{cta}</div>'
        if cta else ""
    )
    st.markdown(
        f'<div style="background:{NM["bg_card"]};border:1px dashed rgba(0,0,0,0.14);'
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


def status_pill(level: str, text: str) -> str:
    """Return HTML for a single status pill. Inline-safe for joining.

    `level` ∈ {ok, info, warning, error, neutral}.
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


def risk_band_pill(band: str) -> str:
    """Pill specific to the four risk bands (Low/Moderate/High/Critical)."""
    color = RISK_BAND_COLORS.get(band, NM["text_secondary"])
    bg = {
        "Low":      "rgba(90,138,0,0.08)",
        "Moderate": "rgba(176,96,0,0.08)",
        "High":     "rgba(196,32,32,0.08)",
        "Critical": "rgba(139,0,0,0.10)",
    }.get(band, "rgba(0,0,0,0.05)")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'background:{bg};border:1px solid {color}40;color:{color};'
        f'border-radius:9999px;padding:3px 10px;font-size:11px;font-weight:700;'
        f'letter-spacing:0.06em;font-family:NType82,\'Space Grotesk\',system-ui,sans-serif;'
        f'text-transform:uppercase;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{color};"></span>'
        f'{band}</span>'
    )


def inline_note(text: str, level: str = "info") -> None:
    """Slim left-bordered note strip — quieter than `st.info`."""
    bg, border, color = _SEVERITY_PALETTE.get(level, _SEVERITY_PALETTE["info"])
    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};'
        f'border-left:3px solid {color};border-radius:8px;'
        f'padding:10px 14px;margin:4px 0 12px;'
        f'font-size:12.5px;color:{NM["text_primary"]};line-height:1.55;'
        f'font-family:Inter,system-ui,sans-serif;">{text}</div>',
        unsafe_allow_html=True,
    )


def tag(text: str, *, mono: bool = False) -> str:
    """Compact white tag chip — used for short identifiers (industry, region, model)."""
    family = (
        "LetteraMonoLL,'Space Mono',monospace" if mono
        else "Inter,system-ui,sans-serif"
    )
    return (
        f'<span style="background:{NM["bg_card"]};color:{NM["text_secondary"]};'
        f'border:1px solid rgba(0,0,0,0.10);padding:4px 10px;border-radius:6px;'
        f'font-size:11px;font-family:{family};box-shadow:0 1px 2px rgba(0,0,0,0.05);'
        f'display:inline-block;margin-right:4px;">{text}</span>'
    )


def render_tags(tags: list[str], *, mono: bool = False) -> None:
    st.markdown(
        "".join(tag(t, mono=mono) for t in tags),
        unsafe_allow_html=True,
    )


def divider(top: int = 18, bottom: int = 18) -> None:
    """A tighter, brand-consistent divider with controllable spacing."""
    st.markdown(
        f'<div style="height:1px;background:rgba(0,0,0,0.07);'
        f'margin:{top}px 0 {bottom}px;"></div>',
        unsafe_allow_html=True,
    )


# ── Brand logo (canonical from .design-package/.../Aegis AI Logo.html) ──────
# The mark is a SQUARED SHIELD with CORNER BRACKETS and an integrated ECG /
# pulse line. Six lockup variants are supported, matching the design package:
#   primary  — dark shield, chartreuse pulse + brackets, on light
#   dark     — chartreuse shield, dark pulse + brackets, on dark surface
#   compact  — small mark + AEGIS AI wordmark with chartreuse divider rule
#   stacked  — centered mark above stacked AEGIS AI wordmark + tagline
#   accent   — dark mark + chartreuse pulse, on a chartreuse field
#   icon     — mark only

def brand_mark_svg(
    width: int = 80,
    *,
    body: str = "#111111",       # shield fill
    accent: str = "#C4FF00",      # ECG line + corner brackets
    stroke: float = 2.5,
    show_inner: bool = True,      # inner outline at 25% opacity for depth
) -> str:
    """Return the canonical shield+ECG+brackets SVG, color-configurable.

    Aspect ratio is fixed at 80:90 (the design source uses 80×90 viewBox).
    """
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
        # Shield body — squared top, rounded corners, pointed bottom
        f'<path d="M 40,4 L 72,4 Q 80,4 80,12 L 80,46 C 80,68 60,82 40,90 '
        f'C 20,82 0,68 0,46 L 0,12 Q 0,4 8,4 Z" fill="{body}"/>'
        f'{inner}'
        # ECG / pulse polyline
        f'<polyline points="10,46 20,46 25,32 30,60 35,42 40,50 46,46 70,46" '
        f'stroke="{accent}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" fill="none"/>'
        # Corner brackets (top-left and top-right Ls)
        f'<path d="M 8,4 L 0,4 L 0,12" stroke="{accent}" stroke-width="2" '
        f'fill="none" stroke-linecap="round"/>'
        f'<path d="M 72,4 L 80,4 L 80,12" stroke="{accent}" stroke-width="2" '
        f'fill="none" stroke-linecap="round"/>'
        f'</g></svg>'
    )


_LOGO_VARIANTS = {
    "primary": {  # on light surface
        "bg":          "transparent",
        "body":        "#111111",
        "accent":      "#C4FF00",
        "wordmark":    "#111111",
        "subtitle":    "#222222",
        "subtitle_text": "UNDERWRITING INTELLIGENCE",
    },
    "dark": {  # on dark surface
        "bg":          "#111111",
        "body":        "#C4FF00",
        "accent":      "#111111",
        "wordmark":    "#FFFFFF",
        "subtitle":    "#888888",
        "subtitle_text": "UNDERWRITING INTELLIGENCE",
    },
    "accent": {  # on chartreuse field
        "bg":          "#C4FF00",
        "body":        "#111111",
        "accent":      "#C4FF00",
        "wordmark":    "#111111",
        "subtitle":    "rgba(0,0,0,0.55)",
        "subtitle_text": "GROUP INSURANCE",
    },
    "compact": {  # white card
        "bg":          "#FFFFFF",
        "body":        "#111111",
        "accent":      "#C4FF00",
        "wordmark":    "#111111",
        "subtitle":    "#222222",
        "subtitle_text": "GROUP INSURANCE",
    },
}


def brand_logo_html(
    *,
    variant: str = "primary",     # primary | dark | accent | compact | stacked | icon
    width: int = 64,              # mark width in px (height auto from 80:90)
    show_wordmark: bool = True,
    show_subtitle: bool = True,
    subtitle: str | None = None,  # override default subtitle
    stacked: bool = False,        # mark above wordmark instead of beside
    bordered: bool = False,       # wrap in a card with border + shadow
) -> str:
    """Return HTML for an Aegis AI brand lockup matching the design package."""
    if variant == "icon":
        return brand_mark_svg(width=width)

    if variant == "stacked":
        return brand_logo_html(
            variant="dark", width=width, show_wordmark=show_wordmark,
            show_subtitle=show_subtitle, subtitle=subtitle, stacked=True,
            bordered=bordered,
        )

    cfg = _LOGO_VARIANTS.get(variant, _LOGO_VARIANTS["primary"])
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
            f'<div style="height:1.5px;background:#C4FF00;border-radius:1px;'
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

    direction = "column" if stacked else "row"
    gap = 14 if stacked else max(int(width * 0.22), 12)
    align = "center" if stacked else "center"

    wrap_padding = "16px 22px" if bordered else "0"
    wrap_border  = (
        "1px solid rgba(0,0,0,0.08)" if bordered and variant != "dark"
        else ("1px solid #222" if bordered and variant == "dark" else "none")
    )
    wrap_radius  = "14px" if bordered else "0"
    wrap_shadow  = "0 1px 4px rgba(0,0,0,0.06)" if bordered else "none"

    return (
        f'<div style="display:inline-flex;flex-direction:{direction};align-items:{align};'
        f'gap:{gap}px;background:{cfg["bg"]};padding:{wrap_padding};'
        f'border:{wrap_border};border-radius:{wrap_radius};box-shadow:{wrap_shadow};">'
        f'{mark}{word_block}'
        f'</div>'
    )


def render_brand_logo(**kwargs) -> None:
    """Streamlit-side wrapper — renders the brand logo via st.markdown."""
    st.markdown(brand_logo_html(**kwargs), unsafe_allow_html=True)


# ── Cards (default / accent / inverse) ──────────────────────────────────────
# Spec from .design-package/.../components-cards.html

def card(
    *,
    eyebrow: str | None = None,
    title: str | None = None,
    body: str | None = None,
    mono_footer: str | None = None,
    badge: str | None = None,
    variant: str = "default",        # default | accent | inverse
    stat: str | None = None,
    stat_color: str | None = None,
) -> str:
    """Return HTML for a Aegis-styled card. Supports default / accent / inverse
    variants per the design package, with optional eyebrow, badge, large stat,
    and a monospace footer line for status readouts."""
    if variant == "accent":
        bg, border, shadow, eyebrow_color, body_color = (
            NM["bg_card"], "rgba(150,200,0,0.40)",
            "0 4px 20px rgba(196,255,0,0.20)",
            NM["accent_text"], NM["text_secondary"],
        )
    elif variant == "inverse":
        bg, border, shadow, eyebrow_color, body_color = (
            NM["bg_inverse"], "#222222",
            "0 4px 16px rgba(0,0,0,0.30)",
            "#888888", "#AAAAAA",
        )
    else:
        bg, border, shadow, eyebrow_color, body_color = (
            NM["bg_card"], NM["border_default"],
            NM["text_primary"] and "0 1px 4px rgba(0,0,0,0.07)",
            NM["text_tertiary"], NM["text_secondary"],
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
    stat_color = stat_color or (NM["accent_text"] if variant == "accent" else title_color)
    stat_html = (
        f'<div style="font-size:28px;font-weight:700;color:{stat_color};'
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
    if variant == "inverse" and mono_footer:
        mono_html = (
            f'<div style="font-family:LetteraMonoLL,\'Space Mono\',monospace;'
            f'font-size:11px;color:{NM["accent"]};'
            f'background:rgba(196,255,0,0.08);padding:6px 10px;border-radius:6px;'
            f'margin-top:10px;border:1px solid rgba(196,255,0,0.15);">{mono_footer}</div>'
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
    """Render a horizontal grid of cards — pass a list of `card(**kwargs)` dicts."""
    columns = st.columns(cols)
    for i, c in enumerate(cards):
        with columns[i % cols]:
            st.markdown(card(**c), unsafe_allow_html=True)


# Common SVG icons for empty states (1.5px stroke, geometric — matches design.md).
ICON_UPLOAD = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'
)
ICON_DATA = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
    '<path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>'
)
ICON_CHART = (
    '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" '
    'stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="3" y1="20" x2="21" y2="20"/>'
    '<rect x="6" y="10" width="3" height="10"/>'
    '<rect x="11" y="6" width="3" height="14"/>'
    '<rect x="16" y="13" width="3" height="7"/></svg>'
)
