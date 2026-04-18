"""Aegis AI — B2B Dashboard entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from dashboard.auth import login_form, logout_button
from dashboard import underwriter_view, hr_view
from dashboard.currency import sidebar_selector

st.set_page_config(
    page_title="Aegis AI — Underwriting Platform",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Page background */
.stApp { background-color: #0d0d0f; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1c1c1e;
    border-right: 1px solid #3a3a3c;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #1c1c1e;
    border: 1px solid #3a3a3c;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] {
    color: #f5f5f7 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #aeaeb2 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

/* Tabs */
[data-testid="stTabs"] button {
    font-size: 14px;
    font-weight: 500;
    color: #aeaeb2;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f5f5f7;
}

/* Divider */
hr { border-color: #3a3a3c; }

/* Headings */
h1 { font-weight: 700; letter-spacing: -0.5px; color: #f5f5f7; }
h2 { font-weight: 600; color: #f5f5f7; }
h3 { font-weight: 600; color: #f5f5f7; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* Containers with border */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #1c1c1e;
    border-color: #3a3a3c !important;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


def main():
    user = st.session_state.get("user")

    if not user:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                "<h1 style='text-align:center;color:#0071e3;margin-bottom:4px;'>Aegis AI</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align:center;color:#6e6e73;font-size:16px;margin-bottom:32px;'>"
                "Dynamic Group Insurance Underwriting Platform</p>",
                unsafe_allow_html=True,
            )
            login_form()
        return

    with st.sidebar:
        st.markdown(f"**{user['name']}**")
        st.caption(user["org"])
        st.caption(f"Role: {user['role']}")
        st.divider()
        sidebar_selector()
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
