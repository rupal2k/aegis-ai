# Phase Progress — Aegis AI

**Last Updated**: 2026-05-02
**Overall Status**: Phase 6 ✅ Complete + Security Hardening ✅ + Security Testing & Remediation ✅ + UI Redesign ✅ + Design System ✅ + Compliance Illustrations ✅ + Brand Fonts ✅ + README Security Fix ✅ + /startserver Skill ✅ + Dashboard Bug Fixes ✅ + Presentation Retheme ✅ + Full Test Suite Clean ✅ + Login Form Fix ✅ + /loadcontext Skill ✅ + Brand Ref Cleanup ✅ + Post-Commit Hook Fix ✅ + Dashboard Overhaul ✅ + HF Dataset Integration ✅ + Clinical Notes Parser ✅ + MLflow Run Naming ✅ + Insurance Charge Adapter ✅ + HF Schema Guard ✅ + UI/UX Design System Improvements ✅ + ML Pipeline Hardening ✅ + Dashboard Docker Fix ✅ + Design System Lock ✅ + Button Text Fix ✅ + Schema Fix ✅ + Render Deploy ✅ + HF Spaces Deploy ✅ + Auth Cold-Start Fix ✅ + Particle Dark UI Theme ✅ + Dashboard Healthcheck Fix ✅

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

### Theme Note
Dark mode implemented in Phase 6 was later replaced by the NullMask light theme (see Post-Capstone section below).

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

### Current Colour Palette (NullMask — see Post-Capstone below)
Dark mode palette was replaced. See NullMask UI Redesign section for current tokens.

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

### Security Hardening — HIPAA & SOC 2 (2026-04-21)

**Status**: ✅ Complete  
**Commit**: `2aa72ed`

#### What Was Fixed

A full HIPAA + SOC 2 audit identified 5 critical and 6 high-severity issues. All 11 were addressed in one commit.

#### Critical Fixes (C-1 → C-5)

| Fix | What Changed |
|-----|-------------|
| **C-1 JWT Auth** | `ingestion/auth/` package created — `jwt.py`, `users.py`, `dependencies.py`. All API endpoints now require `Authorization: Bearer <token>`. `/auth/token` login endpoint added. |
| **C-2 Credentials** | `docker-compose.yml` now uses `${VAR}` references only. Hardcoded fallbacks removed from `database.py` and `scripts/bootstrap.py`. `.env` updated with rotation warnings. |
| **C-3 TLS / nginx** | `nginx/` service added — self-signed cert generated at build time (prod: mount real certs). HTTP → HTTPS redirect. Ports 80 + 443 only exposed externally. |
| **C-4 Dashboard auth** | `dashboard/auth.py` rewritten — passwords verified via `POST /auth/token` (bcrypt on API side). `config/users.json` stores bcrypt hashes. Demo credentials block removed from UI. |
| **C-5 Audit logging** | `aegis.audit` logger added to all PHI-touching endpoints — logs user, company, action, record count on every access. |

#### High Fixes (H-1 → H-5)

| Fix | What Changed |
|-----|-------------|
| **H-1 CORS** | `allow_origins=["*"]` replaced with `ALLOWED_ORIGINS` env var (defaults to `localhost:8501`). |
| **H-2 RBAC** | `require_company_access` dependency — `underwriter` sees all companies, `hr_admin` sees only their own `company_id`. Returns 403 otherwise. |
| **H-3 API docs** | `docs_url=None, redoc_url=None, openapi_url=None` in production (`ENV != development`). |
| **H-4 CI security** | `security` job added to CI — runs `bandit` SAST + `pip-audit` CVE scan before tests run. |
| **H-5 CI secrets** | `echo "... >> $GITHUB_ENV"` replaced with `${{ secrets.X }}` references. Credentials no longer appear in CI logs. |

#### New Files

```
ingestion/auth/__init__.py
ingestion/auth/jwt.py          — create_access_token, decode_token
ingestion/auth/users.py        — bcrypt-based user store (reads config/users.json)
ingestion/auth/dependencies.py — get_current_user, require_underwriter, require_company_access
ingestion/routers/auth_router.py — POST /auth/token
config/users.json              — bcrypt-hashed demo user records
nginx/nginx.conf               — TLS reverse proxy config
nginx/Dockerfile               — self-signed cert generation + nginx image
```

#### Modified Files

```
ingestion/main.py              — auth router, CORS fix, docs gating
ingestion/database.py          — removed hardcoded fallback credential
ingestion/routers/ingest.py    — auth dep + audit logging + error message redaction
ingestion/routers/predict.py   — auth dep + audit logging
ingestion/routers/companies.py — auth dep + RBAC + audit logging
dashboard/auth.py              — bcrypt flow, session timeout (30min), JWT decode
dashboard/api_client.py        — passes Authorization header on every request
docker-compose.yml             — env var refs, mlflow volume, nginx service
.env                           — rotation warnings added
.github/workflows/ci.yml       — security scan job, secrets fix, nginx build
scripts/bootstrap.py           — removed hardcoded fallback credential
tests/test_dashboard.py        — updated for auth flow, new RBAC tests
tests/test_predict_api.py      — uses DATABASE_URL env var
```

#### What's Still Medium / Low Priority (not yet implemented)

- M-1: Rate limiting (`slowapi`)
- M-2: MLflow authentication
- M-3: HASH_SALT strength enforcement at startup
- M-4: Model artifact checksum verification
- L-1: Docker network segmentation
- L-4: Non-root Dockerfile user
- L-5: Pinned image digests

---

## Security Testing & Remediation (2026-04-22)

**Status**: ✅ Complete  
**Commits**: `b63e9b7`, `f692a1c`, `300c212`, `db15088`  
**Security tests**: 25/25 passing (up from 17/25 at test suite creation)

### What Was Done

1. **Comprehensive security review** — Static analysis + automated 25-test suite run against live containers. Initial pass rate 68% (17/25).

2. **Static code review** (via security-review skill) — 4 candidate findings evaluated; 1 confirmed real vulnerability:
   - **MEDIUM confirmed**: `ingest.py` endpoints use only `get_current_user` (authentication) but not `require_company_access` (authorization). An `hr_admin` for COMP_001 can POST wearable/clinical/payroll data for COMP_002 — cross-company data injection. The `require_company_access` dependency exists and is correctly used in `companies.py` and `predict.py` but was missing from all three ingest endpoints.
   - 3 candidates excluded: in-memory blacklist (unused scaffolding, no logout endpoint), JWT dashboard decode (display only, backend enforces independently), SECRET_KEY warning (env vars are trusted).

3. **Critical fixes from test report** — All 7 test failures resolved:

| Fix | Detail |
|-----|--------|
| `/auth/token` returning 404 | Docker image was stale (built before auth modules existed). Rebuilt container. |
| `config/users.json` missing in container | Added `COPY config/ ./config/` to `Dockerfile.api` |
| `DATABASE_URL=localhost` failing | Changed to `db:5432` (Docker internal service name) in `.env` |
| Uvicorn `Server` header exposed | Added `--no-server-header` to uvicorn startup in `entrypoint.sh` |
| Rate limiting missing | `slowapi` wired into `main.py` + `auth_router.py` (5 req/min on `/auth/token`) |
| Security headers missing | Middleware: `X-Frame-Options`, `Content-Security-Policy`, `HSTS`, `X-Content-Type-Options`, `Referrer-Policy` |
| DB port exposed to all interfaces | `docker-compose.yml`: `127.0.0.1:5432:5432` |
| Container running as root | `Dockerfile.api`: `useradd appuser` + `USER appuser` |
| Test bugs (3) | Wrong HTTP method on expired-token test; missing 401 in role-access assertion; missing `load_dotenv()` |

### New/Modified Files

```
Dockerfile.api                         — non-root user (appuser), COPY config/
scripts/entrypoint.sh                  — --no-server-header flag
docker-compose.yml                     — DB port restricted to localhost
ingestion/main.py                      — slowapi rate limiter, security headers middleware
ingestion/routers/auth_router.py       — rate limiting on /auth/token
ingestion/auth/token_blacklist.py      — in-memory blacklist scaffolding (unused until logout endpoint)
ingestion/routers/__init__.py          — exports auth_router cleanly
nginx/nginx.conf                       — added X-Frame-Options, CSP, Referrer-Policy headers
requirements.docker.txt                — slowapi==0.1.8
.env                                   — DATABASE_URL corrected to db:5432
.env.example                           — new file for operator onboarding
tests/security_tests.py               — 25 security tests (all passing)
```

### Remaining Known Issue (not yet fixed)

- **MEDIUM**: `ingest.py` missing `require_company_access` — hr_admin can inject data for other companies via `POST /ingest/wearable|clinical|company`. Fix: add `require_company_access` dependency (same pattern as `companies.py:32` and `predict.py:63`).

---

### NullMask UI Redesign (2026-04-24)

**Status**: ✅ Complete

#### What Changed
Reverted the Phase 6 dark mode and applied the **NullMask Design System** — a light warm-gray B2B aesthetic with Space Grotesk typography, chartreuse accent `#C4FF00`, and an ∅ SVG logo mark. The redesign makes the dashboard look production-ready without changing any backend behaviour.

#### Design Tokens
| Token | Value | Usage |
|-------|-------|-------|
| Page background | `#E3E3DC` | `.stApp` |
| Card background | `#FFFFFF` | Metric cards |
| Sidebar background | `#EAEAE4` | Sidebar panel |
| Border | `rgba(0,0,0,0.07)` | Cards, dividers |
| Primary text | `#111111` | Headings, metric values |
| Muted text | `#999999` | Labels, captions |
| Accent (UI) | `#C4FF00` | Tab underline, logo mark |
| Accent (charts) | `#9BC800` | Bar charts, gauge bar |
| Grid lines | `rgba(0,0,0,0.06)` | Plotly chart grids |

#### Files Changed
| File | Change |
|------|--------|
| `.streamlit/config.toml` | `base="light"`, `primaryColor="#C4FF00"`, `backgroundColor="#E3E3DC"`, `secondaryBackgroundColor="#EAEAE4"`, `textColor="#111111"` |
| `dashboard/app.py` | Full CSS block rewrite with NullMask tokens; Google Fonts import (Space Grotesk, Inter, JetBrains Mono); ∅ SVG logo mark on login page + sidebar; dark "Model Active" badge with chartreuse pulse dot |
| `dashboard/underwriter_view.py` | `PLOT_BG="#FFFFFF"`, `ACCENT="#9BC800"`, `FONT_CLR="#111111"`, `GRID_CLR="rgba(0,0,0,0.06)"`, light translucent gauge step colours |
| `dashboard/hr_view.py` | Same colour constants; scatter scale `["#22C55E","#F59E0B","#EF4444"]`; waterfall `decreasing=#22C55E`, `increasing=#EF4444`, `totals=ACCENT` |
| `dashboard/upload_view.py` | Same colour constants; gauge step colours updated to light translucent variants |
| `dashboard/auth.py` | "Sign in to continue" text colour `#999999` |

#### Key UI Elements Added
- **Login page**: centred ∅ SVG logo (black 52×52px rounded square, chartreuse crosshair circle), Space Grotesk wordmark, subtitle in `#999`
- **Sidebar header**: ∅ logo mark (32px), "Aegis AI" bold + "Underwriting Platform" caption
- **Model status badge**: dark `#111` rounded box, green `#C4FF00` pulse dot, "Model Active" label, "XGBoost v2.1 · SHAP enabled"
- **Metric cards**: white, 12px radius, 1px border, subtle drop shadow
- **Tab active underline**: chartreuse `#C4FF00`
- **Download buttons**: black fill `#111111`, white text

#### Risk Colour Map (unchanged semantics, updated hues)
| Band | Colour |
|------|--------|
| Low | `#22C55E` |
| Moderate | `#F59E0B` |
| High | `#EF4444` |
| Critical | `#991B1B` |

---

### Swagger UI CSP Fix (2026-04-24)

**Status**: ✅ Complete

#### Problem
`http://localhost:8000/docs` displayed a blank page. FastAPI's Swagger UI fetches its JavaScript and CSS from `cdn.jsdelivr.net`, but the security headers middleware enforced `script-src 'self'` on every route — including `/docs` — blocking all external scripts.

#### Root Cause
`ingestion/main.py` security middleware applied a single global CSP:
```python
"Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
```
This blocked `cdn.jsdelivr.net` everywhere, including the Swagger and ReDoc routes.

#### Fix
Middleware now checks the request path and relaxes CSP only for doc routes in development mode:
```python
is_doc_path = request.url.path in ("/docs", "/redoc", "/openapi.json")
if _ENV == "development" and is_doc_path:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "img-src 'self' data:; worker-src blob:;"
    )
else:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    )
```
Production docs remain disabled (`docs_url=None` when `ENV != "development"`), so the relaxed policy never applies in production.

#### File Changed
`ingestion/main.py` — `add_security_headers` middleware only.

---

### Local Dev Startup Commands (2026-04-24)

Running all services outside Docker (hybrid mode — DB + MLflow in Docker, API + Dashboard native):

```bash
# 1. Start DB and MLflow in Docker
docker compose up db mlflow -d

# 2. Start API (native, with development docs enabled)
DATABASE_URL=postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db \
ENV=development \
python -m uvicorn ingestion.main:app --port 8000 --log-level warning

# 3. Start Dashboard (separate terminal)
streamlit run dashboard/app.py --server.port 8501
```

**Service URLs**:
| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |

**Note**: `slowapi` must be installed locally (`pip install slowapi`) — it was previously only in `requirements.docker.txt`.

---

### NullMask Design System Implementation (2026-04-24)

**Status**: ✅ Complete  
**Source**: Design bundle from claude.ai/design → `nullmask-design-system/project/Aegis AI Dashboard.html`

The design bundle contained the full NullMask system with a complete Aegis AI dashboard prototype (React + HTML). This session audited what was already implemented from the previous redesign and filled all remaining gaps.

#### Design Audit Results

| Design Element | Status Before | Action |
|----------------|---------------|--------|
| Color tokens (`#E3E3DC`, `#C4FF00`, `#9BC800`, `#111111`) | ✅ Already done | No change |
| Space Grotesk / Inter / JetBrains Mono fonts | ✅ Already done | No change |
| ∅ logo mark (SVG circle + slash, dark rounded square) | ✅ Already done | No change |
| Model Active badge (dark bg, chartreuse pulse dot) | ✅ Already done | No change |
| White metric cards (border, shadow, `12px` radius) | ✅ Already done | No change |
| Tab active underline (`#C4FF00`) | ✅ Already done | No change |
| SHAP factor horizontal bars | ✅ Already done | No change |
| Risk gauge (Plotly gauge, ACCENT bar colour) | ✅ Already done | No change |
| Wellness ROI waterfall chart | ✅ Already done | No change |
| **User avatar with initials** (chartreuse ghost circle, sidebar) | ❌ Missing | ✅ Implemented |
| **Alerts panel** (4-level severity dots, real portfolio data) | ❌ Missing | ✅ Implemented |
| **Risk band mini-cards** (4-up grid, %, employee count, bar) | ❌ Missing | ✅ Implemented |
| **AI Recommendations** (numbered list, savings in accent font) | ❌ Missing | ✅ Implemented |
| **Glow shadow** CSS variant for accent metric cards | ❌ Missing | ✅ Implemented |
| **Scrollbar** thin styling (4px, transparent bg) | ❌ Missing | ✅ Implemented |
| Settings screen with toggle components | N/A (Streamlit constraint) | Not implemented |
| Fixed TopBar header with avatar | N/A (Streamlit constraint) | Not implemented |

#### What Was Implemented

**`dashboard/app.py`** — Sidebar user avatar + CSS additions:
- User initials extracted from name/email, rendered as 34px chartreuse ghost circle
- Role label shown in uppercase caps (`UNDERWRITER` / `HR MANAGER`)
- Added `nm-glow` CSS class (accent border + `0 0 24px rgba(196,255,0,0.10)` shadow)
- Added thin scrollbar global styling

**`dashboard/underwriter_view.py`** — Two additions:
1. **`_render_alerts(df)`** function — generates 4 alert rows from live portfolio data:
   - `high` (red): Critical risk companies → company names listed
   - `med` (orange): Count of High-risk companies
   - `info` (blue): Companies with >10% premium adjustment, avg HRS above benchmark
   - `ok` (green): Count of Low-risk companies
   - Rendered as white card with color dots, text, styled border
2. **Risk band mini-cards** in tab2 (Company deep dive) — 4-column grid showing Low/Moderate/High/Critical with percentage, employee count, and mini progress bar using actual prediction data

**`dashboard/hr_view.py`** — AI Recommendations section (tab2):
- Replaced `st.container(border=True)` loop with full HTML numbered list
- Each row: numbered badge (chartreuse ghost square), action title, impact text, estimated annual savings
- Savings calculated as `(hrs_mid_improvement / 100) × adjusted_premium × 0.8`
- Savings value shown in `#9BC800` JetBrains Mono (matching design's accent money figure)

#### Design vs Streamlit Constraints
Two elements from the design prototype cannot be ported to Streamlit:
- **Settings screen with per-feature toggles** — Streamlit has `st.toggle()` but not in the design's grid layout with arbitrary content rows
- **Fixed TopBar** — Streamlit's layout model doesn't support a fixed top bar outside the sidebar; page titles use `st.title()` instead

---

### HR Dashboard Chart Fixes (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `bd13c22`

Fixes to `dashboard/hr_view.py` after visual review of the Wellness ROI tab:

#### Waterfall chart (Wellness ROI simulator)
- **Root cause**: Plotly waterfall uses `totals` colour for both `absolute` and `total` measures, so "Current premium" and "Projected premium" bars rendered identically in olive-green
- **Fix**: Replaced `decreasing`/`totals` dicts with `marker_color` array — dark gray (`#374151`) for current, green (`#22C55E`) for savings, accent-olive (`#9BC800`) for projected
- Added dotted connector line and outside text labels (JetBrains Mono) so values are readable without hovering
- Removed redundant auto-generated Plotly legend (`showlegend=False`)

#### Donut chart (Workforce overview — Risk band distribution)
- **Fix**: Filter out zero-percentage bands before passing to `px.pie()` to eliminate empty slivers
- Added mean HRS score as a centre annotation inside the donut hole (Space Grotesk, 18px)
- Labels moved to `textposition="outside"` to avoid overlap at small slice sizes

---

### NullMask Isometric Illustrations (2026-04-24)

**Status**: ✅ Complete  
**Commits**: `9b0ce1f` (add) · `5dfbe76` (fix rendering)  
**Source**: Design bundle `nullmask-design-system/project/Design Elements.html` — 4 isometric SVG elements generated by the NullMask design assistant

#### Illustrations added

| # | Name | Placed on | Page / tab |
|---|------|-----------|------------|
| 01 | Privacy Vault | Login page | Right column alongside sign-in form |
| 02 | Privacy Router | Underwriter Console | Portfolio overview tab — top-right header accent |
| 03 | Privacy Shield | HR Manager | Workforce overview tab — top-right header accent |
| 04 | Zero Node | Upload Dataset | Empty state before CSV is uploaded |

#### Implementation approach

**`dashboard/illustrations.py`** (new file):
- Each SVG extracted from `Design Elements.html` via regex
- Encoded as `data:image/svg+xml;base64,...` URI — the only reliable method for inline SVGs in Streamlit
- Helper `_svg_img(uri, width, style="")` returns a complete `<img src="..." style="..."/>` tag for injection via `st.markdown(unsafe_allow_html=True)`

**Why base64 data URI, not raw inline SVG**: Streamlit's markdown processor does not parse `<svg>` tags — the raw SVG markup was rendered verbatim as plain text. `<img src="data:image/svg+xml;base64,...">` is treated as a standard image element and renders correctly.

**Login page restructure** (`app.py`):
- Changed from 3-column centred layout `[1, 2, 1]` to 2-column `[1, 1]`
- Left: logo + tagline + description + login form
- Right: Privacy Vault illustration (max-width 380px)

**Tab header pattern** (`underwriter_view.py`, `hr_view.py`):
- `st.columns([3, 1])` — subheader in left col, illustration right-aligned at fixed width (160px / 130px) with `opacity:0.85`

**Empty state** (`upload_view.py`):
- `st.columns([1, 1])` — info message left, Zero Node illustration centred right at 220px

#### Files changed
- `dashboard/illustrations.py` — new module (4 constants + helper)
- `dashboard/app.py` — login layout + Privacy Vault
- `dashboard/underwriter_view.py` — Privacy Router in tab1 header
- `dashboard/hr_view.py` — Privacy Shield in tab1 header
- `dashboard/upload_view.py` — Zero Node in empty state

---

### Plotly Waterfall API Fix (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `b6afd7c`

`go.Waterfall` does not accept `marker_color` as a top-level array (that's a `go.Bar` API). Replaced with per-category sub-objects: `decreasing` (savings bar, green), `totals` (projected premium, accent), `increasing` (current premium, dark gray).

---

### Brand Fonts + Compliance Illustrations (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `925c6ee`  
**Source**: Design bundle `i6HuHm-Oohtk-Q0s2nLb-w` — fonts + `Compliance Design Elements.html`

#### Font hierarchy

| Role | Font | Where applied |
|------|------|---------------|
| Display / headings | **NType82** (400 + 700) | All `h1/h2/h3`, tabs, logo mark, inline HTML headings |
| Body / labels | **Inter** | Captions, metric labels, body paragraphs, download buttons |
| Metric values / numbers | **LetteraMonoLL** (400 + 500) | `stMetricValue`, `stMetricDelta`, waterfall text labels, donut annotation |

NType82 and LetteraMonoLL are embedded as base64 `@font-face` data URIs in `BRAND_FONT_CSS` (exported from `illustrations.py`) and injected via `st.markdown(f"<style>{BRAND_FONT_CSS}</style>")` in `app.py`. Inter + Space Grotesk loaded from Google Fonts. JetBrains Mono removed throughout.

#### Compliance illustrations

| # | SVG | Placed on | Replaces |
|---|-----|-----------|---------|
| 01 | SOC 2 Compliance | Login page (right column) | Privacy Vault |
| 02 | Group Insurance | Underwriter portfolio tab header | Privacy Router |
| 03 | HIPAA Privacy | HR workforce tab header | Privacy Shield |
| 04 | Employee Health | Upload empty state | Zero Node |

SVGs extracted from `Compliance Design Elements.html`, base64-encoded as data URIs in `illustrations.py`.

#### Files changed
- `dashboard/illustrations.py` — 4 new compliance SVG constants; `BRAND_FONT_CSS` string with embedded fonts; old privacy SVGs removed
- `dashboard/app.py` — font injection; CSS hierarchy updated; `SOC2_COMPLIANCE` on login
- `dashboard/underwriter_view.py` — `GROUP_INSURANCE`; chart font → Inter
- `dashboard/hr_view.py` — `HIPAA_PRIVACY`; chart/mono fonts → Inter / LetteraMonoLL
- `dashboard/upload_view.py` — `EMPLOYEE_HEALTH`; chart font → Inter

---

### README Security Fix (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `0da4a1e`

Removed the demo credentials table from `README.md` — the public-facing README previously listed plaintext login credentials (`underwriter@safenet.com / demo123`, `hr@technova.com / demo123`, `hr@bharatsteel.com / demo123`). Exposing credentials in a public GitHub README is a security risk even for demo accounts, as it invites credential stuffing and gives attackers a known valid username list.

#### File changed
- `README.md` — deleted 9 lines (Demo Credentials section)

---

### /startserver Claude Code Skill (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `dbf8b2c`

Added `.claude/commands/startserver.md` — a project-level Claude Code slash command that automates full Aegis AI stack startup from scratch.

#### What `/startserver` does

1. Kill any stale native Streamlit process (`pkill -f "streamlit run"`)
2. `docker compose down` — clean teardown of all containers
3. `docker compose up -d` — start all 5 services (db, api, dashboard, mlflow, nginx)
4. Wait + show container status table (names, health, ports)
5. HTTP health checks — API `/health`, Dashboard `/healthz`, MLflow `/health`, nginx port 80
6. PostgreSQL probe — `pg_isready` via `docker exec aegis-db`
7. Module import test — all 9 `dashboard.*` modules (`OK` / `FAIL`)
8. Syntax check — `py_compile` on all 10 `.py` files
9. Final summary table — per-service ✅ / ❌ with `docker logs` diagnosis on failure

#### File added
- `.claude/commands/startserver.md` — 92-line skill definition

---

### Login Form Input Sizing Fix (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `4551f47`

Streamlit's default `st.text_input` renders with oversized input height (~46px). Added CSS rules targeting `.stTextInput input` and `.stFormSubmitButton button` to cap height at 38px with matching `font-size: 14px` and padding — bringing the login form inputs and Sign In button to standard compact proportions.

#### Files changed
- `dashboard/app.py` — added compact input height CSS (22 lines)

---

### Remove NullMask Brand References (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `84597d2`

Removed all 7 occurrences of "NullMask" from the codebase. The design tokens, fonts, and visual style are unchanged — only the third-party brand name was stripped. References replaced with "Aegis AI" or generic terms throughout module docstrings, function docstrings, inline comments, CSS comments, and the /loadcontext skill.

#### Files changed
- `dashboard/illustrations.py` — module docstring: "NullMask" → "Aegis AI"
- `dashboard/underwriter_view.py` — function docstring + inline comment updated
- `dashboard/app.py` — CSS comment updated; BaseWeb input-height CSS also included
- `.claude/commands/loadcontext.md` — 3 guardrail references updated to "Aegis AI"

---

### /loadcontext Claude Code Skill (2026-04-24)

**Status**: ✅ Complete  
**Commit**: `17d9b68`

Added `.claude/commands/loadcontext.md` — a session-start slash command that reads all 6 Claude memory files and 5 vault files, synthesises a structured context brief, and outputs hard guardrails covering architecture, security, NullMask design tokens, CSS rules, code conventions, and vault/git workflow. Includes a self-check checklist Claude runs silently before every file edit, and a guardrail violation handler that blocks deviating changes before they happen.

#### Files changed
- `.claude/commands/loadcontext.md` — new skill (105 lines)
- `.claude/commands/gitmastersync.md` — updated with dedup fix, nginx rebuild, full Docker map, health check

---

### Post-Commit Hook Hardening (2026-04-26)

**Status**: ✅ Complete  
**Commit**: `6730057`

Hardened the post-commit git hook with three defensive fixes: a deduplication guard (prevents the same commit hash being logged twice if the hook fires more than once), a vault-commit skip clause (hook no longer triggers when the active commit is itself a vault sync, eliminating infinite commit loops), and an explicit repo-context flag so all git commands target the code repo rather than the vault repo.

#### Files changed
- `.claude/commands/gitmastersync.md` — updated hook spec with dedup guard + vault-commit skip + explicit repo context

---

### Dashboard UI Overhaul & Design System Alignment (2026-04-28)

**Status**: ✅ Complete  
**Commit**: `8ebcd93`

Comprehensive overhaul of all five dashboard modules to fully align with the Aegis AI design contract (`design.md`) and `design_tokens.py`. `underwriter_view.py` received the largest update (673 lines): risk-band mini-cards, alerts panel, chart theming, and component layout improvements. `hr_view.py` (253 lines), `app.py` (383 lines), `auth.py` (47 lines), and `upload_view.py` (46 lines) were updated for consistent styling, dark text scale enforcement, and `apply_chart_theme()` usage. Three sample CSV files were added to `data/` for dev and demo use.

#### Files changed
- `dashboard/app.py` — CSS + layout overhaul (383 lines)
- `dashboard/underwriter_view.py` — risk-band cards, alerts, chart fixes (673 lines)
- `dashboard/hr_view.py` — chart + component improvements (253 lines)
- `dashboard/upload_view.py` — style alignment (46 lines)
- `dashboard/auth.py` — style updates (47 lines)
- `data/upload_doc_0.csv`, `data/upload_doc_1.csv`, `data/upload_doc_2.csv` — sample data

---

### Hugging Face Dataset Integration + Scorer Hardening (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `d0ef776`

Added support for training from the Hugging Face Hub alongside the local synthetic CSV. `load_from_huggingface()` maps a tabular HF insurance dataset to the Aegis feature schema with graceful fallback when HF is unavailable. `load_training_dataframe()` merges sources with a configurable mode (`local`, `hf`, `both`). `HRSScorer._normalize()` now extracts the shared normalisation logic and guards against degenerate calibration distributions (zero-scale input returns 0.5). MLflow setup moved to a lazy `configure_mlflow()` so importing the module stays side-effect free. New `--use-local` / `--use-hf` / `--use-both` / `--no-hf` CLI flags added.

#### Files changed
- `ml_engine/training/train.py` — HF loader, arg parser, lazy MLflow init, `build_arg_parser()`, `resolve_dataset_mode()`
- `ml_engine/scorer.py` — `_normalize()` helper + degenerate distribution guard
- `ml_engine/artifacts/` — retrained model artifacts (xgb_model.pkl, hrs_scorer.pkl, feature_names.pkl)
- `tests/test_ml_engine.py` — degenerate scorer test
- `tests/test_training_pipeline.py` — 7 new pipeline unit tests (23/23 passing)
- `requirements.txt` / `requirements.docker.txt` — `datasets>=2.15.0`

---

### Clinical Notes Parser — HF Source Switch (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `818f5fd`

Replaced the previous tabular HF dataset with `ayush0205/clinical_data_rf` (19,756 free-text clinical discharge notes). The new `_parse_clinical_note()` function uses regex to extract: age (4 patterns, 80% coverage), gender, BMI, smoker, diabetic, hypertension, and 10 lab/condition flags (cardiac, renal, liver, respiratory/ARDS, sepsis, stroke, mental health, osteoporosis, anaemia, thyroid, vitamin deficiency), plus ICU admission, mechanical ventilation, and SpO2. Wearable telemetry (steps, HR, sleep, active mins) is synthesised from a per-note severity score so all features are coherent and correlated. Loss ratio is derived from age risk + condition count + serious-condition multipliers, randomised with log-normal noise (mean 0.58, std 0.32). 4 new parser unit tests added.

#### Files changed
- `ml_engine/training/train.py` — `_parse_clinical_note()`, rewritten `load_from_huggingface()`, updated `HF_DATASET_NAME` constant
- `tests/test_training_pipeline.py` — 4 parser unit tests (23/23 passing)

---

### MLflow Run Auto-Naming (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `2caac54`

All three existing MLflow runs carried the hardcoded name `final_xgb_with_optuna`, making them indistinguishable in the UI. Added `_build_run_name(dataset_mode, hf_dataset_name)` which derives a descriptive name from data sources used: `xgb_local_csv`, `xgb_hf_<dataset_slug>`, or `xgb_local+<dataset_slug>`. Retroactively renamed the three existing runs: `91d17215` → `xgb_local_synthetic_csv` (R²=0.685, the good baseline), `4dbbf51c` → `xgb_hf_omg_insurance_degenerate` (R²≈0), `f87cbca9` → `xgb_hf_gcc_insurance_degenerate` (R²≈0).

#### Files changed
- `ml_engine/training/train.py` — `_build_run_name()` helper; hardcoded run name replaced

---

### Insurance Charge HF Adapter + Combined Retrain (2026-04-29)

**Status**: Complete  
**MLflow Run**: `b10e7565acbd451e92556509b52dfa6d`

Added a dedicated Hugging Face adapter for `bubuuunel/healthylife-insurance-charge-log` while keeping the existing GCC underwriting mapper, clinical-note parser, and local CSV pipeline intact. The loader now classifies HF datasets by schema and explicitly rejects company-profile datasets such as `devadigax/linkedin-company-profile` for underwriting training because they do not contain employee health features or a usable claim target.

#### Training run
- Local rows: 5,237
- HF rows: 225 (`healthylife-insurance-charge-log`)
- Combined rows: 5,462
- Dataset mode: `both`

#### Metrics
- `train_mae`: 0.3199
- `test_mae`: 0.3981
- `train_rmse`: 0.4271
- `test_rmse`: 0.5392
- `train_r2`: 0.8000
- `test_r2`: 0.6915

#### Verification
- `python -m pytest tests\test_training_pipeline.py -q` -> 17 passed
- `python -m pytest tests\test_ml_engine.py -q` -> 12 passed
- `python -m pytest tests\test_predict_api.py -q` -> 8 passed, 2 skipped
- `python -m pytest tests -q` -> 75 passed, 5 skipped

---

### UI/UX Design System Improvements (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `f61f3d8`

Comprehensive UI/UX pass aligned to the Aegis AI design system. Added a Workstyle Breakdown grid to the Account Review tab showing Desk/Field/Manual categories with avg loss ratio risk scores, employee counts, and mini progress bars. Added risk filter pills (All/High/Moderate/Low) to the Upload tab employee table with session state persistence. Fixed all Plotly chart text — CSS guard-rail cannot reach Plotly iframes, so the fix clears the default Plotly template and applies explicit `update_xaxes`/`update_yaxes` calls. Expanded the CSS guard-rail to cover metric labels, expander headers, subheaders, and span elements. Updated both sidebar and login logos to the Primary-on-light variant from the design system (inner shield accent layer, updated ECG pulse, corner brackets, 68×80 viewBox).

#### Files changed
- `dashboard/app.py` — CSS guard-rail expanded; sidebar + login logo updated to Primary-on-light design
- `dashboard/currency.py` — replaced `st.caption()` with styled markdown (dark #333333)
- `dashboard/design_helpers.py` — `apply_chart_theme()` clears Plotly template; `page_header`/`section_header` colors hardened
- `dashboard/underwriter_view.py` — `_render_workstyle_breakdown()` added; gauge template cleared
- `dashboard/upload_view.py` — risk filter pills + filtered table; gauge template cleared

---

### ML Pipeline Hardening & Artifacts Update (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `f4b7b00`

Consolidated and hardened the ML training pipeline with the full clinical notes parser, HF dataset integration, and scorer hardening into a single clean commit. The `_parse_clinical_note()` regex parser extracts 15+ structured features from free-text discharge notes; `load_from_huggingface()` synthesises coherent wearable telemetry from severity scores; `HRSScorer._normalize()` guards against degenerate distributions. CLI flags (`--use-local`/`--use-hf`/`--use-both`) and `load_training_dataframe()` with graceful fallback complete the pipeline. Updated model artifacts from the latest retrain run.

#### Files changed
- `ml_engine/training/train.py` — full pipeline rewrite: note parser, HF loader, scorer hardening, CLI flags, run naming
- `tests/test_training_pipeline.py` — parser + pipeline unit tests
- `ml_engine/artifacts/hrs_scorer.pkl` — updated scorer artifact
- `ml_engine/artifacts/xgb_model.pkl` — updated model artifact (retrained)

---
### HF-Only Healthylife Retrain (2026-04-29)

**Status**: Complete  
**MLflow Run**: `3084108b84d147a389cbb6f87375ae04`

Trained the underwriting model on `bubuuunel/healthylife-insurance-charge-log` using the HF-only path (`--use-hf`) so the saved artifacts reflect that dataset alone rather than the combined local + HF blend.

#### Training run
- HF rows: 225
- Dataset mode: `hf`

#### Metrics
- `train_mae`: 0.0409
- `test_mae`: 0.0583
- `train_rmse`: 0.0528
- `test_rmse`: 0.0709
- `train_r2`: 0.9764
- `test_r2`: 0.9570

#### Verification
- `python -m pytest tests\test_ml_engine.py -q` -> 12 passed
- `python -m pytest tests\test_predict_api.py -q` -> 8 passed, 2 skipped

---
### Dashboard Docker Fix (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `7210b0e`

The `data/` directory was missing from `Dockerfile.dashboard`, causing a `ModuleNotFoundError: No module named 'data'` on container startup. Added `COPY data/ ./data/` to the dashboard image so the data module is available at runtime.

#### Files changed
- `Dockerfile.dashboard` — added `COPY data/ ./data/`

---
### Design System Lock (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `7f94da0`

Created `CLAUDE.md` at the repo root to permanently encode the Aegis AI design contract. Covers the full NM color scale, banned pale greys, mandatory Plotly `apply_chart_theme()` pattern with `template={}` clear, Streamlit CSS `!important` rules, required helper functions, logo variant usage, and Docker rebuild triggers. Auto-loaded by Claude Code at every session start.

#### Files changed
- `CLAUDE.md` — 133-line design + code rules document

---
### Button Text Visibility Fix (2026-04-29)

**Status**: ✅ Complete  
**Commit**: `dc7d37a`

Primary button labels were invisible in Streamlit 1.56.0 because child `<p>` and `<span>` elements had their own injected colour overriding the parent button's CSS. Added explicit child selectors (`[data-testid="stBaseButton-primary"] *`) with `color: #C4FF00 !important`. Also bumped the MODEL ACTIVE card caption from `#AAAAAA` to `#CCCCCC` for legibility on the dark card background.

#### Files changed
- `dashboard/app.py` — primary button child CSS selectors + MODEL ACTIVE caption colour

---
### Training Snapshot Schema Fix (2026-04-30)

**Status**: ✅ Complete  
**Commit**: `cf12d8b`

Added 11 missing `lab_*` columns to the `training_snapshots` table in `schema.sql` to match the clinical notes parser output. Columns include `lab_heart_flag`, `lab_inflammation_flag`, `lab_diabetes_flag`, `lab_kidney_flag`, `lab_liver_flag`, `lab_iron_flag`, `lab_thyroid_flag`, `lab_bone_flag`, `lab_vitamin_flag`, `lab_domain_count`, and `lab_risk_score`. Neon PostgreSQL table was dropped and re-seeded.

#### Files changed
- `data/schema.sql` — 11 new `lab_*` columns + `lab_risk_score DECIMAL(5,3)`

---
### Render Deployment Setup (2026-04-30)

**Status**: ✅ Complete  
**Commit**: `ee26e94`

Added `render.yaml` Blueprint config for one-click Render deployment of the FastAPI backend. Fixed `entrypoint.sh` to use `${PORT:-8000}` so Render can inject its dynamic port. The API is now live at `https://aegis-ai-wss8.onrender.com`.

#### Files changed
- `render.yaml` — Render Blueprint: Docker runtime, free plan, health check, env var stubs
- `scripts/entrypoint.sh` — `${PORT:-8000}` replaces hardcoded `8000`

---
### Render Entrypoint Fix (2026-04-30)

**Status**: ✅ Complete  
**Commit**: `a12c31c`

`scripts/entrypoint.sh` had git mode `100644` (not executable) causing exit code 128 on Render's Linux container. Fixed with `git update-index --chmod=+x` and a belt-and-suspenders `RUN chmod +x` in `Dockerfile.api`.

#### Files changed
- `Dockerfile.api` — `RUN chmod +x /app/scripts/entrypoint.sh` + split `chown` RUN
- `scripts/entrypoint.sh` — file mode changed to `100755`

---
### Hugging Face Spaces Deployment (2026-04-30)

**Status**: ✅ Complete  
**Commit**: `593843b`

Added root-level `Dockerfile` for HF Spaces Docker SDK deployment. Runs on port 7860, uses UID 1000 non-root user as required by HF. Copies dashboard, ml_engine, ingestion, and data modules. Dashboard is live at `https://huggingface.co/spaces/Rupa2k/aegis-ai` and connects to the Render API via `AEGIS_API_URL` secret.

#### Files changed
- `Dockerfile` — HF Spaces image: port 7860, UID 1000, Streamlit entry point

---
### Auth Cold-Start Timeout Fix (2026-04-30)

**Status**: ✅ Complete  
**Commit**: `f8b97e5`

Render free tier sleeps after 15 minutes of inactivity and takes up to 45 seconds to cold-start. The original 10-second login timeout caused all first-load logins to silently fail with "Incorrect email or password". Raised timeout to 45s and added a distinct "Server is starting up" message to differentiate cold-start timeout from actual bad credentials. Also hardened `API_BASE` to strip whitespace and fall back to localhost if the env var is blank.

#### Files changed
- `dashboard/auth.py` — 45s timeout, `TimeoutException` handling, blank env var guard
- `dashboard/api_client.py` — blank env var guard

---
### Particle Dark Design Theme (2026-05-02)

**Status**: ✅ Complete  
**Commit**: `370cc0d`

Full replacement of the light NullMask palette with the **Particle Dark** design template — a deep-navy dark theme sourced from the Aegis AI Dashboard Particle Dark prototype. `design_tokens.py` was rewritten with the new dark palette (`#070b14` page, `#111c30` cards, `#84cc16` lime accent) and six CSS micro-animation keyframes. `design_helpers.py` gained `hrs_gauge_html()` (animated 270° SVG arc gauge with unique per-instance animation IDs), `hrs_badge_html()` (traffic-light pulsing badge), `metric_card_dark()`, and `shap_waterfall_html()`. All five dashboard modules were migrated to dark backgrounds and light text with the traffic-light risk system (Low `#22c55e` / Moderate `#eab308` / High `#f97316` / Critical `#ef4444`).

#### Files changed
- `dashboard/design_tokens.py` — full dark palette rewrite; `DESIGN_TOKENS_CSS` with `--nm-*` CSS vars; six keyframes
- `dashboard/design_helpers.py` — `hrs_gauge_html()`, `hrs_badge_html()`, `metric_card_dark()`, `shap_waterfall_html()`; updated `apply_chart_theme()`, `risk_band_pill()`, `page_header()`, `card()`
- `dashboard/app.py` — full dark CSS guard-rail; micro-animation keyframes; login + sidebar HTML migrated; Model Active card with `nm-pulseRing` dot and `#84cc16`
- `dashboard/underwriter_view.py` — traffic-light `COLOR_MAP`; dark chart constants; workstyle breakdown, decision card, risk drivers, gauge all migrated; benchmark vlines, filter pills, row-selected card
- `dashboard/hr_view.py` — traffic-light `COLOR_MAP`; dark chart constants; waterfall chart colors and text
- `dashboard/upload_view.py` — traffic-light `COLOR_MAP`; dark chart constants; filter pill colors
- `dashboard/currency.py` — sidebar caption `#333333` → `#64748b`

---
### Dashboard Healthcheck Fix (2026-05-02)

**Status**: ✅ Complete  
**Commit**: `f07a550`

`Dockerfile.dashboard` used `curl` in its `HEALTHCHECK` directive, but `curl` is not installed in the `python:3.11-slim` base image. The health probe always failed, leaving the `aegis-dashboard` container permanently `unhealthy` despite the app being fully functional. Replaced with a Python stdlib `urllib.request` call which requires no extra packages. Also extended `start-period` from 10s to 30s to account for Streamlit's startup time.

#### Files changed
- `Dockerfile.dashboard` — `HEALTHCHECK` directive: `curl` → `python -c "import urllib.request; ..."`, `--timeout=5s` → `10s`, `--start-period=10s` → `30s`

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
| Post-capstone | ✅ Security hardening | ~3h | — | 1 |
| Post-capstone | ✅ Security testing & remediation | ~2h | 25/25 ✅ | 4 |
| Post-capstone | ✅ NullMask UI redesign + Swagger CSP fix | ~1h | — | 1 |
| Post-capstone | ✅ NullMask design system implementation | ~1h | — | 1 |
| Post-capstone | ✅ HR dashboard chart fixes (waterfall + donut) | ~0.5h | — | 1 |
| Post-capstone | ✅ NullMask isometric illustrations (4 pages) | ~0.5h | — | 2 |
| Post-capstone | ✅ Plotly Waterfall API fix | ~0.1h | — | 1 |
| Post-capstone | ✅ Brand fonts (NType82 + LetteraMonoLL) + compliance illustrations | ~1h | — | 1 |
| Post-capstone | ✅ README security fix (removed demo credentials) | ~0.1h | — | 1 |
| Post-capstone | ✅ /startserver Claude Code skill | ~0.2h | — | 1 |
| Post-capstone | ✅ Login form input sizing fix | ~0.1h | — | 1 |
| Post-capstone | ✅ /loadcontext skill + gitmastersync update | ~0.3h | — | 1 |
| Post-capstone | ✅ Remove NullMask brand references from codebase | ~0.1h | — | 1 |
| Post-capstone | ✅ Post-commit hook hardening (dedup + vault skip) | ~0.2h | — | 1 |
| Post-capstone | ✅ Dashboard UI overhaul & design system alignment | ~2h | — | 1 |
| Post-capstone | ✅ HF dataset integration + scorer hardening | ~1h | 23/23 ✅ | 1 |
| Post-capstone | ✅ Clinical notes parser — HF source switch | ~1h | 23/23 ✅ | 1 |
| Post-capstone | ✅ MLflow run auto-naming | ~0.2h | 23/23 ✅ | 1 |
| Post-capstone | ✅ UI/UX design system improvements — workstyle grid, filter pills, chart text fix, primary logo | ~2h | — | 1 |
| Post-capstone | ✅ ML pipeline hardening — clinical notes parser, HF integration, scorer guard, artifacts | ~1h | — | 1 |
| Post-capstone | ✅ Dashboard Docker fix — add data/ to image, fix ModuleNotFoundError | ~0.1h | — | 1 |
| Post-capstone | ✅ Design system lock — CLAUDE.md with full color/Plotly/CSS rules | ~0.5h | — | 1 |
| Post-capstone | ✅ Button text visibility fix — stBaseButton-primary child CSS selectors | ~0.3h | — | 1 |
| Post-capstone | ✅ Training snapshot schema fix — 11 lab_* columns added, Neon reseeded | ~0.3h | — | 1 |
| Post-capstone | ✅ Render deployment — render.yaml + PORT env var fix, API live | ~1h | — | 2 |
| Post-capstone | ✅ HF Spaces deployment — root Dockerfile, port 7860, dashboard live | ~1h | — | 1 |
| Post-capstone | ✅ Auth cold-start fix — 45s timeout + blank env var guard | ~0.5h | — | 1 |
| Post-capstone | ✅ Particle Dark design theme — dark-navy palette, traffic-light risk, micro-animations, animated SVG gauge, all 7 dashboard files migrated | ~3h | — | 1 |
| Post-capstone | ✅ Dashboard healthcheck fix — replace curl with Python urllib in Dockerfile.dashboard HEALTHCHECK | ~0.1h | — | 1 |

**Total Effort to Date**: ~51.0 hours  
**Total Commits**: 53  
**Total Tests**: 75 passed, 5 skipped (latest full pytest); focused ML checks: 17 training pipeline + 12 ml_engine + 8 predict_api

