"""Tests for the prediction API endpoints."""
from fastapi.testclient import TestClient
from ingestion.main import app

client = TestClient(app)


HEALTHY_EMP = {
    "age": 28, "gender": "F", "bmi": 22.5,
    "smoker": False, "diabetic": False, "hypertension": False,
    "avg_daily_steps": 9500, "step_volatility": 600,
    "avg_resting_hr": 62, "hr_trend": 0,
    "avg_active_mins": 55, "avg_sleep_hours": 7.5, "avg_spo2": 98,
    "visit_count": 1, "hospitalized_count": 0,
}

HIGH_RISK_EMP = {
    "age": 58, "gender": "M", "bmi": 34.5,
    "smoker": True, "diabetic": True, "hypertension": True,
    "avg_daily_steps": 2800, "step_volatility": 1800,
    "avg_resting_hr": 88, "hr_trend": 0.9,
    "avg_active_mins": 8, "avg_sleep_hours": 5.5, "avg_spo2": 94,
    "visit_count": 9, "hospitalized_count": 2,
}


def test_predict_employee_healthy():
    r = client.post("/predict/employee", json=HEALTHY_EMP)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["health_risk_score"] <= 100
    assert body["risk_band"] in ["Low", "Moderate", "High", "Critical"]
    assert len(body["top_drivers"]) == 5

def test_predict_employee_high_risk():
    r = client.post("/predict/employee", json=HIGH_RISK_EMP)
    assert r.status_code == 200
    body = r.json()
    assert body["health_risk_score"] > 50

def test_healthy_lower_hrs_than_high_risk():
    r_healthy = client.post("/predict/employee", json=HEALTHY_EMP).json()
    r_high    = client.post("/predict/employee", json=HIGH_RISK_EMP).json()
    assert r_healthy["health_risk_score"] < r_high["health_risk_score"]

def test_predict_employee_validates_bmi():
    bad = {**HEALTHY_EMP, "bmi": 200}
    r = client.post("/predict/employee", json=bad)
    assert r.status_code == 422

def test_predict_company_happy_path():
    r = client.get("/predict/company/COMP_001")
    assert r.status_code == 200
    body = r.json()
    assert body["employee_count"] > 0
    assert 0 <= body["mean_hrs"] <= 100
    total_pct = (body["low_risk_pct"] + body["moderate_risk_pct"]
                 + body["high_risk_pct"] + body["critical_risk_pct"])
    assert 99.0 < total_pct < 101.0

def test_predict_company_unknown():
    r = client.get("/predict/company/COMP_999")
    assert r.status_code == 404

def test_predict_premium_discount():
    r = client.post("/predict/premium", json={"base_premium": 100000, "hrs": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["zone"] == "discount"
    assert body["adjusted_premium"] < 100000

def test_predict_premium_loading():
    r = client.post("/predict/premium", json={"base_premium": 100000, "hrs": 85})
    assert r.status_code == 200
    body = r.json()
    assert body["zone"] == "loading"
    assert body["adjusted_premium"] > 100000

def test_wellness_roi_positive():
    r = client.post("/predict/wellness-roi", json={
        "base_premium": 1000000,
        "current_hrs": 75,
        "projected_hrs_after_program": 45,
    })
    assert r.status_code == 200
    assert r.json()["annual_savings"] > 0

def test_shap_drivers_have_explanations():
    r = client.post("/predict/employee", json=HEALTHY_EMP)
    drivers = r.json()["top_drivers"]
    for d in drivers:
        assert "explanation" in d
        assert len(d["explanation"]) > 5
