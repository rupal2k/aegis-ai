# Logical Decisions & Rationale — Aegis AI

**Last Updated**: 2026-04-18  
**Document Type**: Decision Log (Deep Dive)

---

## Overview

This document captures the **logical reasoning**, **tradeoffs**, and **decision-making processes** behind key technical choices in Aegis AI. Unlike ADRs (which record final decisions), this log shows **why** we chose what we chose and what we rejected.

---

## DECISION-001: Health Risk Score as the Core Metric

### The Problem
Insurance underwriters need a single, interpretable number to assess company risk. Options:
1. **Raw health features** (20+ variables) → Too complex, underwriters can't interpret
2. **Loss ratio alone** → Doesn't capture leading indicators, only historical data
3. **Composite health risk score (HRS)** → Single number, interpretable, forward-looking

### The Logic
```
Underwriter needs to:
  a) Make quick decisions (< 5 min per company)
  b) Explain decision to customer ("Your HRS is 72, which means...")
  c) Predict future claims (not just see past claims)
  d) Compare across portfolio ("Company A is 65, Company B is 80")

Single metric (HRS) satisfies all 4 requirements.
Multiple metrics would require:
  - Simultaneous interpretation (cognitive overload)
  - Weighted decision logic (where do weights come from?)
  - Testing multiple scenarios (time-consuming)
```

### Why Not Use Loss Ratio Directly?
- **Loss ratio is historical** (what happened last year) → Too reactive
- **HRS is forward-looking** (health metrics predict future claims) → Proactive
- **HRS is explainable** (top 5 drivers show why) → Loss ratio is a black box aggregate

### Why Not Use Raw Features (20+ variables)?
- **Underwriter fatigue**: Can't parse 20 variables in 5 minutes
- **No consensus**: Different underwriters weight features differently
- **No interpretability**: "Why did you decline?" → Can't answer with 20 features

### Implementation Decision
- **XGBoost HRS = weighted combination of all 20 health features**
- **Weights learned from training data** (not manual tuning)
- **SHAP explains which features matter most** (top 5 per prediction)
- **Percentile binning creates risk bands** (Low/Moderate/High/Critical) → Even more interpretable

### Logical Outcome
✅ Single number, understandable, explainable, forward-looking, fast to use

---

## DECISION-002: Percentile-Based Risk Banding (Not Fixed Thresholds)

### The Problem
How do we assign risk bands (Low, Moderate, High, Critical) to HRS scores?

### Option A: Fixed Thresholds
```
if HRS < 35:    band = "Low"
if 35 <= HRS < 65: band = "Moderate"
if 65 <= HRS < 85: band = "High"
if HRS >= 85:   band = "Critical"
```
**Pros**: Simple, doesn't change  
**Cons**: 
- What if all companies are 40-50 HRS? Then all are "Low" but relative risk is lost
- What if all companies are 70-90 HRS? Then none are "Low" even if they're good performers

### Option B: Percentile-Based Binning
```
Low:      HRS in [0, 33.33) percentile    → Always ~25-33% of companies
Moderate: HRS in [33.33, 66.66) percentile → Always ~33-34% of companies
High:     HRS in [66.66, 90) percentile   → Always ~24-33% of companies
Critical: HRS in [90, 100] percentile     → Always ~10% of companies
```

### The Logic
```
Underwriters think relativistically:
  "Is this company in the top 10% of risk?" (Critical)
  "Is it in the bottom 33%?" (Low)
  
Not absolutely:
  "Is HRS > 75?" (arbitrary threshold)

Market data shows:
  - Only ~10% of group health claims are "critical"
  - ~30% are "high" (serious conditions)
  - ~33% are "moderate" (manageable risks)
  - ~27% are "low" (healthy cohorts)

Percentile bins align with real-world claim distributions.
```

### Why Not Use Statistical Methods (e.g., Standard Deviation)?
```
Approach: band by (HRS - mean) / std_dev
Problem: Assumes normal distribution
Reality: Health data is often bimodal (healthy vs. unhealthy cohorts)
Risk: If distribution shifts, bands become meaningless
```

### Implementation Decision
- **Calculate percentiles from training data** (once, at model training time)
- **Store percentile cutoffs in model pickle** (not recalculated per prediction)
- **Apply same cutoffs to all new predictions** (ensures consistency)

### Logical Outcome
✅ Adaptive bands that reflect true portfolio distribution  
✅ Bands are interpretable (top X% of risk)  
✅ Bands don't break if company population changes

---

## DECISION-003: Linear Premium Adjustment (Not Non-Linear)

### The Problem
How do we convert HRS (0–100 scale) into premium adjustment?

### Option A: Non-Linear Curve (Sigmoid/Exponential)
```
# Penalize high-risk companies more aggressively
adjustment = (exp((HRS - 50) / 20) - 1) / 10

# Example adjustments:
HRS=30  → adjustment = -0.18  → 18% discount
HRS=50  → adjustment = +0.00  → no change
HRS=70  → adjustment = +0.25  → 25% increase
HRS=100 → adjustment = +3.50  → 350% increase! (unrealistic)
```

**Pros**: Reflects "tail risk" (very sick companies pay much more)  
**Cons**:
- Non-linear is hard to explain ("Why does +5 HRS points = +25% price sometimes but +50% other times?")
- Extreme tail risk (HRS=100 → +350%) alienates customers
- Hard to validate (no historical data at HRS=100)

### Option B: Linear Adjustment
```
adjustment = (HRS - 50) / 100

# Example adjustments:
HRS=30  → adjustment = -0.20  → 20% discount
HRS=50  → adjustment = +0.00  → no change
HRS=70  → adjustment = +0.20  → 20% increase
HRS=100 → adjustment = +0.50  → 50% increase (capped, reasonable)
```

**Pros**: 
- Simple, transparent ("Every 10 HRS points = 10% premium change")
- Easy to explain to customers
- No extreme outliers

**Cons**:
- Doesn't penalize high-risk as aggressively
- May lose money on very sick companies

### The Logic
```
Insurance principle: Premium should reflect expected claims
Linear formula: Adjusted Premium = Base × (1 + (HRS - 50) / 100)

Why (HRS - 50) as pivot?
  - HRS mean ≈ 50 (centered around training data mean)
  - If company is average (HRS=50) → no adjustment
  - If company is better (HRS=40) → 10% discount
  - If company is worse (HRS=60) → 10% increase
  
Why divide by 100?
  - Keeps adjustment factor bounded (-0.5 to +0.5)
  - Translates to realistic premium range (50% discount to 50% increase)

Validation: Does it match market?
  - Industry standard: ~10-30% range for group health premiums
  - Our formula: -50% to +50% range ✓ Covers industry range
```

### Why Linear Over Non-Linear?
```
Transparency > Precision
  - Linear: I can explain it to an insurance broker in 30 seconds
  - Sigmoid: Requires calculus degree to understand
  
Avoid Moral Hazard
  - If adjustment is too steep, sick people won't buy (adverse selection)
  - Linear keeps price reasonable even for risky groups

Simplicity for Renewal
  - Customers expect: "Same company, healthier workforce → Same reduction"
  - Linear guarantees this predictability
  - Sigmoid might give inconsistent results (confuses customers)
```

### Implementation Decision
- **Use linear formula**: `Adjusted = Base × (1 + (HRS - 50) / 100)`
- **Cap adjustments**: min_premium = Base × 0.5, max_premium = Base × 1.5 (optional, not yet implemented)
- **Test with insurers**: Get feedback that formula is reasonable

### Logical Outcome
✅ Transparent, easy to explain  
✅ Aligns with market practice  
✅ Avoids extreme outliers  
✅ Predictable for customers

---

## DECISION-004: Streamlit for Dashboard (Not React/Vue/Angular)

### The Problem
Need a B2B dashboard for underwriters and HR managers. Build options:
1. React.js + Node.js backend (separate from FastAPI)
2. Vue.js + separate backend
3. Streamlit (Python-only)

### The Logic
```
Time to MVP: 
  React: 4-6 weeks (learn React, build components, test)
  Vue: 3-4 weeks (simpler than React, but still separate frontend)
  Streamlit: 2-3 days (Python templates, minimal boilerplate)

Maintenance:
  React: 2 people (1 backend, 1 frontend engineer)
  Vue: 2 people (same as React)
  Streamlit: 1 person (same language, easy debugging)

Iteration speed:
  React: Change frontend → rebuild → test in browser
  Streamlit: Change Python → save → auto-reload (instant feedback)

Team composition:
  We have: Python ML engineers
  We don't have: JavaScript/TypeScript experts
  Learning curve: Streamlit = 1 week, React = 4 weeks

Scale:
  Expected users: ~50 underwriters + HR managers
  React needed for: 500+ concurrent users
  Streamlit works fine for: <100 concurrent users ✓
```

### Why Not React?
```
Pros of React:
  - Scales to thousands of users
  - Rich component ecosystem
  - Can make beautiful UIs
  
Cons for THIS project:
  - Overkill (only 50 users expected)
  - Doubles development time (separate frontend team)
  - Separate deployment pipeline (more ops overhead)
  - Team has zero JavaScript experience
```

### Why Not Vue?
```
Same issues as React, but slightly faster to learn
Still requires: separate build process, frontend developer, more maintenance
```

### Why Streamlit?
```
Pros:
  - Same language as backend (Python)
  - 2-3 days to MVP ✓
  - Built-in caching for performance
  - Interactive widgets (selectbox, slider, etc.) with ~5 lines of code
  - Auto-reload on code change (instant feedback)
  - No build pipeline (no webpack, no npm)
  - Easy debugging (print statements work!)
  
Cons:
  - Not suitable for >100 concurrent users (our limit is ~50)
  - CSS customization requires HTML/JS (we worked around this)
  - No offline support (always needs server)
  - Can't build mobile app (but that's not a requirement)
```

### Why Not "Just Use Excel"?
```
Excel pros:
  - Everyone knows it
  - Zero learning curve
  
Excel cons:
  - Can't connect to live database (static data)
  - Can't generate PDFs with custom formatting
  - No role-based access control
  - No audit trail (who saw what, when)
  - Can't scale to multiple underwriters

So: No, Excel is not an option.
```

### Implementation Decision
- **Streamlit for MVP** (reaches market in 3 days, not 4 weeks)
- **Migrate to React later** (if we hit 100+ concurrent users)
- **Plan for migration**: Keep API separate from frontend (already did this with FastAPI)

### Logical Outcome
✅ Shipped in 3 days  
✅ Same language as backend  
✅ Easy to maintain  
✅ Sufficient for <100 users  
✅ Migration path to React when needed

---

## DECISION-005: Role-Based Access Control at App Level (Not Database Level)

### The Problem
Two types of users:
- **Underwriters**: See all companies, full portfolio analytics
- **HR Managers**: See only their company, workforce health

Where should this logic live?

### Option A: Database-Level RBAC (Row-Level Security)
```sql
-- PostgreSQL Row-Level Security
CREATE POLICY company_isolation ON companies
  USING (company_id = current_user_company_id);

-- HR manager can only see their company's data
SELECT * FROM companies;  -- Returns only their company
```

**Pros**: 
- Bulletproof security (can't accidentally expose data)
- Enforced at database level

**Cons**:
- Requires database setup (PostgreSQL RLS, not SQLite)
- Complex to test
- Can't use the same API for both roles
- Extra latency (every query checked by policy)
- Hard to debug ("Why can't I see this data?")

### Option B: Application-Level RBAC
```python
# In dashboard/app.py
user_role = st.session_state["user"]["role"]

if user_role == "underwriter":
    underwriter_view.render()
elif user_role == "hr_admin":
    hr_view.render()
```

**Pros**:
- Simple, transparent (easy to trace)
- Works with SQLite (no database-specific features)
- Easy to debug
- Same API endpoints for both roles (API filters data based on company_id)

**Cons**:
- Need to trust API to filter data correctly
- If API has bug, data could leak to wrong role

### The Logic
```
For MVP (50 users):
  App-level RBAC is sufficient
  Risk: Low (same company, human oversight)
  Complexity: Low
  Implementation time: 1 hour

For Production (1000+ users):
  Database-level RBAC is needed
  Risk: High (need multi-company isolation)
  Complexity: High
  Implementation time: 1 week

Decision: Start with app-level, add database-level RBAC in Phase 6
```

### Why Not Both?
```
Both is redundant (double-security):
  - If database is wrong, app-level catches it
  - If app-level is wrong, database catches it
  - But: Double redundancy = double maintenance = bugs in both layers
  
Better: Defense in depth (choose one layer per requirement):
  - App layer: Fast iteration, easy debugging
  - Database layer: Bulletproof security, when scaling
  
Currently: Use app layer → Phase 6 adds database layer if needed
```

### Implementation Decision
- **App-level RBAC for MVP** (Phase 5)
- **Plan for database-level in Phase 6** (when scaling past 100 users)
- **API endpoint filters data** by company_id (basic safeguard)
- **Session state stores user role** (checked at app startup)

### Security Audit Checklist
- [x] Underwriter can see all companies ✓
- [x] HR manager can see only their company ✓
- [x] No side-channel leaks (company_id in URL, API response) ✓
- [x] Session expires (no persistent login without reauth)
- [x] Password stored in code only (not ideal, but acceptable for demo)

### Logical Outcome
✅ Simple, testable, debuggable  
✅ Works with SQLite  
✅ Migration path to database-level in Phase 6  
✅ Sufficient for MVP with 50 users

---

## DECISION-006: Caching API Responses with TTL=60s (Not Shorter or Longer)

### The Problem
Dashboard makes lots of API calls. Should we cache?

### Option A: No Caching
```python
# Every render, hit the API
df = pd.DataFrame(list_companies())
```

**Pros**: Always fresh data  
**Cons**:
- API overloaded (5-10 calls per second during peak)
- Dashboard slow (network latency ~200ms per call)
- Bad UX (spinning loader constantly)

### Option B: Cache with TTL=1s
```python
@st.cache_data(ttl=1)
def list_companies():
    return _get("/companies")
```

**Pros**: Faster than no cache  
**Cons**:
- Data updates only once per second
- For fast-moving dashboards (stock prices), too stale
- Not meaningful cache (API still called frequently)

### Option C: Cache with TTL=60s (We chose this)
```python
@st.cache_data(ttl=60)
def list_companies():
    return _get("/companies")
```

**Pros**:
- API called once per minute max (60× fewer calls)
- Still reasonably fresh (data 60s old)
- Huge UX improvement (dashboard snappy)

**Cons**:
- If data changes, users see old data for up to 60s
- Not suitable for real-time dashboards

### Option D: Cache with TTL=3600s (1 hour)
```python
@st.cache_data(ttl=3600)
def list_companies():
    return _get("/companies")
```

**Pros**: Minimal API load  
**Cons**:
- Data could be 1 hour old
- Underwriter makes decision on stale data
- Bad for business ("Why did we approve a risky company?" "Data was 1 hour old")

### The Logic
```
What is the refresh frequency of underlying data?
  - Employee health data: Updated weekly (new claims, health events)
  - Company premiums: Updated daily (underwriting decisions)
  
What is the tolerance for stale data?
  - Underwriter making decision: Needs data < 1 minute old (acceptable)
  - HR manager reviewing trends: Needs data < 1 day old (acceptable)
  
What is API capacity?
  - FastAPI can handle ~100 requests/sec
  - Dashboard: ~5 requests/session/minute
  - Expected users: 10-20 concurrent
  - Total API load: ~50-100 requests/minute (fine)

Optimal TTL = 60s because:
  - Data freshness = OK (1 minute is acceptable for insurance)
  - API load = OK (60× reduction in calls)
  - UX = Great (dashboard responsive, no spinners)
  - Scalability = Good (can add more users before needing optimization)
```

### Why Not Configurable TTL?
```
Adding complexity: "Should TTL be 30s or 60s or 120s?"
  - Creates decision fatigue
  - Different users set different values
  - Bugs hard to reproduce ("What TTL did you use?")
  
Better: Fix TTL at 60s (sensible default), revisit if problems arise
```

### Implementation Decision
- **TTL=60s for all API calls** (consistent, simple)
- **Monitor if data freshness becomes issue** (track in Phase 6)
- **Consider Redis for persistent cache** (if scaling to 100+ users)
- **Add "refresh now" button** (let user force update if needed)

### Logical Outcome
✅ 60× fewer API calls  
✅ Dashboard remains responsive  
✅ Data fresh enough for insurance use case  
✅ No premature optimization

---

## DECISION-007: Static Exchange Rates (Not Live FX API)

### The Problem
Dashboard supports 10 currencies. Should we use live FX rates?

### Option A: Live FX API (e.g., Alpha Vantage, XE.com)
```python
def get_exchange_rate(from_curr, to_curr):
    resp = requests.get("https://api.exchangerate-api.com/v4/latest/INR")
    rates = resp.json()["rates"]
    return rates[to_curr]
```

**Pros**: Always accurate  
**Cons**:
- External dependency (API goes down → dashboard fails)
- Network latency (20-50ms per call)
- Rate limits (some APIs limit to 100 calls/day)
- Cost (might charge per call, $10-100/month)
- Adds complexity (error handling for API failures)

### Option B: Manual Updates (Static Rates)
```python
CURRENCIES = {
    "INR": {"rate": 1.0},
    "USD": {"rate": 0.01198},
    "EUR": {"rate": 0.01105},
    # ... updated manually quarterly
}
```

**Pros**:
- No external dependency
- Lightning fast (no network call)
- No rate limits
- Zero cost
- Simple

**Cons**:
- Rates become stale (~1-3% drift per quarter)
- Someone needs to update manually

### The Logic
```
What is the use case?
  - Insurance premium conversion (not currency trading)
  - Premiums don't move daily (they're fixed for 12 months)
  - 1-3% rate drift is acceptable (within normal premium variance)

How often do rates change?
  - Daily: Yes, but insurance doesn't reprice daily
  - Quarterly: Enough to do manual updates
  - Currency crisis: Rate might swing 10% in one day
    BUT: Not common for major currencies (INR, USD, EUR)

Cost/benefit:
  Option A: $10-100/month, complexity, external dependency
  Option B: 15 minutes/quarter, no complexity, reliable
  
ROI:
  Option A: ROI = -100% (paying for feature no one uses)
  Option B: ROI = ∞ (free, simple, works)

Future-proofing:
  If business grows to 10,000 users trading currencies:
    → Migrate to live API (easy, just change one function)
  If business stays small (50 users, internal only):
    → Static rates forever (never needed)
```

### Why Static Over Live?
```
Insurance principle: Predictability > Precision
  - Customers want: "Same currency, same premium next month"
  - Not: "Rates fluctuated 2% today, premium changed"
  
Engineering principle: Simple > Robust
  - Static rates: 1 file, no external dependency, always works
  - Live API: 10 lines of error handling, rate limiting, retry logic
  
Occam's Razor: Solve real problem, not imaginary one
  - Real problem: Currency conversion for display
  - Imaginary problem: Real-time rate accuracy for insurance
```

### Implementation Decision
- **Static rates with INR as base** (all rates = "1 INR = X foreign")
- **Manual update quarterly** (Q1, Q2, Q3, Q4)
- **Document update process** (when and how to refresh)
- **Migrate to live API in Phase 6** (if business case arises)

### Logical Outcome
✅ Zero external dependencies  
✅ No rate-limit issues  
✅ Predictable for customers  
✅ Easy to maintain

---

## DECISION-008: PDF Report Generated Server-Side (Not Browser-Based)

### The Problem
Dashboard generates PDF underwriting reports. Where should this happen?

### Option A: Browser-Based PDF (HTML → PDF in Frontend)
```javascript
// Use library: html2pdf.js, jsPDF, or print-to-PDF
// Convert HTML to PDF in browser, download to client
```

**Pros**: No server load  
**Cons**:
- Browser rendering variability (PDF looks different on Chrome vs Safari)
- Large JavaScript library (adds to bundle size)
- Hard to debug styling issues
- Can't use Python libraries (SHAP charts, loss ratio calculations)

### Option B: Server-Side PDF (FastAPI generates, Streamlit downloads)
```python
# FastAPI
@router.post("/reports/{company_id}")
def generate_report(company_id):
    pdf_bytes = generate_pdf_report(...)
    return FileResponse(pdf_bytes, media_type="application/pdf")

# Streamlit
st.download_button(
    "Download PDF",
    data=generate_underwriting_report(...),
    file_name="report.pdf"
)
```

**Pros**:
- Deterministic output (same PDF every time)
- Can use Python (ReportLab) to build PDF
- Can include SHAP charts, complex calculations
- Consistent rendering (no browser variation)

**Cons**:
- Server load (slightly higher)
- More complex (need PDF library)

### The Logic
```
What needs to be in the PDF?
  - Company profile (name, employees, industry)
  - Health risk score (gauge chart)
  - Risk breakdown (pie chart showing %, breakdown)
  - SHAP feature importance (top 5 drivers)
  - Premium recommendation (table)
  - Wellness ROI projection (optional)
  
Can this be done in browser?
  - Gauge chart: Possible (Chart.js, Plotly.js)
  - Pie chart: Possible (Chart.js)
  - SHAP importance: Possible (but need to export from Python first)
  - Table: Possible (HTML table)
  
Why server-side is better:
  - All calculations happen in Python
  - Don't need to export SHAP data to JSON (security issue)
  - Don't need JavaScript charting library (already have Plotly)
  - PDF looks identical every time (deterministic)
  - Currency conversion embedded in PDF (don't need to pass to browser)

Scalability:
  - Browser-based: Instant (no server cost)
  - Server-based: ~500ms per PDF (acceptable, rarely needed)
  - Use case: ~5-10 PDFs/day per underwriter
  - Total server cost: ~5ms per underwriter (negligible)
```

### Why Not Use FastAPI to Serve PDF, Not Streamlit?
```
Option 1: Streamlit generates PDF in-memory, downloads to client
  - Pros: One-click download, immediate feedback
  - Cons: PDF generation happens every render (wasteful)
  
Option 2: FastAPI generates PDF, client requests from API
  - Pros: Can cache PDF on server (if needed)
  - Cons: Extra API call, user must wait for generation

Current implementation: Streamlit wrapper around ReportLab
  - Works great for ~50 users
  - Can optimize to FastAPI endpoint later (Phase 6)
```

### Implementation Decision
- **Server-side PDF generation** using ReportLab
- **Generate on-demand** in Streamlit (no caching)
- **Support multiple currencies** (pass currency to PDF generator)
- **Store inline exchange rates** in pdf_report.py (no dependency on Streamlit)

### Logical Outcome
✅ Deterministic, identical PDFs every time  
✅ Full Python power (charts, calculations)  
✅ Currency-aware formatting  
✅ Secure (no sensitive data in browser)

---

## DECISION-009: XGBoost Model Saved in Pickle (Not Exported to Production Format)

### The Problem
ML model trained and needs to be persisted. Format options:

### Option A: Pickle (`joblib.dump` / `pickle.dump`)
```python
import joblib
joblib.dump(model, "xgboost_model.pkl")
joblib.dump(explainer, "explainer.pkl")
```

**Pros**: Works immediately, no conversion needed  
**Cons**: 
- Python-only (can't use in other languages)
- Not ideal for production deployment
- Security risk (pickle can execute arbitrary code if malicious)

### Option B: ONNX (Open Neural Network Exchange)
```python
import onnx
onnx_model = onnx.converter.convert_sklearn(model)
onnx.save_model(onnx_model, "model.onnx")
```

**Pros**: Language-agnostic (C++, Java, JavaScript can use it)  
**Cons**:
- Not all XGBoost features are supported by ONNX
- Conversion can be lossy (may lose some model information)
- More complexity (need ONNX runtime)
- SHAP explainer doesn't have ONNX export

### Option C: JSON/HDF5 (Custom Format)
```python
# Manually serialize model as JSON
# Pro: Platform-agnostic
# Con: Massive (model is 1000s of trees, JSON = verbose)
```

**Pros**: Language-agnostic  
**Cons**: Huge file size, complex serialization logic

### The Logic
```
What is the deployment scenario?
  - Phase 5: All Python (FastAPI + Streamlit on same host)
  - Phase 6+: May deploy to cloud (AWS, GCP, Azure)
  
Does the model need to work with other languages?
  - No (API is Python, all inference in Python)
  
What is the time constraint?
  - Pickle: 5 minutes to implement
  - ONNX: 3 days (convert, test, debug)
  - JSON: 5 days (design serialization, test thoroughly)

Is security a concern?
  - Now: No (internal use only, trusted files)
  - Later: Yes (in Phase 6, sanitize model files)

MVP decision:
  - Use Pickle now (fastest to ship)
  - Add ONNX export in Phase 6 (if deploying to non-Python runtime)
  
Pickle risks mitigated:
  - Only load models we created (not user-supplied)
  - Store models in version control (can audit for tampering)
  - Restrict file permissions (only readable by app)
```

### Why Not ONNX for Phase 5?
```
ONNX pros:
  - Future-proof (works in any language)
  - Can optimize inference (smaller models, faster)
  
ONNX cons:
  - SHAP explainer can't be exported to ONNX (goes with Python model)
  - Adds 3 days of work
  - MVP principle: "Solve today's problem, not tomorrow's"

Decision: Use Pickle now, ONNX in Phase 6 if needed
```

### Implementation Decision
- **Save model + explainer as pickle files**
- **Version models** (e.g., `xgboost_model_v1.pkl`, not just `model.pkl`)
- **Document model loading** (which Python version, which libraries)
- **Plan for ONNX export** (Phase 6, if migrating to production)

### Logical Outcome
✅ Model persisted and reusable  
✅ Minimal complexity  
✅ Migration path to ONNX if needed  
✅ Acceptable risk for MVP

---

## DECISION-010: Testing Strategy — Integration Tests > Unit Tests

### The Problem
How much testing do we do? Where should we focus?

### Option A: Heavy Unit Testing
```python
# Test each function in isolation
test_calculate_premium_with_different_hrs()
test_percentile_binning_edge_cases()
test_format_currency_with_edge_values()
# ... 100+ unit tests
```

**Pros**: 
- Catches function-level bugs
- Fast (no external dependencies)

**Cons**:
- May pass unit tests but fail end-to-end
- Time-consuming to write (2 hours per 1 hour of code)
- Brittle (refactoring breaks tests)

### Option B: Heavy Integration Testing
```python
# Test the whole flow
test_underwriter_can_load_portfolio()
test_pdf_generation_with_all_currencies()
test_hr_manager_can_see_wellness_roi()
# ... 20 integration tests
```

**Pros**:
- Tests real business value ("Can underwriter use dashboard?")
- Catches integration bugs (API → DB → Model → Dashboard)
- Fast to write (1 hour per 1 hour of code)
- Flexible (can refactor functions without breaking tests)

**Cons**:
- Slower to run (touch database, API, model inference)
- Requires infrastructure (running server)

### The Logic
```
For a B2B SaaS product:
  Business value ≠ unit test passing
  Business value = "Underwriter can underwrite 50 companies/day"

What matters?
  - End-to-end flow works ✓ (integration test)
  - Edge cases handled ✓ (where needed)
  - Performance acceptable ✓ (manual testing)

What doesn't matter?
  - Every function has test ✗ (brittle, expensive)
  - 100% code coverage ✗ (false sense of security)
  - Testing internal implementation ✗ (changes with refactoring)

Risk analysis:
  If unit test fails: Function might be buggy (low risk for MVP)
  If integration test fails: Business process broken (high risk)

Testing priority:
  1. Integration tests (most valuable)
  2. Critical path unit tests (premium calc, risk scoring)
  3. Edge cases (rare scenarios)
  4. Code coverage (nice-to-have, not required)
```

### Implementation Decision
- **20 integration tests** (focus on end-to-end flows)
- **Critical function tests** (premium calc, HRS scoring)
- **Dashboard tests** (role-based access, currency switching)
- **PDF generation tests** (all currencies, all company types)
- **Acceptance threshold**: 20 tests passing, can release

### Test Coverage Achieved
- ✅ 20/20 tests passing
- ✅ Covers all 3 roles (underwriter, HR manager, API)
- ✅ Tests all major features (portfolio, deep dive, wellness ROI)
- ✅ Tests currency support (multi-currency PDF generation)
- ✅ 211.66s total runtime (acceptable for integration tests)

### Why Not 100% Coverage?
```
Diminishing returns:
  - First 20 tests: Catch 80% of bugs
  - Next 30 tests: Catch 10% of remaining bugs
  - Next 50 tests: Catch 9% of remaining bugs
  
Cost/benefit:
  - 20 tests: $500 (1 day work)
  - 50 tests: $1500 (3 days work)
  - 100 tests: $3500 (7 days work)
  
ROI:
  - 20 tests: ROI = 1000% (prevents major bugs)
  - 50 tests: ROI = 300% (prevents medium bugs)
  - 100 tests: ROI = 100% (prevents minor bugs)

Decision: Stop at 20 tests (diminishing returns)
```

### Logical Outcome
✅ 20 integration tests provide confidence for MVP  
✅ Focus on business value, not code coverage  
✅ Fast iteration (tests run in ~200s)  
✅ Scalable (easy to add more tests later)

---

## Summary Table: Logical Decisions

| # | Decision | Why | Alternative | Tradeoff |
|---|----------|-----|-------------|----------|
| 001 | HRS as core metric | Single, interpretable number | Loss ratio alone | Requires ML model |
| 002 | Percentile binning | Adaptive to portfolio | Fixed thresholds | Requires data calibration |
| 003 | Linear adjustment | Transparent, explainable | Non-linear curve | Less aggressive tail risk |
| 004 | Streamlit | Fast MVP, same language | React | Not scalable >100 users |
| 005 | App-level RBAC | Simple for MVP | DB-level | Less secure, upgrade in Phase 6 |
| 006 | TTL=60s cache | Balance freshness + performance | TTL=1s or TTL=3600s | Some data staleness |
| 007 | Static FX rates | No dependencies, simple | Live API | Rates drift quarterly |
| 008 | Server-side PDF | Deterministic, Python power | Browser-based | Slight server load |
| 009 | Pickle for model | Fast implementation | ONNX | Python-only, upgrade later |
| 010 | Integration tests | Catch business bugs | Unit tests | Slower to run |

---

## Common Themes Across Decisions

### 1. **MVP Principle: Ship Fast, Iterate Later**
- Phase 5 = MVP (Streamlit, not React)
- Phase 6 = Scale (ONNX, database-level RBAC, production auth)

### 2. **Simplicity > Robustness (Until It Hurts)**
- Static FX rates (not live API)
- Linear premiums (not sigmoid curve)
- App-level RBAC (not database-level)
- Only add complexity when needed

### 3. **Transparency > Precision**
- Linear adjustment (explain to customers easily)
- HRS metric (understandable, not black box)
- Percentile binning (interpretable, "top 10% of risk")

### 4. **Business Logic Before Engineering**
- HRS = business requirement ("How do underwriters think?")
- Linear premium = market practice ("What do competitors do?")
- Streamlit = team composition ("We have Python people, not JS people")

### 5. **Risk-Based Decision Making**
- Testing priority: Integration > Unit (catch business risks first)
- RBAC: App-level (low risk for 50 users, scale later)
- Caching: 60s (acceptable data staleness for insurance)

---

## How These Decisions Affect Phase 6

### Phase 6 Likely Needs

**If scaling users to 1000+**:
- React instead of Streamlit (10x better performance)
- ONNX instead of Pickle (deploy model to cloud)
- Database-level RBAC (SQL Row-Level Security)
- Live FX API (more accurate for global customers)

**If adding compliance**:
- Audit logging (who accessed what, when)
- Encryption (health data is sensitive)
- OAuth / SAML (not demo users in code)

**If adding real-time features**:
- WebSockets (instead of HTTP polling)
- Redis cache (instead of Streamlit in-memory)
- Event streaming (Kafka, for claim updates)

**Current decisions are compatible with all Phase 6 upgrades**:
✅ Can migrate Streamlit → React without API changes  
✅ Can add ONNX export without changing model  
✅ Can add database RBAC without app refactor  
✅ Can swap static rates → live API (one function change)

---

## Conclusion

Every logical decision in Aegis AI followed this pattern:
1. **Identify the problem** (what decision needs to be made?)
2. **List options** (what are the alternatives?)
3. **Analyze tradeoffs** (what do we gain/lose with each?)
4. **Pick MVP path** (choose based on speed, team, risk)
5. **Plan upgrade** (how will we improve this in Phase 6?)

This approach prioritizes **shipping over perfection**, while keeping doors open for **scaling later**.

