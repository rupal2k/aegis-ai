# API Layer Architecture — Aegis AI

**Last Updated**: 2026-04-18  
**Phase**: 3–4 ✅  
**Source Files**: `ingestion/main.py`, `ingestion/routers/predict.py`, `ingestion/routers/companies.py`, `ingestion/routers/ingest.py`, `ingestion/models/schemas.py`, `ingestion/normalizer.py`

---

## Overview

The FastAPI backend is the **single point of truth** for the entire platform. It:
- Validates all incoming data (Pydantic models with physiological range checks)
- Serves ML predictions (HRS, premium, wellness ROI)
- Provides company/employee data to the dashboard
- Ingests real wearable and clinical data (Phase 6 ready)

---

## 1. Application Entry Point (`ingestion/main.py`)

```python
app = FastAPI(
    title="Aegis AI — Underwriting Platform API",
    description="Tier 1 + Tier 2: secure ingestion + ML-powered predictions.",
    version="1.1.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(predict.router)
app.include_router(companies.router)   # Added in Phase 5
```

### Router Architecture
Each domain has its own router (file), registered with the main app. This pattern:
- Keeps files small and focused (each under 130 lines)
- Allows independent testing of each domain
- Provides clean URL prefix grouping (`/predict/*`, `/companies/*`, `/ingest/*`)

### CORS Middleware
```python
allow_origins=["*"]
```
Currently set to allow all origins (development). In production, this would be:
```python
allow_origins=["https://app.aegis-ai.com", "https://dashboard.aegis-ai.com"]
```
Without CORS headers, the Streamlit dashboard running on port 3000 cannot call the API on port 8000 (browser blocks cross-origin requests).

---

## 2. Prediction Router (`ingestion/routers/predict.py`)

### Endpoint 1: Single Employee Prediction

```
POST /predict/employee
```

**Request Schema** (`EmployeePredictionRequest`):
```python
age:               int    [18, 70]       # Hard physiological bounds
avg_daily_steps:   float  [0, 30,000]    # Above 30K = sensor error
avg_resting_hr:    float  [40, 120]      # Below 40 = clinical, above 120 = tachycardia
avg_spo2:          float  [85, 100]      # Below 85 = medical emergency
avg_sleep_hours:   float  [3, 12]        # Defaults to 7.0 if not provided
bmi:               float  [10, 60]       # 10 = cachexia, 60 = morbid obesity
chronic_count:     int    (optional)     # Computed as diabetic + hypertension if None
```

**Response Schema** (`EmployeePredictionResponse`):
```python
{
    "predicted_loss_ratio": 0.9234,
    "health_risk_score": 62.4,
    "risk_band": "High",
    "top_drivers": [
        {"feature": "smoker", "value": 1.0, "shap_value": 0.412, 
         "direction": "increases risk", "explanation": "Smoking status increases risk"}
    ]
}
```

**Logic flow**:
```
Pydantic validates request → auto-compute chronic_count if missing → 
model.predict_one(emp) → enrich each SHAP driver with plain-language explanation → 
return response
```

**SHAP Driver Enrichment**:
```python
def _enrich_driver(model, driver: dict) -> FeatureDriver:
    return FeatureDriver(
        feature     = driver["feature"],
        value       = driver["value"],
        shap_value  = driver["shap_value"],
        direction   = driver["direction"],
        explanation = model.explainer.plain_language(driver),  # Human-readable
    )
```
This adds a `plain_language` field: `"Smoking status increases risk"` instead of `"smoker: +0.412"`.

---

### Endpoint 2: Company Prediction (Portfolio Engine)

```
GET /predict/company/{company_id}
```

**Logic flow**:
```
1. Validate company exists (404 if not found)
2. Pull all employee snapshots from training_snapshots (single SQL query)
3. Cast all columns to numeric (handling string-stored numbers in DB)
4. Run model.predict_company(df) → batch XGBoost inference on all employees
5. Compute HRS band distribution:
   - low:      HRS < 30  (% of workforce)
   - moderate: 30 ≤ HRS < 60
   - high:     60 ≤ HRS < 80
   - critical: HRS ≥ 80
6. Return complete CompanyPredictionResponse
```

**Numeric casting step**:
```python
df = df.apply(
    lambda col: pd.to_numeric(col, errors="coerce").fillna(col) 
    if col.dtype == object else col
)
```
This step is critical. SQLite/PostgreSQL may return numeric columns as strings depending on how data was loaded. Without explicit casting, XGBoost throws type errors. Using `errors="coerce"` safely handles the cast (non-numeric values → NaN, then filled with original).

**Band Distribution** (applied in endpoint, not in model):
```python
hrs_array = np.array(result["hrs_distribution"])
low      = float((hrs_array < 30).mean() * 100)
moderate = float(((hrs_array >= 30) & (hrs_array < 60)).mean() * 100)
high     = float(((hrs_array >= 60) & (hrs_array < 80)).mean() * 100)
critical = float((hrs_array >= 80).mean() * 100)
```

**Why compute band distribution in the endpoint, not in the model?**
The model returns raw HRS distribution as a list. Computing percentages in the endpoint gives the API more flexibility — the thresholds (30, 60, 80) can be adjusted without retraining the model.

---

### Endpoint 3: Premium Calculation

```
POST /predict/premium
```

**Request**:
```json
{"base_premium": 800000, "hrs": 72.4}
```

**Response**:
```json
{
    "base_premium":      800000,
    "adjusted_premium":  896000,
    "adjustment_pct":    12.0,
    "zone":              "loading",
    "recommendation":    "High risk. Apply surcharge or require wellness program."
}
```

**Logic**: Thin wrapper around `ml_engine.premium_calculator.calculate_premium_adjustment`. The endpoint exists to:
- Expose the calculation via REST (usable by any client)
- Allow the dashboard to call it independently from prediction
- Keep ML engine decoupled from API routing

---

### Endpoint 4: Wellness ROI

```
POST /predict/wellness-roi
```

**Request**:
```json
{
    "base_premium": 800000,
    "current_hrs": 72.4,
    "projected_hrs_after_program": 55.0
}
```

**Response**:
```json
{
    "current_premium":   896000,
    "projected_premium": 800000,
    "annual_savings":    96000,
    "hrs_improvement":   17.4,
    "current_zone":      "loading",
    "projected_zone":    "standard"
}
```

**Why `projected_hrs_after_program` as a field name (not just `target_hrs`)?**
Field names serve as documentation. `projected_hrs_after_program` is unambiguous about what it represents — the HR team is inputting their expected outcome, not just a number.

---

## 3. Companies Router (`ingestion/routers/companies.py`)

Added in Phase 5 to serve dashboard needs.

### Endpoint 1: List All Companies

```
GET /companies
```

```sql
SELECT company_id, company_name, industry, city, employee_count, base_premium
FROM companies
ORDER BY company_name
```

**Why raw SQL, not ORM?** This query has no dynamic parameters. Using ORM (`db.query(Company).all()`) would generate identical SQL but with extra boilerplate. Raw SQL is more readable for simple queries.

### Endpoint 2: Company Employee Snapshot

```
GET /companies/{company_id}/employees
```

```sql
SELECT s.employee_id, s.age, s.gender, s.bmi,
       s.smoker, s.diabetic, s.hypertension, s.chronic_count,
       s.avg_daily_steps, s.avg_resting_hr, s.avg_sleep_hours,
       s.visit_count, s.hospitalized_count, s.loss_ratio, s.high_risk,
       e.job_category
FROM training_snapshots s
JOIN employees e ON e.employee_id = s.employee_id
WHERE s.company_id = :cid
```

**Why JOIN employees for `job_category`?**
`training_snapshots` stores aggregated health features (averages across 12 months), but `job_category` is a static attribute stored only in `employees`. The JOIN is necessary to include it in the dashboard's employee scatter plot (age vs. claims).

**Why `training_snapshots` not `telemetry`?**
`telemetry` has 12 rows per employee (one per month). `training_snapshots` has 1 row per employee (12-month average). Querying raw telemetry for 500 employees = 6,000 rows. Snapshots = 500 rows. The join is simpler and the dashboard only needs aggregated values.

---

## 4. Pydantic Schemas (`ingestion/models/schemas.py`)

### Why Pydantic?

Every API boundary — requests in, responses out — is defined as a Pydantic model. This provides:
1. **Automatic validation**: Bad request → 422 Unprocessable Entity (not 500 crash)
2. **Self-documenting**: Schema shows up in Swagger UI at `/docs`
3. **Type coercion**: String "42" auto-converted to int 42 where type is `int`
4. **Default values**: `avg_spo2: float = Field(97.0, ...)` means field is optional in request

### Input Validation: Wearable Data

```python
class WearablePayload(BaseModel):
    external_employee_id: str = Field(..., description="Raw ID, will be hashed")
    company_id:           str = Field(..., pattern=r"^COMP_\d{3}$")  # Regex validation
    
    daily_steps:      Optional[int]   = Field(None, alias="steps")        # Accept "steps" or "daily_steps"
    heart_rate_rest:  Optional[int]   = Field(None, alias="restingHR")    # Accept camelCase
    
    @field_validator("daily_steps")
    def steps_sanity(cls, v):
        if v is not None and (v < 0 or v > 100_000):
            raise ValueError(f"Step count out of sensor range: {v}")
        return v
```

**Three layers of validation**:
1. **Type check** (Pydantic): Is `daily_steps` an int?
2. **Range validator** (`@field_validator`): Is it between 0 and 100,000?
3. **Business normalizer** (`normalize_wearable`): Clamp to safe physiological range

This layered approach:
- Rejects clearly bad data (negative steps = sensor bug)
- Fixes borderline data (steps=31,000 → clamp to 30,000)
- Doesn't crash on missing fields (all wearable fields are Optional)

### The `pattern` Validator on `company_id`

```python
company_id: str = Field(..., pattern=r"^COMP_\d{3}$")
```

This regex enforces `COMP_001` through `COMP_999`. If a client sends `company_id: "COMP01"` (missing underscore) or `"comp_001"` (lowercase), they get a clear 422 error with the invalid field named. This prevents garbage data from propagating to SQL queries.

### Why Separate Request and Response Models?

```python
# Request: only what the API accepts
class PremiumRequest(BaseModel):
    base_premium: float = Field(..., gt=0)  # Must be positive
    hrs:          float = Field(..., ge=0, le=100)

# Response: everything the API returns
class PremiumResponse(BaseModel):
    base_premium:      float
    adjusted_premium:  float
    adjustment_pct:    float
    zone:              str
    recommendation:    str
```

Separation means:
- Adding a new response field doesn't require clients to send it
- Removing a request field is backward compatible
- Response fields can be computed (not just echoed)

---

## 5. Ingestion Router (`ingestion/routers/ingest.py`)

Handles real data coming in from corporate health portals. Three endpoints:

### `/ingest/wearable` — Wearable Device Data
```
POST /ingest/wearable
Content: WearablePayload (single record)
→ Normalises → Stores to telemetry table
→ Returns: IngestResponse (records stored, errors)
```

### `/ingest/clinical` — Clinical Event Data
```
POST /ingest/clinical
Content: ClinicalEventPayload
→ Validates ICD-10 code format, claim amount range
→ Normalises → Stores to clinical_events table
```

### `/ingest/company` — Employee Roster Upload
```
POST /ingest/company
Content: CompanyBatchUpload (up to 1,000 employees)
→ Batch normalises all employees
→ Stores to employees table
→ Returns: IngestResponse with partial-success handling
```

**Partial Success Pattern**:
```python
class IngestResponse(BaseModel):
    status: Literal["success", "partial", "failed"]
    records_received: int
    records_stored: int
    errors: List[str] = []
```

If 47 of 50 records succeed and 3 fail validation, the API returns:
```json
{"status": "partial", "records_received": 50, "records_stored": 47, "errors": ["Record 12: BMI 70 exceeds limit", ...]}
```
This is better than rejecting the entire batch for one bad record.

---

## 6. Health Router

```
GET /health
→ {"status": "ok", "model_loaded": true, "db_connected": true}
```

Checks:
- Is the FastAPI process running? (obvious)
- Is the ML model loaded into memory? (might fail if artifacts missing)
- Is the database accessible? (might fail if PostgreSQL is down)

Used by:
- Load balancer health checks (in production)
- Dashboard startup (Streamlit can verify API is up before loading)
- Automated testing (`_server_up()` in test suite)

---

## 7. Full API Route Map

```
GET  /                              → Service info + route discovery
GET  /health                        → Health check (model + DB)
GET  /docs                          → Swagger UI (auto-generated)
GET  /redoc                         → ReDoc UI (alternative docs)

POST /ingest/wearable               → Ingest wearable data record
POST /ingest/clinical               → Ingest clinical event record
POST /ingest/company                → Batch upload employee roster

POST /predict/employee              → Single employee HRS + SHAP
GET  /predict/company/{company_id}  → Company-level HRS + distribution
POST /predict/premium               → HRS → adjusted premium
POST /predict/wellness-roi          → Projected ROI of wellness program

GET  /companies                     → List all companies (dashboard)
GET  /companies/{company_id}/employees → Employee data for HR view
```

**11 total endpoints** across 4 routers.

---

## 8. Database Session Management

```python
# ingestion/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_db():
    db = SessionLocal()
    try:
        yield db        # FastAPI uses this as a dependency
    finally:
        db.close()      # Always close, even if exception
```

**Dependency Injection Pattern**:
```python
@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    ...
```

FastAPI injects the `db` session automatically. The `finally: db.close()` ensures sessions are never leaked, even if the endpoint throws an exception. This prevents connection pool exhaustion.

---

## 9. Error Handling Strategy

### 404 — Company Not Found
```python
if not company:
    raise HTTPException(status_code=404, detail=f"Unknown company: {company_id}")
```

### 404 — No Employee Data
```python
if not rows:
    raise HTTPException(
        status_code=404,
        detail="No employee data found. Run feature snapshot generation first."
    )
```

The error message includes a **hint** ("Run feature snapshot generation first"). This is valuable for developers integrating the API — they know exactly what to do next.

### 422 — Validation Error (automatic)
Pydantic throws `RequestValidationError` when input doesn't match schema. FastAPI converts this to:
```json
{
    "detail": [
        {
            "loc": ["body", "avg_resting_hr"],
            "msg": "Input should be less than or equal to 120",
            "type": "less_than_equal"
        }
    ]
}
```
No code needed — Pydantic + FastAPI handle this automatically.

---

## 10. Key Decisions Made in the API Layer

| Decision | Choice | Reason |
|----------|--------|--------|
| Router per domain | `/predict`, `/companies`, `/ingest` | Separation of concerns, smaller files |
| Raw SQL for simple queries | Used in companies router | Readability over ORM abstraction |
| Pydantic validators | Separate per model | Validate at system boundary, not inside logic |
| Singleton model | `get_model()` | Avoid 500ms reload on every request |
| Partial success response | `status: "partial"` | Don't reject whole batch for one bad record |
| SHAP enrichment in endpoint | `_enrich_driver()` | Keeps AegisModel clean, adds context at API level |
| `training_snapshots` table | Pre-computed features | Query 500 rows not 6,000 rows |

---

## Links
- [[ML Engine Architecture]] — What the model does internally
- [[Data Generation & Pipeline]] — How training_snapshots were created
- [[Dashboard Deep Dive]] — How the dashboard calls these endpoints
- [[Decisions & Rationale#DECISION-002]] — FastAPI vs Django vs Flask
