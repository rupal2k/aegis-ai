import pandas as pd
from pathlib import Path

OUTPUT = Path("data/output")

def test_files_exist():
    for f in ["companies.csv", "employees.csv", "telemetry.csv",
              "clinical_events.csv", "training_dataset.csv"]:
        assert (OUTPUT / f).exists(), f"Missing file: {f}"

def test_employee_count():
    df = pd.read_csv(OUTPUT / "employees.csv")
    assert len(df) == 5000, f"Expected 5000 employees, got {len(df)}"

def test_no_nulls_in_key_columns():
    df = pd.read_csv(OUTPUT / "employees.csv")
    for col in ["employee_id", "company_id", "age", "bmi"]:
        assert df[col].isnull().sum() == 0, f"Nulls found in {col}"

def test_loss_ratio_bounds():
    df = pd.read_csv(OUTPUT / "training_dataset.csv")
    assert df["loss_ratio"].min() >= 0
    assert df["loss_ratio"].max() < 15

def test_health_risk_correlation():
    df = pd.read_csv(OUTPUT / "training_dataset.csv")
    corr = df["avg_daily_steps"].corr(df["loss_ratio"])
    assert corr < -0.1, f"Weak signal — correlation was {corr:.3f}"

def test_anonymization():
    df = pd.read_csv(OUTPUT / "employees.csv")
    assert not df["employee_id"].str.startswith("EMP_").any(), \
        "Raw IDs found — anonymization failed"

def test_company_count():
    df = pd.read_csv(OUTPUT / "companies.csv")
    assert len(df) == 20