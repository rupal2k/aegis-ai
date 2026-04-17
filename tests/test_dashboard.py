"""Tests for Phase 5 — dashboard backend endpoints and helpers."""
import pytest
import httpx
from dashboard.auth import DEMO_USERS
from dashboard.pdf_report import generate_underwriting_report

BASE = "http://localhost:8000"


def _server_up():
    try:
        httpx.get(f"{BASE}/health", timeout=3).raise_for_status()
        return True
    except Exception:
        return False


requires_server = pytest.mark.skipif(not _server_up(), reason="API server not running")


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_underwriter_credentials(self):
        u = DEMO_USERS["underwriter@safenet.com"]
        assert u["password"] == "demo123"
        assert u["role"] == "underwriter"
        assert "company_id" not in u

    def test_hr_technova_has_company_id(self):
        u = DEMO_USERS["hr@technova.com"]
        assert u["role"] == "hr_admin"
        assert u["company_id"] == "COMP_001"

    def test_hr_bharatsteel_has_company_id(self):
        u = DEMO_USERS["hr@bharatsteel.com"]
        assert u["role"] == "hr_admin"
        assert u["company_id"] == "COMP_002"

    def test_invalid_user_not_in_dict(self):
        assert DEMO_USERS.get("fake@example.com") is None

    def test_wrong_password_fails(self):
        u = DEMO_USERS["underwriter@safenet.com"]
        assert u["password"] != "wrongpass"


# ── Companies endpoint ────────────────────────────────────────────────────────

@requires_server
class TestCompaniesEndpoint:
    def test_list_companies_count(self):
        r = httpx.get(f"{BASE}/companies")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 20

    def test_list_companies_fields(self):
        r = httpx.get(f"{BASE}/companies")
        company = r.json()[0]
        for field in ["company_id", "company_name", "industry", "city",
                      "employee_count", "base_premium"]:
            assert field in company, f"Missing field: {field}"

    def test_company_employees_comp001(self):
        r = httpx.get(f"{BASE}/companies/COMP_001/employees")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0

    def test_company_employees_fields(self):
        r = httpx.get(f"{BASE}/companies/COMP_001/employees")
        emp = r.json()[0]
        for field in ["employee_id", "age", "gender", "bmi", "smoker",
                      "loss_ratio", "job_category"]:
            assert field in emp, f"Missing field: {field}"

    def test_company_employees_unknown_company(self):
        r = httpx.get(f"{BASE}/companies/COMP_999/employees")
        assert r.status_code == 200
        assert r.json() == []


# ── Underwriter portfolio ─────────────────────────────────────────────────────

@requires_server
class TestUnderwriterPortfolio:
    def test_all_companies_predictable(self):
        companies = httpx.get(f"{BASE}/companies").json()
        errors = []
        for c in companies:
            try:
                r = httpx.get(f"{BASE}/predict/company/{c['company_id']}")
                r.raise_for_status()
            except Exception as e:
                errors.append(f"{c['company_id']}: {e}")
        assert errors == [], f"Prediction failed for: {errors}"

    def test_premium_all_companies(self):
        companies = httpx.get(f"{BASE}/companies").json()
        for c in companies:
            pred = httpx.get(f"{BASE}/predict/company/{c['company_id']}").json()
            prem = httpx.post(f"{BASE}/predict/premium",
                              json={"base_premium": float(c["base_premium"]),
                                    "hrs": pred["mean_hrs"]}).json()
            assert "adjusted_premium" in prem
            assert "zone" in prem


# ── HR view ───────────────────────────────────────────────────────────────────

@requires_server
class TestHRView:
    def test_hr_company_prediction(self):
        pred = httpx.get(f"{BASE}/predict/company/COMP_001").json()
        assert pred["employee_count"] > 0
        assert 0 <= pred["mean_hrs"] <= 100
        total = (pred["low_risk_pct"] + pred["moderate_risk_pct"] +
                 pred["high_risk_pct"] + pred["critical_risk_pct"])
        assert 99.0 < total < 101.0

    def test_hr_employees_data_types(self):
        rows = httpx.get(f"{BASE}/companies/COMP_001/employees").json()
        for emp in rows[:5]:
            assert isinstance(emp["age"], int)
            assert isinstance(emp["bmi"], float)
            assert isinstance(emp["loss_ratio"], float)


# ── Wellness ROI ──────────────────────────────────────────────────────────────

@requires_server
class TestWellnessROI:
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
            }).json()
            assert roi["annual_savings"] >= prev_savings
            prev_savings = roi["annual_savings"]

    def test_zero_improvement_zero_savings(self):
        roi = httpx.post(f"{BASE}/predict/wellness-roi", json={
            "base_premium": 1_000_000.0,
            "current_hrs": 50.0,
            "projected_hrs_after_program": 50.0,
        }).json()
        assert roi["annual_savings"] == 0.0

    def test_crossing_zone_boundary(self):
        roi = httpx.post(f"{BASE}/predict/wellness-roi", json={
            "base_premium": 1_000_000.0,
            "current_hrs": 75.0,
            "projected_hrs_after_program": 25.0,
        }).json()
        assert roi["current_zone"] == "loading"
        assert roi["projected_zone"] == "discount"
        assert roi["annual_savings"] > 0


# ── PDF report ────────────────────────────────────────────────────────────────

@requires_server
class TestPDFReport:
    def _get_data(self):
        pred = httpx.get(f"{BASE}/predict/company/COMP_001").json()
        prem = httpx.post(f"{BASE}/predict/premium",
                          json={"base_premium": 920000.0,
                                "hrs": pred["mean_hrs"]}).json()
        company_data = {**pred, "company_name": "TechNova", "company_id": "COMP_001"}
        return company_data, prem

    def test_pdf_is_valid_bytes(self):
        company_data, prem = self._get_data()
        pdf = generate_underwriting_report(company_data, prem)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_drivers(self):
        company_data, prem = self._get_data()
        assert len(company_data.get("top_risk_drivers", [])) > 0
        pdf = generate_underwriting_report(company_data, prem)
        assert pdf[:4] == b"%PDF"

    def test_pdf_empty_drivers_still_works(self):
        company_data, prem = self._get_data()
        company_data["top_risk_drivers"] = []
        pdf = generate_underwriting_report(company_data, prem)
        assert pdf[:4] == b"%PDF"
