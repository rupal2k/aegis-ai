"""
Aegis AI — flexible CSV normalizer for the scoring tab.

Detects and transforms three upload formats into a uniform roster of feature
dicts ready for `predict_employee`:

    1. ROSTER  — wide rows of demographics (the original schema):
         employee_id, age, gender, bmi, smoker, diabetic, hypertension, job_category, ...

    2. LAB     — long-format lab marker rows:
         report_id, unique_id, gender, lab_name, report_date, marker_code, value,
         min_value, max_value, unit, normal_range, status, risk_level

    3. ACTIVITY — wide rows of yearly health-domain status + activity metrics:
         user_id, year, Bone Health, Diabetes, Heart Health, Inflammation, Iron,
         Kidney Health, Liver Health, Thyroid Health, Vitamin Deficiency,
         step_count, steps_active_minutes, distance_in_meters, mindful_min,
         total_active_minutes

The normalizer fills any missing demographics (age/bmi/job_category/smoker/...)
with population medians derived from `data/output/training_dataset.csv` so the
underwriting model has a complete feature row to score against.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

DATASET_PATH = Path("data/output/training_dataset.csv")

Format = Literal["roster", "lab", "activity", "unknown"]

# ── Marker-code → health-domain map (LAB long-format) ────────────────────────
# Codes are normalized via _norm_code (uppercase, alphanumeric only). Add more
# aliases as new lab panels appear.
_MARKER_TO_DOMAIN: dict[str, str] = {
    # Iron / anemia
    "HB":      "iron", "HGB": "iron", "HEMOGLOBIN": "iron",
    "PCV":     "iron", "HCT": "iron", "HEMATOCRIT": "iron",
    "MCV":     "iron", "MCH": "iron", "MCHC": "iron",
    "RBC":     "iron", "FERRITIN": "iron", "IRON": "iron", "TIBC": "iron",
    # Diabetes
    "HBA1C":   "diabetes", "HBA1": "diabetes", "GHB": "diabetes",
    "FBS":     "diabetes", "FPG": "diabetes", "GLUCOSE": "diabetes",
    "RBS":     "diabetes", "PPBS": "diabetes", "OGTT": "diabetes",
    "INSULIN": "diabetes",
    # Heart / lipids
    "TC":      "heart", "CHOL": "heart", "CHOLESTEROL": "heart",
    "LDL":     "heart", "HDL": "heart", "VLDL": "heart",
    "TG":      "heart", "TRIG": "heart", "TRIGLYCERIDES": "heart",
    "TROPONIN":"heart", "CKMB": "heart", "BNP": "heart", "NTPROBNP": "heart",
    "APO":     "heart", "APOA": "heart", "APOB": "heart",
    # Liver
    "ALT":     "liver", "SGPT": "liver",
    "AST":     "liver", "SGOT": "liver",
    "ALP":     "liver", "GGT": "liver",
    "BILIRUBIN":"liver", "BILT": "liver", "BILD": "liver", "BILI": "liver",
    "ALB":     "liver", "ALBUMIN": "liver", "TPROT": "liver",
    # Kidney
    "CREATININE":"kidney", "CREA": "kidney", "CR": "kidney",
    "UREA":    "kidney", "BUN": "kidney", "EGFR": "kidney",
    "URICACID":"kidney", "UA": "kidney",
    # Thyroid
    "TSH":     "thyroid", "T3": "thyroid", "T4": "thyroid",
    "FT3":     "thyroid", "FT4": "thyroid",
    # Bone
    "CALCIUM": "bone", "CA": "bone", "PHOSPHORUS": "bone", "PHOS": "bone",
    "VITD":    "bone", "VITAMIND": "bone", "D25OH": "bone",
    # Vitamins
    "VITB12":  "vitamin", "B12": "vitamin", "FOLATE": "vitamin", "FOL": "vitamin",
    # Inflammation
    "CRP":     "inflammation", "HSCRP": "inflammation",
    "ESR":     "inflammation", "WBC": "inflammation",
    "ABAS":    "inflammation",   # absolute basophil count
    "ANEU":    "inflammation",   # absolute neutrophil count
    "ALYM":    "inflammation",
    "AMON":    "inflammation",
    "AEOS":    "inflammation",
}

# Activity wide-format → domain map (case/whitespace-insensitive)
_ACTIVITY_DOMAIN_COLUMNS: dict[str, str] = {
    "boneHealth":         "bone",
    "diabetes":           "diabetes",
    "heartHealth":        "heart",
    "inflammation":       "inflammation",
    "iron":               "iron",
    "kidneyHealth":       "kidney",
    "liverHealth":        "liver",
    "thyroidHealth":      "thyroid",
    "vitaminDeficiency":  "vitamin",
}


def _norm_code(c) -> str:
    return "".join(ch for ch in str(c).upper() if ch.isalnum())


def _norm_col(c) -> str:
    return "".join(ch for ch in str(c) if ch.isalnum())


def detect_format(df: pd.DataFrame) -> Format:
    """Return one of: 'roster' | 'lab' | 'activity' | 'unknown'."""
    cols = {_norm_col(c).lower() for c in df.columns}

    if {"markercode", "value", "uniqueid"}.issubset(cols) or {
        "markercode", "value"
    }.issubset(cols):
        return "lab"
    if "stepcount" in cols and any(
        _norm_col(d).lower() in cols for d in _ACTIVITY_DOMAIN_COLUMNS
    ):
        return "activity"
    if {"employeeid", "age", "bmi"}.issubset(cols) or {
        "employeeid", "age"
    }.issubset(cols):
        return "roster"
    return "unknown"


def _is_outofrange(status, risk_level=None) -> bool:
    s = str(status).strip().lower() if status is not None else ""
    if s in {"outofrange", "out_of_range", "abnormal", "high", "low", "critical"}:
        return True
    if risk_level is not None:
        rl = str(risk_level).strip().lower()
        if rl in {"medium", "med", "moderate", "high", "critical"}:
            return True
    return False


def _population_defaults() -> dict:
    """Median demographics from the training dataset for filling missing fields."""
    if not DATASET_PATH.exists():
        return dict(age=38, gender="M", bmi=25.0,
                    smoker=0, diabetic=0, hypertension=0,
                    job_category="desk")
    df = pd.read_csv(DATASET_PATH)
    return dict(
        age=int(df["age"].median()),
        gender=df["gender"].mode().iloc[0],
        bmi=round(float(df["bmi"].median()), 1),
        smoker=int(df["smoker"].mode().iloc[0]),
        diabetic=int(df["diabetic"].mode().iloc[0]),
        hypertension=int(df["hypertension"].mode().iloc[0]),
        job_category=df["job_category"].mode().iloc[0],
    )


def _normalize_lab(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot LAB long-format into one row per `unique_id` with lab_*_flag columns."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Tolerant column lookup
    by_norm = {_norm_col(c).lower(): c for c in df.columns}
    uid_col   = by_norm.get("uniqueid") or by_norm.get("userid") or by_norm.get("memberid")
    code_col  = by_norm.get("markercode") or by_norm.get("code")
    status_col= by_norm.get("status")
    risk_col  = by_norm.get("risklevel")
    gender_col= by_norm.get("gender") or by_norm.get("sex")

    if not uid_col or not code_col:
        raise ValueError("LAB CSV must have unique_id / user_id and marker_code columns.")

    df["_uid"]    = df[uid_col].astype(str)
    df["_domain"] = df[code_col].map(lambda c: _MARKER_TO_DOMAIN.get(_norm_code(c)))
    df["_flag"]   = df.apply(
        lambda r: _is_outofrange(
            r[status_col] if status_col else None,
            r[risk_col]   if risk_col   else None,
        ),
        axis=1,
    )

    domains = ["heart", "inflammation", "diabetes", "kidney", "liver",
               "iron", "thyroid", "bone", "vitamin"]

    pivot_rows = []
    for uid, sub in df.groupby("_uid"):
        flags = {f"lab_{d}_flag": 0 for d in domains}
        for d in domains:
            if (sub.loc[sub["_domain"] == d, "_flag"]).any():
                flags[f"lab_{d}_flag"] = 1

        gender = (
            sub[gender_col].dropna().astype(str).str.upper().str[0].iloc[0]
            if gender_col and not sub[gender_col].dropna().empty
            else None
        )
        if gender not in ("M", "F", "O"):
            gender = None

        # Heuristic: if HBA1C / FBS / glucose markers are flagged → user is diabetic
        diabetic_inferred = int(flags["lab_diabetes_flag"])
        # Hypertension: if BP-related lipid/heart markers are flagged
        hypertension_inferred = int(flags["lab_heart_flag"]) if not gender else 0

        row = {"employee_id": uid, "gender": gender, **flags,
               "diabetic_inferred": diabetic_inferred,
               "hypertension_inferred": hypertension_inferred}
        pivot_rows.append(row)

    return pd.DataFrame(pivot_rows)


def _normalize_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Map Activity wide-format into one row per user_id with lab flags + telemetry."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    by_norm = {_norm_col(c).lower(): c for c in df.columns}

    uid_col = by_norm.get("userid") or by_norm.get("uniqueid") or by_norm.get("memberid")
    if not uid_col:
        raise ValueError("Activity CSV must have user_id / unique_id / member_id column.")

    out_rows = []
    for _, r in df.iterrows():
        flags = {
            "lab_heart_flag":         0, "lab_inflammation_flag": 0,
            "lab_diabetes_flag":      0, "lab_kidney_flag":       0,
            "lab_liver_flag":         0, "lab_iron_flag":         0,
            "lab_thyroid_flag":       0, "lab_bone_flag":         0,
            "lab_vitamin_flag":       0,
        }
        for src_key, domain in _ACTIVITY_DOMAIN_COLUMNS.items():
            col = by_norm.get(src_key.lower())
            if col and _is_outofrange(r.get(col)):
                flags[f"lab_{domain}_flag"] = 1

        steps   = r.get(by_norm.get("stepcount", ""))
        active  = r.get(by_norm.get("totalactiveminutes", "")) or r.get(
            by_norm.get("stepsactiveminutes", "")
        )

        out_rows.append({
            "employee_id":      str(r[uid_col]),
            **flags,
            "avg_daily_steps":  float(steps)  if pd.notna(steps)  else None,
            "avg_active_mins":  float(active) / 365.0 if pd.notna(active) else None,
            "diabetic_inferred":     int(flags["lab_diabetes_flag"]),
            "hypertension_inferred": int(flags["lab_heart_flag"]),
        })

    return pd.DataFrame(out_rows)


# Telemetry defaults — kept identical to upload_view._TELEMETRY_DEFAULTS so
# scoring matches whether or not wearable fields are present.
_TELEMETRY_DEFAULTS = {
    "avg_daily_steps":    6000,
    "step_volatility":    500.0,
    "avg_resting_hr":     72.0,
    "hr_trend":           0.0,
    "avg_active_mins":    30.0,
    "avg_sleep_hours":    7.0,
    "avg_spo2":           97.0,
    "visit_count":        0,
    "hospitalized_count": 0,
}


def to_feature_records(
    df: pd.DataFrame,
    fmt: Format,
    *,
    user_overrides: dict | None = None,
) -> tuple[list[dict], dict]:
    """Return (records_for_predict_employee, report).

    `user_overrides` lets the caller substitute defaults (e.g. average age=38)
    set in the UI. Anything not in overrides falls back to dataset medians.
    """
    user_overrides = user_overrides or {}
    defaults = {**_population_defaults(), **user_overrides}

    if fmt == "lab":
        canonical = _normalize_lab(df)
        source = "lab"
    elif fmt == "activity":
        canonical = _normalize_activity(df)
        source = "activity"
    else:
        canonical = df.copy()
        canonical.columns = [c.strip().lower() for c in canonical.columns]
        source = "roster"

    records: list[dict] = []
    filled = set()

    for _, r in canonical.iterrows():
        # Demographics — preferred from CSV; fallback to defaults
        gender = r.get("gender")
        if isinstance(gender, str):
            gender = gender.upper().strip()[:1]
        if gender not in ("M", "F", "O"):
            gender = defaults["gender"]
            filled.add("gender")

        age = r.get("age")
        try:
            age = int(age)
            if not 18 <= age <= 70:
                raise ValueError
        except (TypeError, ValueError):
            age = defaults["age"]
            filled.add("age")

        bmi = r.get("bmi")
        try:
            bmi = float(bmi)
            if not 10 <= bmi <= 60:
                raise ValueError
        except (TypeError, ValueError):
            bmi = defaults["bmi"]
            filled.add("bmi")

        job = r.get("job_category")
        if not isinstance(job, str) or job.lower() not in ("desk", "field", "manual"):
            job = defaults["job_category"]
            filled.add("job_category")
        else:
            job = job.lower()

        smoker       = _coerce_int(r.get("smoker"),       defaults["smoker"],       filled, "smoker")
        diabetic     = _coerce_int(
            r.get("diabetic"),
            r.get("diabetic_inferred", defaults["diabetic"]),
            filled,
            "diabetic",
        )
        hypertension = _coerce_int(
            r.get("hypertension"),
            r.get("hypertension_inferred", defaults["hypertension"]),
            filled,
            "hypertension",
        )

        eid = r.get("employee_id") or r.get("unique_id") or f"AUTO_{len(records):05d}"

        feat = {
            "age":          age,
            "gender":       gender,
            "bmi":          bmi,
            "smoker":       bool(smoker),
            "diabetic":     bool(diabetic),
            "hypertension": bool(hypertension),
            "job_category": job,
            "chronic_count": int(diabetic) + int(hypertension),
            **_TELEMETRY_DEFAULTS,
        }

        # Override telemetry with provided values if the activity uploader gave us any
        if pd.notna(r.get("avg_daily_steps")) if "avg_daily_steps" in r.index else False:
            feat["avg_daily_steps"] = float(r["avg_daily_steps"])
        if pd.notna(r.get("avg_active_mins")) if "avg_active_mins" in r.index else False:
            feat["avg_active_mins"] = float(r["avg_active_mins"])

        records.append({"employee_id": str(eid), "_features": feat})

    return records, {
        "source": source,
        "rows": len(records),
        "filled_with_defaults": sorted(filled),
        "defaults_used": defaults,
    }


def _coerce_int(value, fallback, filled: set, name: str) -> int:
    bool_map = {"true": 1, "false": 0, "yes": 1, "no": 0,
                "1": 1, "0": 0, "y": 1, "n": 0,
                "1.0": 1, "0.0": 0, "t": 1, "f": 0}
    if value is None or (isinstance(value, float) and np.isnan(value)):
        filled.add(name)
        return int(fallback) if fallback is not None else 0
    s = str(value).strip().lower()
    if s in bool_map:
        return bool_map[s]
    try:
        return 1 if float(s) > 0 else 0
    except ValueError:
        filled.add(name)
        return int(fallback) if fallback is not None else 0
