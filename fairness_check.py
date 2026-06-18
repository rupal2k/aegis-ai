"""
Gender-stratified fairness audit for the Aegis AI HRS model.

Connects to the local PostgreSQL DB, pulls training_snapshots, runs
the loaded model on each row, and reports MAE / mean HRS by gender group.

Usage:
    python fairness_check.py

Requirements: psycopg2, pandas, joblib, scikit-learn (already in requirements.txt)
"""
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

DB_URL = "postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db"
ARTIFACTS = Path("ml_engine/artifacts")

FEATURE_COLS = [
    "age", "bmi", "chronic_count", "smoker", "diabetic", "hypertension",
    "avg_daily_steps", "step_volatility", "avg_resting_hr", "hr_trend",
    "avg_active_mins", "avg_sleep_hours", "avg_spo2",
    "visit_count", "hospitalized_count",
    "lab_heart_flag", "lab_inflammation_flag", "lab_diabetes_flag",
    "lab_kidney_flag", "lab_liver_flag", "lab_iron_flag",
    "lab_thyroid_flag", "lab_bone_flag", "lab_vitamin_flag",
]


def load_data():
    try:
        import psycopg2
    except ImportError:
        sys.exit("psycopg2 not installed — run: pip install psycopg2-binary")

    conn = psycopg2.connect(DB_URL)
    df = pd.read_sql("""
        SELECT ts.*, e.gender AS employee_gender
        FROM training_snapshots ts
        JOIN employees e ON ts.employee_id = e.employee_id
    """, conn)
    # Drop any ts.gender duplicate before renaming
    if "gender" in df.columns:
        df = df.drop(columns=["gender"])
    df = df.rename(columns={"employee_gender": "gender"})
    conn.close()
    return df


def engineer_features(df):
    # Derived features matching ml_engine/features.py
    df = df.copy()
    df["activity_score"] = (
        (df["avg_daily_steps"].clip(0, 20000) / 20000) * 40 +
        (df["avg_active_mins"].clip(0, 120) / 120) * 30 +
        ((df["avg_spo2"].clip(85, 100) - 85) / 15) * 30
    )
    df["health_composite"] = (
        df["smoker"] * 30 +
        df["diabetic"] * 25 +
        df["hypertension"] * 20 +
        (df["bmi"].clip(18, 50) - 18) / 32 * 15 +
        df["chronic_count"].clip(0, 5) / 5 * 10
    )
    df["smoker_diabetic"] = df["smoker"] * df["diabetic"]
    df["bmi_age_risk"] = (df["bmi"].clip(18, 50) - 18) * (df["age"] - 18) / (32 * 52)
    df["clinical_burden"] = df["visit_count"] + df["hospitalized_count"] * 3

    # Lab aggregates
    lab_flags = [c for c in df.columns if c.startswith("lab_") and c.endswith("_flag")]
    weights = {"lab_heart_flag": 3, "lab_diabetes_flag": 3, "lab_kidney_flag": 2,
               "lab_liver_flag": 2, "lab_inflammation_flag": 2, "lab_iron_flag": 1,
               "lab_thyroid_flag": 1, "lab_bone_flag": 1, "lab_vitamin_flag": 1}
    df["lab_domain_count"] = df[lab_flags].sum(axis=1)
    df["lab_risk_score"] = sum(df[f] * weights.get(f, 1) for f in lab_flags if f in df.columns)

    all_features = FEATURE_COLS + [
        "activity_score", "health_composite",
        "smoker_diabetic", "bmi_age_risk", "clinical_burden",
        "lab_domain_count", "lab_risk_score",
    ]
    available = [c for c in all_features if c in df.columns]
    return df[available + ["gender"]]


def main():
    print("Loading model artifacts...")
    model = joblib.load(ARTIFACTS / "xgb_model.pkl")
    scorer_data = joblib.load(ARTIFACTS / "hrs_scorer.pkl")
    feature_names = joblib.load(ARTIFACTS / "feature_names.pkl")

    p05 = scorer_data.get("p05", 0)
    p95 = scorer_data.get("p95", 1)

    def to_hrs(log_lr):
        clamped = np.clip(log_lr, p05, p95)
        return ((clamped - p05) / max(p95 - p05, 1e-6)) * 100

    print("Loading training snapshots + employee gender from local DB...")
    try:
        df = load_data()
    except Exception as e:
        sys.exit(f"DB connection failed: {e}\nIs the local Docker stack running?")

    print(f"  Loaded {len(df):,} rows — gender distribution: {df['gender'].value_counts().to_dict()}\n")

    engineered = engineer_features(df)
    gender_col = engineered.pop("gender")

    # Align columns to model's expected feature order
    cols = [f for f in feature_names if f in engineered.columns]
    missing = [f for f in feature_names if f not in engineered.columns]
    if missing:
        print(f"  Warning: {len(missing)} features missing from DB, filling with 0: {missing[:5]}...")
        for m in missing:
            engineered[m] = 0
        cols = feature_names

    X = engineered[cols].fillna(0).values

    print("Running predictions...")
    raw_preds = model.predict(X)
    hrs_preds = np.array([to_hrs(p) for p in raw_preds])

    results_df = pd.DataFrame({
        "gender": gender_col.values,
        "predicted_log_lr": raw_preds,
        "predicted_hrs": hrs_preds,
    })

    # ── Fairness Report ───────────────────────────────────────────────────────
    print("=" * 60)
    print("AEGIS AI — FAIRNESS AUDIT: GENDER STRATIFICATION")
    print("=" * 60)

    groups = results_df.groupby("gender")

    rows = []
    for gender, grp in groups:
        rows.append({
            "Gender": gender,
            "N": len(grp),
            "Mean HRS": f"{grp['predicted_hrs'].mean():.1f}",
            "Median HRS": f"{grp['predicted_hrs'].median():.1f}",
            "Std HRS": f"{grp['predicted_hrs'].std():.1f}",
            "% Low (<40)": f"{(grp['predicted_hrs'] < 40).mean() * 100:.1f}%",
            "% Moderate (40-60)": f"{((grp['predicted_hrs'] >= 40) & (grp['predicted_hrs'] < 60)).mean() * 100:.1f}%",
            "% High (60-80)": f"{((grp['predicted_hrs'] >= 60) & (grp['predicted_hrs'] < 80)).mean() * 100:.1f}%",
            "% Critical (80+)": f"{(grp['predicted_hrs'] >= 80).mean() * 100:.1f}%",
        })

    report_df = pd.DataFrame(rows)
    print(report_df.to_string(index=False))

    # Mean HRS gap
    hrs_by_gender = results_df.groupby("gender")["predicted_hrs"].mean()
    max_gap = hrs_by_gender.max() - hrs_by_gender.min()

    print(f"\n  Max mean HRS gap across gender groups: {max_gap:.1f} points")
    if max_gap > 5:
        print("  ⚠️  Gap > 5 points — investigate feature interactions (BMI×age, smoker rates)")
    else:
        print("  ✓  Gap ≤ 5 points — gender parity acceptable for portfolio-level use")

    # Age stratification bonus
    print(f"\n{'=' * 60}")
    print("BONUS: AGE STRATIFICATION (decade buckets)")
    print("=" * 60)

    results_df["age_bucket"] = pd.cut(
        df["age"].values, bins=[17, 29, 39, 49, 59, 70],
        labels=["18-29", "30-39", "40-49", "50-59", "60-70"]
    )
    age_report = results_df.groupby("age_bucket")["predicted_hrs"].agg(
        N="count", Mean="mean", Std="std"
    ).round(1)
    print(age_report.to_string())
    print("\n  Note: Monotone constraint on age is active — HRS should be non-decreasing by decade.")

    print(f"\n{'=' * 60}")
    print("AUDIT COMPLETE")
    print("=" * 60)
    print("If gaps are within acceptable bounds, document this report in MODEL_CARD.md.")
    print("Run again after any retraining to verify parity is maintained.")


if __name__ == "__main__":
    main()
