# Daily Notes — 2026-04-18

**Date**: 2026-04-18  
**Phase**: 5 Complete ✅ (Phase 6 also complete — see [[Phase Progress]])  
**Mood**: ✅ Productive — all major blockers resolved

---

## 🎯 Today's Focus

- [x] Phase 5 checklist complete + verified
- [x] Multi-currency support fully implemented
- [x] All 20 tests passing
- [x] Dashboard UI fixed (light theme, metric cards working)
- [x] Set up Obsidian project tracking

---

## 📊 What Was Done

### Morning: Bug Resolution
1. **Port 8000 issue** → User killed tool runner PIDs, server restarted ✅
2. **pycache stale bytecode** → Cleared `__pycache__`, `/companies` endpoint now works ✅
3. **ModuleNotFoundError** → Added `sys.path.insert` to `app.py` ✅

### Mid-Morning: UI Fixes
1. **Blank metric cards** → Switched from `.stMetric label` CSS to `[data-testid="stMetric"]` ✅
2. **Dark theme conflict** → Created `.streamlit/config.toml` with light theme ✅
3. **Verified UI**: Metrics now display correctly (labels + values) ✅

### Afternoon: Multi-Currency Implementation
1. **Created `dashboard/currency.py`**
   - 10 currencies: INR (base), USD, EUR, GBP, AED, SGD, AUD, JPY, CAD, CHF
   - Functions: `fmt()`, `fmt_crore()`, `sidebar_selector()`
   - All rates relative to INR (1 INR = X foreign)

2. **Updated `dashboard/app.py`**
   - Added `sidebar_selector()` call in sidebar
   - Currency persisted to `st.session_state["currency"]`

3. **Updated `dashboard/underwriter_view.py`**
   - Portfolio metric uses `fmt_crore()`
   - Table columns dynamically rename: `"Base (USD)"`, `"Adjusted (EUR)"`, etc.
   - Column values multiplied by active currency rate
   - PDF download passes `currency=active_code()`

4. **Updated `dashboard/hr_view.py`**
   - All 4 metrics use `fmt()` from currency module
   - Waterfall chart Y values scaled by currency rate
   - Tick prefix uses currency symbol
   - Success message uses `fmt()` for savings

5. **Updated `dashboard/pdf_report.py`**
   - Added `currency: str = "INR"` parameter
   - Inline `_RATES` dict (no Streamlit dependency)
   - `_fmt()` helper for currency-aware formatting
   - Report header shows selected currency
   - Premium table uses `_fmt()` instead of hardcoded "Rs."

### Verification
- ✅ PDF generation works for all 6 tested currencies (INR, USD, EUR, GBP, AED, JPY)
- ✅ All PDFs have valid `%PDF-1.4` headers
- ✅ Currency module imports cleanly
- ✅ All 20 tests still passing (211.66s)

### Evening: Obsidian Setup
- Created foundational vault docs in `C:\Rupalprojects\Rupal\Aegis AI\`:
  `Aegis AI Hub.md`, `Phase Progress.md`, `Architecture Decisions.md`, `Bug Log.md`, `Daily Notes/`
  (Vault later grew to 13 files — see [[INDEX]])

---

## 🧭 Current State

### ✅ Completed
- **Phase 1**: Data generation & schema ✅
- **Phase 2**: ML model training ✅
- **Phase 3**: FastAPI core ✅
- **Phase 4**: Premium calculation ✅
- **Phase 5**: Streamlit dashboard + multi-currency ✅

### ✅ Subsequently Completed
- **Phase 6**: Containerisation & CI/CD — Docker, GitHub Actions, dark mode, 63/63 tests (see [[Phase Progress]])

### 📈 Metrics
- **Lines of code**: ~2000 (dashboard alone)
- **API endpoints**: 11 live
- **Dashboard tabs**: 6 (3 underwriter + 3 HR)
- **Currencies supported**: 10
- **Test coverage**: 20/20 passing (grew to 63/63 by end of Phase 6)
- **Bugs resolved today**: 5 (7 total across all phases)

---

## 🔧 Technical Highlights

### Multi-Currency Architecture
```
User selects currency in sidebar
    ↓
st.session_state["currency"] = "USD"
    ↓
All views call active_code() to get selected currency
    ↓
Monetary values multiplied by CURRENCIES[code]["rate"]
    ↓
Chart tooltips & table cells show converted amounts
    ↓
PDF report generates with currency-specific formatting
```

**Key insight**: By storing rates as `1 INR = X foreign`, all calculations are consistent. No need for bid/ask spreads (not relevant for insurance).

### CSS Safe Pattern
```css
/* ❌ UNSAFE: Hides child elements */
.stMetric label { color: red; }

/* ✅ SAFE: Targets container only */
[data-testid="stMetric"] {
    background-color: #f5f5f7;
    border: 1px solid #e0e0e5;
}

/* Key: Streamlit uses data-testid for stable selectors */
```

### sys.path Fix Pattern
```python
# At top of dashboard/app.py:
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Why: Streamlit adds script dir (/dashboard) to sys.path
# This adds project root instead, so relative imports work
```

---

## 🚦 Blockers Encountered & Resolved

| Blocker | Status | Solution |
|---------|--------|----------|
| Port 8000 held by tool runner | ✅ Fixed | User killed PID from terminal |
| pycache stale bytecode | ✅ Fixed | `find ... -name __pycache__ -delete` |
| ModuleNotFoundError | ✅ Fixed | `sys.path.insert(0, project_root)` |
| Blank metric values | ✅ Fixed | Changed CSS selector + light theme |
| Unicode encode error | ✅ Fixed | Replaced `→` with `->` |

**Total blocker time**: ~50 minutes  
**Resolution approach**: Investigate root cause → targeted fix (not workarounds)

---

## 💡 Key Learnings

1. **Streamlit sys.path is script-centric**
   - When running `streamlit run dashboard/app.py`, only `dashboard/` is added to sys.path
   - Solution: Always `sys.path.insert(0, project_root)` for multi-level imports

2. **CSS selectors matter**
   - `.st*` classes are fragile (change between Streamlit versions)
   - `[data-testid="..."]` is stable (Streamlit's public API)

3. **Pycache is invisible**
   - Hot-reload can load stale bytecode without warning
   - Always clear `__pycache__` after code changes

4. **Currency as `1 INR = X` is canonical**
   - Easier to convert FROM base than TO base
   - All math stays in INR domain, converts at display time

5. **Claude Code tool runner proxy !== OS process**
   - Can't be killed by `taskkill` or `lsof`
   - User must kill from their own terminal (different context)

---

## 📋 Next Steps (Post-Capstone)

All Phase 5 next steps completed in Phase 6. See [[Phase Progress]] for full record.

Remaining roadmap items:
- [ ] OAuth 2.0 / SAML authentication
- [ ] Deploy to cloud (Railway / Render / AWS ECS)
- [ ] Kafka real-time pipeline
- [ ] Model drift monitoring

---

## 🎓 Resources & Links

- **Obsidian vault**: `C:\Rupalprojects\Rupal\Aegis AI\`
- **Repo**: `c:\Rupalprojects\aegis-ai`
- **Phase 5 summary**: [[Phase Progress#Phase 5 Streamlit Dashboard]]
- **All architectural decisions**: [[Architecture Decisions]]

---

## ✨ End of Day Status

**Phase 5**: ✅ **COMPLETE**  
**Dashboard**: ✅ Working (light theme → later upgraded to dark mode in Phase 6)  
**Tests**: ✅ 20/20 passing (grew to 63/63 by Phase 6)  
**Bugs**: ✅ All 5 resolved (2 more found and fixed in Phase 6)  
**Obsidian**: ✅ Set up with foundational docs (vault grew to 13 files)  

**Signed off**: Claude Sonnet 4.6
