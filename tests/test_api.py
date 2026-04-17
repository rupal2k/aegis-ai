"""End-to-end API tests using FastAPI TestClient."""
from fastapi.testclient import TestClient
from ingestion.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "service" in r.json()

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_health_db():
    r = client.get("/health/db")
    assert r.status_code == 200
    assert r.json()["database"] == "reachable"

def test_wearable_rejects_unknown_company():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_999",
        "month": 5,
        "steps": 8000,
        "restingHR": 68,
    })
    assert r.status_code == 404

def test_wearable_rejects_invalid_month():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_001",
        "month": 15,
        "steps": 8000,
    })
    assert r.status_code == 422

def test_wearable_rejects_extreme_hr():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_001",
        "month": 5,
        "restingHR": 300,
    })
    assert r.status_code == 422

def test_company_upload_happy_path():
    r = client.post("/ingest/company", json={
        "company_id": "COMP_001",
        "employees": [{
            "external_employee_id": "NEW_EMP_0001",
            "age": 34, "gender": "M", "bmi": 24.5,
            "smoker": False, "diabetic": False, "hypertension": False,
            "job_category": "desk"
        }]
    })
    assert r.status_code == 201
    assert r.json()["records_stored"] == 1

def test_wearable_happy_path():
    client.post("/ingest/company", json={
        "company_id": "COMP_001",
        "employees": [{
            "external_employee_id": "WEARABLE_TEST_EMP",
            "age": 30, "gender": "F", "bmi": 22.0,
            "smoker": False, "diabetic": False, "hypertension": False,
            "job_category": "desk"
        }]
    })
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "WEARABLE_TEST_EMP",
        "company_id": "COMP_001",
        "month": 6,
        "steps": 9500,
        "restingHR": 65,
        "sleepHours": 7.5,
    })
    assert r.status_code == 201
    assert r.json()["status"] == "success"
