"""HTTP client wrapper for the Aegis AI backend API."""
import httpx
import streamlit as st
import os

API_BASE = os.environ.get("AEGIS_API_URL", "http://localhost:8000")

if API_BASE == "http://localhost:8000":
    st.warning(
        "AEGIS_API_URL is not configured — API calls will fail. "
        "Set this secret in your HuggingFace Space settings to the Render API URL.",
        icon="⚠️",
    )


def _headers() -> dict:
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _get(path: str, **params):
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(f"{API_BASE}{path}", params=params, headers=_headers())
            if r.status_code == 503:
                st.warning("API is starting up — please wait a moment and retry.")
                st.stop()
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        st.error("Request timed out. The API may be starting up — please retry in 30 seconds.")
        st.stop()
    except httpx.RequestError as e:
        st.error(f"Cannot reach API at {API_BASE}. Check AEGIS_API_URL secret.")
        st.stop()


def _post(path: str, json_body: dict):
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{API_BASE}{path}", json=json_body, headers=_headers())
            if r.status_code == 503:
                st.warning("API is starting up — please wait a moment and retry.")
                st.stop()
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        st.error("Request timed out. The API may be starting up — please retry in 30 seconds.")
        st.stop()
    except httpx.RequestError:
        st.error(f"Cannot reach API at {API_BASE}. Check AEGIS_API_URL secret.")
        st.stop()


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
