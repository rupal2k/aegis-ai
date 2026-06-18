"""Feature engineering for the Aegis AI underwriting model."""
import pandas as pd
import numpy as np


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
    # Derived activity/health
    "activity_score", "health_composite",
    # Interaction
    "smoker_diabetic", "bmi_age_risk", "clinical_burden",
    # Lab domain flags (0 = normal / not tested, 1 = out-of-range)
    "lab_heart_flag", "lab_inflammation_flag", "lab_diabetes_flag",
    "lab_kidney_flag", "lab_liver_flag", "lab_iron_flag",
    "lab_thyroid_flag", "lab_bone_flag", "lab_vitamin_flag",
    # Lab aggregate features
    "lab_domain_count", "lab_risk_score",
]

# Monotone constraints in FEATURE_COLUMNS order.
# +1 = feature must increase predicted loss_ratio (more = higher risk)
# -1 = feature must decrease predicted loss_ratio (more = lower risk)
#  0 = no constraint
MONOTONE_CONSTRAINTS = (
    1,   # age
    1,   # bmi
    1,   # chronic_count
    1,   # smoker
    1,   # diabetic
    1,   # hypertension
    -1,  # avg_daily_steps
    0,   # step_volatility (ambiguous)
    1,   # avg_resting_hr
    1,   # hr_trend (rising resting HR = more risk)
    -1,  # avg_active_mins
    0,   # avg_sleep_hours (J-curve: too little and too much both bad)
    -1,  # avg_spo2
    1,   # visit_count
    1,   # hospitalized_count
    -1,  # activity_score
    1,   # health_composite
    1,   # smoker_diabetic
    1,   # bmi_age_risk
    1,   # clinical_burden
    1,   # lab_heart_flag
    1,   # lab_inflammation_flag
    1,   # lab_diabetes_flag
    1,   # lab_kidney_flag
    1,   # lab_liver_flag
    1,   # lab_iron_flag
    1,   # lab_thyroid_flag
    1,   # lab_bone_flag
    1,   # lab_vitamin_flag
    1,   # lab_domain_count
    1,   # lab_risk_score
)

TARGET_COLUMN = "loss_ratio"
TARGET_LOG    = "loss_ratio_log"

# Weights for lab_risk_score — reflect clinical cost burden
_LAB_WEIGHTS = {
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

_LAB_FLAGS = list(_LAB_WEIGHTS.keys())


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw training_dataset.csv (or a prediction row dict) and produces
    model-ready features.

    Lab features default to 0 when absent so inference is backward-compatible
    with employees who have no lab records on file.
    """
    df = df.copy()

    # Clamp inputs to training distribution — prevents XGBoost extrapolation
    # into sparse tree leaves for values beyond the augmentation bounds.
    if "chronic_count" in df.columns:
        df["chronic_count"] = df["chronic_count"].fillna(0).clip(0, 4).astype(int)
    if "bmi" in df.columns:
        df["bmi"] = df["bmi"].clip(15.0, 50.0)

    # Handle categorical gender
    df["gender_male"] = (df["gender"] == "M").astype(int) if "gender" in df.columns else 0

    # Convert bool-ish columns to int
    for col in ["smoker", "diabetic", "hypertension"]:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # Fill any remaining nulls for core features
    numeric_fill = {
        "avg_daily_steps": 5000, "step_volatility": 0,
        "avg_resting_hr":  72,   "hr_trend": 0,
        "avg_active_mins": 30,   "avg_sleep_hours": 7.0,
        "avg_spo2":        97.0,
        "visit_count":     0,    "hospitalized_count": 0,
    }
    for col, default in numeric_fill.items():
        if col in df.columns:
            df[col] = df[col].fillna(default)

    # Fill missing lab features with 0 (not tested = assume normal)
    for col in _LAB_FLAGS:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0).astype(int)

    # Derived: activity_score (0-100, higher = healthier)
    steps_norm = np.clip(df["avg_daily_steps"] / 10000, 0, 1.2)
    hr_norm    = np.clip((80 - df["avg_resting_hr"]) / 30, 0, 1)
    sleep_norm = np.clip(1 - np.abs(df["avg_sleep_hours"] - 7.5) / 3, 0, 1)
    df["activity_score"] = ((steps_norm + hr_norm + sleep_norm) / 3 * 100).round(2)

    # Derived: health_composite (penalty score, higher = more risk)
    df["health_composite"] = (
        df["smoker"]       * 15 +
        df["diabetic"]     * 20 +
        df["hypertension"] * 15 +
        np.clip(df["bmi"] - 25, 0, 20) * 1.5 +
        (df["age"] / 60) * 10
    ).round(2)

    # Interaction features
    df["smoker_diabetic"] = df["smoker"] * df["diabetic"]
    df["bmi_age_risk"]    = (df["bmi"] / 25.0) * (df["age"] / 40.0)
    df["clinical_burden"] = df["visit_count"] * (1 + df["hospitalized_count"])

    # Lab aggregate features
    df["lab_domain_count"] = df[_LAB_FLAGS].sum(axis=1)
    df["lab_risk_score"] = sum(
        w * df[col] for col, w in _LAB_WEIGHTS.items()
    ).round(4)

    # Log-transform the target to handle the long tail
    if TARGET_COLUMN in df.columns:
        df[TARGET_LOG] = np.log1p(df[TARGET_COLUMN])

    return df


def get_feature_matrix(df: pd.DataFrame):
    """Return X (features) and y (target) as numpy arrays."""
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[available].values
    y = df[TARGET_LOG].values if TARGET_LOG in df.columns else None
    return X, y, available
