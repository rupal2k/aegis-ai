"""Tests for premium calibration logic."""
import numpy as np
import pandas as pd
import pytest


def _make_corporate_df():
    """Minimal corporate quotes dataframe for testing."""
    return pd.DataFrame({
        "industry":                             ["Construction", "Automotive", "Agriculture",
                                                 "Construction", "IT", "IT", "Automotive"],
        "region":                               ["South", "North", "East", "North", "South", "West", "East"],
        "sum_assured_lakhs":                    [4.0, 7.0, 2.0, 10.0, 5.0, 20.0, 3.0],
        "estimated_annual_premium_per_employee_inr": [25000, 28000, 18000, 30000, 22000, 35000, 27000],
    })


def test_compute_industry_multipliers_returns_dict():
    from ml_engine.training.calibrate_premium import compute_industry_multipliers
    result = compute_industry_multipliers(_make_corporate_df())
    assert isinstance(result, dict)
    assert "Construction" in result
    assert "IT" in result


def test_compute_industry_multipliers_normalised_near_one():
    from ml_engine.training.calibrate_premium import compute_industry_multipliers
    result = compute_industry_multipliers(_make_corporate_df())
    values = list(result.values())
    # At least one value should be close to 1.0 (the median industry)
    assert any(abs(v - 1.0) < 0.3 for v in values)


def test_compute_region_multipliers_keys():
    from ml_engine.training.calibrate_premium import compute_region_multipliers
    result = compute_region_multipliers(_make_corporate_df())
    assert set(result.keys()) == {"South", "North", "East", "West"}


def test_compute_region_multipliers_all_positive():
    from ml_engine.training.calibrate_premium import compute_region_multipliers
    result = compute_region_multipliers(_make_corporate_df())
    assert all(v > 0 for v in result.values())


def test_compute_sum_assured_multipliers_bands():
    from ml_engine.training.calibrate_premium import compute_sum_assured_multipliers
    result = compute_sum_assured_multipliers(_make_corporate_df())
    assert set(result.keys()) == {"1-3L", "4-7L", "8-15L", "15L+"}


def test_compute_sum_assured_multipliers_base_band_near_one():
    from ml_engine.training.calibrate_premium import compute_sum_assured_multipliers
    result = compute_sum_assured_multipliers(_make_corporate_df())
    # 4-7L is the normalisation band — should be exactly 1.0
    assert result["4-7L"] == pytest.approx(1.0)
