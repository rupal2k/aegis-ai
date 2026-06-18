"""Dashboard authentication — bcrypt-hashed passwords, JWT-backed sessions."""
import time
import streamlit as st
import httpx
import os

API_BASE = os.environ.get("AEGIS_API_URL", "http://localhost:8000")
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes idle


def login_form():
    """Renders login form. Returns user dict if authenticated."""
    saved_email = st.session_state.get("_login_email", "")

    with st.form("login_form"):
        email = st.text_input(
            "Work email",
            value=saved_email,
            placeholder="you@company.com",
        )
        pwd = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )
        submit = st.form_submit_button(
            "Sign in",
            use_container_width=True,
            type="primary",
        )

    st.caption("Forgot your password? Contact your Aegis administrator to reset it.")

    if submit:
        _email = email.strip()
        if not _email:
            st.error("Work email is required.")
            return st.session_state.get("user")
        if "@" not in _email or "." not in _email.split("@")[-1]:
            st.error("Enter a valid work email address.")
            return st.session_state.get("user")
        if not pwd:
            st.error("Password is required.")
            return st.session_state.get("user")

        # Preserve email so failed logins don't clear the field
        st.session_state["_login_email"] = _email

        with st.spinner("Signing in… (first request may take up to 30s)"):
            token_data, timed_out = _fetch_token(_email.lower(), pwd)

        if token_data:
            st.session_state["token"]       = token_data["access_token"]
            st.session_state["user"]        = _decode_token_claims(token_data["access_token"])
            st.session_state["last_active"] = time.time()
            st.session_state.pop("_login_email", None)
            st.rerun()
        elif timed_out:
            st.warning("Server is starting up — please try again in a few seconds.")
        else:
            st.error("Incorrect email or password — please try again.")

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

def _fetch_token(email: str, password: str) -> tuple[dict | None, bool]:
    try:
        r = httpx.post(
            f"{API_BASE}/auth/token",
            data={"username": email, "password": password},
            timeout=45.0,
        )
        if r.status_code == 200:
            return r.json(), False
        if r.status_code == 503:
            return None, True   # cold-starting — treat same as timeout
    except httpx.TimeoutException:
        return None, True
    except httpx.RequestError:
        pass
    return None, False


def _decode_token_claims(token: str) -> dict:
    """Decode JWT payload without verifying sig (dashboard is read-only display)."""
    import base64, json
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}
