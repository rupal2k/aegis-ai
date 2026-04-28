"""
Convert the real user lab + activity data into training-ready rows.

Reads:
  data/upload_doc_0.csv  — annual per-user: 9 lab domains + activity metrics
  data/upload_doc_2.csv  — individual lab results (used for risk level counts)

Outputs:
  data/output/real_user_training.csv  — 237 rows, same schema as training_dataset.csv

Run: python data/build_lab_training_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
rng = np.random.default_rng(42)

OUTPUT_DIR  = Path("data/output")
UPLOAD_ACT  = Path("data/upload_doc_0.csv")   # activity + lab summary
UPLOAD_LAB  = Path("data/upload_doc_2.csv")   # individual lab results

# Maps domain column names in Doc 0 → feature flag names
DOMAIN_TO_FLAG = {
    "Bone Health":         "lab_bone_flag",
    "Diabetes":            "lab_diabetes_flag",
    "Heart Health":        "lab_heart_flag",
    "Inflammation":        "lab_inflammation_flag",
    "Iron":                "lab_iron_flag",
    "Kidney Health":       "lab_kidney_flag",
    "Liver Health":        "lab_liver_flag",
    "Thyroid Health":      "lab_thyroid_flag",
    "Vitamin Deficiency":  "lab_vitamin_flag",
}

LAB_FLAGS = list(DOMAIN_TO_FLAG.values())

LAB_WEIGHTS = {
    "lab_diabetes_flag":     0.25,
    "lab_heart_flag":        0.20,
    "lab_kidney_flag":       0.18,
    "lab_liver_flag":        0.12,
    "lab_inflammation_flag": 0.10,
    "lab_iron_flag":         0.05,
    "lab_bone_flag":         0.04,
    "lab_thyroid_flag":      0.03,
    "lab_vitamin_flag":      0.03,
}


def load_lab_risk_per_user(lab_path: Path) -> pd.DataFrame:
    """
    From individual lab results, compute per-user:
      - lab_high_count:   markers with risk_level == 'high'
      - lab_medium_count: markers with risk_level == 'medium'
      - lab_oor_count:    total out-of-range markers
    """
    df = pd.read_csv(lab_path)
    agg = df.groupby("unique_id").agg(
        lab_high_count   = ("risk_level", lambda x: (x == "high").sum()),
        lab_medium_count = ("risk_level", lambda x: (x == "medium").sum()),
        lab_oor_count    = ("status",     lambda x: (x == "outofrange").sum()),
        lab_total_tests  = ("marker_code", "count"),
    ).reset_index().rename(columns={"unique_id": "user_id_b64"})
    return agg


def build_real_user_rows() -> pd.DataFrame:
    print("Loading activity + lab summary...")
    df_act = pd.read_csv(UPLOAD_ACT)
    print(f"  {len(df_act)} rows, {df_act.user_id.nunique()} users, years {sorted(df_act.year.unique())}")

    print("Loading individual lab results...")
    lab_risk = load_lab_risk_per_user(UPLOAD_LAB)
    print(f"  {len(lab_risk)} users with individual lab data")

    # Use latest year per user for the most current health state
    df = df_act.sort_values("year").groupby("user_id").last().reset_index()
    n = len(df)
    print(f"  Using latest year: {n} users")

    # ── Lab domain flags ────────────────────────────────────────────────────
    for domain_col, flag_col in DOMAIN_TO_FLAG.items():
        df[flag_col] = (df[domain_col] == "outofrange").astype(int)

    # ── Activity features ───────────────────────────────────────────────────
    # step_count is annual total → convert to daily average
    df["avg_daily_steps"] = (df["step_count"].fillna(0) / 365).round(0).clip(lower=0)
    df["avg_active_mins"] = (df["total_active_minutes"].fillna(0) / 365).round(1).clip(lower=0)
    # Estimate step volatility from mindful_min as a proxy for consistency
    df["step_volatility"] = (df["mindful_min"].fillna(0) / 365 * 120 + 400).clip(100, 3000).round(0)

    # ── Inferred demographics ───────────────────────────────────────────────
    # Age: correlated with number of out-of-range domains
    df["lab_domain_count"] = df[LAB_FLAGS].sum(axis=1)
    df["age"] = np.clip(
        rng.normal(34, 7, n) + df["lab_domain_count"] * 1.8,
        22, 62
    ).astype(int)

    # BMI: correlated with heart + diabetes lab results
    df["bmi"] = np.clip(
        rng.normal(23.5, 3.2, n)
        + df["lab_heart_flag"].values * 2.5
        + df["lab_diabetes_flag"].values * 3.0,
        16, 42
    ).round(1)

    # Smoker: correlated with inflammation + liver outofrange
    p_smoke = np.clip(
        0.08
        + df["lab_inflammation_flag"].values * 0.14
        + df["lab_heart_flag"].values * 0.10
        + df["lab_liver_flag"].values * 0.08,
        0, 0.85
    )
    df["smoker"] = (rng.uniform(size=n) < p_smoke).astype(int)

    # Diabetic: lab Diabetes domain is the primary signal
    df["diabetic"] = df["lab_diabetes_flag"].values

    # Hypertension: lab Heart Health domain is the primary signal
    df["hypertension"] = df["lab_heart_flag"].values

    df["chronic_count"] = df["diabetic"] + df["hypertension"]

    # ── Wearable proxies (not in real data — derived from activity) ─────────
    # Resting HR: higher for sedentary/heart-risk users
    df["avg_resting_hr"] = np.clip(
        rng.normal(70, 7, n)
        + df["lab_heart_flag"].values * 5
        + df["smoker"].values * 3
        - (df["avg_daily_steps"].values / 3500),
        55, 102
    ).round(1)

    df["hr_trend"]       = rng.normal(0, 0.15, n)
    df["avg_sleep_hours"] = np.clip(rng.normal(6.8, 0.75, n), 4.5, 9.5).round(1)
    df["avg_spo2"] = np.clip(
        rng.normal(97.5, 0.5, n) - df["smoker"].values * 1.2,
        90, 100
    ).round(1)

    # ── Clinical proxy (from individual lab risk counts) ────────────────────
    df["visit_count"] = np.clip(
        rng.poisson(1.5 + df["lab_domain_count"] * 0.55, n), 0, 15
    ).astype(int)
    df["hospitalized_count"] = (
        rng.uniform(size=n) < (df["lab_domain_count"] * 0.04)
    ).astype(int)

    # ── Lab risk score ───────────────────────────────────────────────────────
    df["lab_risk_score"] = sum(
        w * df[col] for col, w in LAB_WEIGHTS.items()
    ).round(4)

    # ── Derive loss_ratio ────────────────────────────────────────────────────
    # Combine lab risk + activity risk + clinical flags into a single risk value
    # then exponentiate to get a heavy-tailed loss ratio distribution
    activity_factor = np.clip(1.0 - df["avg_daily_steps"].values / 10000, 0, 1)
    risk = (
        df["lab_risk_score"].values * 3.0
        + activity_factor * 1.0
        + df["smoker"].values * 0.45
        + df["chronic_count"].values * 0.35
    )
    noise = rng.uniform(0.65, 1.40, n)
    df["premium_share"]  = rng.uniform(4500, 12000, n).round(0)
    df["total_claims"]   = np.clip(
        (np.expm1(risk) * df["premium_share"].values * 0.16 * noise).round(2),
        0, None
    )
    df["loss_ratio"]     = (df["total_claims"] / df["premium_share"]).round(4).clip(0, 120)
    df["high_risk"]      = (df["loss_ratio"] > 1.2).astype(int)

    # ── Metadata ─────────────────────────────────────────────────────────────
    df["employee_id"]  = [f"REAL_{i:05d}" for i in range(n)]
    df["company_id"]   = "REAL_DATA"
    df["gender"]       = rng.choice(["M", "F"], size=n, p=[0.54, 0.46])
    df["job_category"] = rng.choice(["desk", "field", "manual"], size=n, p=[0.4, 0.35, 0.25])

    # Keep only the columns matching training_dataset.csv schema + lab flags
    keep_cols = [
        "employee_id", "company_id", "age", "gender", "bmi", "smoker",
        "diabetic", "hypertension", "job_category",
        "avg_daily_steps", "step_volatility", "avg_resting_hr", "hr_trend",
        "avg_active_mins", "avg_sleep_hours", "avg_spo2",
        "total_claims", "visit_count", "hospitalized_count",
        "premium_share", "loss_ratio", "high_risk", "chronic_count",
        # Lab features
        "lab_bone_flag", "lab_diabetes_flag", "lab_heart_flag",
        "lab_inflammation_flag", "lab_iron_flag", "lab_kidney_flag",
        "lab_liver_flag", "lab_thyroid_flag", "lab_vitamin_flag",
        "lab_domain_count", "lab_risk_score",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    print(f"\nReal user dataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Loss ratio — mean: {df['loss_ratio'].mean():.3f}, "
          f"max: {df['loss_ratio'].max():.3f}, "
          f"high-risk: {df['high_risk'].mean()*100:.1f}%")
    print(f"  Avg lab_domain_count: {df['lab_domain_count'].mean():.2f}")
    print(f"  Avg lab_risk_score:   {df['lab_risk_score'].mean():.3f}")

    return df


if __name__ == "__main__":
    df = build_real_user_rows()
    out = OUTPUT_DIR / "real_user_training.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved → {out}")
