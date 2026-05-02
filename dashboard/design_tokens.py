"""
Aegis AI — Design system tokens (NullMask) — Particle Dark edition.

Exports `DESIGN_TOKENS_CSS` — a `<style>` block that defines `--nm-*` CSS custom
properties for colors, typography, spacing, radii, and shadows. Inject this
BEFORE any other dashboard CSS so new modules can reference `var(--nm-*)`.

Source: design package + Aegis AI Dashboard.html (dark/Particle Dark variant, May 2026)

Theme: Deep navy dark with lime-green accent (#84cc16) and traffic-light risk colors.
"""

DESIGN_TOKENS_CSS = """
<style>
:root {
    /* ── Backgrounds (dark navy) ─────────────────────── */
    --nm-bg-page:        #070b14;
    --nm-bg-base:        #0d1424;
    --nm-bg-raised:      #111c30;
    --nm-bg-card:        #111c30;
    --nm-bg-card-hover:  #162036;
    --nm-bg-inverse:     #FFFFFF;

    /* ── Brand accent (lime green — dark-mode optimised) */
    --nm-accent:         #84cc16;
    --nm-accent-bright:  #a3e635;
    --nm-accent-dim:     #65a30d;
    --nm-accent-ghost:   rgba(132,204,22,0.12);
    --nm-accent-border:  rgba(132,204,22,0.25);
    --nm-accent-text:    #84cc16;

    /* ── Text (light on dark) ────────────────────────── */
    --nm-text-primary:   #f0f4f8;
    --nm-text-secondary: #94a3b8;
    --nm-text-tertiary:  #64748b;
    --nm-text-muted:     #475569;
    --nm-text-inverse:   #111111;
    --nm-text-accent:    #84cc16;

    /* ── Borders (subtle on dark) ────────────────────── */
    --nm-border-subtle:  rgba(255,255,255,0.04);
    --nm-border-default: rgba(255,255,255,0.07);
    --nm-border-strong:  rgba(255,255,255,0.14);
    --nm-border-accent:  rgba(132,204,22,0.25);

    /* ── Traffic-light risk semantic ─────────────────── */
    --nm-risk-low:       #22c55e;
    --nm-risk-moderate:  #eab308;
    --nm-risk-high:      #f97316;
    --nm-risk-critical:  #ef4444;

    /* ── General semantic ────────────────────────────── */
    --nm-success:        #22c55e;
    --nm-warning:        #eab308;
    --nm-error:          #ef4444;
    --nm-info:           #60a5fa;

    /* ── Shadows / elevation ─────────────────────────── */
    --nm-shadow-sm:      0 1px 3px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.20);
    --nm-shadow-md:      0 4px 12px rgba(0,0,0,0.40), 0 2px 4px rgba(0,0,0,0.20);
    --nm-shadow-lg:      0 8px 28px rgba(0,0,0,0.50), 0 3px 8px rgba(0,0,0,0.20);
    --nm-shadow-accent:  0 4px 20px rgba(132,204,22,0.25);

    /* ── Type families ───────────────────────────────── */
    --nm-font-display:   'NType82', 'Space Grotesk', system-ui, sans-serif;
    --nm-font-body:      'Inter', system-ui, sans-serif;
    --nm-font-mono:      'LetteraMonoLL', 'Space Mono', monospace;

    /* ── Type scale ──────────────────────────────────── */
    --nm-text-2xs:       0.625rem;
    --nm-text-xs:        0.75rem;
    --nm-text-sm:        0.875rem;
    --nm-text-base:      1rem;
    --nm-text-lg:        1.125rem;
    --nm-text-xl:        1.25rem;
    --nm-text-2xl:       1.5rem;
    --nm-text-3xl:       1.875rem;
    --nm-text-4xl:       2.25rem;
    --nm-text-5xl:       3rem;
    --nm-text-6xl:       3.75rem;
    --nm-text-7xl:       4.5rem;

    /* ── Weights ─────────────────────────────────────── */
    --nm-weight-light:   300;
    --nm-weight-regular: 400;
    --nm-weight-medium:  500;
    --nm-weight-bold:    700;

    /* ── Line heights ────────────────────────────────── */
    --nm-leading-tight:  0.95;
    --nm-leading-snug:   1.1;
    --nm-leading-normal: 1.5;
    --nm-leading-relaxed:1.75;

    /* ── Tracking ────────────────────────────────────── */
    --nm-tracking-tight: -0.03em;
    --nm-tracking-snug:  -0.015em;
    --nm-tracking-wide:  0.05em;
    --nm-tracking-caps:  0.12em;

    /* ── Spacing (8px grid) ──────────────────────────── */
    --nm-space-1:   0.25rem;
    --nm-space-2:   0.5rem;
    --nm-space-3:   0.75rem;
    --nm-space-4:   1rem;
    --nm-space-5:   1.25rem;
    --nm-space-6:   1.5rem;
    --nm-space-8:   2rem;
    --nm-space-10:  2.5rem;
    --nm-space-12:  3rem;
    --nm-space-16:  4rem;

    /* ── Radii ───────────────────────────────────────── */
    --nm-radius-sm:   4px;
    --nm-radius-md:   8px;
    --nm-radius-lg:   12px;
    --nm-radius-xl:   16px;
    --nm-radius-pill: 9999px;
}

/* ── Micro-interaction keyframes ─────────────────────── */
@keyframes nm-fadeIn  { from { opacity:0; transform:translateY(8px); }  to { opacity:1; transform:translateY(0); } }
@keyframes nm-slideIn { from { opacity:0; transform:translateX(-10px); } to { opacity:1; transform:translateX(0); } }
@keyframes nm-countUp { from { opacity:0; transform:scale(0.85); }       to { opacity:1; transform:scale(1); } }
@keyframes nm-pulseRing {
  0%,100% { box-shadow: 0 0 0 0 rgba(132,204,22,0.40); }
  50%      { box-shadow: 0 0 0 6px rgba(132,204,22,0); }
}
@keyframes nm-criticalPulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.40); }
  50%      { box-shadow: 0 0 0 5px rgba(239,68,68,0); }
}
@keyframes nm-gaugeSweep {
  from { stroke-dashoffset: 339; }
  to   { stroke-dashoffset: var(--gauge-offset); }
}
</style>
"""


# Python-side convenience constants for Plotly / Matplotlib (can't read CSS vars).
# Synced with the CSS above — dark palette edition.
NM = {
    # Backgrounds
    "bg_page":        "#070b14",
    "bg_base":        "#0d1424",
    "bg_raised":      "#111c30",
    "bg_card":        "#111c30",
    "bg_card_hover":  "#162036",
    "bg_inverse":     "#FFFFFF",

    # Accent — lime green
    "accent":         "#84cc16",
    "accent_bright":  "#a3e635",
    "accent_dim":     "#65a30d",
    "accent_text":    "#84cc16",
    "accent_ghost":   "rgba(132,204,22,0.12)",
    "accent_border":  "rgba(132,204,22,0.25)",

    # Text — light on dark
    "text_primary":   "#f0f4f8",
    "text_secondary": "#94a3b8",
    "text_tertiary":  "#64748b",
    "text_inverse":   "#111111",

    # Borders
    "border_default": "rgba(255,255,255,0.07)",
    "border_strong":  "rgba(255,255,255,0.14)",
    "grid":           "rgba(255,255,255,0.05)",

    # Traffic-light risk colors
    "risk_low":       "#22c55e",
    "risk_moderate":  "#eab308",
    "risk_high":      "#f97316",
    "risk_critical":  "#ef4444",

    # Semantic
    "success":        "#22c55e",
    "warning":        "#eab308",
    "error":          "#ef4444",
    "info":           "#60a5fa",

    # Typography
    "font_display":   "NType82, 'Space Grotesk', system-ui, sans-serif",
    "font_body":      "Inter, system-ui, sans-serif",
    "font_mono":      "LetteraMonoLL, 'Space Mono', monospace",
}

# Risk-band → traffic-light color mapping (canonical for all charts + badges)
RISK_BAND_COLORS = {
    "Low":      "#22c55e",
    "Moderate": "#eab308",
    "High":     "#f97316",
    "Critical": "#ef4444",
}
