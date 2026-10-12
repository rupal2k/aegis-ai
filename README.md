---
title: Aegis AI
emoji: 🛡️
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Aegis AI

**Health-risk-based underwriting for group health insurance.**

[![CI](https://github.com/rupal2k/aegis-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rupal2k/aegis-ai/actions/workflows/ci.yml)
[![API status](https://img.shields.io/website?url=https%3A%2F%2Faegis-ai-wss8.onrender.com%2Fhealth&label=API&up_message=online&down_message=offline&cacheSeconds=300)](https://aegis-ai-wss8.onrender.com/docs)
![Python](https://img.shields.io/badge/python-3.11-blue)

Aegis AI scores the health risk of a corporate workforce from anonymized wearable and clinical data and turns that score into a premium recommendation. Every score comes with an explanation of what drove it.

Group health policies are usually priced from the previous year's claims, which reacts slowly to changes in workforce health and gives wellness programs no measurable effect on price. Aegis AI produces a **Health Risk Score (HRS, 0–100)** per employee and per company, explains it with SHAP, and maps it to a discounted, standard or loaded premium.

**[Live demo →](https://huggingface.co/spaces/Rupa2k/aegis-ai)**

[![Aegis AI dashboard sign-in screen](docs/images/dashboard-login.png)](https://huggingface.co/spaces/Rupa2k/aegis-ai)

| | |
|---|---|
| **Live demo** | [huggingface.co/spaces/Rupa2k/aegis-ai](https://huggingface.co/spaces/Rupa2k/aegis-ai) |
| **API reference** | [aegis-ai-wss8.onrender.com/docs](https://aegis-ai-wss8.onrender.com/docs) |
| **Model card** | [MODEL_CARD.md](MODEL_CARD.md) |

> The demo is free-tier hosted and may take up to a minute to wake after a period of inactivity.

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [API overview](#api-overview)
- [Model](#model)
- [Data and privacy](#data-and-privacy)
- [Project structure](#project-structure)
- [Testing and CI](#testing-and-ci)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- **Health Risk Score.** An XGBoost model predicts each employee's expected loss ratio, which is calibrated to a 0–100 score and aggregated per company.
- **Explainability.** Every prediction includes ranked SHAP drivers in plain language, so an underwriter can see why a score is high.
- **Premium engine.** Maps HRS to three pricing bands: discount (0–40), standard (41–60) and loading (61–100).
- **Wellness ROI.** Projects the premium saving from a target improvement in a company's HRS.
- **Role-based access.** Underwriters see the full book. HR administrators see only their own company, and the API enforces this scoping on every request.
- **Reproducible training.** Hyperparameter search with Optuna. Every run is tracked in MLflow.
- **Reporting.** PDF underwriting reports and CSV upload for scoring new employee rosters.

## Architecture

```
 Wearables / clinical events / HR rosters
                  │
                  ▼
 ┌────────────────────────────────┐      ┌──────────────────────────────┐
 │ Ingestion API (FastAPI)        │      │ ML engine                    │
 │ validate · normalize · hash IDs├─────►│ features → XGBoost → HRS     │
 │ JWT auth · role-scoped access  │◄─────┤ SHAP explainer · premiums    │
 └───────────────┬────────────────┘      └──────────────┬───────────────┘
                 │                                      │
                 ▼                                      ▼
          PostgreSQL                          MLflow (experiment tracking)
                 ▲
                 │ REST
 ┌───────────────┴────────────────┐
 │ Dashboard (Streamlit + Plotly) │
 │ Underwriter view · HR view     │
 └────────────────────────────────┘
```

| Layer | Stack |
|---|---|
| Ingestion and serving | FastAPI, Pydantic, SQLAlchemy, PostgreSQL |
| Machine learning | XGBoost, Optuna, SHAP, scikit-learn, MLflow |
| Dashboard | Streamlit, Plotly, ReportLab |
| Delivery | Docker, GitHub Actions, Render (API), Hugging Face Spaces (dashboard) |

## Getting started

### Prerequisites

- Docker with Docker Compose, with at least 4 GB of memory available to containers
- Python 3.11 (only for running without Docker)

### Run with Docker Compose

```bash
git clone https://github.com/rupal2k/aegis-ai.git
cd aegis-ai
cp .env.example .env        # then set SECRET_KEY, HASH_SALT and the database password
```

Add dashboard users, either as `config/users.json` (git-ignored) or as a JSON string in the `AEGIS_USERS_JSON` environment variable:

```json
[
  {
    "email": "underwriter@example.com",
    "password_hash": "<bcrypt hash>",
    "role": "underwriter",
    "name": "Demo Underwriter",
    "org": "Example Insurance"
  },
  {
    "email": "hr@example.com",
    "password_hash": "<bcrypt hash>",
    "role": "hr_admin",
    "name": "Demo HR Admin",
    "org": "Example Corp",
    "company_id": "<company id>"
  }
]
```

Generate a password hash with:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

Start the stack:

```bash
docker compose up -d
```

On first start, the API generates synthetic data, seeds the database and trains the model in the background, which takes about 3–5 minutes. The API is reachable straight away, and the prediction endpoints start working once the model is trained.

| Service | URL |
|---|---|
| Dashboard | http://localhost:8501 |
| API docs | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |

### Run without Docker

Requires a running PostgreSQL instance and `DATABASE_URL` set in the environment.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.docker.txt

python data/generate.py            # synthetic dataset
python data/load_to_db.py          # load into PostgreSQL
python -m ml_engine.training.train # train and register the model

uvicorn ingestion.main:app --reload --no-server-header   # API on :8000
streamlit run dashboard/app.py                           # dashboard on :8501
```

## API overview

All endpoints except health checks require a bearer token from `POST /auth/token`. Full request and response schemas are at [`/docs`](https://aegis-ai-wss8.onrender.com/docs).

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/token` | Exchange credentials for a JWT |
| `GET` | `/health`, `/health/db` | Service and database health |
| `POST` | `/ingest/wearable` | Ingest one wearable telemetry record |
| `POST` | `/ingest/clinical` | Ingest one clinical event |
| `POST` | `/ingest/company` | Bulk-upload an employee roster |
| `POST` | `/predict/employee` | HRS and SHAP drivers for one employee |
| `GET` | `/predict/company/{company_id}` | Aggregated HRS for a company |
| `POST` | `/predict/premium` | Premium recommendation from an HRS |
| `POST` | `/predict/wellness-roi` | Projected saving from an HRS improvement |
| `GET` | `/companies` | Companies visible to the caller |
| `GET` | `/companies/{company_id}/employees` | Employees of a company |

## Model

The production model is a gradient-boosted regressor (XGBoost) that predicts log loss ratio from 31 engineered features covering activity, resting heart rate, sleep, SpO2, clinical history and lab markers. Optuna tunes the hyperparameters with cross-validated MAE as the objective, and the prediction is calibrated to the 0–100 HRS scale.

Performance figures, intended use, limitations, the fairness audit (`fairness_check.py`) and the retraining policy are documented in the **[model card](MODEL_CARD.md)**. Training runs and their results are recorded in [TRAINING_RESULTS.md](TRAINING_RESULTS.md).

> **Intended use.** This is a research and demonstration system trained on synthetic data. It is not validated for real underwriting decisions.

## Data and privacy

- **Synthetic dataset.** 20 fictional companies across 15 industries, 5,000 employees, 60,000 monthly telemetry records and about 19,000 clinical events with ICD-10 codes. Variables are correlated realistically, for example lower activity goes with higher claims. See [`data/generate.py`](data/generate.py).
- **Pseudonymization.** Employee identifiers are salted and SHA-256 hashed before storage. Raw identifiers are never persisted.
- **Least privilege.** Base premiums and portfolio-level data are never returned to HR administrator accounts.
- **Configuration.** All secrets come from environment variables. Nothing sensitive is committed to the repository.

## Project structure

```
aegis-ai/
├── ingestion/            FastAPI service: auth, ingestion, prediction, health
│   ├── auth/             JWT issuing, user store, role dependencies
│   ├── models/           Pydantic schemas
│   └── routers/          auth, ingest, predict, companies, health
├── ml_engine/            Feature engineering, scoring, SHAP, premium calculator
│   ├── training/         Training pipeline (XGBoost + Optuna + MLflow)
│   └── artifacts/        Serialized model and scorer
├── dashboard/            Streamlit app: underwriter and HR views, PDF reports
├── data/                 Synthetic data generator and database loader
├── scripts/              Container entrypoint and first-run bootstrap
├── tests/                Pytest suite
├── nginx/                TLS reverse proxy for the Compose stack
├── docker-compose.yml
├── Dockerfile.api        API image (Render)
├── Dockerfile            Dashboard image (Hugging Face Spaces)
└── render.yaml           Render blueprint
```

## Testing and CI

```bash
python -m pytest tests/ -v
```

The suite covers data quality, normalization, the API and authorization rules, the ML engine, the training pipeline and dashboard components.

Each push to `main` runs the [CI workflow](.github/workflows/ci.yml):

1. **Security.** Bandit static analysis and a `pip-audit` dependency CVE scan
2. **Test.** Generate data into a disposable PostgreSQL service, train a reduced model and run the test suite
3. **Build.** Build the API, dashboard and nginx Docker images

## Roadmap

- Streaming ingestion (Kafka) for continuous telemetry
- Per-employee HRS trends over time
- Per-tenant database isolation
- Drift monitoring with automated retraining triggers
- Confidence intervals on premium quotes
- SSO / OAuth in place of the static user store

## License

Released under the MIT License.
