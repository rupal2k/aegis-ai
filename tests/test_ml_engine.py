"""Tests for the ML engine components."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from ml_engine.features           import engineer_features, get_feature_matrix, FEATURE_COLUMNS
from ml_engine.scorer             import HRSScorer
from ml_engine.premium_calculator import calculate_premium_adjustment, calculate_wellness_roi


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "employee_id":   ["a","b","c"],
        "company_id":    ["COMP_001"]*3,
        "age":           [30, 45, 55],
        "gender":        ["M","F","M"],
        "bmi":           [22.0, 28.5, 31.0],
        "smoker":        [0, 0, 1],
        "diabetic":      [0, 0, 1],
        "hypertension":  [0, 1, 1],
        "chronic_count": [0, 1, 2],
        "job_category":  ["desk","field","manual"],
        "avg_daily_steps":    [9500, 6000, 3500],
        "step_volatility":    [800, 1200, 1500],
        "avg_resting_hr":     [62, 72, 85],
        "hr_trend":           [0.1, 0.3, 0.8],
        "avg_active_mins":    [60, 35, 15],
        "avg_sleep_hours":    [7.5, 6.5, 5.5],
        "avg_spo2":           [98, 97, 95],
        "visit_count":        [1, 3, 7],
        "hospitalized_count": [0, 0, 2],
        "total_claims":       [500, 4000, 25000],
        "premium_share":      [12000]*3,
        "loss_ratio":         [0.04, 0.33, 2.08],
        "high_risk":          [0, 0, 1],
    })


def test_engineer_features_adds_derived_columns(sample_df):
    result = engineer_features(sample_df)
    assert "activity_score"   in result.columns
    assert "health_composite" in result.columns
    assert "loss_ratio_log"   in result.columns

def test_activity_score_higher_for_healthy(sample_df):
    result = engineer_features(sample_df)
    assert result["activity_score"].iloc[0] > result["activity_score"].iloc[2]

def test_health_composite_higher_for_sick(sample_df):
    result = engineer_features(sample_df)
    assert result["health_composite"].iloc[2] > result["health_composite"].iloc[0]

def test_feature_matrix_shape(sample_df):
    result = engineer_features(sample_df)
    X, y, features = get_feature_matrix(result)
    assert X.shape[0] == 3
    assert X.shape[1] == len(features)
    assert y is not None

def test_hrs_scorer_bounds():
    scorer = HRSScorer()
    scorer.fit(np.array([0.1, 0.5, 1.0, 2.0, 3.0, 4.0]))
    assert 0 <= scorer.score(0.1) <= 100
    assert 0 <= scorer.score(4.0) <= 100
    assert scorer.score(5.0) == 100  # capped
    assert scorer.score(-1.0) == 0   # floored

def test_hrs_risk_bands():
    scorer = HRSScorer()
    scorer.fit(np.linspace(0, 5, 100))
    assert scorer.risk_band(20) == "Low"
    assert scorer.risk_band(45) == "Moderate"
    assert scorer.risk_band(70) == "High"
    assert scorer.risk_band(90) == "Critical"

def test_premium_discount_zone():
    r = calculate_premium_adjustment(100_000, 20)
    assert r["zone"] == "discount"
    assert r["adjusted_premium"] < 100_000

def test_premium_standard_zone():
    r = calculate_premium_adjustment(100_000, 50)
    assert r["zone"] == "standard"
    assert r["adjusted_premium"] == 100_000

def test_premium_loading_zone():
    r = calculate_premium_adjustment(100_000, 85)
    assert r["zone"] == "loading"
    assert r["adjusted_premium"] > 100_000

def test_wellness_roi_positive_savings():
    r = calculate_wellness_roi(100_000, current_hrs=75, projected_hrs_after_program=45)
    assert r["annual_savings"] > 0
    assert r["hrs_improvement"] == 30

def test_model_artifact_exists():
    assert Path("ml_engine/artifacts/xgb_model.pkl").exists(), \
        "Run training first: python -m ml_engine.training.train"
    assert Path("ml_engine/artifacts/hrs_scorer.pkl").exists()
