# Aegis AI — Dynamic Group Insurance Underwriting Platform

![CI](https://github.com/rupal2k/aegis-ai/workflows/CI/badge.svg)

A B2B SaaS platform that shifts group health insurance from **reactive** pricing (based on last year's claims) to **proactive** underwriting (based on real-time workforce health telemetry).

---

## The Problem

Insurers price corporate group health policies on stale, annual claims data. Manufacturers look as risky as tech companies until a bad year proves otherwise. Wellness programs produce no measurable premium benefit because there's no standard way to quantify their impact.

Aegis AI solves this by ingesting continuous anonymized health telemetry (wearable data + clinical events), scoring each corporate workforce with a dynamic **Health Risk Score** (0–100), and translating that into precision premium pricing — with full SHAP explainability.

---

## Architecture

Three tiers:

| Tier | Technology | Purpose |
|------|-----------|---------|
| **Data ingestion** | FastAPI + Pandas + PostgreSQL | Accept, validate, normalize, anonymize |
| **AI underwriting** | XGBoost + Optuna + SHAP + MLflow | Predict loss ratio, explain drivers |
| **B2B portal** | Streamlit + Plotly | Two role-based dashboards |

---

## Quick Start

**Requirements:** Docker Desktop with at least 4 GB memory allocated.

```bash
git clone https://github.com/rupal2k/aegis-ai.git
cd aegis-ai
docker-compose up -d
```

Wait ~5 minutes on first run (data generation + model training happen automatically).

Then open:
- **Dashboard:** http://localhost:8501
- **API docs:** http://localhost:8000/docs
- **MLflow:** http://localhost:5000


## Key Features

- **Real-time prediction API** — < 100ms per employee, served from cached XGBoost
- **SHAP explainability** — every risk score comes with ranked drivers in plain language
- **Dynamic premium engine** — three-tier pricing: discount (0–40), standard (41–60), loading (61–100)
- **Wellness ROI calculator** — HR can simulate premium savings from projected HRS improvements
- **MLflow tracking** — every training run is reproducible and inspectable
- **Role-based portal** — underwriters see all groups; HR admins see only their own company (row-level access)
- **Anonymization-first** — employee IDs are SHA-256 hashed before storage; raw PII never persists

---

## Dataset

- **20 fictional companies** across 15 industries
- **5,000 employees** with realistic demographics
- **60,000 monthly telemetry records** (steps, resting HR, sleep, SpO2, active minutes)
- **~19,000 clinical events** with ICD-10 codes and claim amounts
- All synthetic but **statistically correlated** — lower activity → higher claims, as in real data

See `data/generate.py` for the generator.

---

## Model Performance

| Metric | Value |
|--------|-------|
| Test MAE (log loss ratio) | ~0.40 |
| Test R² | ~0.78 |
| Prediction latency | 60–80 ms |
| Optuna trials | 30 |
| Training time | ~3 min |

All metrics logged to MLflow on every training run.

---

## Project Structure

```
aegis-ai/
├── data/                    # Synthetic data generator + schema
├── ingestion/               # FastAPI service (Tier 1)
│   ├── models/              # Pydantic schemas
│   └── routers/             # ingest, predict, health endpoints
├── ml_engine/               # ML pipeline (Tier 2)
│   ├── features.py          # feature engineering
│   ├── scorer.py            # HRS calibration
│   ├── explainer.py         # SHAP wrapper
│   ├── premium_calculator.py
│   └── training/train.py    # XGBoost + Optuna + MLflow
├── dashboard/               # Streamlit portal (Tier 3)
├── tests/                   # pytest suite (20 tests)
├── scripts/                 # Bootstrap helpers
├── docker-compose.yml
├── Dockerfile.api
└── Dockerfile.dashboard
```

---

## Local Development

```bash
# Without Docker — all services run on host
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.docker.txt

python data/generate.py
python data/load_to_db.py
python -m ml_engine.training.train

uvicorn ingestion.main:app --reload --no-server-header  # API on :8000
streamlit run dashboard/app.py              # UI on :8501
```

### Run Tests

```bash
python -m pytest tests/ -v
```

20 tests across data quality, normalisation, API endpoints, ML engine, and dashboard components.

---

## API Reference

### Ingestion

- `POST /ingest/wearable` — single telemetry record
- `POST /ingest/clinical` — single clinical event
- `POST /ingest/company` — bulk employee roster upload

### Prediction

- `POST /predict/employee` — HRS + SHAP drivers for one employee
- `GET /predict/company/{company_id}` — aggregated workforce HRS
- `POST /predict/premium` — HRS → adjusted premium
- `POST /predict/wellness-roi` — project premium savings from HRS improvement

Full OpenAPI spec auto-generated at `/docs`.

---

## Security Notes

- All employee IDs are SHA-256 hashed with a salt before database insert
- Base premium and company risk profiles are stored but never exposed to HR admin accounts (row-level access enforced at the API router)
- Secrets are environment-variable driven — no credentials in code
- In production, replace hardcoded user list with OAuth/SSO + full JWT lifecycle

---

## Future Work

- Streaming ingestion via Kafka for true real-time telemetry
- Per-employee HRS trends over time (requires time-partitioned model)
- Multi-tenant database isolation (currently all companies share one schema)
- Model drift monitoring + auto-retrain triggers
- Calibrated confidence intervals on premium quotes

---

## Tech Stack

FastAPI · PostgreSQL · Pandas · XGBoost · Optuna · SHAP · MLflow · Streamlit · Plotly · Docker · GitHub Actions · Pydantic · SQLAlchemy

---

## License

MIT License — Capstone project by Rupal.
