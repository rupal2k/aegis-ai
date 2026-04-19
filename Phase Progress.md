# Phase Progress — Aegis AI

**Last Updated**: 2026-04-18  
**Overall Status**: Phase 6 ✅ Complete — All phases done

---

## Phase 1: Data Setup & Ingestion ✅

**Completed**: Yes  
**Commits**: `48dfbef`, `dc9d3aa`, `4f9b401`

### Checklist
- [x] Generate synthetic employee health data (10,000 records)
- [x] Create PostgreSQL/SQLite schema (companies, employees, training_snapshots)
- [x] Build data pipeline (`ingestion/pipeline.py`)
- [x] Validate data quality (null checks, range validation)
- [x] Load data via CLI: `python -m ingestion.pipeline load`

### Files
- `ingestion/schema.py` — SQLAlchemy ORM models
- `ingestion/pipeline.py` — ETL logic
- `ingestion/synthetic_data.py` — Fake data generation

### Notes
- Synthetic data includes realistic health metrics (BMI, resting HR, steps, sleep, etc.)
- Database supports both SQLite (dev) and PostgreSQL (prod)

---

## Phase 2: ML Model Training ✅

**Completed**: Yes  
**Commits**: `0c4379e`, `e4ab265`

### Checklist
- [x] Split data into train/test (80/20)
- [x] Train XGBoost model on health features
- [x] Calculate SHAP feature importance
- [x] Persist model & SHAP explainer to disk
- [x] Compute risk bands (Low, Moderate, High, Critical) via percentile binning

### Files
- `ml/trainer.py` — Model training pipeline
- `ml/explainer.py` — SHAP integration
- `ml/models/` — Saved XGBoost model + explainer

### Model Performance
- Features: 20 health variables
- Output: Health Risk Score (HRS, 0–100), loss ratio prediction
- Inference: ~50ms per company

### Notes
- SHAP provides top 5 feature importance scores per prediction (used in dashboard)
- Risk bands are calculated from HRS percentiles (automatically calibrated)

---

## Phase 3: FastAPI Backend Core ✅

**Completed**: Yes  
**Commit**: `c0da6cf` (module 4 complete)

### Checklist
- [x] Set up FastAPI app on port 8000
- [x] Build `/predict/company/{id}` endpoint
- [x] Build `/predict/employee` endpoint (single prediction)
- [x] Implement health risk scoring logic
- [x] Add authentication (JWT / bearer token)
- [x] Add request validation (Pydantic models)

### Files
- `ingestion/main.py` — FastAPI app
- `ingestion/routers/predictions.py` — Prediction endpoints

### Endpoints (Phase 3)
```
GET /health                          → API health check
GET /companies                       → List all companies (Phase 5)
GET /companies/{id}/employees       → Company employee snapshot (Phase 5)
POST /predict/company/{id}          → Get company HRS, risk bands, top drivers
POST /predict/employee              → Single employee prediction
POST /predict/premium               → Calculate adjusted premium
POST /predict/wellness-roi          → ROI simulator
```

### Notes
- All endpoints cached via Streamlit `@st.cache_data(ttl=60)`
- Database queries use SQLAlchemy ORM

---

## Phase 4: Premium Calculation & Decision Endpoints ✅

**Completed**: Yes  
**Commit**: `252c2f6` (Phase 4 check complete)

### Checklist
- [x] Build premium adjustment algorithm (HRS → adjustment %)
- [x] Implement zone-based pricing (metro, tier-2, tier-3)
- [x] Build `/predict/premium` endpoint
- [x] Add underwriting recommendation logic (Accept, Review, Decline)
- [x] Build `/predict/wellness-roi` endpoint

### Files
- `ingestion/routers/predictions.py` — Premium logic

### Premium Algorithm
```
Adjusted Premium = Base Premium × (1 + adjustment_factor)
adjustment_factor = (HRS - 50) / 100  [scaled from mean=50]

Zone Assignment:
  - metro: multiplier 1.0×
  - tier-2: multiplier 0.85×
  - tier-3: multiplier 0.70×
```

### Underwriting Recommendation
```
HRS < 35          → "Accept (low risk)"
35 ≤ HRS < 65    → "Review (moderate risk)"
65 ≤ HRS < 85    → "Conditional Accept (high risk)"
HRS ≥ 85         → "Decline (critical risk)"
```

### Notes
- Wellness ROI simulator allows HR to project premium savings from HRS reduction
- All calculations are deterministic (no randomness)

---

## Phase 5: Streamlit Dashboard ✅

**Completed**: Yes  
**Commits**: `8485c41` (Phase 5 completed), plus `0c4379e`, `e4ab265`

### Checklist - Backend Endpoints
- [x] New `/companies` read-only router (list + per-company employees)
- [x] Register router in `ingestion/main.py`
- [x] Test endpoints return correct schema

### Checklist - Dashboard Infrastructure
- [x] Create `dashboard/` package with `__init__.py`
- [x] Build `dashboard/api_client.py` (httpx helpers + caching)
- [x] Build `dashboard/auth.py` (login form, 3 demo users)
- [x] Build `dashboard/pdf_report.py` (ReportLab PDF generation)
- [x] Build `dashboard/currency.py` (10 currencies, fmt helpers)
- [x] Build `dashboard/app.py` (main entry + routing)
- [x] Create `.streamlit/config.toml` (light theme)

### Checklist - Dashboard Views
- [x] **Underwriter View** (`underwriter_view.py`)
  - [x] Portfolio overview (bar chart by risk)
  - [x] Ranked table (all companies, sortable)
  - [x] Company deep dive (gauge, risk breakdown)
  - [x] Top risk drivers (5 features, importance scores)
  - [x] Underwriting decision (recommendation + PDF download)
  - [x] Risk distribution histogram
  - [x] Industry risk profile

- [x] **HR Manager View** (`hr_view.py`)
  - [x] Workforce overview (pie chart, key metrics)
  - [x] Age vs claims scatter plot
  - [x] Top risk drivers (SHAP importance)
  - [x] Recommended interventions (3 actions)
  - [x] Wellness ROI simulator (waterfall, savings projection)

### Checklist - Multi-Currency Support
- [x] Create currency module with 10 currencies
- [x] Add `fmt()`, `fmt_crore()`, `sidebar_selector()` functions
- [x] Update underwriter view to use currency helpers
- [x] Update HR view to use currency helpers
- [x] Update PDF report generator for currency
- [x] Persist currency selection in `st.session_state`
- [x] All monetary values update dynamically

### Files
- `dashboard/__init__.py` — Empty package marker
- `dashboard/api_client.py` — httpx + caching layer
- `dashboard/auth.py` — Login, logout, session state
- `dashboard/pdf_report.py` — ReportLab PDF generation
- `dashboard/currency.py` — Currency conversion + formatting
- `dashboard/app.py` — Entry point + role-based routing
- `dashboard/underwriter_view.py` — 3 tabs for underwriters
- `dashboard/hr_view.py` — 3 tabs for HR managers
- `.streamlit/config.toml` — Light theme config

### Demo Users
```
Email: underwriter@safenet.com | Role: underwriter | Password: demo123
Email: hr@technova.com         | Role: hr_admin    | Company: COMP_001 | Password: demo123
Email: hr@bharatsteel.com      | Role: hr_admin    | Company: COMP_002 | Password: demo123
```

### Test Coverage
- 20 automated tests (all passing)
- Test execution time: 211.66 seconds
- Classes: TestAuth, TestCompaniesEndpoint, TestUnderwriterPortfolio, TestHRView, TestWellnessROI, TestPDFReport

### Major Issues Fixed
| Issue | Root Cause | Fix |
|-------|-----------|-----|
| ModuleNotFoundError | Streamlit sys.path | `sys.path.insert(0, project_root)` in `app.py` |
| Blank metric values | Dark theme CSS `.stMetric label` | Switched to `[data-testid="stMetric"]` |
| Stale bytecode | Old `.pyc` files | Cleared `__pycache__` directories |
| Port 8000 in use | Tool runner proxy | User killed PID from terminal |

### Notes
- Dashboard uses Apple's color palette (iOS-style green/orange/red)
- All API calls cached to reduce server load (60-second TTL)
- PDF reports are dynamic (currency-aware, formatted per selection)
- Light theme ensures good readability for B2B context

---

## Phase 6: Containerisation & CI/CD ✅

**Completed**: Yes  
**Date**: 2026-04-18  
**Commits**: `b8007d3`, `dd57169`, `01816bb`

### Checklist — Docker
- [x] `Dockerfile.api` — python:3.11-slim, installs deps, runs bootstrap + uvicorn
- [x] `Dockerfile.dashboard` — python:3.11-slim, Streamlit with env config
- [x] `docker-compose.yml` — 4 services: db, mlflow, api, dashboard
- [x] `.dockerignore` — excludes venv, pycache, data/output, artifacts
- [x] `requirements.docker.txt` — clean UTF-8 deps (original requirements.txt is UTF-16 encoded)
- [x] Health checks on all services (pg_isready, /health, /_stcore/health)
- [x] `depends_on: db: condition: service_healthy` — API waits for DB

### Checklist — Bootstrap
- [x] `scripts/bootstrap.py` — idempotent: checks data/DB/model before each step
- [x] `scripts/entrypoint.sh` — runs bootstrap then `exec uvicorn`
- [x] Step 1: Generate data CSVs (skipped if exist)
- [x] Step 2: Load CSVs to Postgres (skipped if DB already seeded)
- [x] Step 3: Train XGBoost model (skipped if .pkl artifacts exist)

### Checklist — CI/CD
- [x] `.github/workflows/ci.yml` — two jobs: test + docker-build
- [x] `test` job: Ubuntu + Postgres service container, runs all tests
- [x] `docker-build` job: builds API + dashboard images (no push), GHA layer cache
- [x] `AEGIS_CI_FAST=1` reduces Optuna from 30 → 5 trials in CI

### Checklist — Documentation
- [x] `README.md` replaced with full professional README
- [x] Architecture diagram, quick start, API reference, demo credentials, roadmap

### Checklist — Verified Working
- [x] Clean `docker-compose build --no-cache` succeeded
- [x] `docker-compose up -d` starts all 4 services
- [x] Dashboard accessible at http://localhost:8501
- [x] API docs at http://localhost:8000/docs
- [x] MLflow UI at http://localhost:5000
- [x] 63/63 tests passing (`python -m pytest tests/ -v`)
- [x] Pushed to GitHub — CI badge at `rupal2k/aegis-ai`

### Bugs Fixed During Phase 6
| Bug | Cause | Fix |
|-----|-------|-----|
| BUG-006: Dashboard connection refused | `localhost` doesn't resolve cross-container | Read `AEGIS_API_URL` env var |
| BUG-007: Metric text invisible | Light theme config + no explicit color CSS | Full dark mode overhaul |

### Dark Mode Implementation
- `.streamlit/config.toml`: `base="dark"`, `backgroundColor="#0d0d0f"`
- Explicit `[data-testid="stMetricValue"]` CSS — immune to theme inheritance issues
- Chart colors updated: `PLOT_BG="#1c1c1e"`, `FONT_CLR="#f5f5f7"`, `ACCENT="#0a84ff"`

### Key Technical Decisions
- `requirements.docker.txt` created separately — original `requirements.txt` is UTF-16 encoded (spaces between every character), pip cannot parse it
- `restart: unless-stopped` on all services — bootstrap is idempotent so container restarts are safe
- `N_OPTUNA_TRIALS = 5 if AEGIS_CI_FAST else 30` — CI pipeline stays under 2 minutes

### Bootstrap Sequence (First `docker-compose up`)
```
docker-compose up -d
    ↓
db starts → healthcheck passes (pg_isready)
    ↓
api starts (depends_on: db healthy)
    ↓
scripts/entrypoint.sh:
    python scripts/bootstrap.py
        [1/3] Generate data CSVs (if missing)    ~30s
        [2/3] Load CSVs to Postgres (if empty)   ~10s
        [3/3] Train XGBoost model (if no pkl)    ~3min
    exec uvicorn ingestion.main:app
    ↓
dashboard starts (depends_on: api)
```

### Test Suite Results
```
63 passed in 73.98s
```

| File | Tests | What it covers |
|------|-------|---------------|
| `test_api.py` | 8 | Ingestion endpoints, Pydantic validation |
| `test_dashboard.py` | 20 | Auth, companies, portfolio, HR, wellness ROI, PDF |
| `test_data.py` | 7 | Data quality, correlations, anonymization |
| `test_ml_engine.py` | 11 | Feature engineering, HRS scorer, premium zones |
| `test_normalizer.py` | 7 | SHA-256 hashing, clamping, wearable/clinical normalisation |
| `test_predict_api.py` | 10 | Prediction endpoints, SHAP drivers, premium API |

### Dark Mode Colour Palette
| Token | Value | Usage |
|-------|-------|-------|
| Page background | `#0d0d0f` | `.stApp` |
| Card / sidebar | `#1c1c1e` | Metric cards, sidebar |
| Border | `#3a3a3c` | Card borders, dividers, grid lines |
| Primary text | `#f5f5f7` | Headings, metric values |
| Muted text | `#aeaeb2` | Labels, captions |
| Accent | `#0a84ff` | iOS-style blue, charts, progress bars |

---

## Post-Capstone: Feature Additions

### Upload Dataset Tab (2026-04-18)

**Status**: ✅ Complete

#### What Was Built
Added a 4th tab **"Upload dataset"** to the Underwriter Console, allowing any underwriter to analyse their own workforce CSV for instant risk scoring — without storing data on the server.

#### Files Changed
| File | Change |
|------|--------|
| `dashboard/upload_view.py` | **New** — full upload + analysis module |
| `dashboard/underwriter_view.py` | Added `tab4` + `import dashboard.upload_view` |

#### Feature Flow
```
Underwriter opens "Upload dataset" tab
    ↓
Fills company name, industry, base premium (INR)
    ↓
Downloads CSV template OR uploads their own CSV
    ↓
Client-side validation (age 18-70, bmi 10-60, gender M/F/O, job desk/field/manual)
    ↓
"Run risk analysis" → POST /predict/employee for each row
    (national-average telemetry defaults — no wearable data needed)
    ↓
Results: 4 metric cards + risk breakdown bar chart + HRS gauge
    ↓
Employee-level table sorted by risk score + PDF download
    ↓
"Start new analysis" clears session and resets form
```

#### CSV Format (8 required columns)
```
employee_id, age, gender (M/F/O), bmi,
smoker, diabetic, hypertension, job_category (desk/field/manual)
```

#### Technical Notes
- No backend changes — uses existing `/predict/employee` endpoint
- No DB storage — session-only via `st.session_state["upload_results"]`
- Telemetry defaults: 6000 steps, 72 BPM HR, 7h sleep, 97% SpO2
- Docker: rebuilt `aegis-dashboard` with `docker-compose build dashboard`

---

## Summary

| Phase | Status | Effort | Tests | Commits |
|-------|--------|--------|-------|---------|
| 1 | ✅ Complete | ~3h | — | 3 |
| 2 | ✅ Complete | ~2h | — | 2 |
| 3 | ✅ Complete | ~4h | — | 1 |
| 4 | ✅ Complete | ~2h | — | 1 |
| 5 | ✅ Complete | ~8h | 20/20 ✅ | 7 |
| **6** | **✅ Complete** | **~5h** | **63/63 ✅** | **3** |
| Post-capstone | ✅ Upload tab | ~1h | — | 1 |

**Total Effort to Date**: ~25 hours  
**Total Commits**: 18  
**Total Tests**: 63/63 passing

