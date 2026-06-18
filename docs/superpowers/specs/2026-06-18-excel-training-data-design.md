# Design: Excel Training Data Integration & Premium Calibration

**Date**: 2026-06-18  
**Approach**: B — Replacement + calibration with rollback  
**Status**: Approved

---

## Goals

1. Replace synthetic `data/output/training_dataset.csv` with real Indian market employee health data (Files 1+2)
2. Augment with HuggingFace dataset as before
3. Calibrate `premium_calculator.py` multipliers from real corporate insurance quotes (File 3)
4. Easy rollback via git tag + `--use-legacy` flag

---

## Source Files

| File | Rows | Level | Role |
|------|------|-------|------|
| `Traning Assets/premium as per market practice.xlsx` | 508 | Employee | Claims + features |
| `Traning Assets/weight based risk premium.xlsx` | 511 | Employee | Weighted HRS + premium |
| `Traning Assets/group_health_insurance_quotes_200_corporates.xlsx` | 200 | Corporate | Premium calibration |

Files 1+2 share `Employee_ID` — inner join yields ~508 matched rows with both `Historical_Claims_INR` and `Weight_Based_Premium_INR` on the same record.

---

## Section 1: Data Layer

### New functions in `ml_engine/training/train.py`

**`load_excel_datasets()`**
- Reads both employee Excel files
- Inner-joins on `Employee_ID`
- Passes joined dataframe to `map_employee_excel_dataframe()`
- Returns dataframe in Aegis feature schema

**`map_employee_excel_dataframe(df)`**

| Source column | Target column | Method |
|---------------|---------------|--------|
| `Age` | `age` | Direct cast to float |
| `Gender` (Male/Female) | `gender` | Map → M/F |
| `BMI` | `bmi` | Direct |
| `Avg_Daily_Steps` | `avg_daily_steps` | Direct |
| `Avg_Sleep_Hours` | `avg_sleep_hours` | Direct |
| `Chronic_Conditions` | `chronic_count` | Direct, clamp 0–4 |
| `Systolic_BP >= 130` or `Diastolic_BP >= 80` | `hypertension` | Derived (JNC-8 threshold) |
| `Diabetes_Risk_Score > 50` | `diabetic` | Derived |
| `Stress_Score`, `Activity_Level`, `Wellness_Engagement_Score`, age, BMI | `smoker` | Synthesized heuristic |
| Health indicators | `avg_resting_hr`, `hr_trend`, `avg_active_mins`, `avg_spo2` | Synthesized (same pattern as HF mappers) |
| Age, BP, BMI, chronic_count | All `lab_*` flags | Synthesized |
| `Historical_Claims_INR / Weight_Based_Premium_INR` | `loss_ratio` | Real loss ratio, clamped 0.05–6.0; zero-claim rows get 0.05 |

### Updated `load_training_dataframe()`

New dataset modes added:

| Mode | Sources |
|------|---------|
| `excel` | Excel files only |
| `excel-hf` | Excel + HuggingFace (new default when Excel files present) |
| `local` | Synthetic CSV only |
| `hf` | HuggingFace only |
| `both` | Synthetic CSV + HuggingFace (legacy behaviour) |

Detection: if Excel files exist at `Traning Assets/`, default mode is `excel-hf`. Otherwise falls back to `both`.

### New CLI flags

| Flag | Dataset mode |
|------|-------------|
| `--use-excel` | `excel` |
| `--use-excel-hf` | `excel-hf` |
| `--use-legacy` | `local` (synthetic CSV — rollback path) |
| `--use-local` / `--no-hf` | `local` (unchanged) |
| `--use-hf` | `hf` (unchanged) |
| `--use-both` | `both` (unchanged) |

---

## Section 2: Premium Calculator Calibration

### New file: `ml_engine/training/calibrate_premium.py`

One-time script. Reads File 3, computes three multiplier tables, prints them for copy-paste into `premium_calculator.py`. No runtime file reads.

**Table 1 — Industry risk multipliers**
- Group `estimated_annual_premium_per_employee_inr` by `industry`
- Compute median per industry
- Normalise to 1.0 at overall median
- Output as `INDUSTRY_RISK_MULTIPLIERS` dict

**Table 2 — Region multipliers**
- Group by `region` (North/South/East/West)
- Compute median premium per region
- Normalise to 1.0 at overall median
- Replaces current metro/tier-2/tier-3 zones in `premium_calculator.py`
- `zone` param on `/predict/premium` accepts North/South/East/West (old values kept as aliases)

**Table 3 — Sum assured band adjustments**
- Bucket `sum_assured_lakhs` into bands: 1–3, 4–7, 8–15, 15+
- Compute median premium per band, normalise to 1.0 at band 4–7
- New optional param `sum_assured_lakhs` on `/predict/premium` (defaults to 5 → no change for existing callers)

### Changes to `ml_engine/premium_calculator.py`
- Replace hardcoded zone multiplier dict with region-derived values
- Add `INDUSTRY_RISK_MULTIPLIERS` dict (applied when `industry` param supplied)
- Add `SUM_ASSURED_BAND_MULTIPLIERS` dict (applied when `sum_assured_lakhs` param supplied)
- All three tables are constants — no file I/O at runtime

---

## Section 3: Rollback Plan

### Before retraining
```powershell
git -C "c:/Rupalprojects/aegis-ai" tag pre-excel-retrain
```
Existing artifacts are committed at this tag. Full artifact restore:
```powershell
git checkout pre-excel-retrain -- ml_engine/artifacts/
git commit -m "revert: roll back to pre-excel artifacts"
```

### Training workflow
```powershell
# Step 1 — derive premium tables (once)
python -m ml_engine.training.calibrate_premium

# Step 2 — retrain HRS model on Excel + HF data
python -m ml_engine.training.train --use-excel-hf

# Step 3 — commit new artifacts
git add ml_engine/artifacts/ ml_engine/premium_calculator.py
git commit -m "ml: retrain on real Indian market data + recalibrate premium calculator"

# Step 4 — push to GitHub + HuggingFace
git push origin main
hf upload Rupa2k/aegis-ai "c:\Rupalprojects\aegis-ai" . --repo-type=space
```

### Rollback trigger
If `test_r2 < 0.65` or dashboard behaviour regresses:
```powershell
git checkout pre-excel-retrain -- ml_engine/artifacts/
git commit -m "revert: roll back to pre-excel artifacts"
```
No code changes required — only artifacts are rolled back.

---

## Files Changed

| File | Change |
|------|--------|
| `ml_engine/training/train.py` | `load_excel_datasets()`, `map_employee_excel_dataframe()`, new CLI flags, updated `load_training_dataframe()` |
| `ml_engine/training/calibrate_premium.py` | New file — derives premium multiplier tables from File 3 |
| `ml_engine/premium_calculator.py` | Replace hardcoded zone table; add industry + sum_assured multipliers |
| `ml_engine/artifacts/*.pkl` | Updated after retrain |

## Files NOT Changed

- `data/output/training_dataset.csv` — preserved as legacy fallback
- All dashboard, API, and test files — no changes required
- `Traning Assets/*.xlsx` — local only, gitignored, never committed

---

## Success Criteria

- `test_r2 >= 0.70` (current baseline: 0.69)
- All 75 existing tests still passing
- `/predict/premium` returns plausible INR values for Indian market inputs
- `--use-legacy` successfully retrains from synthetic data (rollback verified)
