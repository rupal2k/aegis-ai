# Model Card — Aegis AI Health Risk Score (HRS) Model

**Model:** XGBoost Regressor → Health Risk Score (0–100)
**Version:** Production v1 (commit `02786aa`, June 19, 2026)
**Owner:** Rupal (rupal2k)
**Contact:** Via GitHub Issues

---

## Model Summary

Aegis AI predicts a **Health Risk Score (0–100)** for individual corporate employees and aggregates it to a company-level underwriting signal. The score is calibrated to a dynamic premium zone: Discount (0–40), Standard (41–60), Loading (61–100).

The underlying model is an XGBoost regressor trained to predict `log(loss_ratio)` from 31 features spanning demographics, wearable telemetry, clinical events, and lab domain flags.

---

## Intended Use

| Use | Appropriate? |
|-----|-------------|
| Group health insurance underwriting for Indian corporates (50–10,000 employees) | ✅ Yes |
| Premium adjustment recommendations for HR departments | ✅ Yes |
| Wellness program ROI estimation (projected HRS → premium delta) | ✅ Yes |
| Portfolio-level risk triage across multiple employer groups | ✅ Yes |
| Individual retail health insurance underwriting | ❌ No |
| Clinical diagnosis or medical decision-making | ❌ No |
| Employment screening or HR decisions about individuals | ❌ No |
| Any jurisdiction outside Indian group mediclaim norms | ❌ Not validated |

---

## Model Architecture

| Property | Value |
|----------|-------|
| Algorithm | XGBoost Regressor (histogram method) |
| Target variable | `log(loss_ratio)` |
| Features | 31 (demographics, telemetry, clinical, lab flags) |
| Monotone constraints | Yes — age/smoker/BMI increase risk; steps/SPO2/active_mins decrease risk |
| Hyperparameter tuning | Optuna TPE, 50 trials, CV MAE objective |
| Explainability | SHAP TreeExplainer (top-5 drivers per prediction) |
| Calibration | Percentile normalisation (p05=0, p95=100) → 0–100 HRS |

---

## Performance

### Production Model (Neon DB, `--use-both` mode, all 31 features populated)

| Metric | Value |
|--------|-------|
| Test MAE (log loss ratio) | ~0.40 |
| Test R² | ~0.54 |
| Prediction latency | 60–80 ms per employee |
| Company-level latency | ~2–4 s (500-employee cohort) |

### Local Training Run (HF dataset only, `--use-hf` mode, lab columns = 0)

| Metric | Value | Note |
|--------|-------|------|
| Test MAE | 0.1067 | HF feature mapping mismatch |
| Test R² | -0.0001 | Not representative — see TRAINING_RESULTS.md |

> The local run metrics reflect an imperfect HF dataset mapping with zero-valued lab features. Use the production metrics above for all reporting and evaluation.

---

## Training Data

| Source | Records | Coverage |
|--------|---------|----------|
| Synthetic employees (Aegis bootstrap) | 5,000 | 20 Indian companies, 15 industries |
| Wearable telemetry (monthly) | 60,004 | Steps, HR, sleep, SpO2, active minutes |
| Clinical events (ICD-10) | 19,160 | Visits, hospitalisations, claim amounts |
| Lab domain flags (9 domains) | 5,000 | Cardiac, diabetes, inflammation, kidney, liver, iron, thyroid, bone, vitamin |
| HF supplement (gcc-insurance-underwriting-risk) | 8,000 | Mapped to Aegis feature format |

**Data is entirely synthetic.** Correlations were designed to reflect Indian population health patterns (high diabetes prevalence, urban sedentary risk, regional variation) but have not been validated against real insurer claims data.

---

## Known Limitations

1. **Synthetic training data only.** The model has not been validated against real claims history from any Indian insurer. Loss ratio predictions are relative signals, not actuarially certified values.

2. **Lab columns default to 0 in local development.** After schema migration, lab features are zero-filled unless explicitly reseeded. This suppresses lab-related risk signals in local environments.

3. **No temporal modelling.** The model scores each month independently. It cannot predict whether a company's risk will improve or worsen over the next quarter.

4. **No confidence intervals.** HRS is returned as a point estimate. Actuaries should treat it as a directional signal, not a precise liability figure.

5. **Indian market only.** Premium multipliers are calibrated against ~200 Indian corporate health market quotes. Applying this model in other geographies will produce miscalibrated premiums.

6. **HF dataset mapping is approximate.** The `OMG091213/gcc-insurance-underwriting-risk` dataset columns were mapped heuristically to Aegis features. This mode should be used for pre-training only, not as the primary data source.

---

## Fairness Considerations

### Gender Stratification — Audit Results (June 19, 2026)

Ran `python fairness_check.py` on 5,000 local training snapshots (n=2,675 M, n=2,325 F).

| Gender | N | Mean HRS | Median HRS | Std HRS | % Low (<40) | % Moderate | % High | % Critical |
|--------|---|----------|------------|---------|-------------|------------|--------|------------|
| F | 2,325 | 16.6 | 12.3 | 18.4 | 93.5% | 0.3% | 3.1% | 3.1% |
| M | 2,675 | 16.2 | 12.4 | 17.5 | 94.4% | 0.0% | 2.7% | 3.0% |

**Max mean HRS gap: 0.5 points — PASS** (threshold: 5 points). Gender parity is acceptable for portfolio-level use.

### Age Stratification — Monotone Constraint Verification

| Age Bucket | N | Mean HRS | Std HRS |
|------------|---|----------|---------|
| 18–29 | 571 | 12.2 | 14.8 |
| 30–39 | 1,963 | 14.9 | 16.5 |
| 40–49 | 1,905 | 17.9 | 19.0 |
| 50–59 | 528 | 20.7 | 19.9 |
| 60–70 | 33 | 22.7 | 25.9 |

Monotone constraint on `age` is active and verified — HRS increases strictly by decade as expected. Rerun `fairness_check.py` after any model retraining to confirm parity is maintained.

### Age Stratification

Monotone constraint on `age` (positive) is enforced — older employees cannot score lower than identical younger employees holding all else equal. This aligns with actuarial expectation but should be reviewed if the model is extended to individual retail products where age discrimination laws differ.

### Chronic Condition Groups

Employees with diabetic=1 or hypertension=1 will systematically score higher (by design). Confirm with legal that this use is compliant with IRDA's group mediclaim underwriting guidelines before using HRS as a declination criterion.

---

## Ethical Constraints

- **HRS is a group signal, not an individual verdict.** It is designed for portfolio-level pricing decisions, not to identify or penalise specific employees.
- **Raw employee data never persists.** Employee IDs are SHA-256 hashed before database insert. The model does not receive or store PII.
- **HR admin access is scoped.** HR admins can see their company's aggregate HRS and employee-level scores but cannot see premium pricing rationale (underwriter view only).
- **SHAP explanations are mandatory.** No prediction is surfaced without a ranked list of contributing factors, enabling auditability for every underwriting decision.

---

## Update and Retraining Policy

| Trigger | Action |
|---------|--------|
| New synthetic data cohort | Retrain with `--use-both`, update `hrs_scorer.pkl` calibration |
| R² drops below 0.40 on holdout | Investigate feature drift, retrain |
| New lab domain added to schema | Add flag to `features.py`, retrain, recalibrate |
| HF dataset updated | Re-run `--use-hf` pre-training before `--use-both` fine-tuning |

---

## Citation

```
Aegis AI Health Risk Score Model
Rupal (rupal2k), 2026
IIM Lucknow AIB Capstone Project
https://github.com/rupal2k/aegis-ai
```
