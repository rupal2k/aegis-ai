# Aegis AI — Dynamic Group Insurance Underwriting Platform

![CI](https://github.com/rupal2k/aegis-ai/workflows/CI/badge.svg)

A B2B SaaS platform that shifts group health insurance from **reactive** pricing (based on last year's claims) to **proactive** underwriting (based on real-time workforce health telemetry).

---

## The Problem

Insurers price corporate group health policies on stale, annual claims data. Manufacturers look as risky as tech companies until a bad year proves otherwise. Wellness programs produce no measurable premium benefit because there's no standard way to quantify their impact.

Aegis AI solves this by ingesting continuous anonymized health telemetry (wearable data + clinical events), scoring each corporate workforce with a dynamic **Health Risk Score (HRS)** on a 0–100 scale, and translating that into precision premium pricing — with full SHAP explainability.

---

## Architecture

Three tiers:

| Tier | Technology | Purpose |
|------|-----------|---------|
| **Data ingestion** | FastAPI + Pandas + PostgreSQL | Accept, validate, normalise, anonymise |
| **AI underwriting** | XGBoost + Optuna + SHAP + MLflow | Predict loss ratio, explain risk drivers |
| **B2B portal** | Streamlit + Plotly | Two role-based dashboards |

```
┌──────────────────────────────────────────────────────┐
│  Streamlit Dashboard  (port 8501)                    │
│  ├─ Underwriter Console  (all 20 companies)          │
│  └─ HR Manager Dashboard (single company + wellness) │
└──────────────────────┬───────────────────────────────┘
                       │ httpx  (@st.cache_data ttl=60)
                       ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI Backend  (port 8000)                        │
│  ├─ /predict/company/{id}  <- XGBoost + SHAP         │
│  ├─ /predict/premium       <- 3-zone pricing         │
│  ├─ /predict/wellness-roi  <- ROI simulator          │
│  └─ /companies/*           <- Dashboard data         │
└──────────────────────┬───────────────────────────────┘
                       │ SQLAlchemy
                       ▼
┌──────────────────────────────────────────────────────┐
│  PostgreSQL  (port 5432)                             │
│  companies | employees | training_snapshots          │
│  telemetry | clinical_events                         │
└──────────────────────────────────────────────────────┘
        MLflow (port 5000) tracks training runs
```

---

## Quick Start

**Requirement:** Docker Desktop with at least 4 GB RAM allocated.

```bash
git clone https://github.com/rupal2k/aegis-ai.git
cd aegis-ai
docker-compose up -d
```

The first run takes **3–5 minutes** — the API container automatically:
1. Generates 5,000 synthetic employee records (with 12-month health telemetry)
2. Seeds the PostgreSQL database
3. Trains the XGBoost model with Optuna hyperparameter tuning

Watch progress:
```bash
docker-compose logs -f api
```

When you see `Uvicorn running on http://0.0.0.0:8000`, open:

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| API docs | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |

---

## Demo Credentials

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Underwriter | `underwriter@safenet.com` | `demo123` | All 20 companies + PDF reports |
| HR Manager | `hr@technova.com` | `demo123` | TechNova Solutions only |
| HR Manager | `hr@bharatsteel.com` | `demo123` | Bharat Steel Works only |

---

## Features

### Underwriter Console
- **Portfolio overview** — all companies ranked by Health Risk Score, colour-coded by risk band
- **Company deep dive** — HRS gauge, risk band distribution, SHAP-driven top risk drivers
- **Underwriting recommendation** — Accept / Standard / Conditional / Decline with premium delta
- **PDF report download** — multi-currency underwriting reports (10 currencies supported)
- **Industry risk profile** — aggregate benchmarks by sector

### HR Manager Dashboard
- **Workforce health overview** — risk band donut, key metrics (steps, HR, smokers, chronic)
- **Age vs claims scatter** — with chronic condition colour overlay
- **Top risk drivers** — SHAP importance with HR-friendly plain-language labels
- **Recommended interventions** — wellness program suggestions mapped to top 3 drivers
- **Wellness ROI simulator** — project premium savings from a target HRS improvement

### Multi-Currency Support
10 currencies with real-time switching: INR, USD, EUR, GBP, AED, SGD, AUD, JPY, CAD, CHF

---

## How It Works

### Health Risk Score (HRS)

```
Employee features (21 variables)
  ├─ Demographics: age, BMI, chronic conditions, smoker
  ├─ Telemetry: steps, resting HR, sleep, SpO2, active minutes
  ├─ Clinical: visit count, hospitalisations
  └─ Engineered: activity_score, health_composite, interaction terms
           |
    XGBoost (log loss ratio prediction, 60-trial Optuna search)
           |
    HRSScorer (percentile normalisation -> 0-100)
           |
    Risk Band: Low (<30) | Moderate (30-60) | High (60-80) | Critical (80+)
```

### Dynamic Premium Pricing

```
HRS 0-40:   Discount zone  -> up to 15% off  (healthy groups rewarded)
HRS 41-60:  Standard zone  -> no adjustment  (average groups at book rate)
HRS 61-100: Loading zone   -> up to 30% up   (high-risk groups loaded)
```

### SHAP Explainability

Every prediction includes the top 5 feature contributors:
```json
{
  "feature": "avg_resting_hr",
  "value": 84.2,
  "shap_value": 0.312,
  "direction": "increases risk",
  "explanation": "Resting heart rate (84 bpm) increases risk"
}
```

---

## Project Structure

```
aegis-ai/
├── data/
│   ├── generate.py           # Synthetic data generator (5K employees, 12 months telemetry)
│   └── load_to_db.py         # CSV -> PostgreSQL loader
│
├── ml_engine/
│   ├── features.py           # Feature engineering (21 features incl. interaction terms)
│   ├── scorer.py             # HRSScorer (loss ratio -> 0-100 via percentile normalisation)
│   ├── explainer.py          # SHAP wrapper (per-employee + company-level)
│   ├── premium_calculator.py # 3-zone pricing + wellness ROI
│   ├── training/train.py     # Optuna tuning + XGBoost + MLflow tracking
│   └── artifacts/            # Saved model + scorer + feature names (git-ignored)
│
├── ingestion/
│   ├── main.py               # FastAPI app + router registration
│   ├── normalizer.py         # SHA-256 anonymisation + range clamping
│   ├── models/schemas.py     # Pydantic request/response models
│   └── routers/
│       ├── predict.py        # /predict/* endpoints
│       ├── companies.py      # /companies/* endpoints
│       ├── ingest.py         # /ingest/* endpoints (wearable, clinical, company)
│       └── health.py         # /health
│
├── dashboard/
│   ├── app.py                # Entry point + routing + auth gate
│   ├── auth.py               # Login form + session state
│   ├── api_client.py         # httpx helpers + @st.cache_data(ttl=60)
│   ├── currency.py           # 10-currency conversion + fmt helpers
│   ├── underwriter_view.py   # 3-tab underwriter dashboard
│   ├── hr_view.py            # 3-tab HR manager dashboard
│   └── pdf_report.py         # ReportLab underwriting report generator
│
├── tests/                    # 20 integration tests (all passing, ~211s)
│
├── scripts/
│   ├── bootstrap.py          # Idempotent first-run setup (data + DB + model)
│   └── entrypoint.sh         # Docker entrypoint (bootstrap -> uvicorn)
│
├── Dockerfile.api            # FastAPI + ML engine image
├── Dockerfile.dashboard      # Streamlit dashboard image
├── docker-compose.yml        # Full stack: db + mlflow + api + dashboard
├── requirements.docker.txt   # Clean dependencies for Docker builds
└── .github/workflows/ci.yml  # GitHub Actions: test + docker build
```

---

## Running Tests

With the stack running:
```bash
docker-compose exec api python -m pytest tests/ -v
```

Without Docker (local dev):
```bash
pip install -r requirements.docker.txt
python data/generate.py
python data/load_to_db.py
python -m ml_engine.training.train
python -m pytest tests/ -v
```

---

## API Reference

Full interactive docs at `http://localhost:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API + model + DB health check |
| GET | `/companies` | List all companies |
| GET | `/companies/{id}/employees` | Employee health snapshot |
| GET | `/predict/company/{id}` | Company HRS + SHAP drivers |
| POST | `/predict/employee` | Single employee prediction |
| POST | `/predict/premium` | HRS -> adjusted premium |
| POST | `/predict/wellness-roi` | Wellness program ROI projection |
| POST | `/ingest/wearable` | Ingest wearable device data |
| POST | `/ingest/clinical` | Ingest clinical event |
| POST | `/ingest/company` | Bulk employee roster upload |

---

## Local Development (No Docker)

```bash
# Terminal 1 — API
uvicorn ingestion.main:app --reload --port 8000

# Terminal 2 — Dashboard
streamlit run dashboard/app.py

# Terminal 3 — MLflow (optional)
mlflow server --host 0.0.0.0 --port 5000
```

---

## Technology Choices

| Decision | Choice | Why |
|----------|--------|-----|
| ML model | XGBoost | Accurate, fast, SHAP-native explainability |
| Hyperparameter tuning | Optuna (60 trials) | Bayesian optimisation > grid search |
| Explainability | SHAP TreeExplainer | Interpretable for underwriters |
| Experiment tracking | MLflow | Full auditability of training runs |
| Backend | FastAPI | Async, Pydantic validation, auto Swagger docs |
| Frontend | Streamlit | Python-only, rapid iteration for MVP |
| Database | PostgreSQL | Production-grade, scales beyond SQLite |
| Privacy | SHA-256 salted hash | Employee IDs anonymised at point of entry |
| Currency | 10 static FX rates | No external dependency, quarterly refresh |

---

## Roadmap

- [ ] OAuth 2.0 / SAML authentication (replace demo users)
- [ ] Audit logging and compliance reporting
- [ ] Live FX API integration (replace static rates)
- [ ] Real-time pipeline (Kafka streaming HRS updates)
- [ ] Kubernetes deployment with horizontal scaling
- [ ] ONNX model export for non-Python runtimes

---

*Built with FastAPI · XGBoost · SHAP · Streamlit · PostgreSQL · Docker*
