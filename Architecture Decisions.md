# Architecture Decisions — Aegis AI

**Last Updated**: 2026-04-22  
**Document Type**: Architecture Decision Record (ADR)

---

## Overview

This document records key architectural decisions, design tradeoffs, and patterns used in Aegis AI.

---

## ADR-001: XGBoost + SHAP for Health Risk Scoring

**Decision**: Use XGBoost for predicting health risk (HRS) and SHAP for explainability.

**Rationale**:
- XGBoost is fast, handles non-linear relationships well, and captures interactions between health variables
- SHAP provides model-agnostic explanations (top 5 features per prediction) for underwriter transparency
- Better than linear models (logistic regression) for capturing complex health patterns
- Better than deep learning for this small dataset (10K records) and interpretability requirements

**Tradeoffs**:
- ✅ Interpretable + accurate
- ❌ Not real-time online learning (batch retraining only)
- ❌ Requires periodic model retraining as data grows

**Implementation**: `ml/trainer.py`, `ml/explainer.py`  
**Persisted to**: `ml/models/xgboost_model.pkl`, `ml/models/explainer.pkl`

---

## ADR-002: FastAPI for Backend

**Decision**: Use FastAPI (async Python) instead of Django or Flask.

**Rationale**:
- Native async support (future scalability)
- Built-in OpenAPI/Swagger documentation
- Pydantic for automatic request/response validation
- Lightweight and fast (lower overhead than Django)
- Integrates well with ML model inference

**Tradeoffs**:
- ✅ Modern, fast, easy to debug
- ❌ Smaller ecosystem than Django
- ❌ Requires familiarity with async patterns

**Implementation**: `ingestion/main.py`, `ingestion/routers/*.py`  
**Port**: 8000 (local dev), configurable for production

---

## ADR-003: Streamlit for Frontend Dashboard

**Decision**: Use Streamlit instead of React/Vue for dashboard.

**Rationale**:
- Rapid development (no frontend framework learning curve)
- Python-only (same language as backend/ML)
- Interactive widgets with minimal boilerplate
- Caching layer (`@st.cache_data`) reduces API calls
- Session state management built-in

**Tradeoffs**:
- ✅ Fast to prototype, easy to iterate
- ✅ No separate frontend deployment
- ❌ Not suitable for high-load scenarios (1000+ concurrent users)
- ❌ Limited styling customization (CSS workarounds needed)

**Implementation**: `dashboard/app.py`, `dashboard/*_view.py`  
**Port**: 3000 (via `streamlit run`)

**CSS Customization Strategy**:
- Use `[data-testid="..."]` selectors (safe, targets container only)
- Avoid `.st*` class selectors (too fragile, breaks on Streamlit updates)
- Light theme via `.streamlit/config.toml` (not CSS)

---

## ADR-004: SQLAlchemy ORM + PostgreSQL/SQLite

**Decision**: Use SQLAlchemy ORM with choice of PostgreSQL or SQLite backend.

**Rationale**:
- ORM abstracts database differences (dev on SQLite, prod on PostgreSQL)
- Type hints + Pydantic models provide validation
- Relationships (company → employees → snapshots) naturally expressed
- FastAPI integration via dependency injection

**Tradeoffs**:
- ✅ Flexible database choice
- ✅ Type-safe queries
- ❌ ORM overhead (but acceptable for this scale ~50K rows)
- ❌ Requires schema migrations (not yet implemented)

**Implementation**: `ingestion/schema.py` (models), `ingestion/main.py` (session mgmt)  
**Database**: SQLite for dev (`aegis.db`), PostgreSQL for prod

---

## ADR-005: Synthetic Data for Development

**Decision**: Generate synthetic employee health data rather than using real data.

**Rationale**:
- Privacy (no real PII)
- Reproducibility (same seed → same data)
- Simplicity (no data licensing/compliance)
- Fast iteration (no waiting for real data)

**Tradeoffs**:
- ✅ Privacy-first, fast iteration
- ❌ May not capture real-world edge cases
- ❌ Model trained on synthetic data may not generalize perfectly

**Implementation**: `ingestion/synthetic_data.py`  
**Data Volume**: 10,000 employees across ~50 companies

---

## ADR-006: Caching API Responses with Streamlit

**Decision**: Use Streamlit's `@st.cache_data(ttl=60)` decorator for all API calls.

**Rationale**:
- Reduces server load (5-10× fewer API calls during active session)
- Improves dashboard responsiveness (no network latency on re-render)
- TTL=60s balances freshness vs. performance

**Tradeoffs**:
- ✅ Much faster UX
- ❌ Data is not real-time (60-second lag acceptable for this use case)
- ❌ Cache invalidation requires session reload

**Implementation**: `dashboard/api_client.py` (all public functions decorated)

---

## ADR-007: ReportLab for PDF Generation

**Decision**: Use ReportLab for server-side PDF generation (not browser-based).

**Rationale**:
- Full control over layout + formatting
- Deterministic output (no browser rendering variability)
- No JavaScript/browser dependency
- Currency-aware formatting (external to Streamlit context)

**Tradeoffs**:
- ✅ Reliable, server-side control
- ✅ Currency agnostic (inline `_RATES` dict)
- ❌ Limited design flexibility vs. HTML/CSS
- ❌ Must maintain separate _RATES dict (not DRY)

**Implementation**: `dashboard/pdf_report.py`  
**Output**: Downloadable as `aegis_report_{company_id}.pdf`

---

## ADR-008: Role-Based Access Control (RBAC)

**Decision**: Implement role-based routing (underwriter vs. hr_admin) at app level.

**Rationale**:
- Underwriters see all companies + portfolio analytics
- HR admins see only their company + workforce health
- Simple, non-invasive (no database-level RBAC needed yet)

**Tradeoffs**:
- ✅ Simple to implement, easy to test
- ❌ Not production-grade (needs audit logging, OAuth integration)
- ❌ Demo users stored in code (not in database)

**Implementation**: `dashboard/auth.py`, `dashboard/app.py` (routing logic)

**Demo Users**:
```python
USERS = {
    "underwriter@safenet.com": {"name": "...", "org": "SafeNet", "role": "underwriter"},
    "hr@technova.com":         {"name": "...", "org": "TechNova", "role": "hr_admin", "company_id": "COMP_001"},
    "hr@bharatsteel.com":      {"name": "...", "org": "Bharat Steel", "role": "hr_admin", "company_id": "COMP_002"},
}
```

---

## ADR-009: Multi-Currency Support with Static Exchange Rates

**Decision**: Support 10 currencies via static exchange rate table (not live FX API).

**Rationale**:
- B2B insurance premiums don't need real-time FX (rates change slowly)
- Reduces external dependencies (no API call to FX service)
- Rates updated manually (quarterly or as needed)
- All rates stored as `1 INR = X foreign currency` (consistent base)

**Supported Currencies**:
```
INR, USD, EUR, GBP, AED, SGD, AUD, JPY, CAD, CHF
```

**Tradeoffs**:
- ✅ Simple, no external API
- ✅ Predictable, no rate-fetch failures
- ❌ Rates can become stale (manual update required)
- ❌ Not suitable for real-time trading

**Implementation**: `dashboard/currency.py` (CURRENCIES dict)  
**Format Functions**: `fmt()`, `fmt_crore()`, `convert()`

---

## ADR-010: Risk Band Calculation via Percentile Binning

**Decision**: Assign risk bands (Low, Moderate, High, Critical) based on HRS percentiles.

**Rationale**:
- Automatic calibration (bins adjust as data changes)
- Ensures balanced distribution across risk bands
- Interpretable (e.g., "top 10% of risk" = Critical)

**Binning Strategy**:
```
Low:      HRS in [0, 33.33) percentile    → Band = "Low"
Moderate: HRS in [33.33, 66.66) percentile → Band = "Moderate"
High:     HRS in [66.66, 90) percentile    → Band = "High"
Critical: HRS in [90, 100] percentile      → Band = "Critical"
```

**Tradeoffs**:
- ✅ Adaptive, fair distribution
- ❌ Requires full dataset percentile calculation
- ❌ Not suitable if you want fixed thresholds (e.g., HRS > 80 = always Critical)

**Implementation**: `ml/trainer.py` (computed during training)

---

## ADR-011: Premium Adjustment Algorithm

**Decision**: Linear adjustment based on HRS (relative to mean=50).

**Formula**:
```
Adjusted Premium = Base Premium × (1 + adjustment_factor)

where:
  adjustment_factor = (HRS - 50) / 100
  
Examples:
  HRS=30  → adjustment = -0.20  → 20% discount
  HRS=50  → adjustment = +0.00  → no change
  HRS=70  → adjustment = +0.20  → 20% increase
  HRS=100 → adjustment = +0.50  → 50% increase
```

**Tradeoffs**:
- ✅ Simple, transparent, easy to explain to customers
- ❌ Not market-driven (should be validated against competitor pricing)
- ❌ Assumes linear relationship (may underestimate tail risk)

**Implementation**: `ingestion/routers/predictions.py`

---

## ADR-012: Zone-Based Pricing

**Decision**: Apply geographic zone multipliers to premium.

**Zones**:
```
metro:  1.00×  (big cities: Delhi, Mumbai, Bangalore, etc.)
tier-2: 0.85×  (second-tier cities: Ahmedabad, Pune, etc.)
tier-3: 0.70×  (smaller cities, rural areas)
```

**Rationale**:
- Reflects different healthcare infrastructure + costs across regions
- Common insurance practice

**Tradeoffs**:
- ✅ Market-realistic
- ❌ Zone assignment is manual (not auto-geocoded)

**Implementation**: `ingestion/routers/predictions.py`

---

## ADR-013: Underwriting Recommendation Logic

**Decision**: Automated recommendation based on HRS threshold.

```
HRS < 35          → "Accept (low risk)"
35 ≤ HRS < 65    → "Review (moderate risk)"
65 ≤ HRS < 85    → "Conditional Accept (high risk)"
HRS ≥ 85         → "Decline (critical risk)"
```

**Rationale**:
- Guides underwriter decision without removing human judgment
- Reduces decision fatigue (clear baseline)

**Tradeoffs**:
- ✅ Consistent, auditable
- ❌ May reject profitable niche segments (e.g., small high-risk company)

**Implementation**: `ingestion/routers/predictions.py`

---

## ADR-014: Wellness ROI Simulator Algorithm

**Decision**: Linear projection of premium savings from HRS reduction.

**Formula**:
```
Projected HRS = Current HRS - improvement_target
Projected Premium = calculate_premium(base_premium, Projected HRS)
Annual Savings = Current Premium - Projected Premium
```

**Tradeoffs**:
- ✅ Simple, intuitive for HR teams
- ❌ Assumes linear HRS-to-premium mapping (may be oversimplified)

**Implementation**: `ingestion/routers/predictions.py`  
**Used by**: HR Manager wellness tab

---

## ADR-015: Authentication — JWT Bearer Tokens

**Decision**: Replace session-based demo auth with JWT authentication backed by bcrypt user store.

**Rationale**:
- HIPAA/SOC 2 compliance requires authentication on all PHI-touching endpoints
- JWT is stateless — no server-side session storage needed
- bcrypt password hashing (cost 12) prevents credential leakage from user store
- `config/users.json` stores pre-hashed passwords — version-controlled, simple to manage for demo scale

**Implementation**:
- `ingestion/auth/jwt.py` — `create_access_token()` / `decode_token()` (HS256, 8h expiry)
- `ingestion/auth/users.py` — bcrypt verification against `config/users.json`
- `ingestion/auth/dependencies.py` — `get_current_user`, `require_company_access` FastAPI dependencies
- `ingestion/routers/auth_router.py` — `POST /auth/token` login endpoint
- `dashboard/auth.py` — calls `/auth/token`, stores JWT in `st.session_state`, 30-min idle timeout

**Demo Users** (passwords bcrypt-hashed at cost 12, all demo123):
```
underwriter@safenet.com  → role: underwriter (sees all companies)
hr@technova.com          → role: hr_admin (COMP_001 only)
hr@bharatsteel.com       → role: hr_admin (COMP_002 only)
```

**Known Gap**: RBAC enforced on `/predict/*` and `/companies/*` but missing on `/ingest/*` endpoints — hr_admin can ingest data for other companies.

**Future Upgrade Path**: OAuth 2.0 / SAML 2.0 (Okta, Azure AD), database-backed user table.

---

## ADR-016: Rate Limiting via slowapi

**Decision**: Apply per-IP rate limiting on the `/auth/token` endpoint using `slowapi`.

**Rationale**:
- Prevents brute-force credential attacks without requiring infrastructure-level WAF
- `slowapi` wraps FastAPI transparently — minimal code change
- 5 requests/minute per IP is standard for login endpoints

**Implementation**: `ingestion/main.py` (Limiter setup), `ingestion/routers/auth_router.py` (`@limiter.limit("5/minute")`)

**Tradeoffs**:
- ✅ Simple, zero infra, works in Docker
- ❌ In-memory counter resets on restart (not distributed — fine for single-node demo)
- ❌ Bypassable via IP rotation (acceptable for demo, upgrade to Redis-backed for prod)

---

## ADR-017: Security Headers Middleware + Server Header Suppression

**Decision**: Add ASGI middleware to inject security response headers on every response; suppress Uvicorn's `Server` header.

**Headers Added**:
```
X-Frame-Options: DENY                       (clickjacking protection)
X-Content-Type-Options: nosniff             (MIME sniffing protection)
X-XSS-Protection: 1; mode=block             (legacy XSS filter)
Strict-Transport-Security: max-age=31536000 (HSTS — HTTPS enforcement)
Content-Security-Policy: default-src 'self' (CSP)
Referrer-Policy: strict-origin-when-cross-origin
Server: AegisAI                             (replaces Uvicorn version string)
```

**Server Header**: Uvicorn injects its own header at the ASGI layer before middleware runs. Fixed by adding `--no-server-header` to the uvicorn CLI in `scripts/entrypoint.sh`.

**Implementation**: `ingestion/main.py` (`add_security_headers` middleware), `scripts/entrypoint.sh`

---

## ADR-018: Non-Root Container User

**Decision**: Run the API container as a non-root `appuser` (UID 1000).

**Rationale**:
- Container processes running as root can escalate to host root if container escape occurs
- Industry standard: all production containers should run as non-root
- Required by SOC 2 CC6.6 (least privilege)

**Implementation**: `Dockerfile.api` — `RUN useradd -m -u 1000 appuser` + `RUN chown -R appuser:appuser /app` + `USER appuser`

**Tradeoffs**:
- ✅ Significantly reduces blast radius of container compromise
- ❌ File permissions must be set explicitly (chown before USER switch)

---

## Summary Table

| ADR | Decision | Rationale | Status |
|-----|----------|-----------|--------|
| 001 | XGBoost + SHAP | Accuracy + interpretability | ✅ Implemented |
| 002 | FastAPI | Modern, fast, async | ✅ Implemented |
| 003 | Streamlit | Rapid dev, Python-only | ✅ Implemented |
| 004 | SQLAlchemy + Postgres/SQLite | Flexible, type-safe | ✅ Implemented |
| 005 | Synthetic data | Privacy, reproducibility | ✅ Implemented |
| 006 | Streamlit caching | Performance | ✅ Implemented |
| 007 | ReportLab PDF | Deterministic, currency-aware | ✅ Implemented |
| 008 | Role-based RBAC | Simple access control | ✅ Implemented |
| 009 | Static FX rates | Simplicity | ✅ Implemented |
| 010 | Percentile risk binning | Adaptive, fair | ✅ Implemented |
| 011 | Linear premium adjustment | Transparency | ✅ Implemented |
| 012 | Zone pricing | Market-realistic | ✅ Implemented |
| 013 | Automated recommendations | Consistency | ✅ Implemented |
| 014 | Wellness ROI simulator | HR decision support | ✅ Implemented |
| 015 | JWT bearer auth + bcrypt | HIPAA/SOC2 compliance | ✅ Implemented |
| 016 | Rate limiting (slowapi) | Brute-force protection | ✅ Implemented |
| 017 | Security headers middleware | OWASP hardening | ✅ Implemented |
| 018 | Non-root container user | Least privilege | ✅ Implemented |

