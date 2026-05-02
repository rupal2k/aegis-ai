Have to revert back the UI updates break


Fetch this design file, read its readme, and implement the relevant aspects of the design. https://api.anthropic.com/v1/design/h/4Xi3bVqCRUHRwVFTAcJ17A
Implement: Use this design file to redesign the frontend dashboard and make it look more production ready while keeping other project aspects intact


---

## 2026-04-24 — Dashboard bug fixes + Presentation retheme

### Dashboard fixes (commit 50b475c)

**SVG illustrations** — Streamlit's `nh3` sanitizer strips `data:` URIs from both `img src` and CSS `url()`. Fixed all 4 illustration call sites by switching to `_render_illus()` which uses `st.components.v1.html()` (iframe, bypasses nh3 entirely).

**Plotly legend text invisible** — Plotly's default template overrides `layout.font.color` and does not cascade to legend text. Added explicit `legend=dict(font=dict(color=FONT_CLR))` to `_chart_defaults()` in `hr_view.py` and `underwriter_view.py`.

**TypeError: duplicate legend kwarg** — After adding `legend` to `_chart_defaults()`, the pie chart in `hr_view.py` also passed `legend=` explicitly → Python duplicate keyword argument error. Fixed by extracting defaults dict and calling `.update()` on the nested `legend` key before spreading.

**Form labels faint** — Added CSS rule targeting `.stTextInput label` and `[data-testid="stWidgetLabel"]` with `color: #111111 !important` in `app.py`.

**SOC2 illustration cropped** — `_render_illus()` `height_px` was too small for the 400×420 viewBox. Fixed: `width="320px"`, `height_px=360`.

### Presentation retheme (commit bdfe1c0 — vault branch)

Rewrote `Aegis AI - Presentation.md` with NullMask light design system:
- `theme: black` → `theme: white`, background `#E3E3DC`
- All emojis removed
- White card containers (`#FFFFFF`, 12px radius) for all content blocks
- `#C4FF00` chartreuse accent (blockquote borders, tag labels, table headers)
- Tag labels as dark-background chips: PREDICT / PERSONALIZE / OPTIMIZE / EMPOWER
- ∅ logo mark SVG (circle + diagonal slash) on title and closing slides
- Dark closing slide (`#111111`) as brand contrast moment
- Terse, declarative copy throughout — no hedging, no exclamation marks

### Server cleanup
- Cleared all `__pycache__` dirs from repo
- Deleted `export_presentation_pdf.py` (temp utility script)
- Deleted temp `aegis_presentation_print.html` and empty `aegis_ai_presentation.pdf` from Desktop
- Docker prune: no dangling images or volumes

---

## 2026-05-02 — Particle Dark design theme

Applied the **Particle Dark** design template fetched from the Aegis AI Dashboard prototype. Full dark-navy theme across all 7 dashboard files in a single session.

### What changed (commit `370cc0d`)

**`design_tokens.py`** — complete rewrite to dark palette:
- Page background `#070b14`, card/raised `#111c30`, page base `#0d1424`
- Lime green accent `#84cc16` (replacing chartreuse `#C4FF00`)
- Traffic-light risk system: Low `#22c55e` / Moderate `#eab308` / High `#f97316` / Critical `#ef4444`
- Six CSS keyframes: `nm-fadeIn`, `nm-slideIn`, `nm-countUp`, `nm-pulseRing`, `nm-criticalPulse`, `nm-gaugeSweep`

**`design_helpers.py`** — new components added:
- `hrs_gauge_html()` — animated 270° SVG arc gauge with unique per-instance keyframe IDs (avoids animation collision when multiple gauges appear on one page)
- `hrs_badge_html()` — traffic-light pulsing dot badge
- `metric_card_dark()` — dark card with 2px gradient top border and `nm-countUp` animation
- `shap_waterfall_html()` — bidirectional SHAP bars (green left/orange-red right with centre axis)

**`app.py`** — full dark CSS guard-rail, login + sidebar HTML migrated, Model Active card with `nm-pulseRing` dot

**All 5 view files** (`underwriter_view.py`, `hr_view.py`, `upload_view.py`, `currency.py`) — `COLOR_MAP`, `PLOT_BG`, `FONT_CLR`, `ACCENT` constants updated; all inline HTML migrated to dark backgrounds and light text.

### Docker & Git
- Docker dashboard image rebuilt from scratch
- Container restarted (`aegis-dashboard`)
- Pushed to GitHub `origin/main`
- Vault synced and pushed to `origin/vault`

