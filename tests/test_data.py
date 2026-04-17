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
    print(f"\n  loss_ratio range : {df['loss_ratio'].min():.3f} - {df['loss_ratio'].max():.3f}")
    print(f"  median           : {df['loss_ratio'].median():.3f}")
    print(f"  99th percentile  : {df['loss_ratio'].quantile(0.99):.3f}")

    assert df["loss_ratio"].min() >= 0, "Negative loss ratio found"
    assert df["loss_ratio"].isnull().sum() == 0, "Null values in loss_ratio"
    assert df["loss_ratio"].median() < 5, f"Median too high: {df['loss_ratio'].median():.2f}"
    assert df["loss_ratio"].quantile(0.95) < 20, "95th percentile too high"

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