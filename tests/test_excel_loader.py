"""Tests for Excel dataset loader and mapper."""
import numpy as np
import pandas as pd
import pytest


def _make_joined_df(n=5):
    """Minimal joined File1+File2 dataframe for testing."""
    rng = np.random.default_rng(42)
    # Fixed 5-row anchor values; for n>5 tile and trim
    _age    = [30.0, 45.0, 55.0, 25.0, 60.0]
    _gender = ["Male", "Female", "Male", "Female", "Male"]
    _bmi    = [22.0, 28.5, 31.0, 24.0, 35.0]
    _sbp    = [115.0, 135.0, 150.0, 118.0, 145.0]
    _dbp    = [75.0, 82.0, 95.0, 70.0, 88.0]
    _drs    = [20.0, 55.0, 70.0, 15.0, 80.0]
    _cc     = [0.0, 1.0, 2.0, 0.0, 3.0]
    _claims = [0.0, 50000.0, 120000.0, 0.0, 200000.0]
    _steps  = [9000.0, 6500.0, 3500.0, 10000.0, 2000.0]
    _sleep  = [7.5, 6.5, 5.5, 8.0, 5.0]
    _stress = [20.0, 50.0, 80.0, 15.0, 90.0]
    _act    = ["High", "Moderate", "Low", "High", "Low"]
    _wes    = [80.0, 60.0, 30.0, 90.0, 20.0]
    _prem   = [200000.0, 250000.0, 300000.0, 180000.0, 350000.0]

    def _tile(lst):
        import itertools
        return list(itertools.islice(itertools.cycle(lst), n))

    return pd.DataFrame({
        "Employee_ID":              [f"EMP{i:04d}" for i in range(n)],
        "Age":                      _tile(_age),
        "Gender":                   _tile(_gender),
        "BMI":                      _tile(_bmi),
        "Systolic_BP":              _tile(_sbp),
        "Diastolic_BP":             _tile(_dbp),
        "Diabetes_Risk_Score":      _tile(_drs),
        "Chronic_Conditions":       _tile(_cc),
        "Historical_Claims_INR":    _tile(_claims),
        "Avg_Daily_Steps":          _tile(_steps),
        "Avg_Sleep_Hours":          _tile(_sleep),
        "Stress_Score":             _tile(_stress),
        "Activity_Level":           _tile(_act),
        "Wellness_Engagement_Score":_tile(_wes),
        "Weight_Based_Premium_INR": _tile(_prem),
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
