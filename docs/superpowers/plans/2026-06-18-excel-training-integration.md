# Excel Training Data Integration & Premium Calibration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace synthetic training data with real Indian market employee health data from two Excel files, calibrate the premium calculator from corporate insurance quotes, and preserve easy rollback via git tag + `--use-legacy` flag.

**Architecture:** New `load_excel_datasets()` inner-joins the two employee files on `Employee_ID` to get real loss ratios (`Historical_Claims_INR / Weight_Based_Premium_INR`). A one-time `calibrate_premium.py` script derives industry/region/sum-assured multipliers from the corporate quotes file and prints them as dict literals for pasting into `premium_calculator.py`. Existing callers are unaffected — all new params are optional with safe defaults.

**Tech Stack:** pandas, openpyxl, numpy, xgboost, optuna, mlflow, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `ml_engine/training/train.py` | Modify | Add `load_excel_datasets()`, `map_employee_excel_dataframe()`, new CLI flags, updated `load_training_dataframe()` |
| `ml_engine/training/calibrate_premium.py` | Create | One-time script: reads File 3, prints multiplier dicts |
| `ml_engine/premium_calculator.py` | Modify | Add `INDUSTRY_RISK_MULTIPLIERS`, `REGION_MULTIPLIERS`, `SUM_ASSURED_BAND_MULTIPLIERS` constants; optional params on `calculate_premium_adjustment()` |
| `tests/test_excel_loader.py` | Create | Tests for mapper + loader + new training modes |
| `tests/test_calibrate_premium.py` | Create | Tests for calibrate script logic |

---

## Task 1: Rollback Preparation

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Create git tag at current clean state**

```powershell
git -C "c:/Rupalprojects/aegis-ai" tag pre-excel-retrain
```

Expected: no output (tag created silently)

- [ ] **Step 2: Verify tag exists**

```powershell
git -C "c:/Rupalprojects/aegis-ai" tag | Select-String "pre-excel-retrain"
```

Expected: `pre-excel-retrain`

- [ ] **Step 3: Add Excel training files to .gitignore**

Open `c:/Rupalprojects/aegis-ai/.gitignore` and add at the bottom:

```
# Local training assets (real market data — never commit)
Traning Assets/
```

- [ ] **Step 4: Commit gitignore update**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add .gitignore
git -C "c:/Rupalprojects/aegis-ai" commit -m "chore: gitignore local Excel training assets"
```

---

## Task 2: Excel Mapper — Tests + Implementation

**Files:**
- Create: `tests/test_excel_loader.py`
- Modify: `ml_engine/training/train.py`

- [ ] **Step 1: Write failing tests for `map_employee_excel_dataframe()`**

Create `tests/test_excel_loader.py`:

```python
"""Tests for Excel dataset loader and mapper."""
import numpy as np
import pandas as pd
import pytest


def _make_joined_df(n=5):
    """Minimal joined File1+File2 dataframe for testing."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "Employee_ID":              [f"EMP{i:04d}" for i in range(n)],
        "Age":                      [30.0, 45.0, 55.0, 25.0, 60.0],
        "Gender":                   ["Male", "Female", "Male", "Female", "Male"],
        "BMI":                      [22.0, 28.5, 31.0, 24.0, 35.0],
        "Systolic_BP":              [115.0, 135.0, 150.0, 118.0, 145.0],
        "Diastolic_BP":             [75.0, 82.0, 95.0, 70.0, 88.0],
        "Diabetes_Risk_Score":      [20.0, 55.0, 70.0, 15.0, 80.0],
        "Chronic_Conditions":       [0.0, 1.0, 2.0, 0.0, 3.0],
        "Historical_Claims_INR":    [0.0, 50000.0, 120000.0, 0.0, 200000.0],
        "Avg_Daily_Steps":          [9000.0, 6500.0, 3500.0, 10000.0, 2000.0],
        "Avg_Sleep_Hours":          [7.5, 6.5, 5.5, 8.0, 5.0],
        "Stress_Score":             [20.0, 50.0, 80.0, 15.0, 90.0],
        "Activity_Level":           ["High", "Moderate", "Low", "High", "Low"],
        "Wellness_Engagement_Score":[80.0, 60.0, 30.0, 90.0, 20.0],
        "Weight_Based_Premium_INR": [200000.0, 250000.0, 300000.0, 180000.0, 350000.0],
    })


def test_mapper_returns_required_columns():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    required = [
        "age", "gender", "bmi", "smoker", "diabetic", "hypertension",
        "chronic_count", "avg_daily_steps", "avg_sleep_hours",
        "avg_resting_hr", "hr_trend", "avg_active_mins", "avg_spo2",
        "step_volatility", "visit_count", "hospitalized_count",
        "lab_heart_flag", "lab_diabetes_flag", "lab_kidney_flag",
        "lab_liver_flag", "lab_inflammation_flag", "lab_iron_flag",
        "lab_thyroid_flag", "lab_bone_flag", "lab_vitamin_flag",
        "loss_ratio",
    ]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_mapper_gender_normalized():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    assert set(df["gender"].unique()).issubset({"M", "F"})


def test_mapper_hypertension_derived():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    # Row 1: Systolic=135, should be hypertensive (>=130)
    assert df["hypertension"].iloc[1] == 1
    # Row 0: Systolic=115, Diastolic=75, should not be hypertensive
    assert df["hypertension"].iloc[0] == 0


def test_mapper_diabetic_derived():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    # Row 0: Diabetes_Risk_Score=20, not diabetic
    assert df["diabetic"].iloc[0] == 0
    # Row 1: Diabetes_Risk_Score=55, diabetic
    assert df["diabetic"].iloc[1] == 1


def test_mapper_loss_ratio_real():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    # Row 1: 50000/250000 = 0.2
    assert abs(df["loss_ratio"].iloc[1] - 0.2) < 0.001


def test_mapper_zero_claims_clamped():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    # Row 0: Historical_Claims=0 → clamped to 0.05
    assert df["loss_ratio"].iloc[0] == pytest.approx(0.05)


def test_mapper_loss_ratio_within_bounds():
    from ml_engine.training.train import map_employee_excel_dataframe
    df = map_employee_excel_dataframe(_make_joined_df())
    assert df["loss_ratio"].between(0.05, 6.0).all()


def test_mapper_row_count_preserved():
    from ml_engine.training.train import map_employee_excel_dataframe
    raw = _make_joined_df(10)
    result = map_employee_excel_dataframe(raw)
    assert len(result) == 10
```

- [ ] **Step 2: Run tests to confirm they fail**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py -v 2>&1 | Select-Object -First 20
```

Expected: `ImportError` or `AttributeError` — `map_employee_excel_dataframe` does not exist yet.

- [ ] **Step 3: Implement `map_employee_excel_dataframe()` in `train.py`**

Add this function to `ml_engine/training/train.py` after the `map_insurance_charge_hf_dataframe()` function (around line 378):

```python
EXCEL_FILES = {
    "premium": Path("Traning Assets/premium as per market practice.xlsx"),
    "weight":  Path("Traning Assets/weight based risk premium.xlsx"),
}


def map_employee_excel_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map joined File1+File2 employee rows into the Aegis feature schema.

    Expects columns from both files inner-joined on Employee_ID:
    Age, Gender, BMI, Systolic_BP, Diastolic_BP, Diabetes_Risk_Score,
    Chronic_Conditions, Historical_Claims_INR, Avg_Daily_Steps, Avg_Sleep_Hours,
    Stress_Score, Activity_Level, Wellness_Engagement_Score, Weight_Based_Premium_INR
    """
    rng = np.random.default_rng(RANDOM_STATE)
    out = pd.DataFrame()

    # --- Direct mappings ---
    out["age"]          = df["Age"].astype(float)
    out["gender"]       = df["Gender"].str.strip().map(
        {"Male": "M", "Female": "F", "male": "M", "female": "F"}
    ).fillna("M")
    out["bmi"]          = df["BMI"].astype(float)
    out["avg_daily_steps"] = df["Avg_Daily_Steps"].astype(float)
    out["avg_sleep_hours"] = df["Avg_Sleep_Hours"].astype(float)
    out["chronic_count"]   = df["Chronic_Conditions"].fillna(0).clip(0, 4).astype(float)

    # --- Derived ---
    out["hypertension"] = (
        (df["Systolic_BP"].astype(float) >= 130) |
        (df["Diastolic_BP"].astype(float) >= 80)
    ).astype(int)
    out["diabetic"] = (df["Diabetes_Risk_Score"].astype(float) > 50).astype(int)

    # --- Synthesized: smoker (no direct column — heuristic from stress + BMI) ---
    stress   = df["Stress_Score"].astype(float) / 100.0
    bmi_risk = np.clip((df["BMI"].astype(float) - 22) / 18, 0, 1)
    p_smoker = np.clip(0.06 + stress * 0.14 + bmi_risk * 0.06, 0, 0.28)
    out["smoker"] = (rng.random(len(df)) < p_smoker).astype(int)

    # --- Synthesized: telemetry ---
    wellness = df["Wellness_Engagement_Score"].astype(float) / 100.0
    activity_map = {"High": 0.85, "Moderate": 0.50, "Low": 0.20}
    activity = df["Activity_Level"].map(activity_map).fillna(0.50).astype(float)

    out["avg_resting_hr"] = np.clip(
        72 - wellness * 18 + rng.normal(0, 3, len(df)), 45, 110
    )
    out["hr_trend"]       = np.clip(
        (1 - wellness) * 2.2 - 0.8 + rng.normal(0, 0.5, len(df)), -5, 5
    )
    out["avg_active_mins"] = np.clip(
        activity * 70 + rng.normal(0, 8, len(df)), 0, 90
    )
    out["avg_spo2"]       = np.clip(
        96.0 + wellness * 2.5 + rng.normal(0, 0.3, len(df)), 90, 100
    )
    out["step_volatility"] = np.clip(
        (1 - wellness) * 1200 + 100 + rng.normal(0, 150, len(df)), 50, 3000
    )

    # --- Clinical counts ---
    claims = df["Historical_Claims_INR"].fillna(0).astype(float)
    out["visit_count"]        = np.clip(
        1 + out["chronic_count"] * 1.5 + (claims > 0).astype(float) * 1.5,
        0, 10
    ).round()
    out["hospitalized_count"] = (claims > 50000).astype(int)

    # --- Lab flags ---
    age  = out["age"]
    sbp  = df["Systolic_BP"].astype(float)
    dbp  = df["Diastolic_BP"].astype(float)
    bmi  = out["bmi"]
    out["lab_heart_flag"]       = ((age >= 55) | (sbp >= 140) |
                                   (out["diabetic"] & (age >= 45))).astype(int)
    out["lab_diabetes_flag"]    = out["diabetic"]
    out["lab_kidney_flag"]      = ((bmi >= 33) | (out["chronic_count"] >= 2) |
                                   (dbp >= 90)).astype(int)
    out["lab_liver_flag"]       = ((bmi >= 32) | out["smoker"].astype(bool)).astype(int)
    out["lab_inflammation_flag"]= ((sbp >= 140) | (out["chronic_count"] >= 2)).astype(int)
    out["lab_iron_flag"]        = (
        (out["gender"] == "F") & (age >= 30) &
        (df["Wellness_Engagement_Score"].astype(float) < 50)
    ).astype(int)
    out["lab_thyroid_flag"]     = ((out["gender"] == "F") & (age >= 45)).astype(int)
    out["lab_bone_flag"]        = (age >= 60).astype(int)
    out["lab_vitamin_flag"]     = (
        (out["avg_daily_steps"] < 4000) |
        (df["Wellness_Engagement_Score"].astype(float) < 40)
    ).astype(int)

    # --- Target: real loss ratio ---
    premium = df["Weight_Based_Premium_INR"].astype(float).replace(0, np.nan)
    raw_lr  = claims / premium
    out["loss_ratio"] = np.clip(raw_lr.fillna(0.05), 0.05, 6.0)

    return out
```

- [ ] **Step 4: Run tests — all should pass**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py::test_mapper_returns_required_columns tests/test_excel_loader.py::test_mapper_gender_normalized tests/test_excel_loader.py::test_mapper_hypertension_derived tests/test_excel_loader.py::test_mapper_diabetic_derived tests/test_excel_loader.py::test_mapper_loss_ratio_real tests/test_excel_loader.py::test_mapper_zero_claims_clamped tests/test_excel_loader.py::test_mapper_loss_ratio_within_bounds tests/test_excel_loader.py::test_mapper_row_count_preserved -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/training/train.py tests/test_excel_loader.py
git -C "c:/Rupalprojects/aegis-ai" commit -m "feat: add Excel employee data mapper for Indian market training data"
```

---

## Task 3: Excel Loader — Tests + Implementation

**Files:**
- Modify: `tests/test_excel_loader.py`
- Modify: `ml_engine/training/train.py`

- [ ] **Step 1: Add failing test for `load_excel_datasets()`**

Append to `tests/test_excel_loader.py`:

```python
def test_load_excel_datasets_skips_when_files_missing(tmp_path, monkeypatch):
    """When Excel files don't exist, load_excel_datasets raises FileNotFoundError."""
    from ml_engine.training import train
    # Point EXCEL_FILES at a temp path that doesn't have the files
    monkeypatch.setattr(train, "EXCEL_FILES", {
        "premium": tmp_path / "missing1.xlsx",
        "weight":  tmp_path / "missing2.xlsx",
    })
    with pytest.raises(FileNotFoundError):
        train.load_excel_datasets()


def test_load_excel_datasets_inner_joins_on_employee_id(tmp_path, monkeypatch):
    """load_excel_datasets inner-joins on Employee_ID, dropping unmatched rows."""
    import openpyxl
    from ml_engine.training import train

    # File1: 3 employees
    f1_data = pd.DataFrame({
        "Employee_ID": ["EMP001", "EMP002", "EMP003"],
        "Age": [30.0, 40.0, 50.0],
        "Gender": ["Male", "Female", "Male"],
        "BMI": [22.0, 26.0, 30.0],
        "Systolic_BP": [115.0, 125.0, 140.0],
        "Diastolic_BP": [75.0, 80.0, 90.0],
        "Diabetes_Risk_Score": [20.0, 45.0, 65.0],
        "Chronic_Conditions": [0.0, 1.0, 2.0],
        "Historical_Claims_INR": [0.0, 30000.0, 90000.0],
        "Avg_Daily_Steps": [8000.0, 6000.0, 3000.0],
        "Avg_Sleep_Hours": [7.5, 6.5, 5.5],
        "Stress_Score": [25.0, 50.0, 75.0],
        "Activity_Level": ["High", "Moderate", "Low"],
        "Wellness_Engagement_Score": [75.0, 55.0, 30.0],
    })
    # File2: 2 of 3 employees match
    f2_data = pd.DataFrame({
        "Employee_ID": ["EMP001", "EMP002"],
        "Health_Risk_Score_Weighted": [35.0, 48.0],
        "Weight_Based_Premium_INR": [200000.0, 250000.0],
    })

    p1 = tmp_path / "premium.xlsx"
    p2 = tmp_path / "weight.xlsx"
    f1_data.to_excel(p1, index=False)
    f2_data.to_excel(p2, index=False)

    monkeypatch.setattr(train, "EXCEL_FILES", {"premium": p1, "weight": p2})

    result = train.load_excel_datasets()
    # Only 2 matched rows
    assert len(result) == 2
    assert "loss_ratio" in result.columns
```

- [ ] **Step 2: Run test to confirm it fails**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py::test_load_excel_datasets_skips_when_files_missing tests/test_excel_loader.py::test_load_excel_datasets_inner_joins_on_employee_id -v
```

Expected: `AttributeError` — `load_excel_datasets` does not exist yet.

- [ ] **Step 3: Implement `load_excel_datasets()` in `train.py`**

Add after `EXCEL_FILES` constant (after `map_employee_excel_dataframe()`):

```python
def load_excel_datasets() -> pd.DataFrame:
    """
    Inner-join the two employee Excel files on Employee_ID and return
    a dataframe in the Aegis feature schema.

    Raises FileNotFoundError if either file is missing.
    """
    for key, path in EXCEL_FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Training asset not found: {path}. "
                "Copy the Excel files to 'Traning Assets/' to use --use-excel."
            )

    print(f"Loading Excel training assets...")
    df1 = pd.read_excel(EXCEL_FILES["premium"])
    df2 = pd.read_excel(EXCEL_FILES["weight"])[
        ["Employee_ID", "Health_Risk_Score_Weighted", "Weight_Based_Premium_INR"]
    ]

    joined = df1.merge(df2, on="Employee_ID", how="inner")
    print(f"  File 1: {len(df1):,} rows | File 2: {len(df2):,} rows | Joined: {len(joined):,} rows")

    return map_employee_excel_dataframe(joined)
```

- [ ] **Step 4: Run tests — both should pass**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py::test_load_excel_datasets_skips_when_files_missing tests/test_excel_loader.py::test_load_excel_datasets_inner_joins_on_employee_id -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/training/train.py tests/test_excel_loader.py
git -C "c:/Rupalprojects/aegis-ai" commit -m "feat: add load_excel_datasets() — inner-join employee files for real loss ratio"
```

---

## Task 4: New Training Modes + CLI Flags

**Files:**
- Modify: `tests/test_excel_loader.py`
- Modify: `ml_engine/training/train.py`

- [ ] **Step 1: Add failing tests for new training modes**

Append to `tests/test_excel_loader.py`:

```python
def test_resolve_dataset_mode_use_excel():
    from ml_engine.training.train import resolve_dataset_mode, build_arg_parser
    parser = build_arg_parser()
    args = parser.parse_args(["--use-excel"])
    assert resolve_dataset_mode(args) == "excel"


def test_resolve_dataset_mode_use_excel_hf():
    from ml_engine.training.train import resolve_dataset_mode, build_arg_parser
    parser = build_arg_parser()
    args = parser.parse_args(["--use-excel-hf"])
    assert resolve_dataset_mode(args) == "excel-hf"


def test_resolve_dataset_mode_use_legacy():
    from ml_engine.training.train import resolve_dataset_mode, build_arg_parser
    parser = build_arg_parser()
    args = parser.parse_args(["--use-legacy"])
    assert resolve_dataset_mode(args) == "local"


def test_load_training_dataframe_excel_mode(tmp_path, monkeypatch):
    """In 'excel' mode, load_training_dataframe calls load_excel_datasets."""
    from ml_engine.training import train

    sentinel = pd.DataFrame({
        "age": [30.0], "gender": ["M"], "bmi": [22.0],
        "smoker": [0], "diabetic": [0], "hypertension": [0],
        "chronic_count": [0.0], "avg_daily_steps": [8000.0],
        "avg_sleep_hours": [7.5], "avg_resting_hr": [68.0],
        "hr_trend": [0.0], "avg_active_mins": [45.0], "avg_spo2": [98.0],
        "step_volatility": [500.0], "visit_count": [1.0],
        "hospitalized_count": [0], "lab_heart_flag": [0],
        "lab_diabetes_flag": [0], "lab_kidney_flag": [0],
        "lab_liver_flag": [0], "lab_inflammation_flag": [0],
        "lab_iron_flag": [0], "lab_thyroid_flag": [0],
        "lab_bone_flag": [0], "lab_vitamin_flag": [0],
        "loss_ratio": [0.3], "dataset_source": ["excel"],
    })
    monkeypatch.setattr(train, "load_excel_datasets", lambda: sentinel)

    df, counts = train.load_training_dataframe(dataset_mode="excel")
    assert counts["excel"] == 1
    assert "loss_ratio" in df.columns
```

- [ ] **Step 2: Run to confirm they fail**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py::test_resolve_dataset_mode_use_excel tests/test_excel_loader.py::test_resolve_dataset_mode_use_excel_hf tests/test_excel_loader.py::test_resolve_dataset_mode_use_legacy tests/test_excel_loader.py::test_load_training_dataframe_excel_mode -v
```

Expected: `FAILED` — unrecognised CLI args and unknown dataset mode.

- [ ] **Step 3: Update `build_arg_parser()` in `train.py`**

In `build_arg_parser()`, add three new arguments to the mutually exclusive group (after the existing `--no-hf` entry, before `return parser`):

```python
    group.add_argument(
        "--use-excel",
        action="store_true",
        help="Load data from Excel training assets only",
    )
    group.add_argument(
        "--use-excel-hf",
        action="store_true",
        help="Load data from Excel training assets + Hugging Face (recommended)",
    )
    group.add_argument(
        "--use-legacy",
        action="store_true",
        help="Force synthetic CSV (rollback path — same as --use-local)",
    )
```

- [ ] **Step 4: Update `resolve_dataset_mode()` in `train.py`**

Replace the existing `resolve_dataset_mode()` function body:

```python
def resolve_dataset_mode(args) -> str:
    if getattr(args, "use_local", False) or getattr(args, "no_hf", False) or getattr(args, "use_legacy", False):
        return "local"
    if getattr(args, "use_excel", False):
        return "excel"
    if getattr(args, "use_excel_hf", False):
        return "excel-hf"
    if getattr(args, "use_hf", False):
        return "hf"
    if getattr(args, "use_both", False):
        return "both"
    # Auto-detect: use excel-hf if files are present, otherwise fall back to both
    if all(p.exists() for p in EXCEL_FILES.values()):
        return "excel-hf"
    return DEFAULT_DATA_MODE
```

- [ ] **Step 5: Update `load_training_dataframe()` in `train.py`**

Replace the existing `if dataset_mode not in ...` check and `selected_sources` list:

```python
def load_training_dataframe(
    dataset_mode: str = DEFAULT_DATA_MODE,
    hf_dataset_name: str = HF_DATASET_NAME,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Load one or more training sources into a single dataframe."""
    valid_modes = {"local", "hf", "both", "excel", "excel-hf"}
    if dataset_mode not in valid_modes:
        raise ValueError(f"Unsupported dataset mode: {dataset_mode}. Choose from {valid_modes}")

    selected_sources = []
    if dataset_mode in {"local", "both"}:
        selected_sources.append(("local", load_local_dataset))
    if dataset_mode == "excel":
        selected_sources.append(("excel", load_excel_datasets))
    if dataset_mode == "excel-hf":
        selected_sources.append(("excel", load_excel_datasets))
        selected_sources.append(("huggingface", lambda: load_from_huggingface(hf_dataset_name)))
    if dataset_mode in {"hf", "both"}:
        selected_sources.append(("huggingface", lambda: load_from_huggingface(hf_dataset_name)))

    frames = []
    source_counts: Dict[str, int] = {}
    errors = []

    for source_name, loader in selected_sources:
        try:
            df = loader().copy()
        except Exception as exc:
            if dataset_mode not in {"both", "excel-hf"}:
                raise
            errors.append((source_name, exc))
            print(f"WARNING: Failed to load {source_name} dataset: {exc}")
            continue

        df["dataset_source"] = source_name
        frames.append(df)
        source_counts[source_name] = len(df)

    if not frames:
        details = "; ".join(f"{name}: {exc}" for name, exc in errors) or "no sources selected"
        raise RuntimeError(f"Unable to load any training data ({details})")

    df = pd.concat(frames, ignore_index=True, sort=False)
    print(f"Using dataset mode: {dataset_mode}")
    for source_name, row_count in source_counts.items():
        print(f"  {source_name:>11s}: {row_count:,} rows")
    print(f"  {'combined':>11s}: {len(df):,} rows")
    return df, source_counts
```

- [ ] **Step 6: Run tests — all four should pass**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_excel_loader.py -v
```

Expected: `12 passed` (8 from Task 2 + 4 new)

- [ ] **Step 7: Commit**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/training/train.py tests/test_excel_loader.py
git -C "c:/Rupalprojects/aegis-ai" commit -m "feat: add --use-excel, --use-excel-hf, --use-legacy CLI flags + excel-hf dataset mode"
```

---

## Task 5: Premium Calibration Script

**Files:**
- Create: `ml_engine/training/calibrate_premium.py`
- Create: `tests/test_calibrate_premium.py`

- [ ] **Step 1: Write failing tests for calibration logic**

Create `tests/test_calibrate_premium.py`:

```python
"""Tests for premium calibration logic."""
import numpy as np
import pandas as pd
import pytest


def _make_corporate_df():
    """Minimal corporate quotes dataframe for testing."""
    return pd.DataFrame({
        "industry":                             ["Construction", "Automotive", "Agriculture",
                                                 "Construction", "IT", "IT", "Automotive"],
        "region":                               ["South", "North", "East", "North", "South", "West", "East"],
        "sum_assured_lakhs":                    [4.0, 7.0, 2.0, 10.0, 5.0, 20.0, 3.0],
        "estimated_annual_premium_per_employee_inr": [25000, 28000, 18000, 30000, 22000, 35000, 27000],
    })


def test_compute_industry_multipliers_returns_dict():
    from ml_engine.training.calibrate_premium import compute_industry_multipliers
    result = compute_industry_multipliers(_make_corporate_df())
    assert isinstance(result, dict)
    assert "Construction" in result
    assert "IT" in result


def test_compute_industry_multipliers_normalised_near_one():
    from ml_engine.training.calibrate_premium import compute_industry_multipliers
    result = compute_industry_multipliers(_make_corporate_df())
    values = list(result.values())
    # At least one value should be close to 1.0 (the median industry)
    assert any(abs(v - 1.0) < 0.3 for v in values)


def test_compute_region_multipliers_keys():
    from ml_engine.training.calibrate_premium import compute_region_multipliers
    result = compute_region_multipliers(_make_corporate_df())
    assert set(result.keys()) == {"South", "North", "East", "West"}


def test_compute_region_multipliers_all_positive():
    from ml_engine.training.calibrate_premium import compute_region_multipliers
    result = compute_region_multipliers(_make_corporate_df())
    assert all(v > 0 for v in result.values())


def test_compute_sum_assured_multipliers_bands():
    from ml_engine.training.calibrate_premium import compute_sum_assured_multipliers
    result = compute_sum_assured_multipliers(_make_corporate_df())
    assert set(result.keys()) == {"1-3L", "4-7L", "8-15L", "15L+"}


def test_compute_sum_assured_multipliers_base_band_near_one():
    from ml_engine.training.calibrate_premium import compute_sum_assured_multipliers
    result = compute_sum_assured_multipliers(_make_corporate_df())
    # 4-7L is the normalisation band — should be exactly 1.0
    assert result["4-7L"] == pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to confirm they fail**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_calibrate_premium.py -v
```

Expected: `ModuleNotFoundError` — module does not exist yet.

- [ ] **Step 3: Implement `calibrate_premium.py`**

Create `ml_engine/training/calibrate_premium.py`:

```python
"""
One-time script to derive premium multiplier tables from corporate insurance quotes.

Run:
    python -m ml_engine.training.calibrate_premium

Copy the printed dict literals into ml_engine/premium_calculator.py.
"""
from pathlib import Path
import pandas as pd
import numpy as np

CORPORATE_FILE = Path("Traning Assets/group_health_insurance_quotes_200_corporates.xlsx")
PREMIUM_COL    = "estimated_annual_premium_per_employee_inr"


def _load_corporate_df(path: Path = CORPORATE_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Corporate quotes file not found: {path}")
    return pd.read_excel(path)


def compute_industry_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per industry normalised to overall median."""
    overall = df[PREMIUM_COL].median()
    by_industry = df.groupby("industry")[PREMIUM_COL].median()
    return {k: round(float(v / overall), 3) for k, v in by_industry.items()}


def compute_region_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per region (North/South/East/West) normalised to overall median."""
    overall = df[PREMIUM_COL].median()
    by_region = df.groupby("region")[PREMIUM_COL].median()
    return {k: round(float(v / overall), 3) for k, v in by_region.items()}


def compute_sum_assured_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per sum-assured band normalised to 4-7L band."""
    bins   = [0, 3, 7, 15, 10000]
    labels = ["1-3L", "4-7L", "8-15L", "15L+"]
    df = df.copy()
    df["_band"] = pd.cut(df["sum_assured_lakhs"], bins=bins, labels=labels)
    by_band  = df.groupby("_band", observed=True)[PREMIUM_COL].median()
    base     = float(by_band.get("4-7L", by_band.median()))
    return {k: round(float(v / base), 3) for k, v in by_band.items()}


def main():
    df = _load_corporate_df()
    print(f"Loaded {len(df):,} corporate quotes.\n")

    industry = compute_industry_multipliers(df)
    region   = compute_region_multipliers(df)
    bands    = compute_sum_assured_multipliers(df)

    print("# Paste these into ml_engine/premium_calculator.py\n")
    print(f"INDUSTRY_RISK_MULTIPLIERS = {industry!r}\n")
    print(f"REGION_MULTIPLIERS = {region!r}\n")
    print(f"SUM_ASSURED_BAND_MULTIPLIERS = {bands!r}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests — all six should pass**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_calibrate_premium.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run the script and capture output**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m ml_engine.training.calibrate_premium
```

Expected output (values will be real numbers from File 3):
```
Loaded 200 corporate quotes.

# Paste these into ml_engine/premium_calculator.py

INDUSTRY_RISK_MULTIPLIERS = {'Agriculture': X.XXX, 'Automotive': X.XXX, ...}

REGION_MULTIPLIERS = {'East': X.XXX, 'North': X.XXX, 'South': X.XXX, 'West': X.XXX}

SUM_ASSURED_BAND_MULTIPLIERS = {'1-3L': X.XXX, '4-7L': 1.0, '8-15L': X.XXX, '15L+': X.XXX}
```

**Copy this output — you will paste it in Task 6.**

- [ ] **Step 6: Commit**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/training/calibrate_premium.py tests/test_calibrate_premium.py
git -C "c:/Rupalprojects/aegis-ai" commit -m "feat: add calibrate_premium.py — derives market multipliers from corporate quotes"
```

---

## Task 6: Update Premium Calculator

**Files:**
- Modify: `ml_engine/premium_calculator.py`
- Modify: `tests/test_ml_engine.py`

- [ ] **Step 1: Write failing tests for new multipliers**

Append to `tests/test_ml_engine.py`:

```python
def test_premium_adjustment_industry_multiplier():
    from ml_engine.premium_calculator import calculate_premium_adjustment, INDUSTRY_RISK_MULTIPLIERS
    # At least one industry multiplier must differ from 1.0
    assert any(v != 1.0 for v in INDUSTRY_RISK_MULTIPLIERS.values())
    # Passing a known industry should change adjusted premium vs no industry
    base = 100000.0
    industry = next(iter(INDUSTRY_RISK_MULTIPLIERS))
    with_industry    = calculate_premium_adjustment(base, 50.0, industry=industry)
    without_industry = calculate_premium_adjustment(base, 50.0)
    if INDUSTRY_RISK_MULTIPLIERS[industry] != 1.0:
        assert with_industry["adjusted_premium"] != without_industry["adjusted_premium"]


def test_premium_adjustment_region_multiplier():
    from ml_engine.premium_calculator import calculate_premium_adjustment, REGION_MULTIPLIERS
    assert len(REGION_MULTIPLIERS) == 4
    assert set(REGION_MULTIPLIERS.keys()) == {"North", "South", "East", "West"}


def test_premium_adjustment_sum_assured_bands():
    from ml_engine.premium_calculator import calculate_premium_adjustment, SUM_ASSURED_BAND_MULTIPLIERS
    assert set(SUM_ASSURED_BAND_MULTIPLIERS.keys()) == {"1-3L", "4-7L", "8-15L", "15L+"}
    assert SUM_ASSURED_BAND_MULTIPLIERS["4-7L"] == pytest.approx(1.0)


def test_premium_adjustment_backward_compatible():
    """Calling with no new params must return same result as before."""
    from ml_engine.premium_calculator import calculate_premium_adjustment
    result = calculate_premium_adjustment(100000.0, 50.0)
    assert result["adjusted_premium"] == 100000.0
    assert result["adjustment_pct"] == 0.0


def test_premium_adjustment_all_params():
    from ml_engine.premium_calculator import calculate_premium_adjustment
    result = calculate_premium_adjustment(
        100000.0, 50.0, industry="IT", region="North", sum_assured_lakhs=5.0
    )
    assert "adjusted_premium" in result
    assert result["adjusted_premium"] > 0
```

- [ ] **Step 2: Run to confirm they fail**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_ml_engine.py::test_premium_adjustment_industry_multiplier tests/test_ml_engine.py::test_premium_adjustment_region_multiplier tests/test_ml_engine.py::test_premium_adjustment_sum_assured_bands tests/test_ml_engine.py::test_premium_adjustment_backward_compatible tests/test_ml_engine.py::test_premium_adjustment_all_params -v
```

Expected: `FAILED` — `INDUSTRY_RISK_MULTIPLIERS` does not exist yet.

- [ ] **Step 3: Paste calibration output + update `premium_calculator.py`**

Replace the entire contents of `ml_engine/premium_calculator.py` with:

```python
"""Translate Health Risk Score into a dynamic premium adjustment."""

# Derived from 200-corporate market quotes via ml_engine/training/calibrate_premium.py
# Re-run calibrate_premium.py after adding new quote data to update these tables.
INDUSTRY_RISK_MULTIPLIERS = {}   # <-- PASTE computed dict from Task 5 Step 5 here

REGION_MULTIPLIERS = {}          # <-- PASTE computed dict from Task 5 Step 5 here

SUM_ASSURED_BAND_MULTIPLIERS = {} # <-- PASTE computed dict from Task 5 Step 5 here


def _get_sum_assured_band(sum_assured_lakhs: float) -> str:
    if sum_assured_lakhs <= 3:
        return "1-3L"
    if sum_assured_lakhs <= 7:
        return "4-7L"
    if sum_assured_lakhs <= 15:
        return "8-15L"
    return "15L+"


def calculate_premium_adjustment(
    base_premium: float,
    hrs: float,
    industry: str = None,
    region: str = None,
    sum_assured_lakhs: float = 5.0,
) -> dict:
    """
    Dynamic premium pricing based on HRS with optional market multipliers.

    HRS 0-40  : discount zone (up to 15% off)
    HRS 41-60 : standard rate
    HRS 61-100: loading zone (up to 30% surcharge)

    Optional multipliers (applied to base_premium before HRS adjustment):
    - industry: industry-specific risk loading from Indian market data
    - region: regional cost-of-care factor (North/South/East/West)
    - sum_assured_lakhs: sum assured band adjustment
    """
    # Apply market multipliers to base premium
    multiplier = 1.0
    if industry and industry in INDUSTRY_RISK_MULTIPLIERS:
        multiplier *= INDUSTRY_RISK_MULTIPLIERS[industry]
    if region and region in REGION_MULTIPLIERS:
        multiplier *= REGION_MULTIPLIERS[region]
    band = _get_sum_assured_band(sum_assured_lakhs)
    multiplier *= SUM_ASSURED_BAND_MULTIPLIERS.get(band, 1.0)
    effective_base = base_premium * multiplier

    if hrs <= 40:
        discount = (40 - hrs) / 40 * 0.15
        adjusted = effective_base * (1 - discount)
        return {
            "base_premium":     base_premium,
            "adjusted_premium": round(adjusted, 2),
            "adjustment_pct":   round(-discount * 100, 2),
            "zone":             "discount",
            "recommendation":   "Low-risk group. Offer preferred rates to retain.",
        }

    if hrs <= 60:
        return {
            "base_premium":     base_premium,
            "adjusted_premium": round(effective_base, 2),
            "adjustment_pct":   round((multiplier - 1) * 100, 2),
            "zone":             "standard",
            "recommendation":   "Average risk. Price at book rate.",
        }

    loading  = (hrs - 60) / 40 * 0.30
    adjusted = effective_base * (1 + loading)
    return {
        "base_premium":     base_premium,
        "adjusted_premium": round(adjusted, 2),
        "adjustment_pct":   round(loading * 100, 2),
        "zone":             "loading",
        "recommendation":   "High risk. Apply surcharge or require wellness program.",
    }


def calculate_wellness_roi(
    base_premium: float,
    current_hrs: float,
    projected_hrs_after_program: float,
    industry: str = None,
    region: str = None,
    sum_assured_lakhs: float = 5.0,
) -> dict:
    """Estimates ROI of a wellness program based on projected HRS improvement."""
    current  = calculate_premium_adjustment(base_premium, current_hrs,
                                            industry, region, sum_assured_lakhs)
    improved = calculate_premium_adjustment(base_premium, projected_hrs_after_program,
                                            industry, region, sum_assured_lakhs)
    annual_savings = current["adjusted_premium"] - improved["adjusted_premium"]
    return {
        "current_premium":   current["adjusted_premium"],
        "projected_premium": improved["adjusted_premium"],
        "annual_savings":    round(annual_savings, 2),
        "hrs_improvement":   round(current_hrs - projected_hrs_after_program, 1),
        "current_zone":      current["zone"],
        "projected_zone":    improved["zone"],
    }
```

**Important:** After pasting the file, replace the three empty `{}` dicts with the actual values printed by the calibrate script in Task 5 Step 5.

- [ ] **Step 4: Run the full test suite**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/test_ml_engine.py tests/test_calibrate_premium.py tests/test_excel_loader.py -v
```

Expected: all tests pass (exact count depends on existing suite size — no regressions).

- [ ] **Step 5: Commit**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/premium_calculator.py tests/test_ml_engine.py
git -C "c:/Rupalprojects/aegis-ai" commit -m "feat: calibrate premium calculator from Indian market corporate quotes"
```

---

## Task 7: Full Retrain + Verify

**Files:**
- Modify: `ml_engine/artifacts/xgb_model.pkl`
- Modify: `ml_engine/artifacts/hrs_scorer.pkl`
- Modify: `ml_engine/artifacts/feature_names.pkl`

- [ ] **Step 1: Confirm rollback tag exists**

```powershell
git -C "c:/Rupalprojects/aegis-ai" tag | Select-String "pre-excel-retrain"
```

Expected: `pre-excel-retrain`

- [ ] **Step 2: Run full test suite to confirm clean baseline**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/ -q --ignore=tests/security_tests.py
```

Expected: `75 passed, 5 skipped` (or similar — no failures).

- [ ] **Step 3: Retrain model on Excel + HuggingFace data**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m ml_engine.training.train --use-excel-hf
```

Expected output (approximate):
```
Loading Excel training assets...
  File 1: 508 rows | File 2: 511 rows | Joined: XXX rows
Loading dataset from Hugging Face (...)...
  Loaded XXX rows ...
Using dataset mode: excel-hf
       excel: XXX rows
huggingface: XXX rows
   combined: XXX rows
XXX features prepared: [...]
[1/3] Tuning hyperparameters with Optuna...
  Best CV MAE: X.XXXX
[2/3] Training final model with best params...
  Metrics:
    train_mae    X.XXXX
    test_mae     X.XXXX
    train_r2     X.XXXX
    test_r2      X.XXXX    ← must be >= 0.65
[3/3] Calibrating HRS scorer...
  Saved: ml_engine/artifacts/xgb_model.pkl
Training complete.
```

- [ ] **Step 4: Verify metrics meet threshold**

`test_r2` must be **>= 0.65**. If it falls below:
```powershell
# Rollback artifacts
git -C "c:/Rupalprojects/aegis-ai" checkout pre-excel-retrain -- ml_engine/artifacts/
git -C "c:/Rupalprojects/aegis-ai" commit -m "revert: roll back to pre-excel artifacts — test_r2 below threshold"
```
Then stop and investigate data quality before re-attempting.

- [ ] **Step 5: Run full test suite again to confirm no regressions**

```powershell
cd "c:/Rupalprojects/aegis-ai"
python -m pytest tests/ -q --ignore=tests/security_tests.py
```

Expected: same pass count as Step 2.

- [ ] **Step 6: Commit updated artifacts**

```powershell
git -C "c:/Rupalprojects/aegis-ai" add ml_engine/artifacts/
git -C "c:/Rupalprojects/aegis-ai" commit -m "ml: retrain on real Indian market data (excel-hf mode) — test_r2=X.XX"
```

Replace `X.XX` with the actual `test_r2` from Step 3.

- [ ] **Step 7: Push to GitHub and HuggingFace**

```powershell
git -C "c:/Rupalprojects/aegis-ai" push origin main
hf upload Rupa2k/aegis-ai "c:\Rupalprojects\aegis-ai" . --repo-type=space
```

- [ ] **Step 8: Update vault**

Open `C:\Rupalprojects\Obsidian Vault\Aegis AI\Phase Progress.md` and add entry:

```
### Excel Training Data Integration & Premium Calibration (2026-06-18)

**Status**: ✅ Complete
**Commits**: [list commit hashes]

Replaced synthetic training CSV with 500+ real Indian market employee health records
(inner-joined from two Excel files). Premium calculator calibrated from 200 corporate
insurance quotes — industry, region, and sum-assured multipliers now reflect real INR
market data. Rollback: `git checkout pre-excel-retrain -- ml_engine/artifacts/`.
```

---

## Rollback Reference

If anything degrades after deployment:

```powershell
# Restore pre-retrain artifacts from git tag
git -C "c:/Rupalprojects/aegis-ai" checkout pre-excel-retrain -- ml_engine/artifacts/
git -C "c:/Rupalprojects/aegis-ai" commit -m "revert: roll back to pre-excel artifacts"
git -C "c:/Rupalprojects/aegis-ai" push origin main
hf upload Rupa2k/aegis-ai "c:\Rupalprojects\aegis-ai" . --repo-type=space
```

To train from synthetic data while keeping Excel code:
```powershell
python -m ml_engine.training.train --use-legacy
```
