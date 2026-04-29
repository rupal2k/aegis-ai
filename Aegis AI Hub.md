# Aegis AI — Project Hub

**Status**: All 6 Phases Complete ✅ + Security Hardening ✅ + Security Testing ✅ + UI Redesign ✅ + Design System Implementation ✅ + Chart Fixes ✅ + Compliance Illustrations ✅ + Brand Fonts ✅ + README Security Fix ✅ + /startserver Skill ✅ + Dashboard Bug Fixes ✅ + Login Form Fix ✅ + /loadcontext Skill ✅ + Brand Ref Cleanup ✅ + Post-Commit Hook Fix ✅ + Dashboard Overhaul ✅ + HF Dataset Integration ✅ + Clinical Notes Parser ✅ + MLflow Run Naming ✅ | **Deployed**: Docker + GitHub Actions CI  
**Repository**: `c:\Rupalprojects\aegis-ai`  
**Last Updated**: 2026-04-29

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

All 10 bugs resolved ✅ — full root causes, code snippets, and prevention rules in [[Bug Log]].

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| **Test Coverage** | 23/23 ✅ ML engine; 88 functional + security suite |
| **API Endpoints** | 13 live (incl. `/auth/token` login) |
| **Dashboard Tabs** | 7 (4 underwriter + 3 HR manager) |
| **Currencies** | 10 (INR, USD, EUR, GBP, AED, SGD, AUD, JPY, CAD, CHF) |
| **Risk Bands** | 4 — Low · Moderate · High · Critical |
| **Docker Services** | 5 — one `docker-compose up -d` |
| **CI Pipeline** | GitHub Actions: security scan → test → docker-build |
| **Auth** | JWT + bcrypt, 30-min session timeout |
| **Security** | HSTS, CSP, rate limiting, non-root container, TLS |

---

## 📝 Daily Progress

Dev journal: [[Daily Notes/Daily notes]] (Phase 5) · Phase 6 log embedded in [[Phase Progress]]

---

## ✅ Post-Capstone Additions

- [x] **Upload Dataset tab** — underwriters can analyse their own CSV workforce data (session-only, no DB storage)
- [x] **HIPAA / SOC 2 security hardening** — JWT auth, RBAC, TLS, audit logging, CORS, CI security scan
- [x] **Security test suite** — 25 automated security tests (all passing after remediation)
- [x] **Security remediation** — stale Docker image, non-root user, rate limiting, security headers, server header suppression
- [x] **NullMask UI redesign** — replaced dark theme with NullMask light design system; Space Grotesk font, `#C4FF00` accent, ∅ logo mark, white metric cards, production-ready B2B aesthetic across all 6 dashboard files
- [x] **Swagger UI CSP fix** — `ingestion/main.py` middleware now exempts `/docs`, `/redoc`, `/openapi.json` from strict `script-src 'self'` CSP in development mode, allowing Swagger UI to load from `cdn.jsdelivr.net`
- [x] **NullMask design system implementation** — fetched official design bundle (claude.ai/design), audited all 14 design elements, implemented 6 missing ones: user avatar with initials, data-driven alerts panel, risk band mini-cards, numbered AI recommendations with estimated savings, glow shadow CSS variant, thin scrollbar
- [x] **HR dashboard chart fixes** — waterfall per-bar colours (gray/green/accent-olive) + dotted connector + outside labels; donut zero-band filtering + mean HRS centre annotation (`bd13c22`)
- [x] **NullMask isometric illustrations** — 4 SVG design elements placed across dashboard pages: Privacy Vault on login, Privacy Router on underwriter portfolio tab, Privacy Shield on HR workforce tab, Zero Node on upload empty state; stored as base64 data URIs in `dashboard/illustrations.py` (`9b0ce1f`, `5dfbe76`)
- [x] **Plotly Waterfall API fix** — replaced invalid `marker_color` array with correct `decreasing`/`totals`/`increasing` sub-objects; HR ROI tab now renders correctly (`b6afd7c`)
- [x] **Brand fonts** — NType82 (display headlines/tabs), LetteraMonoLL (metric values/delta/chart numbers), Inter (body/labels/captions) embedded as base64 `@font-face` in `dashboard/illustrations.py`; `BRAND_FONT_CSS` injected globally from `app.py` (`925c6ee`)
- [x] **Compliance illustrations** — replaced 4 NullMask privacy SVGs with Aegis-specific compliance art from design bundle: SOC 2 → login, Group Insurance → underwriter portfolio, HIPAA Privacy → HR workforce tab, Employee Health → upload empty state (`925c6ee`)
- [x] **README security fix** — removed demo credentials table (`underwriter@safenet.com`, `hr@technova.com`, `hr@bharatsteel.com`) from public README to prevent credential exposure (`0da4a1e`)
- [x] **`/startserver` Claude Code skill** — `.claude/commands/startserver.md` automates full stack startup: stops native processes, `docker compose down/up`, health checks (API/Dashboard/MLflow/PostgreSQL/nginx), module import tests, syntax checks (`dbf8b2c`)
- [x] **Login form input sizing fix** — reduced oversized Streamlit `st.text_input` fields from ~46px to compact 38px height via targeted CSS in `app.py` (`4551f47`)
- [x] **Remove NullMask brand references** — stripped all 7 occurrences of "NullMask" from docstrings, comments, CSS, and skills; design tokens and visual style unchanged (`84597d2`)
- [x] **`/loadcontext` Claude Code skill** — session-start slash command that loads all 6 memory files + 5 vault files, outputs a structured context brief, and enforces architecture/security/design/code/vault guardrails before any code work begins (`17d9b68`)
- [x] **Post-commit hook hardening** — dedup guard + vault-commit skip + explicit repo context; prevents duplicate log entries and infinite commit loops (`6730057`)
- [x] **Dashboard UI overhaul & design system alignment** — comprehensive update of all 5 dashboard modules to `design.md` contract; dark text scale, `apply_chart_theme()` everywhere, risk-band mini-cards and alerts panel refined (`8ebcd93`)
- [x] **HF dataset integration + scorer hardening** — `load_from_huggingface()` with HF Hub support; `load_training_dataframe()` with `local`/`hf`/`both` modes and graceful fallback; `HRSScorer._normalize()` degenerate-distribution guard; `--use-local`/`--use-hf`/`--use-both` CLI flags; 7 new pipeline tests (`d0ef776`)
- [x] **Clinical notes parser — HF source switch** — `_parse_clinical_note()` regex parser extracts age, gender, BMI, 13 condition flags, ICU, SpO2 from 19,756 discharge notes; synthesises wearable telemetry from severity; `ayush0205/clinical_data_rf` replaces previous tabular HF dataset (`818f5fd`)
- [x] **MLflow run auto-naming** — `_build_run_name()` derives descriptive names from data sources; retroactively renamed 3 existing runs for clarity in MLflow UI (`2caac54`)

## 🔧 Next Steps (Post-Capstone)

- [ ] **Fix ingest RBAC gap** — add `require_company_access` to `/ingest/wearable`, `/ingest/clinical`, `/ingest/company` (hr_admin can currently inject data for other companies)
- [ ] OAuth 2.0 / SAML authentication (replace file-based user store)
- [ ] Deploy to cloud — see [[Aegis AI - Free Deployment Plan]] (Neon + Render + Hugging Face Spaces)
- [ ] Live FX API integration (replace static rates)
- [ ] Real-time pipeline (Kafka streaming HRS updates)
- [ ] Model drift monitoring + auto-retrain triggers
- [ ] Kubernetes deployment with horizontal scaling
