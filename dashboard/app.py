"""Aegis AI — B2B Dashboard entry point."""
import streamlit as st

from dashboard.auth import login_form, logout_button
from dashboard import underwriter_view, hr_view

st.set_page_config(
    page_title="Aegis AI — Underwriting Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stMetric { background-color: #F9F8F2; padding: 12px; border-radius: 8px;
            border: 0.5px solid #D3D1C7; }
.stMetric label { font-size: 13px; color: #5F5E5A; }
</style>
""", unsafe_allow_html=True)


def main():
    user = st.session_state.get("user")

    if not user:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(
                "<h1 style='text-align:center;color:#0C447C;'>Aegis AI</h1>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align:center;color:#5F5E5A;'>"
                "Dynamic Group Insurance Underwriting Platform</p>",
                unsafe_allow_html=True
            )
            login_form()
        return

    with st.sidebar:
        st.markdown(f"### {user['name']}")
        st.caption(f"{user['org']}")
        st.caption(f"Role: **{user['role']}**")
        st.divider()
        logout_button()
        st.divider()
        st.caption("Aegis AI v1.0")
        st.caption("Powered by XGBoost + SHAP")

    if user["role"] == "underwriter":
        underwriter_view.render()
    elif user["role"] == "hr_admin":
        hr_view.render()
    else:
        st.error(f"Unknown role: {user['role']}")


if __name__ == "__main__":
    main()
