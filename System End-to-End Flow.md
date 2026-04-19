# System End-to-End Flow — Aegis AI

**Last Updated**: 2026-04-18  
**Purpose**: Trace data from origin to screen — every transformation documented

---

## Overview

This document traces a single piece of data — an employee's wearable reading — from the moment it arrives at the API to the moment it affects a premium recommendation on screen.

It also covers the full underwriting workflow from login to PDF download.

---

## Flow 1: Synthetic Data Generation → Database

```
python data/generate.py
    ↓
generate_companies()
  → 20 companies with industry-based risk_profile [0.28–0.75]
  → Saved to data/output/companies.csv
    ↓
generate_employees(companies)
  → 5,000 employees, proportional to employee_count
  → age/bmi/smoker/diabetic/hypertension correlated with company risk_profile
  → employee_id = SHA-256(salt + "EMP_00001")[:16]  (anonymised immediately)
  → Saved to data/output/employees.csv
    ↓
generate_telemetry(employees, companies)
  → 60,000 rows (5,000 employees × 12 months)
  → steps/HR/sleep/spo2 derived from fitness = f(bmi, smoker, risk_profile)
  → Seasonal variation via cosine function (peaks mid-year)
  → Saved to data/output/telemetry.csv
    ↓
generate_clinical_events(employees, companies)
  → ~20,000–30,000 events (Poisson-distributed visit count)
  → Event types routed by conditions (diabetics → diabetes events)
  → Real ICD-10 codes (I10, E11.9, J45.909...)
  → Saved to data/output/clinical_events.csv
    ↓
build_training_dataset(employees, telemetry, clinical, companies)
  → Aggregates telemetry to 1 row/employee (mean steps, step_volatility, hr_trend...)
  → Aggregates clinical to 1 row/employee (visit_count, hospitalized_count, total_claims)
  → Merges all on employee_id
  → Computes loss_ratio = total_claims / premium_share
  → Computes high_risk = (loss_ratio > 1.2)
  → Saved to data/output/training_dataset.csv
    ↓
data/load_to_db.py
  → Creates SQLite/PostgreSQL tables (companies, employees, telemetry, clinical_events)
  → Loads CSVs into tables
  → Creates training_snapshots (pre-joined, pre-aggregated feature view)
```

**Time cost**: ~30 seconds on modern hardware (60,000 telemetry rows)

---

## Flow 2: Model Training → Artifacts

```
python -m ml_engine.training.train
    ↓
load_and_prepare()
  → Reads data/output/training_dataset.csv
  → engineer_features():
      + activity_score = (steps_norm + hr_norm + sleep_norm) / 3 × 100
      + health_composite = smoker×15 + diabetic×20 + hypertension×15 + BMI_excess + age
      + smoker_diabetic = smoker × diabetic
      + bmi_age_risk = (bmi/25) × (age/40)
      + clinical_burden = visit_count × (1 + hospitalized_count)
      + loss_ratio_log = log1p(loss_ratio)
  → get_feature_matrix() → X (5000×21), y (5000 log-loss-ratios)
  → Stratified train/test split (80/20) on loss_ratio quartiles
    ↓
Optuna hyperparameter search (60 trials)
  → Each trial: 3-fold CV on X_train, scores by MAE
  → TPE sampler focuses on promising parameter regions
  → Best trial selected
    ↓
Final model training
  → best_params["n_estimators"] = 2000 (with early stopping)
  → 10% validation holdout for early stopping
  → XGBoost trains until validation MAE stops improving (50 rounds patience)
  → Best iteration logged to MLflow
    ↓
HRSScorer calibration
  → fit(training_predictions):  p05 = 5th percentile, p95 = 95th percentile
  → Defines the mapping: [p05, p95] → [0, 100]
    ↓
Artifacts saved:
  ml_engine/artifacts/xgb_model.pkl        (XGBoost model)
  ml_engine/artifacts/hrs_scorer.pkl       ({"p05": ..., "p95": ..., "fitted": True})
  ml_engine/artifacts/feature_names.pkl    (["age", "bmi", "chronic_count", ...])
  
MLflow experiment logged:
  http://localhost:5000/#/experiments/aegis-underwriting
  → params: n_estimators, max_depth, learning_rate, ...
  → metrics: train_mae, test_mae, train_r2, test_r2, hrs_p05, hrs_p95
  → artifacts: xgb_model.pkl, hrs_scorer.pkl, feature_names.pkl
```

---

## Flow 3: API Server Startup

```
uvicorn ingestion.main:app --reload --port 8000
    ↓
FastAPI app initialised
  → Routers mounted: /health, /ingest/*, /predict/*, /companies/*
  → CORS middleware added
  → Pydantic models loaded (schema validation ready)
    ↓
First API call to /predict/* triggers get_model()
  → AegisModel.__init__():
      joblib.load("xgb_model.pkl")         → XGBoost model object (~100MB)
      joblib.load("hrs_scorer.pkl")        → {"p05": -0.03, "p95": 1.28, "fitted": True}
      joblib.load("feature_names.pkl")     → ["age", "bmi", "chronic_count", ...]
      AegisExplainer(model, feature_names) → shap.TreeExplainer(model)
  → _MODEL_INSTANCE = AegisModel()  (singleton, loads once)
    ↓
API ready at http://localhost:8000
  → Swagger UI at http://localhost:8000/docs
```

**First-request cost**: ~500ms (pickle loading + SHAP explainer init)  
**Subsequent requests**: ~50ms (model already in memory)

---

## Flow 4: Company Prediction Request

```
Dashboard calls: GET /predict/company/COMP_001
    ↓
FastAPI routes to predict_company("COMP_001")
    ↓
DB query (training_snapshots):
  SELECT age, bmi, smoker, ... FROM training_snapshots WHERE company_id = 'COMP_001'
  → Returns 248 rows (TechNova employees)
    ↓
pd.DataFrame(rows)  (248 × 16)
    ↓
Numeric casting:
  df.apply(pd.to_numeric, errors="coerce")  → Handles string-encoded numbers from SQLite
    ↓
model.predict_company(df):
    ↓
  engineer_features(df):
    → Adds activity_score, health_composite, smoker_diabetic, bmi_age_risk, clinical_burden
    → df: 248 × 21
    ↓
  X = df[feature_names].values  (248 × 21 numpy array)
    ↓
  xgb_model.predict(X) → log_preds (248 log-loss-ratios)
    ↓
  np.expm1(log_preds) → pred_lrs (248 actual loss ratios, e.g., 0.72, 1.23, 0.45...)
    ↓
  scorer.score_batch(log_preds) → hrs_array (248 HRS scores, e.g., 34.2, 68.1, 22.7...)
    ↓
  mean_hrs = np.mean(hrs_array)  → e.g., 45.2
    ↓
  explainer.explain_batch(X):
    shap.TreeExplainer.shap_values(X) → 248×21 SHAP matrix
    np.abs(shap_values).mean(axis=0)  → 21 mean absolute importances
    Sort by importance → top 5 features
    → [{"feature": "health_composite", "importance": 0.412}, ...]
    ↓
  Return: {
    "employee_count": 248,
    "mean_loss_ratio": 0.823,
    "mean_hrs": 45.2,
    "risk_band": "Moderate",
    "hrs_distribution": [34.2, 68.1, 22.7, ...],  # All 248 HRS values
    "top_risk_drivers": [{"feature": "health_composite", "importance": 0.412}, ...]
  }
    ↓
Back in predict_company endpoint:
  hrs_array = np.array(result["hrs_distribution"])
  low      = (hrs_array < 30).mean() * 100    → 38.2%
  moderate = (30 ≤ hrs < 60).mean() * 100    → 41.5%
  high     = (60 ≤ hrs < 80).mean() * 100    → 14.8%
  critical = (hrs ≥ 80).mean() * 100          → 5.5%
    ↓
Return CompanyPredictionResponse:
  {
    "company_id": "COMP_001",
    "company_name": "TechNova Solutions",
    "employee_count": 248,
    "mean_loss_ratio": 0.8234,
    "mean_hrs": 45.2,
    "risk_band": "Moderate",
    "low_risk_pct": 38.2,
    "moderate_risk_pct": 41.5,
    "high_risk_pct": 14.8,
    "critical_risk_pct": 5.5,
    "top_risk_drivers": [...]
  }
```

**End-to-end latency**: ~80–150ms for 248 employees

---

## Flow 5: Underwriter Dashboard — Full Login to PDF Download

```
1. User opens browser → http://localhost:3000

2. Streamlit runs dashboard/app.py
   → sys.path.insert(0, project_root)
   → st.set_page_config(layout="wide", ...)
   → CSS injected via st.markdown()

3. st.session_state.get("user") → None → Show login form

4. User enters: underwriter@safenet.com / demo123
   → form submitted
   → USERS["underwriter@safenet.com"] found
   → passwords match
   → st.session_state["user"] = {"name": "Priya Mehta", "role": "underwriter", ...}
   → st.rerun()

5. Streamlit re-executes app.py from top
   → st.session_state["user"] found → Skip login form
   → Sidebar rendered: name, org, role, currency selector (INR default), logout

6. user["role"] == "underwriter" → underwriter_view.render()

7. with st.spinner("Loading portfolio..."):
   → list_companies()
       → Cache miss → GET http://localhost:8000/companies
       → Returns 20 companies [{company_id, company_name, industry, ...}]
       → Stored in Streamlit cache (60s TTL)
   
   → For each of 20 companies (loop):
       get_company_prediction(company_id)
         → Cache miss (first load) → GET /predict/company/{id}
         → Returns {mean_hrs, risk_band, top_risk_drivers, ...}
         → Cached for 60s
       
       calculate_premium(base_premium, mean_hrs)
         → POST /predict/premium
         → Returns {adjusted_premium, adjustment_pct, zone, recommendation}
       
       Append row dict to rows[]

8. df = pd.DataFrame(rows)  →  20 × 10 DataFrame

9. Render 4 metric cards:
   col1: "Total companies" = 20
   col2: "Total employees" = 4,823 (sum)
   col3: "Average HRS"     = 58.4  (mean)
   col4: "Portfolio premium" = fmt_crore(sum of adjusted premiums)
                               → "₹14.20 Cr" (INR) or "$1.70 M" (USD)

10. Render Tab 1: Portfolio overview
    → px.bar(df.sort_values("mean_hrs"), ..., color="risk_band")
    → Table with ProgressColumn for HRS, currency-converted premium columns

11. User switches currency dropdown from INR to USD
    → st.session_state["currency"] = "USD"
    → Streamlit re-renders (no API calls — data already in df)
    → All fmt() calls now multiply by 0.01198
    → Column headers change: "Base (₹)" → "Base (USD)"
    → Table values update: ₹800,000 → "$9,584"
    → Portfolio metric changes: "₹14.20 Cr" → "$1.70 M"

12. User clicks Tab 2: Company deep dive
    → Selectbox shows all 20 companies
    → User selects "Bharat Steel Works"
    → get_company_prediction("COMP_002") — may be cached or fresh
    → calculate_premium(base_premium, mean_hrs)
    
    → Gauge chart: mean_hrs=72.4 shown on 0-100 gauge (in "High" red zone)
    → Risk breakdown bar: Low=18%, Moderate=31%, High=35%, Critical=16%
    → Top 5 risk drivers with normalised progress bars
    → Underwriting decision:
        "Recommendation: High risk. Apply surcharge or require wellness program.
         Adjusted premium: $9,584 (+12.00% vs base $8,558)"

13. User clicks "Download underwriting report (PDF)"
    → generate_underwriting_report(
          {**pred, "company_name": "Bharat Steel Works", "company_id": "COMP_002"},
          prem,
          currency="USD"   ← active currency passed in
       )
    → ReportLab creates in-memory PDF (BytesIO)
    → Returns bytes
    → st.download_button triggers browser download
    → User saves: aegis_report_COMP_002.pdf
```

---

## Flow 6: HR Manager — Wellness ROI Simulator

```
1. hr@technova.com logs in
   → st.session_state["user"]["company_id"] = "COMP_001"
   → hr_view.render()

2. Data loaded:
   → list_companies() → cached
   → company = COMP_001 found
   → get_company_prediction("COMP_001") → {mean_hrs: 45.2, risk_band: "Moderate", ...}
   → calculate_premium(800000, 45.2) → {adjusted_premium: 800000, adjustment_pct: 0.0, zone: "standard"}
   → get_company_employees("COMP_001") → 248 employee records

3. Top metrics:
   → Employees: 248
   → Health risk score: 45.2, Moderate
   → Current premium: ₹800,000 (+0.00% vs book rate)
   → Annual claims est.: ₹658,000 (= 0.823 × 800,000)

4. User opens Tab 3: Wellness ROI Simulator
   → current HRS input: 45.2 (pre-filled from API)
   → improvement slider: user moves to 20 (target: reduce HRS by 20 points)
   → projected = max(0.0, 45.2 - 20) = 25.2

5. calculate_wellness_roi(800000, 45.2, 25.2) called
   → POST /predict/wellness-roi
   → {base_premium: 800000, current_hrs: 45.2, projected_hrs_after_program: 25.2}
   
   → API calls calculate_premium_adjustment(800000, 45.2):
       45.2 in standard zone (41-60) → no adjustment → ₹800,000
   → API calls calculate_premium_adjustment(800000, 25.2):
       25.2 in discount zone (0-40)
       discount = (40 - 25.2) / 40 × 0.15 = 0.0555 → 5.55% off
       adjusted = 800000 × 0.9445 = ₹755,600
   
   → Returns: {
       current_premium:   800000,
       projected_premium: 755600,
       annual_savings:    44400,
       hrs_improvement:   20.0,
       current_zone:      "standard",
       projected_zone:    "discount"
     }

6. Render results:
   → Metric: "Current premium" ₹800,000 [standard]
   → Metric: "Projected premium" ₹755,600 [discount]
   → Metric: "Annual savings" ₹44,400 [20.0 HRS points]
   
   → Waterfall chart (in selected currency, e.g., USD):
       Bar 1 (absolute): $9,580 (current premium)
       Bar 2 (relative, green, going down): -$532 (savings)
       Bar 3 (total, blue): $9,048 (projected premium)
   
   → Success message:
       "A 20-point HRS improvement could save ₹44,400 annually.
        Use this projection when renewing with your insurer."
```

---

## Data Transformation Summary

| Stage | Format | Size |
|-------|--------|------|
| Raw synthetic data | 5 CSVs | ~50MB |
| Database tables | SQLite/PostgreSQL | ~20MB |
| Training dataset | 5,000 × 23 DataFrame | ~2MB |
| ML model artifacts | 3 pickle files | ~100MB |
| API prediction response | JSON | ~5KB per company |
| Dashboard DataFrame | 20 × 10 | <1KB |
| PDF report | bytes | ~50KB |

---

## Latency Budget (Per Full Dashboard Load)

| Step | Latency | Notes |
|------|---------|-------|
| API startup (model load) | 500ms | Once only, singleton |
| list_companies() | 20ms | Simple SELECT |
| 20 × predict/company | ~2,000ms | 20 × 100ms parallel |
| 20 × predict/premium | ~200ms | 20 × 10ms POST |
| Streamlit rendering | ~500ms | Charts, tables, CSS |
| **Total (first load)** | **~3s** | Cached on reload: ~0.5s |
| **Subsequent loads** | **<0.5s** | 60s TTL cache hit |

---

## Links
- [[Data Generation & Pipeline]] — Phase 1 in detail
- [[ML Engine Architecture]] — Phase 2 in detail
- [[API Layer Architecture]] — Phase 3–4 in detail
- [[Dashboard Deep Dive]] — Phase 5 in detail
