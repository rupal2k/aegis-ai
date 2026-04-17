"""Data normalization pipeline — converts raw input into DB-ready records."""
import hashlib
import os
from typing import Dict, Any
import pandas as pd
import numpy as np


HASH_SALT = os.environ.get("HASH_SALT", "aegis_dev_salt_2024")


def anonymize_employee_id(raw_id: str) -> str:
    """SHA-256 with salt → 16-char hash. Same input always produces same output (for joining)."""
    return hashlib.sha256(f"{HASH_SALT}{raw_id}".encode()).hexdigest()[:16]


def clamp(value, low, high):
    """Clip a numeric value into a sane range."""
    if value is None:
        return None
    return max(low, min(high, value))


def normalize_wearable(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts loose dict input → returns one clean row ready for telemetry table.
    Handles:
      - Field name aliases already resolved by Pydantic
      - Outlier clipping (sensor errors)
      - Missing-value imputation with medians
      - Unit normalization (sleep_hours as float)
    """
    record = {
        "employee_id":     anonymize_employee_id(payload["external_employee_id"]),
        "company_id":      payload["company_id"],
        "month":           int(payload["month"]),
        "avg_daily_steps": clamp(payload.get("daily_steps") or 5000, 500, 30000),
        "resting_hr":      clamp(payload.get("heart_rate_rest") or 72, 45, 110),
        "active_minutes":  clamp(payload.get("active_mins") or 30, 0, 240),
        "sleep_hours":     round(float(clamp(payload.get("sleep_hrs") or 7.0, 3.0, 12.0)), 1),
        "spo2":            round(float(clamp(payload.get("oxygen_saturation") or 97.0, 85.0, 100.0)), 1),
    }
    return record


def normalize_clinical(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Clean clinical event for storage in clinical_events table."""
    import secrets
    return {
        "event_id":     f"EVT_{secrets.token_hex(8).upper()}",
        "employee_id":  anonymize_employee_id(payload["external_employee_id"]),
        "company_id":   payload["company_id"],
        "month":        int(payload["month"]),
        "event_type":   payload["event_type"],
        "icd10_code":   payload["icd10_code"].upper().strip(),
        "claim_amount": round(float(payload["claim_amount"]), 2),
        "hospitalized": 1 if payload.get("hospitalized") else 0,
    }


def normalize_employee(company_id: str, emp: Dict[str, Any]) -> Dict[str, Any]:
    """Clean employee record for storage in employees table."""
    return {
        "employee_id":  anonymize_employee_id(emp["external_employee_id"]),
        "company_id":   company_id,
        "age":          int(clamp(emp["age"], 18, 70)),
        "gender":       emp["gender"],
        "bmi":          round(float(clamp(emp["bmi"], 10.0, 60.0)), 1),
        "smoker":       1 if emp.get("smoker") else 0,
        "diabetic":     1 if emp.get("diabetic") else 0,
        "hypertension": 1 if emp.get("hypertension") else 0,
        "job_category": emp["job_category"],
    }


def batch_normalize_wearables(payloads: list) -> pd.DataFrame:
    """Batch-normalize wearable records for bulk inserts (used in Phase 6)."""
    df = pd.DataFrame([normalize_wearable(p) for p in payloads])
    return df
