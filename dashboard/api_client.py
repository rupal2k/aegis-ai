"""HTTP client wrapper for the Aegis AI backend API."""
import httpx
import streamlit as st

API_BASE = "http://localhost:8000"


def _get(path: str, **params):
    with httpx.Client(timeout=15.0) as client:
        r = client.get(f"{API_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


def _post(path: str, json_body: dict):
    with httpx.Client(timeout=15.0) as client:
        r = client.post(f"{API_BASE}{path}", json=json_body)
        r.raise_for_status()
        return r.json()


@st.cache_data(ttl=60)
def list_companies():
    return _get("/companies")


@st.cache_data(ttl=60)
def get_company_prediction(company_id: str):
    return _get(f"/predict/company/{company_id}")


@st.cache_data(ttl=60)
def get_company_employees(company_id: str):
    return _get(f"/companies/{company_id}/employees")


def predict_employee(features: dict):
    return _post("/predict/employee", features)


def calculate_premium(base_premium: float, hrs: float):
    return _post("/predict/premium", {"base_premium": base_premium, "hrs": hrs})


def calculate_wellness_roi(base_premium: float, current_hrs: float, projected_hrs: float):
    return _post("/predict/wellness-roi", {
        "base_premium":                base_premium,
        "current_hrs":                 current_hrs,
        "projected_hrs_after_program": projected_hrs,
    })
