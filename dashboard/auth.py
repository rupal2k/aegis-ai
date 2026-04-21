"""Dashboard authentication — bcrypt-hashed passwords, JWT-backed sessions."""
import time
import streamlit as st
import httpx
import os

API_BASE = os.environ.get("AEGIS_API_URL", "http://localhost:8000")
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes idle


def login_form():
    """Renders login form. Returns user dict if authenticated."""
    st.markdown(
        "<p style='text-align:center;color:#6e6e73;font-size:15px;margin-bottom:24px;'>"
        "Sign in to continue</p>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        email  = st.text_input("Email")
        pwd    = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in", use_container_width=True)

    if submit:
        token_data = _fetch_token(email.lower().strip(), pwd)
        if token_data:
            st.session_state["token"]       = token_data["access_token"]
            st.session_state["user"]        = _decode_token_claims(token_data["access_token"])
            st.session_state["last_active"] = time.time()
            st.rerun()
        else:
            st.error("Invalid credentials.")

    return st.session_state.get("user")


def check_session():
    """Call at the top of every page — clears session if idle > 30 min."""
    last = st.session_state.get("last_active")
    if last and (time.time() - last) > SESSION_TIMEOUT_SECONDS:
        st.session_state.clear()
        st.warning("Session expired. Please sign in again.")
        st.stop()
    if "last_active" in st.session_state:
        st.session_state["last_active"] = time.time()


def logout_button():
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def get_auth_headers() -> dict:
    """Returns Authorization header for API calls."""
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


# ── internals ────────────────────────────────────────────────────────────────

def _fetch_token(email: str, password: str) -> dict | None:
    try:
        r = httpx.post(
            f"{API_BASE}/auth/token",
            data={"username": email, "password": password},
            timeout=10.0,
        )
        if r.status_code == 200:
            return r.json()
    except httpx.RequestError:
        pass
    return None


def _decode_token_claims(token: str) -> dict:
    """Decode JWT payload without verifying sig (dashboard is read-only display)."""
    import base64, json
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}
