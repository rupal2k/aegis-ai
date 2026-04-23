# Aegis AI - User Manual Cheat Sheet

**Last Updated**: 2026-04-24  
**Purpose**: Quick-start guide for using, running, and retraining Aegis AI without reading all deep-dive notes.

---

## What Aegis AI Does

Aegis AI is an **AI-powered group insurance underwriting platform** for:
- scoring employee and company health risk
- calculating adjusted premiums
- generating underwriting recommendations
- simulating wellness ROI for HR teams
- exporting PDF reports

**Main stack**:
- Backend: FastAPI
- Dashboard: Streamlit
- ML: XGBoost + SHAP
- DB: PostgreSQL (Docker) / SQLite fallback
- MLOps: MLflow

---

## Main Views

### Underwriter Console
Use this to:
- view all companies in the portfolio
- compare company HRS (Health Risk Score)
- review top risk drivers
- calculate adjusted premiums
- download underwriting PDFs
- upload a custom workforce CSV for analysis

### HR Manager Dashboard
Use this to:
- view one company's workforce health profile
- inspect employee-level risk patterns
- see top risk drivers
- simulate wellness ROI and premium savings

---

## Core Concepts

| Term | Meaning |
|------|---------|
| **HRS** | Health Risk Score from 0-100; lower is healthier |
| **Risk Bands** | Low, Moderate, High, Critical |
| **Loss Ratio** | Predicted claims relative to premium |
| **Top Drivers** | SHAP-based feature importance behind a score |
| **Adjusted Premium** | Base premium after applying risk logic |

### Risk Bands
- `0-29` -> Low
- `30-59` -> Moderate
- `60-79` -> High
- `80-100` -> Critical

### Premium Zones
- Low-risk -> discount zone
- Average-risk -> standard zone
- High-risk -> loading zone

---

## Demo Users

```text
underwriter@safenet.com  / demo123
hr@technova.com          / demo123
hr@bharatsteel.com       / demo123
```

---

## Fastest Way to Run It

### Option 1 - Full Docker Stack
```bash
docker compose up -d
```

Then open:
- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`  (development only)
- MLflow: `http://localhost:5000`

### Option 2 - Hybrid Local Dev
Use this when developing API/dashboard locally but keeping DB + MLflow in Docker.

```bash
# 1. Start DB and MLflow
docker compose up db mlflow -d

# 2. Start API
DATABASE_URL=postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db \
ENV=development \
python -m uvicorn ingestion.main:app --port 8000 --log-level warning

# 3. Start Dashboard
streamlit run dashboard/app.py --server.port 8501
```

---

## Typical User Workflow

### Underwriter Flow
1. Log in as underwriter.
2. Open portfolio overview.
3. Compare companies by HRS and premium impact.
4. Open a company deep dive.
5. Review risk distribution + top drivers.
6. Check recommendation and adjusted premium.
7. Download PDF report.

### HR Manager Flow
1. Log in as HR manager.
2. Review company metrics and employee health profile.
3. Inspect top risk drivers.
4. Open Wellness ROI tab.
5. test a projected HRS improvement.
6. review projected premium savings.

### Upload Dataset Flow
1. Open **Upload dataset** in Underwriter Console.
2. Fill company details.
3. Download template or upload CSV.
4. Run analysis.
5. Review risk metrics, employee table, and PDF.

**Required CSV columns**:
```text
employee_id, age, gender, bmi, smoker, diabetic, hypertension, job_category
```

---

## Key API Endpoints

```text
GET  /health
POST /auth/token
GET  /companies
GET  /companies/{company_id}/employees
POST /predict/employee
GET  /predict/company/{company_id}
POST /predict/premium
POST /predict/wellness-roi
POST /ingest/wearable
POST /ingest/clinical
POST /ingest/company
```

Use these when:
- integrating another frontend
- testing predictions directly
- sending ingest payloads
- validating auth and RBAC behaviour

---

## How Model Training Works

Training uses synthetic + engineered employee health data to predict loss ratio, then calibrates the output into HRS.

### Training Pipeline
```text
Generate data -> load DB -> build training dataset -> train XGBoost -> calibrate HRS -> save artifacts
```

### Main Training Files
- `ml_engine/training/train.py`
- `ml_engine/features.py`
- `ml_engine/scorer.py`
- `ml_engine/explainer.py`
- `ml_engine/artifacts/`

### Model Artifacts Produced
- `xgb_model.pkl`
- `hrs_scorer.pkl`
- `feature_names.pkl`

### Retrain the Model
If artifacts are missing, bootstrap or training will regenerate them.

Typical training path from docs:
```bash
python -m ml_engine.training.train
```

If using the project bootstrap flow:
```bash
docker compose up -d
```
Bootstrap will:
1. generate data if missing
2. load DB if empty
3. train model if artifacts are missing

---

## Data Generation and Loading

Synthetic data includes:
- companies
- employees
- telemetry
- clinical events
- training snapshots

Common flow:
```text
data generation -> CSV output -> DB load -> training snapshots -> ML training
```

Use this when:
- setting up a fresh environment
- rebuilding demo data
- testing ingestion/training end to end

---

## Health Checks

### Service Check
```bash
docker compose ps
```

### API Check
```bash
curl http://localhost:8000/health
```

### Tests
```bash
python -m pytest tests/ -q --tb=no
```

Expected documented state:
- functional tests passing
- security tests passing
- dashboard/API/MLflow reachable

---

## Security Notes

Current documented security includes:
- JWT authentication
- bcrypt password verification
- RBAC for underwriter vs hr_admin
- rate limiting on `/auth/token`
- CSP, HSTS, and other security headers
- non-root API container
- audit logging on sensitive endpoints

### Known Open Issue
`/ingest/wearable`, `/ingest/clinical`, and `/ingest/company` still need full `require_company_access` enforcement for `hr_admin` users.

---

## When To Use Which Area

- Use **Dashboard** for day-to-day underwriting and HR workflows.
- Use **API** for integration testing and automation.
- Use **MLflow** to inspect training runs and metrics.
- Use **Docker Compose** for the easiest full-system startup.
- Use **local native API/dashboard** when actively developing.

---

## If Something Breaks

Check these first:
1. `docker compose ps`
2. `http://localhost:8000/health`
3. `http://localhost:8501`
4. model artifacts exist
5. DB connection string points to `db:5432` in Docker, `localhost:5432` in native local dev

Common issues already documented in [[Bug Log]].

---

## Best Related Notes

- [[Aegis AI Hub]]
- [[Phase Progress]]
- [[System End-to-End Flow]]
- [[ML Engine Architecture]]
- [[API Layer Architecture]]
- [[Dashboard Deep Dive]]
- [[Architecture Decisions]]
- [[Security Tests/SECURITY_REPORT]]

---

*This note is intentionally short. Use it as the operational cheat sheet, then jump to the deeper docs when needed.*
