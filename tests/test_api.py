"""End-to-end API tests using FastAPI TestClient."""
import os
import pytest
from fastapi.testclient import TestClient
from ingestion.main import app


def _db_available() -> bool:
    """True only when PostgreSQL is reachable (i.e. running inside Docker)."""
    url = os.environ.get("DATABASE_URL", "")
    if not url or "db" in url.split("@")[-1].split(":")[0]:
        # Docker service-name host — won't resolve from the host machine
        return False
    try:
        import psycopg2
        psycopg2.connect(url)
        return True
    except Exception:
        return False

requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not reachable from host")

client = TestClient(app)


def _auth_headers(email: str = "underwriter@safenet.com", password: str = "demo123") -> dict:
    """Get JWT auth headers via the TestClient (no network round-trip)."""
    r = client.post("/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# Module-level cached headers so the rate limiter isn't hit per test.
_UW_HEADERS   = None
_HR_HEADERS   = None

def _uw_headers() -> dict:
    global _UW_HEADERS
    if _UW_HEADERS is None:
        _UW_HEADERS = _auth_headers("underwriter@safenet.com", "demo123")
    return _UW_HEADERS

def _hr_headers(company: str = "COMP_001") -> dict:
    global _HR_HEADERS
    if _HR_HEADERS is None:
        email = "hr@technova.com" if company == "COMP_001" else "hr@bharatsteel.com"
        _HR_HEADERS = _auth_headers(email, "demo123")
    return _HR_HEADERS


# ── Public endpoints ──────────────────────────────────────────────────────────

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
    body = r.json()
    assert "database" in body
    # "reachable" in Docker+Postgres; "unreachable" in TestClient+SQLite env
    assert body["database"] in ("reachable", "unreachable")


# ── Ingest — validation (no auth needed to verify 422, auth needed for 404/201)

def test_wearable_rejects_invalid_month():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_001",
        "month": 15,
        "steps": 8000,
    }, headers=_uw_headers())
    assert r.status_code == 422

def test_wearable_rejects_extreme_hr():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_001",
        "month": 5,
        "restingHR": 300,
    }, headers=_uw_headers())
    assert r.status_code == 422

@requires_db
def test_wearable_rejects_unknown_company():
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "EMP_99999",
        "company_id": "COMP_999",
        "month": 5,
        "steps": 8000,
        "restingHR": 68,
    }, headers=_uw_headers())
    assert r.status_code == 404

@requires_db
def test_company_upload_happy_path():
    r = client.post("/ingest/company", json={
        "company_id": "COMP_001",
        "employees": [{
            "external_employee_id": "NEW_EMP_0001",
            "age": 34, "gender": "M", "bmi": 24.5,
            "smoker": False, "diabetic": False, "hypertension": False,
            "job_category": "desk"
        }]
    }, headers=_uw_headers())
    assert r.status_code == 201
    assert r.json()["records_stored"] == 1

@requires_db
def test_list_companies_underwriter_sees_all():
    """Underwriter role must receive the full company list (≥1 row)."""
    r = client.get("/companies", headers=_uw_headers())
    assert r.status_code == 200
    assert len(r.json()) >= 1


@requires_db
def test_list_companies_hr_admin_sees_only_own():
    """hr_admin must see exactly their own company, not all companies."""
    r = client.get("/companies", headers=_hr_headers("COMP_001"))
    assert r.status_code == 200
    companies = r.json()
    assert len(companies) == 1
    assert companies[0]["company_id"] == "COMP_001"


@requires_db
def test_list_companies_requires_auth():
    r = client.get("/companies")
    assert r.status_code == 401


@requires_db
def test_wearable_happy_path():
    client.post("/ingest/company", json={
        "company_id": "COMP_001",
        "employees": [{
            "external_employee_id": "WEARABLE_TEST_EMP",
            "age": 30, "gender": "F", "bmi": 22.0,
            "smoker": False, "diabetic": False, "hypertension": False,
            "job_category": "desk"
        }]
    }, headers=_uw_headers())
    r = client.post("/ingest/wearable", json={
        "external_employee_id": "WEARABLE_TEST_EMP",
        "company_id": "COMP_001",
        "month": 6,
        "steps": 9500,
        "restingHR": 65,
        "sleepHours": 7.5,
    }, headers=_uw_headers())
    assert r.status_code == 201
    assert r.json()["status"] == "success"
