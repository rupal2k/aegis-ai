"""
Aegis AI - Model training pipeline.

Run: python -m ml_engine.training.train [OPTIONS]

Options:
  --use-local         Use only local CSV dataset
  --use-hf            Use only Hugging Face dataset
  --use-both          Use both local CSV and HF dataset (default - recommended)
  --no-hf             Alias for --use-local (skip HF dataset)
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

import joblib
import mlflow
import mlflow.xgboost
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from dotenv import load_dotenv
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from ml_engine.features import engineer_features, get_feature_matrix
from ml_engine.scorer import HRSScorer

load_dotenv()

DATA_PATH = Path("data/output/training_dataset.csv")
ARTIFACTS = Path("ml_engine/artifacts")
ARTIFACTS.mkdir(exist_ok=True)

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
HF_DATASET_NAME = os.environ.get(
    "AEGIS_HF_DATASET",
    "gcc-insurance-intelligence-lab-dev/gcc-insurance-underwriting-risk",
)
DEFAULT_DATA_MODE = "both"
N_OPTUNA_TRIALS = 5 if os.environ.get("AEGIS_CI_FAST") == "1" else 30
RANDOM_STATE = 42

UNDERWRITING_HF_COLUMNS = {
    "applicant_age",
    "gender",
    "occupation_risk",
    "health_score",
    "bmi",
    "smoker",
    "previous_claims_count",
    "coverage_amount",
    "premium_calculated",
}

INSURANCE_CHARGE_HF_COLUMNS = {
    "age",
    "bmi",
    "children",
    "sex",
    "smoker",
    "region",
    "prediction",
}

COMPANY_PROFILE_HF_COLUMNS = {
    "name",
    "industry",
    "followers_count",
    "associated_members_count",
    "founded_on",
}

optuna.logging.set_verbosity(optuna.logging.WARNING)


def configure_stdout():
    """Prefer UTF-8 stdout in CLI runs without breaking test capture."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def configure_mlflow():
    """Configure MLflow lazily so imports stay side-effect free."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("aegis-underwriting")


def load_local_dataset():
    """Load the synthetic/local training CSV."""
    print(f"Loading local dataset from {DATA_PATH}...")
    return pd.read_csv(DATA_PATH)


def infer_hf_schema(df: pd.DataFrame) -> str:
    """Classify the HF dataset so we can route it through the right mapper."""
    columns = set(df.columns)
    if UNDERWRITING_HF_COLUMNS.issubset(columns):
        return "underwriting_tabular"
    if INSURANCE_CHARGE_HF_COLUMNS.issubset(columns):
        return "insurance_charges"
    if COMPANY_PROFILE_HF_COLUMNS.issubset(columns):
        return "company_profiles"
    if "text" in columns:
        return "clinical_notes"
    raise RuntimeError(
        "Unsupported Hugging Face dataset schema. "
        f"Columns found: {sorted(df.columns.tolist())}"
    )


def map_underwriting_hf_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Map structured underwriting rows into the Aegis feature schema."""
    rng = np.random.default_rng(RANDOM_STATE)

    df_mapped = pd.DataFrame()
    df_mapped["age"] = df["applicant_age"].astype(float)
    df_mapped["gender"] = df["gender"].astype(str)
    df_mapped["bmi"] = df["bmi"].astype(float)
    df_mapped["smoker"] = df["smoker"].astype(int)

    health_normalized = (df["health_score"].astype(float) / 100.0).clip(0.0, 1.0)
    claims_count = df["previous_claims_count"].clip(lower=0).astype(float)
    occupation_risk = (
        df["occupation_risk"].map({"Low": 0.0, "Medium": 1.0, "High": 2.0}).fillna(1.0)
    )

    df_mapped["diabetic"] = (
        (occupation_risk >= 1.0) & (health_normalized < 0.58)
    ).astype(int)
    df_mapped["hypertension"] = (
        (occupation_risk >= 1.0) | (df_mapped["age"] >= 50)
    ).astype(int)
    df_mapped["chronic_count"] = (
        df_mapped["diabetic"] + df_mapped["hypertension"] + (claims_count >= 3).astype(int)
    ).clip(0, 4)

    df_mapped["avg_daily_steps"] = np.clip(
        health_normalized * 9500 + 1200 + rng.normal(0, 450, len(df)),
        1500,
        15000,
    )
    df_mapped["step_volatility"] = np.clip(
        (1.0 - health_normalized) * 1400 + 150 + rng.normal(0, 120, len(df)),
        50,
        3000,
    )
    df_mapped["avg_resting_hr"] = np.clip(
        60 + (1.0 - health_normalized) * 24 + rng.normal(0, 2.5, len(df)),
        45,
        105,
    )
    df_mapped["hr_trend"] = np.clip(
        (claims_count / max(claims_count.max(), 1.0)) * 2.5 + rng.normal(0, 0.8, len(df)) - 1.0,
        -5,
        5,
    )
    df_mapped["avg_active_mins"] = np.clip(
        health_normalized * 55 + 8 + rng.normal(0, 7, len(df)),
        0,
        90,
    )
    df_mapped["avg_sleep_hours"] = np.clip(
        6.0 + health_normalized * 1.8 + rng.normal(0, 0.4, len(df)),
        4.0,
        9.5,
    )
    df_mapped["avg_spo2"] = np.clip(
        95.5 + health_normalized * 2.5 + rng.normal(0, 0.35, len(df)),
        90.0,
        100.0,
    )

    df_mapped["visit_count"] = claims_count.clip(0, 10)
    df_mapped["hospitalized_count"] = (
        (claims_count >= 4) | ((occupation_risk >= 1.0) & (health_normalized < 0.42))
    ).astype(int)

    low_health = health_normalized < 0.55
    df_mapped["lab_heart_flag"] = (
        low_health & ((occupation_risk >= 1.0) | (df_mapped["age"] >= 55))
    ).astype(int)
    df_mapped["lab_diabetes_flag"] = df_mapped["diabetic"]
    df_mapped["lab_kidney_flag"] = (
        low_health & ((df_mapped["bmi"] > 29) | (claims_count >= 3))
    ).astype(int)
    df_mapped["lab_liver_flag"] = (
        low_health & ((df_mapped["smoker"] == 1) | (df_mapped["bmi"] > 31))
    ).astype(int)
    df_mapped["lab_inflammation_flag"] = (
        (occupation_risk >= 1.0) & (health_normalized < 0.50)
    ).astype(int)
    df_mapped["lab_iron_flag"] = (rng.random(len(df)) > 0.82).astype(int)
    df_mapped["lab_thyroid_flag"] = (
        (rng.random(len(df)) > 0.88) | ((df_mapped["gender"] == "F") & (df_mapped["age"] > 45))
    ).astype(int)
    df_mapped["lab_bone_flag"] = (df_mapped["age"] > 58).astype(int)
    df_mapped["lab_vitamin_flag"] = (
        (rng.random(len(df)) > 0.72) | (df_mapped["avg_daily_steps"] < 3500)
    ).astype(int)

    coverage_rate = df["premium_calculated"].astype(float) / df["coverage_amount"].replace(0, np.nan).astype(float)
    coverage_rate = coverage_rate.fillna(coverage_rate.median())
    premium_signal = (coverage_rate / coverage_rate.median()).clip(0.5, 3.0)

    proxy_loss_ratio = (
        0.18
        + (1.0 - health_normalized) * 0.95
        + occupation_risk * 0.18
        + claims_count * 0.11
        + df_mapped["smoker"] * 0.10
        + np.clip(df_mapped["bmi"] - 27, 0, 12) * 0.025
        + (premium_signal - 1.0) * 0.35
    )
    df_mapped["loss_ratio"] = np.clip(
        proxy_loss_ratio * rng.lognormal(mean=0, sigma=0.18, size=len(df)),
        0.10,
        6.0,
    )
    return df_mapped


def map_insurance_charge_hf_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Map tabular insurance-charge rows into the Aegis feature schema."""
    rng = np.random.default_rng(RANDOM_STATE)

    df_mapped = pd.DataFrame()
    df_mapped["age"] = df["age"].astype(float)
    df_mapped["gender"] = (
        df["sex"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"male": "M", "m": "M", "female": "F", "f": "F"})
        .fillna("M")
    )
    df_mapped["bmi"] = df["bmi"].astype(float)
    df_mapped["smoker"] = (
        df["smoker"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin({"yes", "true", "1", "y"})
        .astype(int)
    )

    children = df["children"].fillna(0).clip(lower=0).astype(float)
    region = df["region"].astype(str).str.strip().str.lower()
    region_risk = region.map(
        {
            "southeast": 1.00,
            "southwest": 0.82,
            "northeast": 0.64,
            "northwest": 0.56,
        }
    ).fillna(0.70)

    bmi_risk = np.clip((df_mapped["bmi"] - 25.0) / 15.0, 0.0, 1.5)
    age_risk = np.clip((df_mapped["age"] - 18.0) / 50.0, 0.0, 1.4)
    lifestyle_risk = np.clip(
        df_mapped["smoker"] * 0.55 + bmi_risk * 0.30 + age_risk * 0.20,
        0.0,
        1.6,
    )

    df_mapped["diabetic"] = (
        (df_mapped["bmi"] >= 31.0)
        | ((df_mapped["age"] >= 52.0) & (df_mapped["smoker"] == 1))
    ).astype(int)
    df_mapped["hypertension"] = (
        (df_mapped["age"] >= 45.0)
        | (df_mapped["bmi"] >= 30.0)
        | (df_mapped["smoker"] == 1)
    ).astype(int)
    df_mapped["chronic_count"] = (
        df_mapped["diabetic"]
        + df_mapped["hypertension"]
        + (df_mapped["bmi"] >= 35.0).astype(int)
    ).clip(0, 4)

    df_mapped["avg_daily_steps"] = np.clip(
        10000 - lifestyle_risk * 3800 - children * 180 + rng.normal(0, 550, len(df)),
        1500,
        15000,
    )
    df_mapped["step_volatility"] = np.clip(
        240 + lifestyle_risk * 950 + region_risk * 140 + np.abs(rng.normal(0, 140, len(df))),
        50,
        3000,
    )
    df_mapped["avg_resting_hr"] = np.clip(
        58 + lifestyle_risk * 22 + region_risk * 1.5 + rng.normal(0, 3, len(df)),
        45,
        110,
    )
    df_mapped["hr_trend"] = np.clip(
        lifestyle_risk * 2.6 - 0.8 + rng.normal(0, 0.75, len(df)),
        -5,
        5,
    )
    df_mapped["avg_active_mins"] = np.clip(
        62 - lifestyle_risk * 24 - children * 1.8 + rng.normal(0, 6, len(df)),
        0,
        90,
    )
    df_mapped["avg_sleep_hours"] = np.clip(
        7.6 - df_mapped["smoker"] * 0.35 - bmi_risk * 0.65 + rng.normal(0, 0.35, len(df)),
        4.0,
        9.5,
    )
    df_mapped["avg_spo2"] = np.clip(
        98.4 - df_mapped["smoker"] * 1.2 - bmi_risk * 0.7 + rng.normal(0, 0.25, len(df)),
        90.0,
        100.0,
    )

    df_mapped["visit_count"] = np.clip(
        1.0
        + age_risk * 2.2
        + bmi_risk * 1.7
        + df_mapped["smoker"] * 1.1
        + children * 0.2
        + rng.normal(0, 0.55, len(df)),
        0,
        10,
    ).round()
    df_mapped["hospitalized_count"] = (
        (df_mapped["smoker"] == 1)
        & ((df_mapped["bmi"] >= 34.0) | (df_mapped["age"] >= 58.0))
    ).astype(int)

    df_mapped["lab_heart_flag"] = (
        (df_mapped["age"] >= 55.0)
        | ((df_mapped["smoker"] == 1) & (df_mapped["bmi"] >= 30.0))
    ).astype(int)
    df_mapped["lab_diabetes_flag"] = df_mapped["diabetic"]
    df_mapped["lab_kidney_flag"] = (
        (df_mapped["bmi"] >= 33.0) | (df_mapped["chronic_count"] >= 2)
    ).astype(int)
    df_mapped["lab_liver_flag"] = (
        (df_mapped["smoker"] == 1) | (df_mapped["bmi"] >= 32.0)
    ).astype(int)
    df_mapped["lab_inflammation_flag"] = (
        (df_mapped["smoker"] == 1) | (children >= 4)
    ).astype(int)
    df_mapped["lab_iron_flag"] = ((children >= 3) & (df_mapped["gender"] == "F")).astype(int)
    df_mapped["lab_thyroid_flag"] = (
        (df_mapped["gender"] == "F") & (df_mapped["age"] >= 45.0)
    ).astype(int)
    df_mapped["lab_bone_flag"] = (df_mapped["age"] >= 60.0).astype(int)
    df_mapped["lab_vitamin_flag"] = (
        (df_mapped["avg_daily_steps"] < 4200) | (region == "northeast")
    ).astype(int)

    charges = df["prediction"].astype(float).clip(lower=0.0)
    positive_charges = charges[charges > 0]
    charge_scale = float(positive_charges.median()) if not positive_charges.empty else 1.0
    charge_signal = (charges / max(charge_scale, 1.0)).clip(0.20, 5.0)

    proxy_loss_ratio = (
        0.10
        + charge_signal * 0.62
        + age_risk * 0.18
        + bmi_risk * 0.18
        + df_mapped["smoker"] * 0.32
        + children * 0.02
    )
    df_mapped["loss_ratio"] = np.clip(
        proxy_loss_ratio * rng.lognormal(mean=0.0, sigma=0.10, size=len(df)),
        0.10,
        6.0,
    )
    return df_mapped


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
        ["Employee_ID", "Weight_Based_Premium_INR"]
    ]

    if "Weight_Based_Premium_INR" not in df2.columns:
        raise KeyError(
            f"Expected 'Weight_Based_Premium_INR' in {EXCEL_FILES['weight']} "
            "but column was not found. Check Excel file schema."
        )

    joined = df1.merge(df2, on="Employee_ID", how="inner")
    print(f"  File 1: {len(df1):,} rows | File 2: {len(df2):,} rows | Joined: {len(joined):,} rows")

    return map_employee_excel_dataframe(joined)


def _parse_clinical_note(text: str) -> dict:
    """Extract structured fields from one clinical discharge note."""
    import re

    idx = text.find("### Instruction:")
    end = text.find("### Response:")
    if idx > -1:
        text = text[idx + len("### Instruction:"):end if end > -1 else None].strip()

    def flag(*patterns) -> int:
        return int(any(re.search(p, text, re.IGNORECASE) for p in patterns))

    age = 45.0
    for pat in (
        r"(\d{1,3})[- ]year[s]?[- ]old",
        r"\bAge:\s*(\d{1,3})",
        r"\bage[d]?\s+(\d{1,3})\b",
        r"\b(\d{1,3})[- ]yo\b",
    ):
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            if 0 < value < 120:
                age = float(value)
                break

    female_hits = len(re.findall(r"\b(female|woman|women|she\b|her\b)", text, re.IGNORECASE))
    male_hits = len(re.findall(r"\b(male|man\b|men\b|he\b|his\b)", text, re.IGNORECASE))
    gender = "F" if female_hits > male_hits else "M"

    bmi = 26.0
    match = re.search(r"\bBMI\s*(?:of\s*|=\s*|:\s*)?(\d{1,2}(?:\.\d)?)\b", text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        if 10 < value < 70:
            bmi = value

    smoker = flag(r"\bsmok(?:er|ing|ed)\b", r"\bcurrent smoker\b", r"\btobacco\b")
    diabetic = flag(r"\bdiabet(?:es|ic|ics)\b", r"\bDM\b", r"\binsulin[- ]dependent\b", r"\bT2DM\b", r"\bT1DM\b")
    hypertension = flag(r"\bhypertension\b", r"\bhigh blood pressure\b", r"\bHTN\b")
    cancer = flag(r"\bcancer\b", r"\bmalignant\b", r"\bcarcinoma\b", r"\blymphoma\b", r"\bleukemia\b", r"\bneoplasm\b", r"\btumou?r\b")
    heart_dis = flag(r"\bcardiac\b", r"\bheart failure\b", r"\bmyocardial infarction\b", r"\bcoronary\b", r"\batrial fibr", r"\bangina\b")
    renal = flag(r"\brenal failure\b", r"\bkidney failure\b", r"\bCKD\b", r"\bdialysis\b", r"\bnephrop", r"\bcreatinine elevated\b")
    liver_dis = flag(r"\bliver failure\b", r"\bhepat(?:itis|ic encephalopathy|orenal)\b", r"\bcirrhosis\b", r"\belevated.*(?:AST|ALT|LFT)\b", r"\bbilirubin\b")
    respiratory = flag(r"\bCOPD\b", r"\basthma\b", r"\bARDS\b", r"\bpneumonia\b", r"\brespiratory failure\b", r"\bmechanical ventilation\b")
    sepsis = flag(r"\bsepsis\b", r"\bseptic shock\b", r"\bbacteremia\b")
    stroke = flag(r"\bstroke\b", r"\bcerebral infarct\b", r"\bTIA\b", r"\bischemic.*brain\b")
    mental = flag(r"\bdepression\b", r"\banxiety disorder\b", r"\bschizophrenia\b", r"\bbipolar\b", r"\bpsychiat")
    osteo = flag(r"\bosteoporosis\b", r"\bosteopenia\b", r"\bone fracture\b", r"\bfragility fracture\b")
    anemia = flag(r"\banemia\b", r"\banaemia\b", r"\biron deficiency\b", r"\bhemoglobin\b.*\blow\b")
    thyroid_dis = flag(r"\bhypothyroid\b", r"\bhyperthyroid\b", r"\bthyroid\b")
    vitamin_def = flag(r"\bvitamin D deficiency\b", r"\bvitamin B12\b", r"\bvitamin deficiency\b")

    chronic_conditions = [
        diabetic,
        hypertension,
        cancer,
        heart_dis,
        renal,
        liver_dis,
        respiratory,
        sepsis,
        stroke,
        mental,
        osteo,
        anemia,
        thyroid_dis,
    ]
    chronic_count = sum(chronic_conditions)

    icu = flag(r"\bICU\b", r"\bintensive care unit\b", r"\bcritical care\b")
    ventilated = flag(r"\bmechanical ventilation\b", r"\bintubat", r"\bventilat")
    hospitalized_count = 1 + icu
    visit_count = min(2 + chronic_count + icu * 2, 10)

    avg_spo2 = 97.0
    for pat in (
        r"(?:oxygen saturation|SpO2|O2 sat)[^0-9]*(\d{2,3})%",
        r"(\d{2,3})%\s*to\s*(\d{2,3})%",
    ):
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            value = float(match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1))
            if 70 <= value <= 100:
                avg_spo2 = value
                break

    age_risk = max(age - 18, 0) / 80 * 0.4
    condition_risk = chronic_count * 0.08
    serious_risk = (
        cancer * 0.30
        + icu * 0.20
        + renal * 0.18
        + heart_dis * 0.15
        + sepsis * 0.15
        + ventilated * 0.15
        + stroke * 0.12
        + liver_dis * 0.10
        + respiratory * 0.08
    )
    lifestyle_risk = smoker * 0.10 + (max(bmi - 30, 0) / 10) * 0.10
    loss_ratio = 0.20 + age_risk + condition_risk + serious_risk + lifestyle_risk

    return {
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "smoker": smoker,
        "diabetic": diabetic,
        "hypertension": hypertension,
        "chronic_count": float(chronic_count),
        "avg_daily_steps": None,
        "step_volatility": None,
        "avg_resting_hr": None,
        "hr_trend": None,
        "avg_active_mins": None,
        "avg_sleep_hours": None,
        "avg_spo2": avg_spo2,
        "visit_count": float(visit_count),
        "hospitalized_count": float(hospitalized_count),
        "lab_heart_flag": int(heart_dis),
        "lab_diabetes_flag": int(diabetic),
        "lab_kidney_flag": int(renal),
        "lab_liver_flag": int(liver_dis),
        "lab_inflammation_flag": int(sepsis or respiratory),
        "lab_iron_flag": int(anemia),
        "lab_thyroid_flag": int(thyroid_dis),
        "lab_bone_flag": int(osteo or age > 60),
        "lab_vitamin_flag": int(vitamin_def),
        "loss_ratio": loss_ratio,
        "_severity": age_risk + condition_risk + serious_risk,
    }


def map_clinical_notes_hf_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse clinical-note HF rows and synthesize missing telemetry."""
    rng = np.random.default_rng(RANDOM_STATE)
    records = [_parse_clinical_note(row["text"]) for _, row in df.iterrows()]
    mapped = pd.DataFrame(records)

    severity = np.clip(mapped["_severity"].values, 0, 1.2)
    health = np.clip(1.0 - severity / 1.2, 0.0, 1.0)
    noise = lambda scale, size=len(mapped): rng.normal(0, scale, size)

    mapped["avg_daily_steps"] = np.clip(health * 9000 + 1000 + noise(600), 1000, 15000)
    mapped["step_volatility"] = np.clip((1 - health) * 1400 + 100 + noise(150), 50, 3000)
    mapped["avg_resting_hr"] = np.clip(65 + (1 - health) * 22 + noise(3), 45, 110)
    mapped["hr_trend"] = (rng.random(len(mapped)) - 0.5) * 6
    mapped["avg_active_mins"] = np.clip(health * 55 + 5 + noise(8), 0, 90)
    mapped["avg_sleep_hours"] = np.clip(6.0 + health * 2.0 + noise(0.5), 3, 10)
    mapped["avg_spo2"] = np.clip(mapped["avg_spo2"] + noise(0.3), 80, 100)
    mapped.drop(columns=["_severity"], inplace=True)

    lr_noise = rng.lognormal(0, 0.25, len(mapped))
    mapped["loss_ratio"] = np.clip(mapped["loss_ratio"] * lr_noise, 0.10, 6.0)
    return mapped


def load_from_huggingface(dataset_name: str = HF_DATASET_NAME):
    """Map a supported Hugging Face dataset into the Aegis feature schema."""
    print(f"Loading dataset from Hugging Face ({dataset_name})...")
    try:
        from datasets import load_dataset
    except ImportError:
        raise RuntimeError("'datasets' package not found. Install with: pip install datasets") from None

    ds = load_dataset(dataset_name)
    split = list(ds.keys())[0]
    raw = ds[split].to_pandas()
    schema = infer_hf_schema(raw)

    print(f"  Loaded {len(raw):,} rows from split '{split}' as {schema}")
    if schema == "underwriting_tabular":
        print("  Mapping structured underwriting rows...")
        df = map_underwriting_hf_dataframe(raw)
    elif schema == "insurance_charges":
        print("  Mapping insurance-charge rows...")
        df = map_insurance_charge_hf_dataframe(raw)
    elif schema == "company_profiles":
        raise RuntimeError(
            "This dataset contains company profile metadata, not employee health or claim targets. "
            "It cannot be used to train the current underwriting risk model."
        )
    else:
        print("  Parsing clinical notes...")
        df = map_clinical_notes_hf_dataframe(raw)

    print(
        f"  loss_ratio  mean={df['loss_ratio'].mean():.3f}  "
        f"std={df['loss_ratio'].std():.3f}  "
        f"p5={df['loss_ratio'].quantile(0.05):.3f}  "
        f"p95={df['loss_ratio'].quantile(0.95):.3f}"
    )
    return df


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


def load_and_prepare(
    dataset_mode: str = DEFAULT_DATA_MODE,
    return_source_counts: bool = False,
    hf_dataset_name: str = HF_DATASET_NAME,
):
    df, source_counts = load_training_dataframe(dataset_mode, hf_dataset_name=hf_dataset_name)

    df = engineer_features(df)
    X, y, feature_names = get_feature_matrix(df)
    print(f"  {X.shape[1]} features prepared: {feature_names}")

    y_strata = pd.qcut(y, q=4, labels=False, duplicates="drop")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y_strata
    )
    result = (X_train, X_test, y_train, y_test, feature_names)
    if return_source_counts:
        return result + (source_counts,)
    return result


def objective(trial, X_train, y_train):
    """Optuna objective - minimize MAE via 3-fold CV."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "gamma": trial.suggest_float("gamma", 0, 5),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 5),
        "reg_lambda": trial.suggest_float("reg_lambda", 0, 5),
        "random_state": RANDOM_STATE,
        "verbosity": 0,
        "tree_method": "hist",
    }
    model = xgb.XGBRegressor(**params)
    scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=3,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    return -scores.mean()


def _build_run_name(dataset_mode: str, hf_dataset_name: str) -> str:
    """Derive a meaningful MLflow run name from the data sources used."""
    hf_slug = hf_dataset_name.split("/")[-1].replace("-", "_").replace(".", "_")
    if dataset_mode == "local":
        return "xgb_local_csv"
    if dataset_mode == "hf":
        return f"xgb_hf_{hf_slug}"
    if dataset_mode == "excel":
        return "xgb_excel"
    if dataset_mode == "excel-hf":
        return f"xgb_excel+hf_{hf_slug}"
    if dataset_mode == "both":
        return f"xgb_local+hf_{hf_slug}"
    return f"xgb_local+{hf_slug}"


def tune_and_train(
    X_train,
    y_train,
    X_test,
    y_test,
    feature_names,
    dataset_mode=DEFAULT_DATA_MODE,
    source_counts=None,
    hf_dataset_name: str = HF_DATASET_NAME,
):
    print("\n[1/3] Tuning hyperparameters with Optuna...")
    study = optuna.create_study(direction="minimize", study_name="aegis_xgb")
    study.optimize(
        lambda t: objective(t, X_train, y_train),
        n_trials=N_OPTUNA_TRIALS,
        show_progress_bar=True,
    )
    print(f"\n  Best CV MAE: {study.best_value:.4f}")
    print(f"  Best params: {study.best_params}")

    print("\n[2/3] Training final model with best params...")
    best_params = study.best_params.copy()
    best_params["n_estimators"] = 2000
    best_params.update(
        {
            "random_state": RANDOM_STATE,
            "verbosity": 0,
            "tree_method": "hist",
            "early_stopping_rounds": 50,
        }
    )

    val_size = int(len(X_train) * 0.10)
    X_tr, X_val = X_train[:-val_size], X_train[-val_size:]
    y_tr, y_val = y_train[:-val_size], y_train[-val_size:]

    configure_mlflow()
    run_name = _build_run_name(dataset_mode, hf_dataset_name)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(best_params)
        mlflow.log_param("optuna_trials", N_OPTUNA_TRIALS)
        mlflow.log_param("target", "loss_ratio_log")
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("dataset_mode", dataset_mode)
        mlflow.log_param("hf_dataset_name", hf_dataset_name)
        if source_counts:
            for source_name, row_count in source_counts.items():
                mlflow.log_param(f"rows_{source_name}", row_count)

        model = xgb.XGBRegressor(**best_params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        print(f"  Best iteration: {model.best_iteration}")
        mlflow.log_param("best_iteration", model.best_iteration)

        train_preds = model.predict(X_train)
        test_preds = model.predict(X_test)
        metrics = {
            "train_mae": mean_absolute_error(y_train, train_preds),
            "test_mae": mean_absolute_error(y_test, test_preds),
            "train_rmse": np.sqrt(mean_squared_error(y_train, train_preds)),
            "test_rmse": np.sqrt(mean_squared_error(y_test, test_preds)),
            "train_r2": r2_score(y_train, train_preds),
            "test_r2": r2_score(y_test, test_preds),
        }
        for name, value in metrics.items():
            mlflow.log_metric(name, value)

        print("\n  Metrics:")
        for key, value in metrics.items():
            print(f"    {key:12s} {value:.4f}")

        print("\n[3/3] Calibrating HRS scorer...")
        scorer = HRSScorer()
        scorer.fit(train_preds)
        mlflow.log_metric("hrs_p05", scorer.p05)
        mlflow.log_metric("hrs_p95", scorer.p95)

        model_path = ARTIFACTS / "xgb_model.pkl"
        scorer_path = ARTIFACTS / "hrs_scorer.pkl"
        feats_path = ARTIFACTS / "feature_names.pkl"

        joblib.dump(model, model_path)
        joblib.dump(scorer.to_dict(), scorer_path)
        joblib.dump(feature_names, feats_path)

        mlflow.log_artifact(str(model_path), artifact_path="model")
        mlflow.log_artifact(str(scorer_path), artifact_path="model")
        mlflow.log_artifact(str(feats_path), artifact_path="model")

        print(f"\n  Saved: {model_path}")
        print(f"  Saved: {scorer_path}")
        print(f"  Saved: {feats_path}")
        print(f"  MLflow run: {run.info.run_id}")

    return model, scorer, metrics


def sanity_check(model, scorer, X_test, y_test, feature_names):
    print("\n[Sanity check on 5 test predictions]")
    preds_log = model.predict(X_test[:5])
    preds_actual = np.expm1(preds_log)
    actual_log = y_test[:5]
    actual = np.expm1(actual_log)
    hrs_scores = scorer.score_batch(preds_log)

    print(f"  {'Pred LR':>10s} {'Actual LR':>10s} {'HRS':>6s} {'Band':>10s}")
    for pred_lr, actual_lr, hrs in zip(preds_actual, actual, hrs_scores):
        print(f"  {pred_lr:10.3f} {actual_lr:10.3f} {hrs:6.1f} {scorer.risk_band(hrs):>10s}")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Train Aegis AI underwriting model")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-local",
        action="store_true",
        help="Load data from the local CSV only",
    )
    group.add_argument(
        "--use-hf",
        dest="use_hf",
        action="store_true",
        help=f"Load data from Hugging Face ({HF_DATASET_NAME}) only",
    )
    group.add_argument(
        "--use-hf-dataset",
        dest="use_hf",
        action="store_true",
        help="Alias for --use-hf",
    )
    group.add_argument(
        "--use-both",
        action="store_true",
        help="Combine local CSV and Hugging Face rows into one training run",
    )
    group.add_argument(
        "--no-hf",
        action="store_true",
        help="Alias for --use-local",
    )
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
    parser.add_argument(
        "--hf-dataset",
        default=HF_DATASET_NAME,
        help="Hugging Face dataset ID to load for HF-based training",
    )
    return parser


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


def main(argv=None):
    configure_stdout()
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    dataset_mode = resolve_dataset_mode(args)

    X_train, X_test, y_train, y_test, feature_names, source_counts = load_and_prepare(
        dataset_mode=dataset_mode,
        return_source_counts=True,
        hf_dataset_name=args.hf_dataset,
    )
    model, scorer, metrics = tune_and_train(
        X_train,
        y_train,
        X_test,
        y_test,
        feature_names,
        dataset_mode=dataset_mode,
        source_counts=source_counts,
        hf_dataset_name=args.hf_dataset,
    )
    sanity_check(model, scorer, X_test, y_test, feature_names)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
