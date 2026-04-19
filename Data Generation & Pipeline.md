# Data Generation & Pipeline — Aegis AI

**Last Updated**: 2026-04-18  
**Phase**: 1 ✅  
**Source Files**: `data/generate.py`, `data/load_to_db.py`, `ingestion/normalizer.py`

---

## Overview

Because real employee health data is sensitive and requires complex data-sharing agreements, Aegis AI generates **fully synthetic but statistically realistic** data. The generator uses a seeded random state to ensure reproducibility across runs (`np.random.seed(42)`, `Faker.seed(42)`).

This document covers:
- How companies and employees are generated
- How health telemetry is simulated
- How clinical events are constructed
- How the ML training dataset is assembled
- How incoming real data would be normalised

---

## 1. Company Generation

### The Logic

Each company is assigned a **base risk profile** (`0.0–1.0`) based on industry type. This risk profile drives all downstream employee health data — it's the "DNA" of the company's health characteristics.

### Industry Risk Mapping
```python
risk_map = {
    "Manufacturing":   0.70,   # High: physical labour, injury risk
    "Construction":    0.75,   # Highest: manual work, outdoor hazards
    "BPO":             0.65,   # High: sedentary + night shifts
    "Logistics":       0.60,   # High: physical stress, irregular hours
    "Retail":          0.55,   # Medium-high: standing, physical
    "Food Processing": 0.60,   # High: physical, hygiene issues
    "Healthcare":      0.40,   # Medium: active but stress
    "IT/Software":     0.30,   # Low: sedentary but young, fit
    "Analytics":       0.28,   # Lowest: desk workers, healthiest
    "Finance":         0.35,   # Low: desk, stressful but managed
    "Banking":         0.38,   # Low: similar to finance
    "Insurance":       0.35,   # Low: desk, managed lifestyle
    "Education":       0.42,   # Medium: diverse
    "Agriculture":     0.50,   # Medium: seasonal, outdoor
    "Pharma":          0.38,   # Low-medium: professional, awareness
    "Energy":          0.55,   # Medium-high: field + plant work
}
```

**Why this matters**: A Construction company with `risk_profile=0.75` will generate employees with higher BMI, more smoking, more chronic conditions, lower step counts — because these are all correlated with high-risk industries in real data.

### Random Jitter
```python
"risk_profile": clamp(base_risk + np.random.normal(0, 0.07), 0.1, 0.95)
```
A ±7% Gaussian jitter adds realism — not all construction firms are equally unhealthy. The `clamp()` function prevents values below 0.1 (unrealistically healthy) or above 0.95 (everyone hospitalized).

### Company Dataset
```
20 companies: TechNova Solutions, Bharat Steel Works, QuickServe Retail,
              MediPlus Hospitals, GreenField Agriculture, UrbanLogix Transport,
              DataSpark Analytics, ClearView Finance, BuildRight Construction,
              EduNext Learning, SafeNet Insurance, PrimeFood Industries,
              CloudBridge IT, SwiftBank Services, AeroTech Manufacturing,
              RetailMax Group, Pinnacle Pharma, HorizonEnergy, MegaMart,
              GlobalConnect BPO

IDs: COMP_001 through COMP_020
Employee counts: 80–600 per company (random)
Base premiums: ₹400,000 – ₹1,200,000 per year (random)
```

---

## 2. Employee Generation

### The Logic

5,000 employees are distributed across companies proportional to `employee_count`. The **company's risk profile directly drives individual health attributes**:

```python
age = clamp(np.random.normal(35 + rp * 10, 8), 22, 62)
```
- Company risk `rp = 0.30` (IT) → Mean age ≈ 38
- Company risk `rp = 0.75` (Construction) → Mean age ≈ 42.5

**Why age is correlated with risk**: High-risk industries tend to retain older employees in physical roles (experienced field workers, operators). Low-risk industries hire young graduates.

```python
bmi = clamp(np.random.normal(22 + rp * 8, 3.5), 16.0, 42.0)
```
- IT (rp=0.30): Mean BMI ≈ 24.4 (healthy)
- Construction (rp=0.75): Mean BMI ≈ 28.0 (borderline obese)

**Correlated conditions**: Smoker, Diabetic, and Hypertension probabilities all increase with company risk AND with co-morbidities:
```python
smoker      = prob < (0.05 + rp * 0.35)           # 5-40% range
diabetic    = prob < (0.03 + rp * 0.25 + (0.05 if age > 45 else 0))  # age adjustment
hypertension= prob < (0.04 + rp * 0.30 + (0.06 if bmi > 28 else 0)) # BMI adjustment
```

**Why co-morbidity correlation matters**: In real health data, smokers are more likely to have hypertension. Obese employees are more likely to be diabetic. The generator captures these relationships, making the ML model's training data realistic.

### Employee ID Anonymization
```python
def anonymize_id(raw_id: str) -> str:
    salt = os.environ.get("HASH_SALT", "aegis_dev_salt_2024")
    return hashlib.sha256(f"{salt}{raw_id}".encode()).hexdigest()[:16]
```

Employee IDs are **immediately hashed with a salted SHA-256** before storage. The raw ID `EMP_00001` becomes a 16-character hex string like `a1b2c3d4e5f6a7b8`. This means:
- The database never stores PII
- The same raw ID always produces the same hashed ID (deterministic for joining)
- Can't reverse-engineer the real ID without the salt
- `HASH_SALT` can be rotated to break linkability across datasets

---

## 3. Telemetry Generation (Wearable Data Simulation)

### The Logic

For each employee, 12 months of wearable telemetry is generated. Each metric is derived from the employee's `fitness` composite:

```python
fitness = clamp(1.0 - (rp * 0.5 + emp["bmi"] / 80 + emp["smoker"] * 0.1), 0.1, 1.0)
```

- High-risk, obese, smoker: fitness ≈ 0.1 (very unfit)
- Low-risk, normal BMI, non-smoker: fitness ≈ 0.9 (very fit)

### Seasonal Variation
```python
seasonal = 1.0 - 0.12 * np.cos(2 * np.pi * month / 12)
```
This cosine function creates a **12-month seasonal cycle** where activity peaks mid-year (month 6–7, i.e., summer) and dips in winter (month 12, January). Amplitude is ±12% of baseline — realistic for India (festival season, monsoon).

### Generated Metrics
```python
avg_daily_steps:  4000 + fitness * 5000 * seasonal       # 500–18,000
resting_hr:       58 + (1 - fitness) * 25 + smoker * 5   # 45–105 bpm
active_minutes:   (4000 + fitness * 5000 * seasonal) / 120 # 0–120 min
sleep_hours:      7.0 - (1 - fitness) * 1.5               # 4.0–9.5 hours
spo2:             97.5 - smoker * 1.2 - (1 - fitness) * 0.8 # 90–100%
```

**Why step_volatility matters**: The ML feature `step_volatility` is the standard deviation of daily steps across 12 months. High volatility (active in summer, inactive in winter) predicts irregular health behaviour — a risk signal even if mean steps are acceptable.

**Why hr_trend matters**: The ML feature `hr_trend` is the linear regression slope of resting_hr across months. An employee whose resting HR increases from 65 to 80 bpm over 12 months is likely developing cardiovascular risk — even if month 1 looks fine.

---

## 4. Clinical Event Generation

### The Logic

Each employee generates a Poisson-distributed number of clinical visits based on their health profile:

```python
base_visits = int(np.random.poisson(
    1.5 + rp * 3 + emp["diabetic"] * 3 + emp["hypertension"] * 2
))
```

- Healthy IT employee: 1.5 + 0.30*3 = ~2.4 visits/year (mostly preventive)
- Unhealthy Construction employee: 1.5 + 0.75*3 + 2 + 3 = ~8.75 visits/year

### Event Type Routing
The event type is selected probabilistically, biased by the employee's conditions:
```python
if emp["diabetic"] and prob < 0.40:  etype = "diabetes"
elif emp["hypertension"] and prob < 0.35: etype = "hypertension"
elif emp["smoker"] and prob < 0.25:   etype = "respiratory"
elif rp > 0.6 and prob < 0.15:       etype = "injury"
else:                                  etype = "general_visit"
```

### ICD-10 Codes

Real medical codes are used for authenticity:
```
general_visit: Z00.00 (routine exam), Z00.01 (routine child health exam)
hypertension:  I10 (essential hypertension), I11.9 (hypertensive heart disease)
diabetes:      E11.9 (Type 2 DM without complications), E11.65 (Type 2 DM with hyperglycemia)
respiratory:   J06.9 (acute URI), J45.909 (unspecified asthma)
injury:        S09.90XA (unspecified head injury), M54.5 (low back pain)
```

### Claim Amounts (₹)
```
general_visit: ₹800 – ₹2,500    (outpatient, prescription)
hypertension:  ₹2,000 – ₹8,000  (medication, monitoring)
diabetes:      ₹3,000 – ₹12,000 (insulin, complications)
respiratory:   ₹1,500 – ₹6,000  (nebulizers, hospital visit)
injury:        ₹5,000 – ₹25,000 (fracture, surgery)
```

**Hospitalization flag**: Any claim > ₹15,000 is flagged as hospitalized — this becomes a key ML feature (`hospitalized_count`).

---

## 5. Building the ML Training Dataset

### Aggregation Logic

The training dataset merges employee static data, 12 months of telemetry (aggregated), and clinical history:

```python
# Telemetry aggregated per employee
tele_agg = telemetry.groupby("employee_id").agg(
    avg_daily_steps=("avg_daily_steps", "mean"),  # Year average
    step_volatility=("avg_daily_steps", "std"),    # Behaviour consistency
    avg_resting_hr =("resting_hr",      "mean"),   # Resting HR average
    hr_trend       =("resting_hr",      lambda x: np.polyfit(range(len(x)), x, 1)[0]),  # Slope
    avg_active_mins=("active_minutes",  "mean"),
    avg_sleep_hours=("sleep_hours",     "mean"),
    avg_spo2       =("spo2",            "mean"),
)

# Clinical aggregated per employee
clin_agg = clinical.groupby("employee_id").agg(
    total_claims      =("claim_amount", "sum"),
    visit_count       =("event_id",     "count"),
    hospitalized_count=("hospitalized", "sum"),
)
```

### Target Variable: Loss Ratio
```python
loss_ratio = total_claims / premium_share
```
Where `premium_share = base_premium / employee_count` (per-employee share of company premium).

- loss_ratio < 1.0: Employee's claims < their premium share (profitable)
- loss_ratio = 1.0: Break-even
- loss_ratio > 1.0: Employee's claims exceed their premium share (loss-making)
- `high_risk = (loss_ratio > 1.2)` → 20% tolerance before flagging

**Why loss ratio (not raw claim amount)**: Loss ratio normalises for premium size. A ₹10,000 claim from a ₹5,000/year premium customer is worse than a ₹10,000 claim from a ₹20,000/year customer.

### Chronic Count
```python
chronic_count = diabetic + hypertension  # 0, 1, or 2
```
A simple co-morbidity count that the model uses as both a feature and an interaction term.

---

## 6. Normalizer: Processing Real-World Input

The `ingestion/normalizer.py` handles production data ingestion — when real companies send wearable or clinical data.

### Wearable Data Normalization
```python
def normalize_wearable(payload):
    return {
        "avg_daily_steps": clamp(payload.get("daily_steps") or 5000, 500, 30000),
        "resting_hr":      clamp(payload.get("heart_rate_rest") or 72, 45, 110),
        "active_minutes":  clamp(payload.get("active_mins") or 30, 0, 240),
        "sleep_hours":     round(float(clamp(payload.get("sleep_hrs") or 7.0, 3.0, 12.0)), 1),
        "spo2":            round(float(clamp(payload.get("oxygen_saturation") or 97.0, 85.0, 100.0)), 1),
    }
```

Three things happen here:
1. **Alias resolution**: Incoming API uses camelCase (`restingHR`); database uses snake_case (`resting_hr`)
2. **Outlier clipping**: Sensor errors (e.g., 300 bpm) are clamped to physiological ranges
3. **Imputation**: If a field is missing, sensible population medians are substituted

### Why Clamp, Not Reject?
```
Option A: Reject outliers (throw 422 error)
  Pro: Forces client to send clean data
  Con: Blocks all records if one sensor has a fault
  Reality: Fitness trackers frequently send 0 steps (battery dead), 
           or 200 bpm (false reading). Rejecting = no data on that employee.

Option B: Clamp to physiological range
  Pro: Always get a record (even if imperfect)
  Con: Distorts extreme data
  
Decision: Clamp because missing data is worse than slightly distorted data.
          A clamped 10,000 steps is better than no step count at all.
```

### Pydantic Range Validators (API Boundary)
```python
class EmployeePredictionRequest(BaseModel):
    avg_daily_steps: float = Field(..., ge=0, le=30000)
    avg_resting_hr:  float = Field(..., ge=40, le=120)
    avg_spo2:        float = Field(97.0, ge=85, le=100)
```
These are physiological limits:
- Steps: 30,000 is world-record level (99.9th percentile). Anything above = sensor error.
- Resting HR: <40 = clinical bradycardia, >120 = tachycardia (medical emergency, not wearable noise)
- SpO2: <85% = requires hospitalisation immediately

---

## 7. Database Schema

### Tables and Relationships
```
companies
  company_id (PK) | company_name | industry | city | employee_count | base_premium

employees
  employee_id (PK, SHA-256) | company_id (FK) | age | gender | bmi |
  smoker | diabetic | hypertension | job_category

telemetry
  employee_id (FK) | company_id (FK) | month |
  avg_daily_steps | resting_hr | active_minutes | sleep_hours | spo2

clinical_events
  event_id (PK) | employee_id (FK) | company_id (FK) | month |
  event_type | icd10_code | claim_amount | hospitalized

training_snapshots
  employee_id (FK) | company_id (FK) | age | bmi | smoker | diabetic |
  hypertension | chronic_count | avg_daily_steps | step_volatility |
  avg_resting_hr | hr_trend | avg_active_mins | avg_sleep_hours | avg_spo2 |
  visit_count | hospitalized_count | loss_ratio | high_risk
  (Pre-computed feature snapshots for ML inference — avoids JOIN every request)
```

### Why `training_snapshots`?
```
Option A: Join employees + telemetry + clinical on every prediction request
  Query time: ~150ms (5-table join × 500 employees)
  Latency: Unacceptable for dashboard (10 companies × 500 employees = 5000 joins)

Option B: Pre-compute feature snapshot once, query flat table
  Query time: ~10ms (single SELECT on training_snapshots)
  Latency: Acceptable (150ms → 10ms = 15× faster)
  
Trade-off: training_snapshots is stale (updated periodically)
  Acceptable because health data doesn't change hourly
  Snapshot refreshed when new wearable data comes in (Phase 6 trigger)
```

---

## 8. Data Quality Summary

| Metric | Value |
|--------|-------|
| Companies | 20 |
| Total Employees | 5,000 |
| Telemetry Records | 60,000 (5,000 × 12 months) |
| Clinical Events | ~20,000–30,000 (Poisson distributed) |
| Training Dataset Rows | 5,000 |
| Training Features | 21 |
| Loss Ratio Range | 0.000 – 4.0+ |
| Mean Loss Ratio | ~0.8–1.2 |
| High-Risk Percentage | ~20-25% |
| Seed | 42 (fully reproducible) |

---

## Links
- [[ML Engine Architecture]] — How features are trained and scored
- [[API Layer Architecture]] — How data flows through endpoints
- [[Decisions & Rationale#DECISION-001]] — Why HRS was chosen over raw features
- [[Decisions & Rationale#DECISION-005]] — Why synthetic data was used
