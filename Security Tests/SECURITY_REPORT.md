# Aegis AI — Comprehensive Security Report

**Last Updated:** 2026-04-24  
**Audit Scope:** Live Docker environment, automated security suite, static analysis, dependency audit  
**Repository:** `c:\Rupalprojects\aegis-ai`

---

## Executive Summary

| Check | Result |
|-------|--------|
| Security test suite | **27 / 27 passed** |
| Dependency audit (`pip-audit`) | **0 known vulnerabilities** |
| Bandit static analysis | **0 High / 0 Medium / 1 Low (false positive)** |
| Server header leakage | **Clean** — `server: AegisAI` only, no uvicorn header |
| Auth rate limiting | **Active** — 5 attempts/minute per IP on `/auth/token` |
| Cross-company RBAC | **Enforced** — HR admins restricted to own company |
| Input validation | **Enforced** — Pydantic rejects all malformed payloads |

**Overall posture: LOW RISK**

---

## Audit History

| Date | Event | Outcome |
|------|-------|---------|
| 2026-04-21 | Initial security hardening | JWT auth, TLS, RBAC, audit logging implemented |
| 2026-04-22 | Security test suite added + remediation | 4 HIGH/MEDIUM findings fixed |
| 2026-04-24 (AM) | Re-audit against Docker stack | 27/27 passing; 0 vulns |
| 2026-04-24 (PM) | Server restarted + clean re-verification | All controls confirmed active |

---

## Current Controls

### Authentication
- **JWT Bearer tokens** — HS256, configurable expiry (default 60 min), via `python-jose`
- **bcrypt password hashing** — all passwords stored hashed; plaintext never written to disk
- **Rate limiting** — `/auth/token` capped at 5 requests/minute per IP via SlowAPI
- **Token blacklist** — in-memory revocation list (see open items)

### Authorization
- **Role-based access** — `underwriter` and `hr_admin` roles; enforced via `Depends(get_current_user)`
- **Company-level RBAC** — `require_company_access()` prevents `hr_admin` from touching another company's data
- **Scope enforcement** — all ingest, predict, and company endpoints require valid JWT

### Transport Security
- **TLS termination** — Nginx handles HTTPS in Docker; certs managed via Docker secrets
- **HSTS header** — set by Nginx
- **CORS** — restricted to allowed origins via `ALLOWED_ORIGINS` env var; invalid origins rejected with 400

### Input Validation
- **Pydantic models** on all request bodies — type checks, range validation, required fields
- **Field constraints** — age 18–80, BMI 10–60, HR 30–200, month 1–12, steps ≥ 0
- **SQL injection** — parameterised ORM queries (SQLAlchemy); no raw string interpolation

### Infrastructure
- **No server header leakage** — `--no-server-header` set in Docker entrypoint; middleware adds `server: AegisAI`
- **DB not exposed externally** — PostgreSQL bound to `127.0.0.1:5432` only
- **Secrets via environment** — no credentials in source code; `.env` excluded from git
- **Audit logging** — auth events and ingest operations logged with timestamps

---

## Security Test Results (2026-04-24)

All 27 tests run against live Docker API at `http://localhost:8000`.

### Authentication Security (6/6)
- Invalid credentials rejected with 401
- Missing credentials rejected with 400/422
- SQL injection in username field safely rejected
- Expired JWT token rejected with 401
- Malformed token string rejected with 401
- Missing token on protected endpoint returns 401

### Authorization Security (3/3)
- Underwriter role cannot access endpoints outside its scope
- HR admin cannot access company data for a different company (403)
- HR admin cannot ingest roster for another company (403)

### Security Headers (3/3)
- CORS headers present on responses
- `Content-Type` set correctly
- No `server: uvicorn` header leakage — only `server: AegisAI`

### Input Validation (6/6)
- SQL injection string in `company_id` safely handled
- XSS payload in JSON body safely handled
- Oversized payload (>1MB) rejected
- Invalid JSON body rejected with 422
- Negative age (`age: -1`) rejected with 422
- Extreme BMI (`bmi: 200`) rejected with 422

### Database Security (2/2)
- `DATABASE_URL` not exposed in any API response
- `/health/db` returns generic message on failure — no raw backend error text leaked

### Container Security (1/1)
- Environment variables not exposed through any API endpoint

### Rate Limiting (3/3)
- Repeated auth attempts trigger 429 after 5 requests/minute
- `/health` endpoint not rate-limited (monitoring-safe)
- `/health/db` endpoint not rate-limited

### Common Vulnerabilities (3/3)
- Path traversal attempts (`../../etc/passwd`) safely handled
- Wrong HTTP method returns 405
- `OPTIONS` requests return safe response

---

## Static Analysis — Bandit

```
python -m bandit -r ingestion/ ml_engine/ dashboard/ -ll
```

| Severity | Count |
|----------|-------|
| High | 0 |
| Medium | 0 |
| Low | 1 (false positive) |

**Only finding:**
```
Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'bearer'
Location: ingestion/routers/auth_router.py:54
```

This is a known Bandit false positive. The string `"bearer"` is the standard OAuth2 token type identifier returned in the token response body — it is not a credential. No action required.

---

## Dependency Audit — pip-audit

```
python -m pip_audit -r requirements.docker.txt
```

**Result: No known vulnerabilities found**

Previously resolved: `python-jose==3.3.0` was pinned and had 4 CVEs (CVE-2024-33663, CVE-2024-33664 + GHSA mirrors). Upgraded to `python-jose==3.5.0` on 2026-04-22. Clean since.

---

## Open Items (Non-Blocking)

### 1. In-memory token revocation
**Risk:** LOW for single-instance demo; MEDIUM for production multi-instance deployment  
**Detail:** `ingestion/auth/token_blacklist.py` stores revoked tokens in a Python `set`. State is lost on restart. There is no `/auth/logout` endpoint.  
**Recommendation:** Add Redis-backed revocation + logout endpoint before productionising.

### 2. Weak SECRET_KEY not enforced at startup
**Risk:** LOW (configuration risk, not a code bug)  
**Detail:** `ingestion/auth/jwt.py` logs a warning when `SECRET_KEY` is short or default-like but does not raise. A misconfigured production deploy could use a weak secret.  
**Recommendation:** Add a hard startup check: `if ENV == "production" and len(SECRET_KEY) < 32: raise RuntimeError(...)`.

### 3. MLflow UI unauthenticated
**Risk:** LOW (internal only, not exposed via Nginx)  
**Detail:** MLflow runs on port 5000 with no auth. It is not proxied through Nginx in the current config, so only accessible on the Docker network or via direct port mapping.  
**Recommendation:** Add basic auth or IP restriction if MLflow is ever exposed externally.

### 4. Dashboard container healthcheck failing
**Risk:** OPERATIONAL (no security impact)  
**Detail:** `aegis-dashboard` shows `unhealthy` in `docker compose ps`. The Streamlit process is running but the healthcheck script may time out before Streamlit's startup completes.  
**Recommendation:** Increase `start_period` in the dashboard healthcheck or adjust the check interval.

---

## Files Implementing Security Controls

| File | Control |
|------|---------|
| `ingestion/auth/jwt.py` | JWT encode/decode, expiry, secret validation |
| `ingestion/auth/users.py` | User store + bcrypt verification |
| `ingestion/auth/dependencies.py` | `get_current_user`, `require_company_access` |
| `ingestion/auth/token_blacklist.py` | In-memory token revocation |
| `ingestion/rate_limit.py` | SlowAPI limiter instance |
| `ingestion/routers/auth_router.py` | `/auth/token` with 5/min rate limit |
| `ingestion/routers/ingest.py` | Company-level RBAC on all ingest routes |
| `ingestion/routers/health.py` | Safe DB health response (no error detail leaked) |
| `ingestion/main.py` | CORS, security headers middleware, rate-limit wiring |
| `nginx/nginx.conf` | TLS, HSTS, server header override |
| `scripts/entrypoint.sh` | `--no-server-header` flag on uvicorn startup |
| `tests/security_tests.py` | 27 automated security regression tests |

---

**See also:** [[Security Tests/TEST_REPORT]] | [[Phase Progress]] | [[INDEX]]
