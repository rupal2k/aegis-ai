"""Tests for the normalization pipeline."""
import pytest
from ingestion.normalizer import (
    anonymize_employee_id, normalize_wearable, normalize_clinical, clamp,
)


def test_anonymization_is_deterministic():
    assert anonymize_employee_id("EMP_00001") == anonymize_employee_id("EMP_00001")

def test_anonymization_is_unique():
    assert anonymize_employee_id("EMP_00001") != anonymize_employee_id("EMP_00002")

def test_anonymization_length():
    assert len(anonymize_employee_id("EMP_00001")) == 16

def test_clamp_basic():
    assert clamp(150, 0, 100) == 100
    assert clamp(-5,  0, 100) == 0
    assert clamp(50,  0, 100) == 50
    assert clamp(None, 0, 100) is None

def test_normalize_wearable_clips_outliers():
    payload = {
        "external_employee_id": "EMP_00001",
        "company_id": "COMP_001",
        "month": 5,
        "daily_steps": 999_999,
        "heart_rate_rest": 300,
    }
    r = normalize_wearable(payload)
    assert r["avg_daily_steps"] <= 30000
    assert r["resting_hr"] <= 110

def test_normalize_wearable_imputes_missing():
    payload = {
        "external_employee_id": "EMP_00001",
        "company_id": "COMP_001",
        "month": 5,
    }
    r = normalize_wearable(payload)
    assert r["avg_daily_steps"] == 5000
    assert r["resting_hr"] == 72
    assert r["sleep_hours"] == 7.0

def test_normalize_clinical_uppercases_icd():
    payload = {
        "external_employee_id": "EMP_00001",
        "company_id": "COMP_001",
        "month": 3,
        "event_type": "diabetes",
        "icd10_code": "e11.9",
        "claim_amount": 5000,
        "hospitalized": False,
    }
    r = normalize_clinical(payload)
    assert r["icd10_code"] == "E11.9"
    assert r["hospitalized"] == 0
    assert r["event_id"].startswith("EVT_")
