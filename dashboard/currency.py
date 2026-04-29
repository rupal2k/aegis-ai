"""Currency conversion and formatting helpers."""
import streamlit as st

# Rates relative to INR (1 INR = X foreign currency).
# Approximate mid-market rates — updated manually or swap for a live FX API.
CURRENCIES: dict[str, dict] = {
    "INR": {"symbol": "\u20b9",  "name": "Indian Rupee",       "rate": 1.0,        "suffix": ""},
    "USD": {"symbol": "$",       "name": "US Dollar",           "rate": 0.01198,    "suffix": ""},
    "EUR": {"symbol": "\u20ac",  "name": "Euro",                "rate": 0.01105,    "suffix": ""},
    "GBP": {"symbol": "\u00a3",  "name": "British Pound",       "rate": 0.00943,    "suffix": ""},
    "AED": {"symbol": "AED\u00a0","name": "UAE Dirham",         "rate": 0.04400,    "suffix": ""},
    "SGD": {"symbol": "S$",      "name": "Singapore Dollar",    "rate": 0.01613,    "suffix": ""},
    "AUD": {"symbol": "A$",      "name": "Australian Dollar",   "rate": 0.01852,    "suffix": ""},
    "JPY": {"symbol": "\u00a5",  "name": "Japanese Yen",        "rate": 1.8519,     "suffix": ""},
    "CAD": {"symbol": "C$",      "name": "Canadian Dollar",     "rate": 0.01634,    "suffix": ""},
    "CHF": {"symbol": "CHF\u00a0","name": "Swiss Franc",        "rate": 0.01076,    "suffix": ""},
}


def active_code() -> str:
    return st.session_state.get("currency", "INR")


def convert(inr_value: float, code: str | None = None) -> float:
    code = code or active_code()
    return inr_value * CURRENCIES[code]["rate"]


def fmt(inr_value: float, code: str | None = None) -> str:
    """Return a formatted currency string, e.g. '$1,200' or '¥120,000'."""
    code = code or active_code()
    c = CURRENCIES[code]
    val = inr_value * c["rate"]
    # JPY and similar: no decimal places; others: none for large amounts
    decimals = 2 if val < 1000 and code not in ("JPY",) else 0
    return f"{c['symbol']}{val:,.{decimals}f}"


def fmt_crore(inr_value: float, code: str | None = None) -> str:
    """Format large portfolio totals with a sensible suffix per currency."""
    code = code or active_code()
    val = inr_value * CURRENCIES[code]["rate"]
    if code == "INR":
        return f"\u20b9{val/1e7:.2f}\u00a0Cr"
    elif code == "JPY":
        return f"\u00a5{val/1e8:.2f}\u00a0Bn"
    elif val >= 1e9:
        return f"{CURRENCIES[code]['symbol']}{val/1e9:.2f}\u00a0Bn"
    elif val >= 1e6:
        return f"{CURRENCIES[code]['symbol']}{val/1e6:.2f}\u00a0M"
    else:
        return f"{CURRENCIES[code]['symbol']}{val:,.0f}"


def sidebar_selector() -> str:
    """Render the currency dropdown in the sidebar and persist to session state."""
    options = list(CURRENCIES.keys())
    current = st.session_state.get("currency", "INR")
    idx = options.index(current) if current in options else 0
    chosen = st.selectbox(
        "Display currency",
        options=options,
        index=idx,
        format_func=lambda c: f"{c}  —  {CURRENCIES[c]['name']}",
        key="currency_selector",
    )
    st.session_state["currency"] = chosen
    st.markdown(
        '<div style="font-size:11px;color:#333333;margin-top:2px;'
        'font-family:Inter,system-ui,sans-serif;">Rates are approximate mid-market.</div>',
        unsafe_allow_html=True,
    )
    return chosen
