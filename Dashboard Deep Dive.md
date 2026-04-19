# Dashboard Deep Dive — Aegis AI

**Last Updated**: 2026-04-18  
**Phase**: 5 ✅  
**Source Files**: `dashboard/app.py`, `dashboard/auth.py`, `dashboard/api_client.py`, `dashboard/underwriter_view.py`, `dashboard/hr_view.py`, `dashboard/currency.py`, `dashboard/pdf_report.py`

---

## Overview

The Streamlit dashboard is the **human-facing layer** of Aegis AI. It serves two audiences:

| Role | User | View | Purpose |
|------|------|------|---------|
| Underwriter | SafeNet Insurance | Underwriter Console | See all 20 companies, ranked by risk, generate reports |
| HR Manager | TechNova / Bharat Steel | Workforce Health Dashboard | See their company's health profile, plan wellness programs |

---

## 1. Application Entry Point (`dashboard/app.py`)

### The sys.path Fix

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

This is the **first line of real code** in the file. Without it, every import fails.

**Why it's needed**: When Streamlit runs `dashboard/app.py`, it adds the script's own directory (`dashboard/`) to `sys.path`. So `from dashboard.auth import ...` would try to find `dashboard/dashboard/auth.py` — which doesn't exist.

The fix inserts the **project root** (`c:\Rupalprojects\aegis-ai\`) at position 0 in `sys.path`. Now `from dashboard.auth` correctly resolves to `c:\Rupalprojects\aegis-ai\dashboard\auth.py`.

**Rule**: Any time Streamlit is run from a subdirectory, add this fix.

### Page Configuration

```python
st.set_page_config(
    page_title="Aegis AI — Underwriting Platform",
    page_icon="shield",
    layout="wide",           # Crucial: fills full browser width
    initial_sidebar_state="expanded",
)
```

`layout="wide"` doubles the usable screen area for charts and tables. Without it, Streamlit centres content in a narrow column — fine for forms, terrible for portfolio dashboards.

### Light Theme CSS (Safe Selectors)

```css
/* Safe: targets container only */
[data-testid="stMetric"] {
    background-color: #f5f5f7;
    border: 1px solid #e0e0e5;
    border-radius: 10px;
    padding: 16px 20px;
}

/* NEVER do this — hides metric values */
/* .stMetric label { color: grey; } */
```

**The CSS Rule**: Only target `[data-testid="..."]` selectors. Streamlit's `data-testid` attributes are stable across versions. Class selectors (`.stMetric`, `.stButton`) are internal implementation details that change without notice.

**The Bug That Led to This Rule**: Phase 5 bug BUG-004 — metric values went invisible because `.stMetric label` matched all child spans, including the value span. See [[Bug Log#BUG-004]].

### Authentication Gate

```python
def main():
    user = st.session_state.get("user")
    
    if not user:
        # Show login form centred in column 2 of 3
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_form()
        return  # Exit early — nothing else renders

    # User is logged in: show sidebar + route to correct view
    with st.sidebar:
        sidebar_selector()   # Currency picker
        logout_button()

    if user["role"] == "underwriter":
        underwriter_view.render()
    elif user["role"] == "hr_admin":
        hr_view.render()
```

The pattern `if not user: return` is important — it prevents any authenticated content from rendering. The entire main() function short-circuits at the login gate.

---

## 2. Authentication (`dashboard/auth.py`)

### Demo User Store

```python
USERS = {
    "underwriter@safenet.com": {
        "name": "Priya Mehta",
        "org":  "SafeNet Insurance",
        "role": "underwriter",
        "password": "demo123",
    },
    "hr@technova.com": {
        "name": "Rahul Sharma",
        "org":  "TechNova Solutions",
        "role": "hr_admin",
        "company_id": "COMP_001",
        "password": "demo123",
    },
    "hr@bharatsteel.com": {
        "name": "Sunita Patel",
        "org":  "Bharat Steel Works",
        "role": "hr_admin",
        "company_id": "COMP_002",
        "password": "demo123",
    },
}
```

Three users cover both roles. Password is stored in plaintext because this is a demo — Phase 6 will replace with OAuth + bcrypt hashing.

### Login Flow

```python
def login_form():
    with st.form("login"):
        email    = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit   = st.form_submit_button("Sign in")

    if submit:
        user = USERS.get(email.lower().strip())
        if user and user["password"] == password:
            session_user = {k: v for k, v in user.items() if k != "password"}
            st.session_state["user"] = session_user  # Store without password
            st.rerun()  # Re-render: user is now logged in → show dashboard
        else:
            st.error("Invalid email or password")
```

**Why `st.rerun()`?** After setting `st.session_state["user"]`, Streamlit needs to re-execute `app.py` from the top. Without `st.rerun()`, the page stays on the login form even though the user is now authenticated.

**Why strip password from session?** Storing the password in `st.session_state` is a security risk (accessible via browser developer tools). Only store what's needed for UI decisions (role, name, company_id).

---

## 3. API Client (`dashboard/api_client.py`)

### Request Helpers

```python
API_BASE = "http://localhost:8000"

def _get(path: str):
    resp = httpx.get(f"{API_BASE}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()

def _post(path: str, payload: dict):
    resp = httpx.post(f"{API_BASE}{path}", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

`raise_for_status()` converts HTTP 4xx/5xx into exceptions. This propagates up to Streamlit's error display (`st.error` or uncaught exception banner) rather than silently returning bad data.

### Caching Strategy

```python
@st.cache_data(ttl=60)
def list_companies():
    return _get("/companies")

@st.cache_data(ttl=60)
def get_company_prediction(company_id: str):
    return _get(f"/predict/company/{company_id}")

@st.cache_data(ttl=60)
def get_company_employees(company_id: str):
    return _get(f"/companies/{company_id}/employees")

# NOT cached — always fresh for user input
def predict_employee(features: dict):
    return _post("/predict/employee", features)

def calculate_premium(base_premium, hrs):
    return _post("/predict/premium", {"base_premium": base_premium, "hrs": hrs})

def calculate_wellness_roi(base_premium, current_hrs, projected_hrs):
    return _post("/predict/wellness-roi", {
        "base_premium": base_premium,
        "current_hrs": current_hrs,
        "projected_hrs_after_program": projected_hrs,
    })
```

**Why are premium and wellness ROI not cached?**
These are called with user-provided inputs from sliders and number inputs. Caching would mean: "Adjust slider to 72.4 → see result. Adjust back to 72.4 → see same result (from cache, instant)." This is actually desirable — but the inputs change constantly, making the cache key (function arguments) different each time. Caching is still applied by Streamlit, but effectively misses on every call.

---

## 4. Currency Module (`dashboard/currency.py`)

### Design: INR as Universal Base

All internal values are stored and computed in INR. Conversion to display currency happens only at the moment of rendering.

```python
CURRENCIES = {
    "INR": {"symbol": "₹",    "rate": 1.0,      "name": "Indian Rupee"},
    "USD": {"symbol": "$",    "rate": 0.01198,   "name": "US Dollar"},
    "EUR": {"symbol": "€",    "rate": 0.01105,   "name": "Euro"},
    "GBP": {"symbol": "£",    "rate": 0.00943,   "name": "British Pound"},
    "AED": {"symbol": "AED ", "rate": 0.04400,   "name": "UAE Dirham"},
    "SGD": {"symbol": "S$",   "rate": 0.01613,   "name": "Singapore Dollar"},
    "AUD": {"symbol": "A$",   "rate": 0.01852,   "name": "Australian Dollar"},
    "JPY": {"symbol": "¥",    "rate": 1.8519,    "name": "Japanese Yen"},
    "CAD": {"symbol": "C$",   "rate": 0.01634,   "name": "Canadian Dollar"},
    "CHF": {"symbol": "CHF ", "rate": 0.01076,   "name": "Swiss Franc"},
}
```

### Smart Formatting

```python
def fmt(inr_value: float, code: str = None) -> str:
    code = code or active_code()
    c = CURRENCIES[code]
    val = inr_value * c["rate"]
    decimals = 2 if val < 1000 and code not in ("JPY",) else 0
    return f"{c['symbol']}{val:,.{decimals}f}"
```

**Logic**:
- Small amounts (< ₹1,000 equivalent) get 2 decimal places: `$11.32`
- Large amounts get 0 decimals: `$1,200` not `$1,200.00`
- JPY always gets 0 decimals (yen don't have cents)

```python
def fmt_crore(inr_value: float, code: str = None) -> str:
    val = inr_value * CURRENCIES[code]["rate"]
    if code == "INR":
        return f"₹{val/1e7:.2f} Cr"        # ₹42.50 Cr (crore)
    elif code == "JPY":
        return f"¥{val/1e8:.2f} Bn"         # ¥5.20 Bn (billion yen)
    elif val >= 1e9:
        return f"{sym}{val/1e9:.2f} Bn"     # $5.20 Bn
    elif val >= 1e6:
        return f"{sym}{val/1e6:.2f} M"      # $52.00 M
    else:
        return f"{sym}{val:,.0f}"            # $520,000
```

**Why `fmt_crore` vs `fmt`?** Portfolio totals can be enormous (₹200 Crore portfolio). Showing `₹2,000,000,000` is unreadable. Each currency has its own conventions for large numbers:
- Indian: Crore (1 Cr = 10M)
- Japanese: Billion yen (exchange rate means 1 Crore INR ≈ 180M JPY ≈ 1.8 Bn JPY)
- Western: Billions/Millions

### Session State Persistence

```python
def sidebar_selector() -> str:
    options = list(CURRENCIES.keys())
    chosen = st.selectbox("Display currency", options=options, ...)
    st.session_state["currency"] = chosen  # Persist
    return chosen
```

`st.session_state` persists across re-renders within a session. So switching from USD to EUR in the sidebar immediately updates all monetary displays in both tabs without reloading data.

---

## 5. Underwriter View (`dashboard/underwriter_view.py`)

### Data Loading

```python
with st.spinner("Loading portfolio..."):
    companies = list_companies()
    rows = []
    for c in companies:
        try:
            pred = get_company_prediction(c["company_id"])
            prem = calculate_premium(float(c["base_premium"]), pred["mean_hrs"])
            rows.append({...})
        except Exception as e:
            st.warning(f"Skipping {c['company_name']}: {e}")
```

**Error isolation**: If one company's prediction fails (e.g., no employee data), the `try/except` shows a warning and continues. The rest of the portfolio loads. Without this, one missing company crashes the entire view.

### Tab 1: Portfolio Overview

**Bar Chart (HRS by company)**:
```python
fig = px.bar(
    df.sort_values("mean_hrs"),       # Sort ascending = highest risk at top
    x="mean_hrs", y="company_name",
    color="risk_band",
    color_discrete_map=COLOR_MAP,     # iOS colors: green/orange/red/dark red
    orientation="h",                   # Horizontal bars (company names on Y)
    labels={"mean_hrs": "Health Risk Score", "company_name": ""},
    height=580,
)
fig.update_layout(
    xaxis=dict(range=[0, 100], ...),   # Always 0-100 scale
)
```

**Why horizontal bars?** Company names are long (15-20 characters). Vertical bars would overlap. Horizontal bars give each company a full-width label.

**Why sort ascending?** Top of chart = highest HRS = highest risk = most critical companies visible first (important for underwriters who scroll top-to-bottom).

**Ranked Portfolio Table** (currency-aware):
```python
code = active_code()
display_df["base_premium_fx"] = display_df["base_premium"].apply(
    lambda v: float(v) * CURRENCIES[code]["rate"])

display_df = display_df.rename(columns={
    "base_premium_fx": f"Base ({code})",     # "Base (USD)"
    "adjusted_fx":     f"Adjusted ({code})", # "Adjusted (USD)"
})
```

Column headers **include the currency code** so the user knows which currency they're viewing. Switching currency in the sidebar re-renders the table with new column headers and values.

**ProgressColumn for HRS**:
```python
st.column_config.ProgressColumn("HRS", min_value=0, max_value=100, format="%.1f")
```
Shows a visual progress bar inside the HRS column cell — 72.4 shows as a 72% filled bar, making high-risk rows visually obvious at a glance.

### Tab 2: Company Deep Dive

**Gauge Chart (HRS visualisation)**:
```python
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=pred["mean_hrs"],
    gauge={
        "axis": {"range": [0, 100]},
        "steps": [
            {"range": [0,  30], "color": "#d4f4e2"},   # Light green
            {"range": [30, 60], "color": "#fff0cc"},   # Light yellow
            {"range": [60, 80], "color": "#ffd5d3"},   # Light red
            {"range": [80,100], "color": "#f5c0be"},   # Darker red
        ],
    },
))
```

The gauge provides immediate visual context: is the needle in the green, yellow, or red zone? The coloured zones match the risk bands. Underwriters can read risk at a glance without reading the number.

**Risk Breakdown (Horizontal Bar)**:
Shows what % of the workforce is in each risk band (Low/Moderate/High/Critical). A company with 70% "High" is structurally different from one with 10% "Critical" even if both have the same mean HRS.

**Top Risk Drivers (Progress Bars)**:
```python
for i, d in enumerate(pred["top_risk_drivers"][:5], 1):
    pct = (d["importance"] / pred["top_risk_drivers"][0]["importance"]) * 100
    st.progress(
        pct / 100,
        text=f"**{i}. {d['feature']}** — importance {d['importance']:.3f}",
    )
```

Normalises all driver bars relative to the top driver (top driver = 100% width). This makes relative importance immediately visible.

**Underwriting Decision**:
```python
st.info(
    f"**Recommendation:** {prem['recommendation']}  \n"
    f"Adjusted premium: **{fmt(prem['adjusted_premium'])}** "
    f"({prem['adjustment_pct']:+.2f}% vs base {fmt(float(row['base_premium']))})"
)
```

The `+` prefix in `{prem['adjustment_pct']:+.2f}%` always shows the sign: `+12.00%` or `-7.50%`. Never ambiguous.

**PDF Generation**:
```python
pdf_bytes = generate_underwriting_report(
    {**pred, "company_name": row["company_name"], "company_id": row["company_id"]},
    prem,
    currency=active_code(),    # Pass selected currency to PDF
)
st.download_button("Download underwriting report (PDF)", data=pdf_bytes, ...)
```

The PDF is generated server-side in Python (ReportLab). The selected currency is passed so the PDF shows values in the same currency the user was viewing.

---

## 6. HR View (`dashboard/hr_view.py`)

### Company Isolation

```python
user = st.session_state["user"]
company_id = user["company_id"]   # From auth — never passed by URL

company = next((c for c in companies if c["company_id"] == company_id), None)
if not company:
    st.error("Your company was not found in the database.")
    return
```

HR managers can **only see their own company**. The company_id comes from the authenticated session (set during login), never from a URL parameter. This prevents IDOR attacks (Insecure Direct Object Reference) — an HR manager can't change `?company_id=COMP_003` to see a competitor's data.

### Top Metrics

```python
claims_inr = pred["mean_loss_ratio"] * prem["adjusted_premium"]

c1.metric("Employees",          pred["employee_count"])
c2.metric("Health risk score",  f"{pred['mean_hrs']:.1f}", pred["risk_band"])
c3.metric("Current premium",    fmt(prem["adjusted_premium"]),
          f"{prem['adjustment_pct']:+.2f}% vs book rate")
c4.metric("Annual claims est.", fmt(claims_inr))
```

**Why `mean_loss_ratio × adjusted_premium` for claims estimate?**
- `mean_loss_ratio` is the predicted ratio of (claims / premium)
- Multiplied by the actual premium = estimated claims in absolute INR
- Example: loss_ratio=0.85, premium=₹1,200,000 → claims ≈ ₹1,020,000

The delta on metric card 3 shows the adjustment relative to the "book rate" (base premium). A delta of `-7.50% vs book rate` means the company is healthy enough to get a discount.

### Tab 3: Wellness ROI Simulator

```python
current   = st.number_input("Current HRS", value=float(pred["mean_hrs"]), ...)
improvement = st.slider("HRS improvement target", 0, 40, 15, ...)
projected = max(0.0, current - improvement)

roi = calculate_wellness_roi(float(company["base_premium"]), current, projected)
```

**Design choice**: `number_input` for current HRS (editable — HR manager might want to explore hypotheticals), `slider` for improvement (bounded 0–40, intuitive for "how much can we realistically improve?").

**Waterfall Chart**:
```python
code = active_code()
rate = CURRENCIES[code]["rate"]
sym  = CURRENCIES[code]["symbol"]

wf = go.Figure(go.Waterfall(
    x=["Current premium", "Wellness savings", "Projected premium"],
    y=[roi["current_premium"] * rate,
       -roi["annual_savings"] * rate,    # Negative = savings (bar goes down)
       roi["projected_premium"] * rate],
    measure=["absolute", "relative", "total"],  # First bar from 0, second adds to it, third shows total
    decreasing={"marker": {"color": "#34c759"}}, # Green for savings
    increasing={"marker": {"color": "#ff3b30"}}, # Red for costs
    totals={"marker": {"color": ACCENT}},
    yaxis=dict(tickprefix=sym),
))
```

**Waterfall chart logic**:
- Bar 1 (absolute): Current premium — starts from 0
- Bar 2 (relative): Wellness savings — negative value means bar goes DOWN (showing savings)
- Bar 3 (total): Projected premium — automatically calculated as bar1 + bar2

The green colour for the savings bar and red for costs makes the ROI immediately clear.

---

## 7. PDF Report Generator (`dashboard/pdf_report.py`)

### Why Inline `_RATES`?

```python
_RATES = {
    "INR": (1.0,      "₹"),
    "USD": (0.01198,  "$"),
    "EUR": (0.01105,  "€"),
    ...
}
```

This is a deliberate duplication of `dashboard/currency.py`. Why?

The PDF generator runs in a Python context but **cannot import Streamlit** (no `st.session_state` available outside Streamlit context). If we imported `dashboard.currency`, it would try to access `st.session_state["currency"]` and crash.

By keeping a standalone `_RATES` dict, `pdf_report.py` has no Streamlit dependency and can be called from any Python context (API endpoint, batch job, test, etc.).

**Trade-off**: Two copies of the rate table → must update both when rates change.
**Accepted because**: Rates change infrequently (quarterly), and the tables are small.

### Report Structure

```
┌──────────────────────────────────┐
│  AEGIS AI — UNDERWRITING REPORT  │
│  Generated: 18 April 2026  | USD │
├──────────────────────────────────┤
│  Company Profile                 │
│  ├─ Company: TechNova Solutions  │
│  ├─ ID: COMP_001                 │
│  ├─ Employees: 248               │
│  └─ Report Date: 2026-04-18      │
├──────────────────────────────────┤
│  Health Risk Assessment          │
│  ├─ Mean HRS: 45.2 / 100         │
│  ├─ Risk Band: Moderate           │
│  ├─ Loss Ratio: 0.823            │
│  ├─ Low Risk: 38.2%              │
│  ├─ Moderate: 41.5%              │
│  ├─ High: 14.8%                  │
│  └─ Critical: 5.5%               │
├──────────────────────────────────┤
│  Premium Recommendation          │
│  ├─ Base Premium: $9,580         │
│  ├─ Adjusted Premium: $9,580     │
│  ├─ Adjustment: +0.00%           │
│  └─ Zone: Standard               │
├──────────────────────────────────┤
│  Recommendation text             │
├──────────────────────────────────┤
│  Top Risk Drivers                │
│  ├─ 1. health_composite: 0.412   │
│  ├─ 2. avg_resting_hr: 0.385     │
│  ├─ 3. bmi: 0.312                │
│  ├─ 4. avg_daily_steps: 0.298    │
│  └─ 5. chronic_count: 0.241      │
└──────────────────────────────────┘
```

### ReportLab Table Styling

```python
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E6F1FB")),  # Left column: light blue bg
    ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#B5D4F4")),
    ("PADDING",    (0,0), (-1,-1), 6),
]))
```

Each section uses a different colour scheme:
- Company profile: Blue (`#E6F1FB`)
- Risk assessment: Green (`#E1F5EE`)
- Premium: Yellow/amber (`#FAEEDA`)
- Risk drivers: Purple (`#EEEDFE`)

This colour-coding matches the iOS colour palette used in the Streamlit charts, creating visual consistency between the dashboard and the PDF.

---

## 8. Apple-Style Colour Palette

Used consistently across all charts and UI:
```python
COLOR_MAP = {
    "Low":      "#34c759",   # iOS green  — safe
    "Moderate": "#ff9f0a",   # iOS orange — caution
    "High":     "#ff3b30",   # iOS red    — danger
    "Critical": "#8e0000",   # Dark red   — critical
}
PLOT_BG  = "#ffffff"   # Pure white background
GRID_CLR = "#e5e5ea"   # Apple's standard light grey
FONT_CLR = "#1d1d1f"   # Apple's near-black text
ACCENT   = "#0071e3"   # Apple's standard blue (links, CTAs)
```

**Why iOS colour palette?**
- B2B users are familiar with iOS/macOS conventions
- Green/yellow/red is universally understood for risk levels
- High contrast on white backgrounds
- Accessible (meets WCAG 2.1 contrast ratios)
- Professional and clean — appropriate for insurance context

---

## 9. The Complete Render Sequence

When underwriter logs in and opens the dashboard:

```
1. app.py main() called
2. st.session_state["user"] found → skip login form
3. Sidebar renders (name, org, role, currency selector, logout)
4. user["role"] == "underwriter" → underwriter_view.render()
5. st.spinner("Loading portfolio...")
6. list_companies() → GET /companies (cached or fresh)
7. For each of 20 companies:
   a. get_company_prediction(id) → GET /predict/company/{id}
   b. calculate_premium(base_premium, mean_hrs) → POST /predict/premium
   c. Append row to list
8. pd.DataFrame(rows) → 20 × 10 DataFrame
9. Render 4 metric cards (totals)
10. Render tab1: bar chart + ranked table (currency-aware)
11. Tab2 renders only when clicked (lazy):
    a. Company selectbox
    b. get_company_prediction(selected) → cached
    c. Gauge chart, risk breakdown, drivers, recommendation
    d. PDF generation button
12. Tab3: histogram + industry table
```

---

## 10. Key Technical Decisions in Dashboard

| Decision | Choice | Why |
|----------|--------|-----|
| Horizontal bar chart | Easier to read company names | Names too long for vertical |
| Sort by HRS ascending | Highest risk at top | Underwriter sees critical cases first |
| ProgressColumn for HRS | Visual bar in table cell | Faster to scan than raw number |
| `+` sign format for pct | `f"{pct:+.2f}%"` | Always shows direction (+ or -) |
| Company ID from session | Not from URL param | Prevents IDOR attacks |
| Spinner on load | `st.spinner()` | Signals 20-company load (not frozen) |
| try/except per company | Skips failing companies | One missing company doesn't break all |
| `st.rerun()` after login | Re-execute from top | Forces auth gate re-check |

---

## Links
- [[API Layer Architecture]] — What the dashboard calls
- [[ML Engine Architecture]] — What drives the predictions
- [[Bug Log#BUG-003]] — The ModuleNotFoundError fix
- [[Bug Log#BUG-004]] — The blank metrics CSS fix
- [[Decisions & Rationale#DECISION-004]] — Why Streamlit over React
- [[Decisions & Rationale#DECISION-007]] — Why static FX rates
- [[Decisions & Rationale#DECISION-008]] — Why server-side PDF
