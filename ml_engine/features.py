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
    # Derived
    "activity_score", "health_composite",
]

TARGET_COLUMN = "loss_ratio"
TARGET_LOG    = "loss_ratio_log"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw training_dataset.csv and produces model-ready features.

    Adds two derived features:
      - activity_score: composite of steps + HR + sleep in healthy ranges
      - health_composite: inverse score penalizing chronic conditions + smoking
    """
    df = df.copy()

    # Handle categorical gender
    df["gender_male"] = (df["gender"] == "M").astype(int)

    # Convert bool-ish columns to int
    for col in ["smoker", "diabetic", "hypertension"]:
        df[col] = df[col].astype(int)

    # Fill any remaining nulls
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
