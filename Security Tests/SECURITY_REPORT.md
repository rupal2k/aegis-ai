# Aegis AI - Comprehensive Security Test Report
**Date Generated:** April 24, 2026  
**Audit Scope:** Live localhost verification, automated security tests, dependency audit, and manual code review  
**Repository:** `c:\Rupalprojects\aegis-ai`

---

## Executive Summary

This audit replaced the stale April 22 report with a current review of the codebase and live environment on **April 24, 2026**.

Two important facts were true at the start of this audit:

1. The **running localhost API on `http://localhost:8000`** was a native host process, not the Docker API container. During the initial live check it still exposed a duplicate `Server` header containing **`uvicorn`**, which means that specific process had not been started with `--no-server-header`.
2. The **checked-in code** had real security gaps not reflected in the latest vault summary:
   - `/auth/token` was **not actually rate limited** despite the code comments and docs claiming it was.
   - `/ingest/wearable`, `/ingest/clinical`, and `/ingest/company` allowed an `hr_admin` to target another company's `company_id`.
   - `/health/db` could return raw backend exception text.
   - `requirements.docker.txt` still pinned **`python-jose==3.3.0`**, which `pip-audit` flagged with known advisories.

These issues were remediated in the repo during this session, and the patched code was verified on a temporary updated server.

### Final Outcome

- **Patched security suite:** `27/27 passing`
- **Dependency audit after fixes:** `0 known vulnerabilities`
- **Overall code posture after remediation:** `LOW-MEDIUM risk`

### Residual Caveat

The **currently running localhost process on port 8000 was not restarted by this audit**, so its observed header behavior may still reflect the old startup command until it is restarted with the updated guidance.

---

## Audit Method

### 1. Live localhost verification
Checked the already-running API at `http://localhost:8000`.

Key observations:
- `GET /health` returned `200 OK`
- Response headers included both `server: uvicorn` and `server: AegisAI`
- Invalid CORS origin was rejected with `400 Disallowed CORS origin`
- `/docs`, `/redoc`, and `/openapi.json` were available, indicating development mode

### 2. Automated security suite
Ran:

```bash
python -m pytest tests/security_tests.py -v --tb=short
```

Initial live result against the old localhost process:
- `24 passed, 1 failed`
- The single failure was **server header leakage** (`uvicorn, aegisai`)

After remediation, the suite was re-run against a temporary updated server on `127.0.0.1:8001` with host-compatible DB settings:

```bash
AEGIS_BASE_URL=http://127.0.0.1:8001 python -m pytest tests/security_tests.py -v --tb=short
```

Final patched result:
- `27 passed, 0 failed`

### 3. Dependency audit
Ran `pip-audit` against `requirements.docker.txt`.

Before fix:
- `4 known vulnerabilities in 1 package`
- All findings were tied to `python-jose==3.3.0`

After updating the Docker requirements pin:
- `No known vulnerabilities found`

### 4. Manual security review
Reviewed current security-sensitive files directly:
- `ingestion/main.py`
- `ingestion/rate_limit.py`
- `ingestion/routers/auth_router.py`
- `ingestion/routers/ingest.py`
- `ingestion/routers/health.py`
- `ingestion/auth/dependencies.py`
- `ingestion/auth/jwt.py`
- `Dockerfile.api`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `dashboard/auth.py`

Note: a Bandit run was attempted via a workspace-local install, but that sandbox-local install did not expose a runnable entrypoint cleanly. The final report therefore relies on the successful dynamic tests, dependency scan, and manual code review above.

---

## Findings

## 1. Resolved During This Audit

### 1.1 Missing auth rate limiting
**Severity:** HIGH  
**Status:** RESOLVED

**What was wrong**
- The app initialized `slowapi`, but `/auth/token` had no limiter decorator.
- Live verification confirmed repeated invalid login attempts returned only `401` responses and were never throttled.

**Evidence**
- Six consecutive invalid login attempts returned: `[401, 401, 401, 401, 401, 401]`

**Fix applied**
- Added shared rate-limit module: `ingestion/rate_limit.py`
- Wired proper SlowAPI exception handling in `ingestion/main.py`
- Added `@limiter.limit("5/minute")` to `POST /auth/token`
- Added regression test: `test_auth_endpoint_rate_limited`

**Verification**
- Patched suite confirmed repeated auth attempts now produce `429` responses

---

### 1.2 Cross-company ingest authorization bypass
**Severity:** HIGH  
**Status:** RESOLVED

**What was wrong**
- Ingest routes only used `get_current_user`, not company-level authorization.
- An `hr_admin` tied to `COMP_001` could submit a roster for `COMP_002`.

**Live reproduction before fix**
- Logged in as `hr@technova.com`
- Submitted `POST /ingest/company` for `COMP_002`
- API returned `201 Created`

**Fix applied**
- Added `require_company_access(payload.company_id, user)` checks to:
  - `/ingest/wearable`
  - `/ingest/clinical`
  - `/ingest/company`
- Added regression test: `test_hr_admin_cannot_ingest_other_company_roster`

**Verification**
- Patched suite confirmed cross-company roster ingest now returns `403`

---

### 1.3 DB health endpoint leaked backend error details
**Severity:** MEDIUM  
**Status:** RESOLVED

**What was wrong**
- `/health/db` returned raw exception text when DB connectivity failed.
- In host-native runs with Docker-style `DATABASE_URL=db:5432`, the endpoint could expose backend details, including external docs links embedded in exception messages.

**Fix applied**
- `ingestion/routers/health.py` now logs the exception server-side and returns a generic failure message:
  - `detail: "Database connectivity check failed"`

**Verification**
- Patched security suite passed `test_db_health_endpoint_safe`

---

### 1.4 Vulnerable Docker dependency pin
**Severity:** MEDIUM  
**Status:** RESOLVED

**What was wrong**
- `requirements.docker.txt` pinned `python-jose[cryptography]==3.3.0`
- `pip-audit` reported 4 advisories tied to that package version:
  - `CVE-2024-33663`
  - `CVE-2024-33664`
  - mirrored GHSA/PYSEC records for the same issues

**Fix applied**
- Updated `requirements.docker.txt` to `python-jose[cryptography]==3.5.0`
- This also aligned Docker with the less-stale local `requirements.txt`

**Verification**
- Re-ran `pip-audit`
- Result: `No known vulnerabilities found`

---

## 2. Environment-Specific Observation Still Relevant

### 2.1 Native localhost process still leaked `uvicorn` server header at audit start
**Severity:** LOW-MEDIUM  
**Status:** OBSERVED ON EXISTING PROCESS

**What was observed**
- The live process already running on `http://localhost:8000` returned both:
  - `server: uvicorn`
  - `server: AegisAI`

**Why this happened**
- Docker entrypoint already uses `--no-server-header`
- During this audit, `docker compose ps` showed only `db` and `mlflow` containers running
- So the API on `:8000` was not the Docker API container, but a native host process started separately

**Fix applied to repo**
- Updated `README.md` local dev command to use:

```bash
uvicorn ingestion.main:app --reload --no-server-header
```

**Important note**
- The old localhost process was **not restarted by this audit**, so this finding applies to that pre-existing process until it is restarted.
- The patched temporary verification server on `127.0.0.1:8001` passed the server-header test cleanly.

---

## 3. Additional Observations

### 3.1 CORS behavior
**Status:** ACCEPTABLE FOR CURRENT DEV SETUP

Observed behavior:
- Allowed localhost origins are configurable through `ALLOWED_ORIGINS`
- Invalid origin (`http://evil.example`) was rejected with `400 Disallowed CORS origin`

Risk note:
- Still depends on correct environment configuration per deployment

---

### 3.2 Token revocation remains in-memory only
**Status:** OPEN / NON-BLOCKING FOR DEMO

- `ingestion/auth/token_blacklist.py` uses an in-memory blacklist
- There is still no logout endpoint using it
- Revocation state would not survive process restart or multi-instance deployment

Recommendation:
- If productionized, move revocation to Redis or database-backed storage and add logout/refresh flows

---

### 3.3 Secret enforcement is still warning-based
**Status:** OPEN / CONFIGURATION RISK

- `ingestion/auth/jwt.py` warns if `SECRET_KEY` is short or default-like
- It does **not** fail closed on weak production secrets

Recommendation:
- Enforce strong secret requirements at startup when `ENV != development`

---

### 3.4 Native host startup still needs explicit DB override
**Status:** OPEN / OPERATIONAL NUANCE

- `.env` currently uses Docker-internal DB hostname: `db:5432`
- This is correct for containers but not for host-native API startup

Recommended host-native override:

```bash
DATABASE_URL=postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db
```

---

## Files Changed During This Audit

### Security fixes
- `ingestion/rate_limit.py` — new shared SlowAPI limiter module
- `ingestion/main.py` — proper rate-limit exception handling via SlowAPI helper
- `ingestion/routers/auth_router.py` — actual `5/minute` rate limiting on `/auth/token`
- `ingestion/routers/ingest.py` — company-level RBAC enforced on all ingest routes
- `ingestion/routers/health.py` — DB health endpoint no longer leaks raw backend errors
- `requirements.docker.txt` — `python-jose` upgraded from `3.3.0` to `3.5.0`
- `README.md` — local dev API startup updated to include `--no-server-header`

### Security test coverage
- `tests/security_tests.py`
  - base URL made configurable via `AEGIS_BASE_URL`
  - added `test_hr_admin_cannot_ingest_other_company_roster`
  - added `test_auth_endpoint_rate_limited`

---

## Final Verification Results

### Patched automated suite
```text
27 passed, 0 failed
```

### Dependency audit
```text
No known vulnerabilities found
```

### Live localhost note
```text
Existing localhost :8000 process was not restarted during this audit.
Its initial server-header behavior should be considered stale runtime state,
not the final verified state of the patched code.
```

---

## Recommended Next Steps

### Immediate
1. Restart the existing native API process on `:8000` with `--no-server-header` so the live localhost runtime matches the patched repo state.
2. Rebuild any Docker image that consumes `requirements.docker.txt` so the `python-jose` fix is actually deployed.
3. Keep using the updated `tests/security_tests.py` suite in CI or local verification.

### Short-term
1. Fail closed on weak/default `SECRET_KEY` values outside development.
2. Add persistent token revocation and a logout/refresh flow.
3. Consider adding rate limiting to other write-heavy or sensitive endpoints beyond `/auth/token`.

### Long-term
1. Add production-oriented static analysis execution to local/release workflows, not just CI.
2. Add Redis-backed rate-limit and token revocation storage for multi-instance deployment.
3. Review MLflow exposure and authentication if used beyond local development.

---

## Conclusion

As of **April 24, 2026**, the stale critical findings from the earlier report are no longer accurate for the patched codebase.

This audit confirmed and remediated the most important current issues:
- missing auth throttling
- cross-company ingest authorization bypass
- DB health error leakage
- vulnerable Docker dependency pin

The patched code verified cleanly with **27/27 security tests passing** and a **clean dependency audit**.

The only notable mismatch left is runtime-specific: the already-running localhost API process observed at the start of this audit was not restarted, so its server-header behavior may still reflect pre-audit startup flags until relaunched.
