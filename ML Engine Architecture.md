# ML Engine Architecture — Aegis AI

**Last Updated**: 2026-04-18  
**Phase**: 2 ✅  
**Source Files**: `ml_engine/training/train.py`, `ml_engine/features.py`, `ml_engine/scorer.py`, `ml_engine/explainer.py`, `ml_engine/__init__.py`

---

## Overview

The ML engine converts raw employee health snapshots into a **Health Risk Score (HRS)** — a 0–100 number that captures overall insurance risk. Lower = healthier. Higher = riskier.

The pipeline has 5 stages:
```
Raw Features → Feature Engineering → XGBoost Model → HRSScorer → SHAP Explainer
                                                         ↓
                                                    Risk Band
```

---

## 1. Feature Engineering (`ml_engine/features.py`)

### Why Feature Engineering?

Raw data alone is not predictive enough. XGBoost learns from signal — but raw features have noise, scale differences, and missing non-linear relationships. Feature engineering creates **domain-specific signals** that help the model learn faster and generalise better.

### The 21 Model Features

```python
FEATURE_COLUMNS = [
    # Demographics
    "age", "bmi", "chronic_count",
    "smoker", "diabetic", "hypertension",
    # Telemetry
    "avg_daily_steps", "step_volatility",
    "avg_resting_hr", "hr_trend",
    "avg_active_mins", "avg_sleep_hours", "avg_spo2",
    # Clinical
    "visit_count", "hospitalized_count",
    # Derived
    "activity_score", "health_composite",
    # Interaction
    "smoker_diabetic", "bmi_age_risk", "clinical_burden",
]
```

### Derived Feature 1: `activity_score` (0–100, higher = healthier)
```python
steps_norm = np.clip(avg_daily_steps / 10000, 0, 1.2)   # Normalise steps (peak = 10K)
hr_norm    = np.clip((80 - avg_resting_hr) / 30, 0, 1)  # Low HR = fit
sleep_norm = np.clip(1 - abs(avg_sleep_hours - 7.5) / 3, 0, 1)  # Optimal sleep = 7.5h

activity_score = (steps_norm + hr_norm + sleep_norm) / 3 * 100
```

**Logic**: 
- `steps_norm`: 10,000 steps = 1.0 (WHO recommendation). Above that is capped at 1.2.
- `hr_norm`: A resting HR of 50 bpm (fit athlete) = 1.0. A HR of 80+ bpm = 0.0 (unfit).
- `sleep_norm`: 7.5 hours is optimal (sleep medicine consensus). Too little OR too much reduces score.
- Equal weighting (÷3) — no single metric dominates.

**Why not just use raw metrics?**
Without this composite, XGBoost has to learn the 3-way interaction (steps + HR + sleep). The explicit composite gives it a head start, improving accuracy and reducing training data needed.

### Derived Feature 2: `health_composite` (higher = more risk)
```python
health_composite = (
    smoker       * 15 +    # Strong risk signal
    diabetic     * 20 +    # Strongest single condition
    hypertension * 15 +    # Strong risk signal
    clip(bmi - 25, 0, 20) * 1.5 +  # Risk starts at BMI 25, plateaus at 45
    (age / 60) * 10        # Gradual age risk
)
```

**Logic**:
- Diabetes gets 20 points (highest single-condition risk → 3× higher claims)
- Smoking and hypertension get 15 points each (strong but manageable risk)
- BMI only starts contributing above 25 (WHO threshold for overweight)
- Age contribution caps at 10 points (age 60 = maximum age adjustment)

**Max possible value**: 15+20+15+30+10 = 90 (older, obese, diabetic, smoker, hypertensive)
**Typical value for healthy person**: 0–10

### Interaction Feature 1: `smoker_diabetic`
```python
smoker_diabetic = smoker * diabetic  # 0 or 1 (1 if both present)
```

**Logic**: Smokers with diabetes have dramatically higher risk than the sum of individual risks. A smoker is 2× more likely to have cardiovascular complications from diabetes. The interaction term lets XGBoost capture this synergy without needing to infer it from two separate features.

### Interaction Feature 2: `bmi_age_risk`
```python
bmi_age_risk = (bmi / 25.0) * (age / 40.0)
```

**Logic**: High BMI at age 25 is less risky than high BMI at age 55. This feature encodes the multiplicative interaction between age and obesity. A 45-year-old with BMI 35 has `(35/25) × (45/40) = 1.575`, while a 25-year-old with same BMI has `(35/25) × (25/40) = 0.875` — correctly penalising older-overweight combinations more.

### Interaction Feature 3: `clinical_burden`
```python
clinical_burden = visit_count * (1 + hospitalized_count)
```

**Logic**: 10 outpatient visits with 0 hospitalisations = burden of 10. But 5 visits with 2 hospitalisations = burden of 5 × 3 = 15. Hospitalisations act as a **multiplier** on visit frequency — correctly giving higher weight to serious clinical history.

### Log-Transform of Target
```python
TARGET_LOG = "loss_ratio_log"
df[TARGET_LOG] = np.log1p(df[TARGET_COLUMN])
```

**Why log-transform?**
Loss ratios have a **long right tail** — most employees cluster between 0.0 and 2.0, but outliers can reach 10+ (catastrophic claims). If we train directly on loss ratio:
- Mean squared error is dominated by outliers
- Model learns to predict outliers well, performs poorly for typical cases
- After log1p transform, the distribution is much closer to normal
- Model predicts `log(1 + loss_ratio)`, then we `expm1(prediction)` to reverse

---

## 2. Hyperparameter Tuning with Optuna

### Why Optuna?

Instead of grid search (exhaustive, slow) or random search (no learning), Optuna uses **Bayesian optimisation** (TPE algorithm). It learns which hyperparameters are promising from previous trials, focusing exploration on productive regions of the parameter space.

### Search Space (60 Trials)
```python
params = {
    "n_estimators":     trial.suggest_int("n_estimators", 100, 500),
    "max_depth":        trial.suggest_int("max_depth", 3, 10),
    "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),  # Log scale
    "subsample":        trial.suggest_float("subsample", 0.6, 1.0),
    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
    "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
    "gamma":            trial.suggest_float("gamma", 0, 5),
    "reg_alpha":        trial.suggest_float("reg_alpha", 0, 5),     # L1 regularisation
    "reg_lambda":       trial.suggest_float("reg_lambda", 0, 5),    # L2 regularisation
}
```

**Key decisions**:
- `learning_rate` uses log scale because small differences at low end (0.01 vs 0.02) matter more than at high end (0.20 vs 0.21)
- Regularisation (`reg_alpha`, `reg_lambda`) prevents overfitting on 5,000 samples
- `subsample` / `colsample_bytree` add stochasticity (forest diversity)
- `gamma`: Minimum loss reduction to make a split — prevents overly granular trees

### 3-Fold Cross-Validation Objective
```python
scores = cross_val_score(
    model, X_train, y_train,
    cv=3, scoring="neg_mean_absolute_error", n_jobs=-1
)
return -scores.mean()
```
**Why 3-fold CV instead of validation set?**
- 3-fold uses all training data (more reliable estimate)
- `-1` n_jobs runs folds in parallel (3× speedup)
- MAE chosen over MSE: less sensitive to loss_ratio outliers (which we've already log-transformed)

---

## 3. Final Model Training with Early Stopping

### The Two-Phase Training Approach
```python
best_params["n_estimators"] = 2000  # Set high (early stopping will terminate early)
best_params["early_stopping_rounds"] = 50

# 10% validation split from training data
val_size = int(len(X_train) * 0.10)
X_tr, X_val = X_train[:-val_size], X_train[-val_size:]
y_tr, y_val = y_train[:-val_size], y_train[-val_size:]

model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
```

**Why this approach?**
Optuna found the **best hyperparameters** but used only 100–500 trees. The final training uses 2,000 trees with early stopping:
- Training stops when validation MAE hasn't improved for 50 consecutive rounds
- Result: Optimal number of trees (neither underfitting nor overfitting)
- `model.best_iteration` is logged to MLflow for reproducibility

### MLflow Experiment Tracking
```python
with mlflow.start_run(run_name="final_xgb_with_optuna") as run:
    mlflow.log_params(best_params)
    mlflow.log_metric("test_mae", metrics["test_mae"])
    mlflow.log_metric("test_r2", metrics["test_r2"])
    mlflow.log_artifact(str(model_path), artifact_path="model")
```

All training runs are logged to MLflow at `http://localhost:5000`. This provides:
- Full auditability (which parameters produced which results)
- Model versioning (can roll back to any previous run)
- Artifact storage (model, scorer, feature names all archived)
- Experiment comparison (multiple training runs side-by-side)

### Model Performance Metrics
```
train_mae:  MAE on log-transformed loss ratio (training set)
test_mae:   MAE on log-transformed loss ratio (held-out test set)
train_rmse: Root mean squared error (training)
test_rmse:  Root mean squared error (test)
train_r2:   Coefficient of determination (training)
test_r2:    Coefficient of determination (test)
```

**Stratified Split**: Split uses `pd.qcut(y, q=4)` to ensure all loss ratio quartiles (very low, low, high, very high) are equally represented in train and test sets. Without this, the test set might accidentally have mostly low-risk cases.

---

## 4. HRS Scorer — Converting Loss Ratio to 0–100

### The Problem

The model outputs `log(1 + loss_ratio)` — a dimensionless number that underwriters can't interpret. We need a 0–100 score.

### The Solution: Percentile Normalization
```python
class HRSScorer:
    def fit(self, log_loss_ratio_array):
        self.p05 = float(np.percentile(log_loss_ratio_array, 5))   # 5th percentile
        self.p95 = float(np.percentile(log_loss_ratio_array, 95))  # 95th percentile
        self.fitted = True

    def score(self, log_loss_ratio):
        normalized = (log_loss_ratio - self.p05) / (self.p95 - self.p05)
        return float(np.clip(normalized * 100, 0, 100))
```

**The Logic**:
1. **Fit on training data**: Compute p05 and p95 from all training predictions
2. **Score new predictions**: Map them linearly from [p05, p95] to [0, 100]
3. **Clip**: Any prediction below p05 gets HRS=0; above p95 gets HRS=100

**Why p05/p95 instead of min/max?**
- min/max is sensitive to extreme outliers (one anomalous prediction = distorted scale)
- p05/p95 are robust: 90% of predictions map to 0–100 "comfortably"
- 5% are extremely healthy (HRS < 0, clipped to 0)
- 5% are extremely risky (HRS > 100, clipped to 100)

**Persisted as dict** (not full object) for portability:
```python
joblib.dump(scorer.to_dict(), "hrs_scorer.pkl")
# → {"p05": -0.0321, "p95": 1.2843, "fitted": True}
```

### Risk Band Assignment
```python
def risk_band(self, hrs: float) -> str:
    if hrs < 30:  return "Low"
    if hrs < 60:  return "Moderate"
    if hrs < 80:  return "High"
    return "Critical"
```

**Why these thresholds?**
- `< 30` Low: Bottom 30% of risk — give premium discount
- `30–60` Moderate: Middle 30% — standard rate
- `60–80` High: Top 20%–30% — premium loading
- `≥ 80` Critical: Top 20% — significant loading or decline

These align with typical insurance actuarial buckets (healthy / standard / rated / declined).

---

## 5. SHAP Explainability (`ml_engine/explainer.py`)

### Why SHAP?

XGBoost makes accurate predictions, but without explanation, underwriters can't justify decisions ("Why did we surcharge TechNova 25%?"). SHAP (SHapley Additive exPlanations) assigns each feature a **contribution score** to each prediction.

### How SHAP Works (Simplified)
```
Prediction = base_value + SHAP(age) + SHAP(bmi) + SHAP(smoker) + ...
```
Each SHAP value is the **marginal contribution** of that feature to moving the prediction from the dataset average. Positive SHAP = increases risk; negative SHAP = reduces risk.

### Two Types of Explanation

**Per-employee explanation (`explain_one`)**:
```python
def explain_one(self, x_row, top_n=5) -> list:
    shap_values = self.explainer.shap_values(x_row.reshape(1, -1))[0]
    contributions = [
        {"feature": feat, "value": x_row[i], 
         "shap_value": shap_values[i],
         "direction": "increases risk" if shap_values[i] > 0 else "reduces risk"}
        for i, feat in enumerate(self.feature_names)
    ]
    contributions.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
    return contributions[:top_n]
```
Returns top 5 features by absolute impact. Used for single-employee prediction.

**Company-level explanation (`explain_batch`)**:
```python
def explain_batch(self, X) -> list:
    shap_values = self.explainer.shap_values(X)
    mean_abs = np.abs(shap_values).mean(axis=0)  # Mean across all employees
    return sorted(
        [{"feature": f, "importance": float(v)} for f, v in zip(self.feature_names, mean_abs)],
        key=lambda c: c["importance"], reverse=True
    )
```
Returns mean absolute SHAP per feature — shows which features are most important **across the whole company**. Used in portfolio dashboard and HR view.

### Plain Language Translation
```python
friendly = {
    "avg_daily_steps":  f"Average daily steps ({val:.0f})",
    "smoker":           "Smoking status",
    "diabetic":         "Diabetes diagnosis",
    "hypertension":     "Hypertension diagnosis",
    "bmi":              f"BMI ({val:.1f})",
    "health_composite": "Combined chronic health burden",
    "clinical_burden":  "Clinical visit burden (visits × hospitalisations)",
    ...
}
return f"{label} {direction}"  # e.g. "Average daily steps (3200) increases risk"
```

This converts technical ML output into HR-readable explanations.

---

## 6. AegisModel — Inference Bundle (`ml_engine/__init__.py`)

### What It Holds
```python
class AegisModel:
    def __init__(self):
        self.model = joblib.load(ARTIFACTS / "xgb_model.pkl")
        self.feature_names = joblib.load(ARTIFACTS / "feature_names.pkl")
        self.scorer = HRSScorer.from_dict(joblib.load(ARTIFACTS / "hrs_scorer.pkl"))
        self.explainer = AegisExplainer(self.model, self.feature_names)
```

One object holds everything needed for inference: the trained model, the feature list (order matters for numpy arrays!), the HRS calibration, and the SHAP explainer.

### Singleton Pattern
```python
_MODEL_INSTANCE = None

def get_model() -> AegisModel:
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = AegisModel()
    return _MODEL_INSTANCE
```

**Why singleton?**
- Loading `.pkl` files on every API request takes ~500ms (XGBoost model is large)
- Singleton loads once when FastAPI starts, then reuses the same object
- All API requests share one model instance (no memory waste)
- Thread-safe for reading (no writes to the model instance during inference)

**Side effect**: If the model artifacts on disk change (re-training), the server needs a restart to pick up the new model. This is intentional — not a bug.

### Single Employee Prediction Flow
```python
def predict_one(self, employee_row: dict) -> dict:
    df = pd.DataFrame([employee_row])
    df = engineer_features(df)         # Add derived + interaction features
    X = df[self.feature_names].values  # Order must match training!

    log_pred = float(self.model.predict(X)[0])  # Log(1 + loss_ratio)
    pred_lr  = float(np.expm1(log_pred))         # Reverse log transform
    hrs      = self.scorer.score(log_pred)       # 0-100 score
    drivers  = self.explainer.explain_one(X[0], top_n=5)  # SHAP top 5

    return {
        "predicted_loss_ratio": round(pred_lr, 4),
        "health_risk_score":    round(hrs, 1),
        "risk_band":            self.scorer.risk_band(hrs),
        "top_drivers":          drivers,
    }
```

### Company Prediction Flow
```python
def predict_company(self, employees_df) -> dict:
    df = engineer_features(employees_df)  # Feature engineer all employees
    X = df[self.feature_names].values     # N × 21 matrix

    log_preds = self.model.predict(X)     # N log-loss-ratio predictions
    pred_lrs  = np.expm1(log_preds)       # N actual loss ratio predictions
    hrs_array = self.scorer.score_batch(log_preds)  # N HRS scores

    mean_hrs = float(np.mean(hrs_array))  # Company HRS = mean of all employees
    global_importance = self.explainer.explain_batch(X)  # Company-level SHAP

    return {
        "employee_count":   len(employees_df),
        "mean_loss_ratio":  float(np.mean(pred_lrs)),
        "mean_hrs":         round(mean_hrs, 1),
        "risk_band":        self.scorer.risk_band(mean_hrs),
        "hrs_distribution": hrs_array.tolist(),       # All individual HRS values
        "top_risk_drivers": global_importance[:5],    # Top 5 company drivers
    }
```

**Key insight**: The company HRS is the **arithmetic mean** of all individual HRS scores. This is a deliberate choice:
- Simple and interpretable
- A company with 40 healthy + 10 sick = mean HRS = (0.4 × low + 0.1 × high)
- Alternatives (median, weighted by premium) were considered but rejected (complexity)

---

## 7. Premium Calculator (`ml_engine/premium_calculator.py`)

### The Three-Zone Model (Not Linear!)

```
HRS 0-40:   Discount Zone   → Up to 15% off  (healthy groups)
HRS 41-60:  Standard Zone   → No adjustment  (average groups)
HRS 61-100: Loading Zone    → Up to 30% up   (high-risk groups)
```

### Discount Zone (HRS 0-40)
```python
discount = (40 - hrs) / 40 * 0.15    # Max 15% at HRS=0
adjusted = base_premium * (1 - discount)
```
- HRS=0:  discount = 15% off
- HRS=20: discount = 7.5% off
- HRS=40: discount = 0% (at boundary)

### Loading Zone (HRS 61-100)
```python
loading  = (hrs - 60) / 40 * 0.30    # Max 30% at HRS=100
adjusted = base_premium * (1 + loading)
```
- HRS=60: loading = 0% (at boundary)
- HRS=80: loading = 15% up
- HRS=100: loading = 30% up

### Why Asymmetric (15% discount vs 30% loading)?
```
Insurance actuarial principle: Downside risk > Upside reward

If we're wrong and a "healthy" company has high claims:
  - With 15% discount: We're collecting 85% of base premium
  - We lose money, but not catastrophically

If we're wrong and a "risky" company is actually fine:
  - With 30% loading: We collected 130% of base premium
  - Customer may churn, but we made money while they were with us

Real insurance surcharges are typically 25-50% for high-risk groups.
30% maximum loading is conservative but defensible.
```

### Recommendations
```
Zone=discount:   "Low-risk group. Offer preferred rates to retain."
Zone=standard:   "Average risk. Price at book rate."
Zone=loading:    "High risk. Apply surcharge or require wellness program."
```

### Wellness ROI Calculation
```python
def calculate_wellness_roi(base_premium, current_hrs, projected_hrs):
    current  = calculate_premium_adjustment(base_premium, current_hrs)
    improved = calculate_premium_adjustment(base_premium, projected_hrs)
    
    return {
        "annual_savings": current["adjusted_premium"] - improved["adjusted_premium"],
        "hrs_improvement": current_hrs - projected_hrs,
        "current_zone": current["zone"],
        "projected_zone": improved["zone"],
    }
```

Reuses `calculate_premium_adjustment` for both current and projected scenarios — no duplication. The ROI is simply the premium difference.

---

## 8. Artifacts Produced by Training

```
ml_engine/artifacts/
├── xgb_model.pkl      — Trained XGBoost model (joblib serialised)
├── hrs_scorer.pkl     — HRSScorer calibration dict (p05, p95)
└── feature_names.pkl  — Ordered list of 21 feature names
```

**Why separate `feature_names.pkl`?**
XGBoost requires features in the exact same order as training. Storing the feature name list separately from the model ensures the API can always reconstruct the correct column order, even if `FEATURE_COLUMNS` in `features.py` is later modified.

---

## Summary: Complete ML Inference Pipeline

```
API Request
    ↓
Feature Engineering (engineer_features)
  + derived: activity_score, health_composite
  + interactions: smoker_diabetic, bmi_age_risk, clinical_burden
  + log-transform target if present
    ↓
XGBoost Prediction (predict → log-loss-ratio)
    ↓
HRSScorer (convert log-loss-ratio → 0-100 HRS)
    ↓
Risk Band (HRS → Low/Moderate/High/Critical)
    ↓
SHAP Explainer (top 5 features by contribution)
    ↓
Premium Calculator (HRS → adjusted_premium, zone, recommendation)
    ↓
API Response (JSON with all components)
```

---

## Links
- [[Data Generation & Pipeline]] — How training data was created
- [[API Layer Architecture]] — How the model is served via FastAPI
- [[Decisions & Rationale#DECISION-001]] — Why HRS as core metric
- [[Decisions & Rationale#DECISION-002]] — Why percentile binning
- [[Decisions & Rationale#DECISION-003]] — Why the three-zone premium model
