"""Tests for Phase 5 — dashboard backend endpoints and helpers."""
import os
import pytest
import httpx
from dashboard.pdf_report import generate_underwriting_report

BASE = "http://localhost:8000"


def _server_up():
    try:
        httpx.get(f"{BASE}/health", timeout=3).raise_for_status()
        return True
    except Exception:
        return False


requires_server = pytest.mark.skipif(not _server_up(), reason="API server not running")


def _get_token(email: str = "underwriter@safenet.com", password: str = "demo123") -> str:
    r = httpx.post(f"{BASE}/auth/token", data={"username": email, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

@requires_server
class TestAuth:
    def test_underwriter_login_succeeds(self):
        token = _get_token("underwriter@safenet.com", "demo123")
        assert token

    def test_hr_login_succeeds(self):
        token = _get_token("hr@technova.com", "demo123")
        assert token

    def test_invalid_credentials_rejected(self):
        r = httpx.post(f"{BASE}/auth/token",
                       data={"username": "fake@example.com", "password": "wrong"},
                       timeout=10)
        assert r.status_code == 401

    def test_unauthenticated_request_rejected(self):
        r = httpx.get(f"{BASE}/companies")
        assert r.status_code == 401


# ── Companies endpoint ────────────────────────────────────────────────────────

@requires_server
class TestCompaniesEndpoint:
    def setup_method(self):
        self.token = _get_token()
        self.headers = _auth_headers(self.token)

    def test_list_companies_count(self):
        r = httpx.get(f"{BASE}/companies", headers=self.headers)
        assert r.status_code == 200
        assert len(r.json()) == 20

    def test_list_companies_fields(self):
        r = httpx.get(f"{BASE}/companies", headers=self.headers)
        company = r.json()[0]
        for field in ["company_id", "company_name", "industry", "city",
                      "employee_count", "base_premium"]:
            assert field in company, f"Missing field: {field}"

    def test_company_employees_comp001(self):
        r = httpx.get(f"{BASE}/companies/COMP_001/employees", headers=self.headers)
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_company_employees_fields(self):
        r = httpx.get(f"{BASE}/companies/COMP_001/employees", headers=self.headers)
        emp = r.json()[0]
        for field in ["employee_id", "age", "gender", "bmi", "smoker",
                      "loss_ratio", "job_category"]:
            assert field in emp, f"Missing field: {field}"

    def test_hr_admin_cannot_access_other_company(self):
        hr_token = _get_token("hr@technova.com", "demo123")
        r = httpx.get(f"{BASE}/companies/COMP_002/employees",
                      headers=_auth_headers(hr_token))
        assert r.status_code == 403

    def test_hr_admin_can_access_own_company(self):
        hr_token = _get_token("hr@technova.com", "demo123")
        r = httpx.get(f"{BASE}/companies/COMP_001/employees",
                      headers=_auth_headers(hr_token))
        assert r.status_code == 200


# ── Underwriter portfolio ─────────────────────────────────────────────────────

@requires_server
class TestUnderwriterPortfolio:
    def setup_method(self):
        self.headers = _auth_headers(_get_token())

    def test_all_companies_predictable(self):
        companies = httpx.get(f"{BASE}/companies", headers=self.headers).json()
        errors = []
        for c in companies:
            try:
                r = httpx.get(f"{BASE}/predict/company/{c['company_id']}",
                               headers=self.headers)
                r.raise_for_status()
            except Exception as e:
                errors.append(f"{c['company_id']}: {e}")
        assert errors == [], f"Prediction failed for: {errors}"

    def test_premium_all_companies(self):
        companies = httpx.get(f"{BASE}/companies", headers=self.headers).json()
        for c in companies:
            pred = httpx.get(f"{BASE}/predict/company/{c['company_id']}",
                              headers=self.headers).json()
            prem = httpx.post(f"{BASE}/predict/premium",
                              json={"base_premium": float(c["base_premium"]),
                                    "hrs": pred["mean_hrs"]},
                              headers=self.headers).json()
            assert "adjusted_premium" in prem
            assert "zone" in prem


# ── HR view ───────────────────────────────────────────────────────────────────

@requires_server
class TestHRView:
    def setup_method(self):
        self.headers = _auth_headers(_get_token())

    def test_hr_company_prediction(self):
        pred = httpx.get(f"{BASE}/predict/company/COMP_001",
                         headers=self.headers).json()
        assert pred["employee_count"] > 0
        assert 0 <= pred["mean_hrs"] <= 100
        total = (pred["low_risk_pct"] + pred["moderate_risk_pct"] +
                 pred["high_risk_pct"] + pred["critical_risk_pct"])
        assert 99.0 < total < 101.0

    def test_hr_employees_data_types(self):
        rows = httpx.get(f"{BASE}/companies/COMP_001/employees",
                         headers=self.headers).json()
        for emp in rows[:5]:
            assert isinstance(emp["age"], int)
            assert isinstance(emp["bmi"], float)
            assert isinstance(emp["loss_ratio"], float)


# ── Wellness ROI ──────────────────────────────────────────────────────────────

@requires_server
class TestWellnessROI:
    def setup_method(self):
        self.headers = _auth_headers(_get_token())

    def test_savings_increase_with_improvement(self):
        base_premium = 1_000_000.0
        current_hrs = 60.0
        prev_savings = 0.0
        for improvement in [5, 10, 15, 20]:
            projected = current_hrs - improvement
            roi = httpx.post(f"{BASE}/predict/wellness-roi", json={
                "base_premium": base_premium,
                "current_hrs": current_hrs,
                "projected_hrs_after_program": projected,
            }, headers=self.headers).json()
            assert roi["annual_savings"] >= prev_savings
            prev_savings = roi["annual_savings"]

    def test_zero_improvement_zero_savings(self):
        roi = httpx.post(f"{BASE}/predict/wellness-roi", json={
            "base_premium": 1_000_000.0,
            "current_hrs": 50.0,
            "projected_hrs_after_program": 50.0,
        }, headers=self.headers).json()
        assert roi["annual_savings"] == 0.0

    def test_crossing_zone_boundary(self):
        roi = httpx.post(f"{BASE}/predict/wellness-roi", json={
            "base_premium": 1_000_000.0,
            "current_hrs": 75.0,
            "projected_hrs_after_program": 25.0,
        }, headers=self.headers).json()
        assert roi["current_zone"] == "loading"
        assert roi["projected_zone"] == "discount"
        assert roi["annual_savings"] > 0


# ── PDF report ────────────────────────────────────────────────────────────────

@requires_server
class TestPDFReport:
    def setup_method(self):
        self.headers = _auth_headers(_get_token())

    def _get_data(self):
        pred = httpx.get(f"{BASE}/predict/company/COMP_001",
                         headers=self.headers).json()
        prem = httpx.post(f"{BASE}/predict/premium",
                          json={"base_premium": 920000.0, "hrs": pred["mean_hrs"]},
                          headers=self.headers).json()
        company_data = {**pred, "company_name": "TechNova", "company_id": "COMP_001"}
        return company_data, prem

    def test_pdf_is_valid_bytes(self):
        company_data, prem = self._get_data()
        pdf = generate_underwriting_report(company_data, prem)
        assert isinstance(pdf, bytes) and len(pdf) > 1000 and pdf[:4] == b"%PDF"

    def test_pdf_empty_drivers_still_works(self):
        company_data, prem = self._get_data()
        company_data["top_risk_drivers"] = []
        pdf = generate_underwriting_report(company_data, prem)
        assert pdf[:4] == b"%PDF"
