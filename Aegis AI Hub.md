# Aegis AI — Project Hub

**Status**: All 6 Phases Complete ✅ + Security Hardening ✅ + Security Testing ✅ | **Deployed**: Docker + GitHub Actions CI  
**Repository**: `c:\Rupalprojects\aegis-ai`  
**Last Updated**: 2026-04-22

---

## 🎯 Project Overview

Aegis AI is an **AI-powered B2B group insurance underwriting platform** that predicts employee health risk, adjusts premiums dynamically, and provides wellness ROI projections to HR teams.

**Tech Stack**:
- Backend: FastAPI (Python)
- Frontend: Streamlit (Python)
- ML: XGBoost + SHAP
- Database: PostgreSQL (Docker) / SQLite (local dev fallback)
- Reports: ReportLab (PDF generation)
- Global Support: 10 currencies (INR, USD, EUR, GBP, AED, SGD, AUD, JPY, CAD, CHF)

---

## 📋 Quick Links

| Section | Purpose |
|---------|---------|
| [[../memory]] | **Master LLM guide** — read before any AI coding session |
| [[behaviour]] | Aegis AI-specific LLM rules (quick reference) |
| [[Phase Progress]] | All 6 phases complete — checklists + dev logs |
| [[Decisions & Rationale]] | 10 logical decisions with deep tradeoff analysis |
| [[Architecture Decisions]] | Design decisions, patterns, tradeoffs (15 ADRs) |
| [[Bug Log]] | 7 bugs — root causes, fixes, prevention |
| [[Claude Memory]] | Claude's session memory — what AI knows about this project |

---

## 🚀 Phase Status

- ✅ **Phase 1**: Data setup & synthetic generation
- ✅ **Phase 2**: ML model training (XGBoost + SHAP)
- ✅ **Phase 3**: FastAPI backend core
- ✅ **Phase 4**: Premium calc & prediction endpoints
- ✅ **Phase 5**: Streamlit dashboard (underwriter + HR views)
- ✅ **Phase 6**: Containerisation & CI/CD (Docker + GitHub Actions)

👉 See [[Phase Progress]] for detailed checklist.

---

## 🏗️ Architecture at a Glance

```
┌──────────────────────────────────────────────┐
│   Streamlit Dashboard  (port 8501)           │
│  ├─ Underwriter Console  (all 20 companies)  │
│  └─ HR Manager Dashboard (single company)    │
└──────────────────┬───────────────────────────┘
                   │ httpx (@st.cache_data ttl=60)
                   ↓
┌──────────────────────────────────────────────┐
│   FastAPI Backend  (port 8000)               │
│  ├─ /predict/company/{id}  ← XGBoost + SHAP  │
│  ├─ /predict/premium       ← 3-zone pricing  │
│  ├─ /predict/wellness-roi  ← ROI simulator   │
│  └─ /companies/*           ← Dashboard data  │
└──────────────────┬───────────────────────────┘
                   │ SQLAlchemy ORM
                   ↓
┌──────────────────────────────────────────────┐
│   PostgreSQL  (port 5432)                    │
│   companies | employees | training_snapshots │
│   telemetry | clinical_events                │
└──────────────────────────────────────────────┘
         MLflow (port 5000) tracks training runs
```

👉 See [[Architecture Decisions]] for detailed design rationale.

---

## 🔴 Issues & Fixes

All 7 bugs resolved ✅ — full root causes, code snippets, and prevention rules in [[Bug Log]].

---

## 📊 Key Metrics

- **Test Coverage**: 88/88 automated tests passing (63 functional + 25 security)
- **API Endpoints**: 12 live (+ `/auth/token` login)
- **Dashboard Tabs**: 7 total (4 underwriter + 3 HR manager)
- **Currencies Supported**: 10 (all dynamic, no hardcoding)
- **Risk Bands**: 4 (Low, Moderate, High, Critical)
- **Docker Services**: 5 (db, mlflow, api, dashboard, nginx) — one `docker-compose up -d`
- **CI Pipeline**: GitHub Actions — security scan (bandit + pip-audit) → test → docker-build
- **Auth**: JWT bearer tokens, bcrypt passwords, 30-min session timeout
- **Security**: HSTS, CSP, X-Frame-Options, rate limiting, non-root container, TLS via nginx

---

## 📝 Daily Progress

Dev journal: [[Daily Notes/Daily notes]] (Phase 5) · Phase 6 log embedded in [[Phase Progress]]

---

## ✅ Post-Capstone Additions

- [x] **Upload Dataset tab** — underwriters can analyse their own CSV workforce data (session-only, no DB storage)
- [x] **HIPAA / SOC 2 security hardening** — JWT auth, RBAC, TLS, audit logging, CORS, CI security scan
- [x] **Security test suite** — 25 automated security tests (all passing after remediation)
- [x] **Security remediation** — stale Docker image, non-root user, rate limiting, security headers, server header suppression

## 🔧 Next Steps (Post-Capstone)

- [ ] **Fix ingest RBAC gap** — add `require_company_access` to `/ingest/wearable`, `/ingest/clinical`, `/ingest/company` (hr_admin can currently inject data for other companies)
- [ ] OAuth 2.0 / SAML authentication (replace file-based user store)
- [ ] Deploy to cloud — see [[Aegis AI - Free Deployment Plan]] (Neon + Render + Hugging Face Spaces)
- [ ] Live FX API integration (replace static rates)
- [ ] Real-time pipeline (Kafka streaming HRS updates)
- [ ] Model drift monitoring + auto-retrain triggers
- [ ] Kubernetes deployment with horizontal scaling
