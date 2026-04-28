"""
Aegis AI — Design system tokens (NullMask).

Exports `DESIGN_TOKENS_CSS` — a `<style>` block that defines `--nm-*` CSS custom
properties for colors, typography, spacing, radii, and shadows. Inject this
BEFORE any other dashboard CSS so new modules can reference `var(--nm-*)`.

Source: design package at .design-package/project/colors_and_type.css
        (Aegis AI Design System — April 2026)

This module is purely additive. It does NOT override existing inline colors in
already-built views. Existing hardcoded values continue to work unchanged.
"""

DESIGN_TOKENS_CSS = """
<style>
:root {
    /* ── Backgrounds ─────────────────────────────── */
    --nm-bg-page:        #E3E3DC;
    --nm-bg-base:        #EAEAE4;
    --nm-bg-raised:      #F2F2EC;
    --nm-bg-card:        #FFFFFF;
    --nm-bg-card-hover:  #F8F8F4;
    --nm-bg-inverse:     #111111;

    /* ── Brand accent (chartreuse) ───────────────── */
    --nm-accent:         #C4FF00;
    --nm-accent-bright:  #D4FF33;
    --nm-accent-dim:     #9BC800;
    --nm-accent-ghost:   rgba(196,255,0,0.14);
    --nm-accent-border:  rgba(150,200,0,0.40);
    --nm-accent-text:    #5A7A00;

    /* ── Text ─────────────────────────────────────
       Project rule (feedback_text_colors): pale greys are banned for
       USER-FACING TEXT on the light theme. Use --nm-text-secondary
       (#444) for muted copy and --nm-text-tertiary (#333) for labels.
       --nm-text-muted (#999) exists for parity with the design package
       but should only be used on dark/inverse surfaces. */
    --nm-text-primary:   #111111;
    --nm-text-secondary: #444444;
    --nm-text-tertiary:  #333333;
    --nm-text-muted:     #999999;
    --nm-text-inverse:   #FFFFFF;
    --nm-text-accent:    #5A7A00;

    /* ── Borders ─────────────────────────────────── */
    --nm-border-subtle:  rgba(0,0,0,0.05);
    --nm-border-default: rgba(0,0,0,0.08);
    --nm-border-strong:  rgba(0,0,0,0.16);
    --nm-border-accent:  rgba(150,200,0,0.40);

    /* ── Semantic ────────────────────────────────── */
    --nm-success:        #5A8A00;
    --nm-warning:        #B06000;
    --nm-error:          #C42020;
    --nm-error-dark:     #8B0000;
    --nm-info:           #0060B0;

    /* ── Shadows / elevation ─────────────────────── */
    --nm-shadow-sm:      0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05);
    --nm-shadow-md:      0 4px 12px rgba(0,0,0,0.10), 0 2px 4px rgba(0,0,0,0.06);
    --nm-shadow-lg:      0 8px 28px rgba(0,0,0,0.12), 0 3px 8px rgba(0,0,0,0.06);
    --nm-shadow-accent:  0 4px 20px rgba(196,255,0,0.30);

    /* ── Type families ───────────────────────────── */
    --nm-font-display:   'NType82', 'Space Grotesk', system-ui, sans-serif;
    --nm-font-body:      'Inter', system-ui, sans-serif;
    --nm-font-mono:      'LetteraMonoLL', 'Space Mono', monospace;

    /* ── Type scale ──────────────────────────────── */
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

    /* ── Weights ─────────────────────────────────── */
    --nm-weight-light:   300;
    --nm-weight-regular: 400;
    --nm-weight-medium:  500;
    --nm-weight-bold:    700;

    /* ── Line heights ────────────────────────────── */
    --nm-leading-tight:  0.95;
    --nm-leading-snug:   1.1;
    --nm-leading-normal: 1.5;
    --nm-leading-relaxed:1.75;

    /* ── Tracking ────────────────────────────────── */
    --nm-tracking-tight: -0.03em;
    --nm-tracking-snug:  -0.015em;
    --nm-tracking-wide:  0.05em;
    --nm-tracking-caps:  0.12em;

    /* ── Spacing (8px grid) ──────────────────────── */
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

    /* ── Radii ───────────────────────────────────── */
    --nm-radius-sm:   4px;
    --nm-radius-md:   8px;
    --nm-radius-lg:   12px;
    --nm-radius-xl:   16px;
    --nm-radius-pill: 9999px;
}
</style>
"""


# Python-side convenience constants for plotly / matplotlib that can't read CSS vars.
# Keep these in sync with the CSS above.
NM = {
    "bg_page":        "#E3E3DC",
    "bg_base":        "#EAEAE4",
    "bg_raised":      "#F2F2EC",
    "bg_card":        "#FFFFFF",
    "bg_inverse":     "#111111",

    "accent":         "#C4FF00",
    "accent_bright":  "#D4FF33",
    "accent_dim":     "#9BC800",
    "accent_text":    "#5A7A00",
    "accent_ghost":   "rgba(196,255,0,0.14)",
    "accent_border":  "rgba(150,200,0,0.40)",

    "text_primary":   "#111111",
    "text_secondary": "#444444",
    "text_tertiary":  "#333333",
    "text_inverse":   "#FFFFFF",

    "border_default": "rgba(0,0,0,0.08)",
    "border_strong":  "rgba(0,0,0,0.16)",
    "grid":           "rgba(0,0,0,0.06)",

    "success":        "#5A8A00",
    "warning":        "#B06000",
    "error":          "#C42020",
    "error_dark":     "#8B0000",
    "info":           "#0060B0",

    "font_display":   "NType82, 'Space Grotesk', system-ui, sans-serif",
    "font_body":      "Inter, system-ui, sans-serif",
    "font_mono":      "LetteraMonoLL, 'Space Mono', monospace",
}

# Risk-band → color mapping (canonical for all charts)
RISK_BAND_COLORS = {
    "Low":      "#5A8A00",
    "Moderate": "#B06000",
    "High":     "#C42020",
    "Critical": "#8B0000",
}
