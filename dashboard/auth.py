"""Simple demo auth for the dashboard."""
import streamlit as st

DEMO_USERS = {
    "underwriter@safenet.com": {
        "password": "demo123",
        "role":     "underwriter",
        "name":     "Priya Sharma",
        "org":      "SafeNet Insurance",
    },
    "hr@technova.com": {
        "password": "demo123",
        "role":     "hr_admin",
        "name":     "Raj Mehta",
        "org":      "TechNova Solutions",
        "company_id": "COMP_001",
    },
    "hr@bharatsteel.com": {
        "password": "demo123",
        "role":     "hr_admin",
        "name":     "Anjali Iyer",
        "org":      "Bharat Steel Works",
        "company_id": "COMP_002",
    },
}


def login_form():
    """Renders login form. Returns user dict if authenticated."""
    st.markdown("### Aegis AI — Sign in")
    st.caption("B2B Dynamic Group Insurance Underwriting Platform")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="underwriter@safenet.com")
        pwd   = st.text_input("Password", type="password", placeholder="demo123")
        submit = st.form_submit_button("Sign in", use_container_width=True)

    if submit:
        user = DEMO_USERS.get(email.lower().strip())
        if user and user["password"] == pwd:
            st.session_state["user"] = {**user, "email": email}
            st.rerun()
        else:
            st.error("Invalid credentials. Try the demo accounts below.")

    with st.expander("Demo credentials"):
        st.code(
            "Underwriter:  underwriter@safenet.com / demo123\n"
            "HR Manager:   hr@technova.com        / demo123\n"
            "HR Manager:   hr@bharatsteel.com     / demo123"
        )

    return st.session_state.get("user")


def logout_button():
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
