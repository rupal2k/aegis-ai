# Aegis AI — Project Index

**Last Updated**: 2026-04-22

## 📍 Main Navigation

### LLM Guidelines (Read First)
- **[[../memory]]** — Master LLM guide: Karpathy principles + all project rules (START HERE FOR ANY AI SESSION)
- **[[behaviour]]** — Aegis AI-specific quick-reference (subset of memory.md)

### Project Management
- **[[Aegis AI Hub]]** — Overview, status, metrics
- **[[User Manual Cheat Sheet]]** — Quick operational guide: startup, login, dashboard use, training, and health checks
- **[[Phase Progress]]** — Detailed checklist for all 6 phases + post-capstone additions
- **[[Bug Log]]** — 9 bugs, root causes, fixes, prevention
- **[[Claude Memory]]** — Claude's persistent memory: user profile, feedback rules, project state
- **[[Commit Log]]** — Auto-appended git commit history (hook-driven)
- **[[Daily Notes/Daily notes]]** — Phase 5 dev journal

### Presentation
- **[[Aegis AI - Presentation]]** — Full project slide deck (Advanced Slides, 16 slides, reveal.js)

### Security
- **[[Security Tests/SECURITY_REPORT]]** — Full 25-test security audit report (2026-04-22, 25/25 passing)

### Deep Dives (from actual code)
- **[[Data Generation & Pipeline]]** — How 5K employees + 60K telemetry rows were built
- **[[ML Engine Architecture]]** — XGBoost, Optuna, SHAP, HRSScorer — full internals
- **[[API Layer Architecture]]** — FastAPI endpoints, Pydantic validation, routing
- **[[Dashboard Deep Dive]]** — Streamlit views, currency module, PDF generator
- **[[System End-to-End Flow]]** — Full data journey from raw CSV to PDF download

### Decision Documentation
- **[[Decisions & Rationale]]** — 10 logical decisions with tradeoff analysis
- **[[Architecture Decisions]]** — 15 ADRs (final design choices)

### Deployment
- **[[Aegis AI - Free Deployment Plan]]** — Neon + Render + Hugging Face Spaces (₹0/month)

## 🚀 Status

| Item | Status |
|------|--------|
| All 6 Phases | ✅ Complete |
| Docker Stack | ✅ 5 services (+ nginx TLS), one `docker-compose up -d` |
| CI/CD | ✅ GitHub Actions (security scan → test → docker-build) |
| Dashboard | ✅ Live (dark mode, multi-currency) |
| Tests | ✅ 88/88 passing (63 functional + 25 security) |
| Bugs | ✅ All 9 resolved |
| Auth | ✅ JWT + bcrypt, 30-min timeout |
| Security | ✅ HSTS, CSP, rate limiting, non-root container |

## 📂 File Structure

```
C:\Rupalprojects\Rupal\                   ← vault root
├── memory.md                             (master LLM guide — read first)
└── Aegis AI\                             ← project notebook
    ├── INDEX.md                          (this file — navigation)
    ├── behaviour.md                      (Aegis AI-specific LLM rules)
    ├── Aegis AI Hub.md                   (project overview + status)
    ├── Phase Progress.md                 (phase checklists + dev logs)
    ├── Bug Log.md                        (7 bugs, root causes, fixes)
    ├── Claude Memory.md                  (Claude auto-memory — user profile, feedback, project state)
    ├── Commit Log.md                     (auto-appended git commit history via hook)
    ├── Aegis AI - Presentation.md        (full project slide deck — Advanced Slides, 16 slides)
    ├── Decisions & Rationale.md          (10 logical decisions)
    ├── Architecture Decisions.md         (18 ADRs — includes JWT, rate limiting, security headers)
    ├── Aegis AI - Free Deployment Plan.md (Neon + Render + HF Spaces deployment)
    ├── System End-to-End Flow.md         (full data journey)
    ├── Data Generation & Pipeline.md     (Phase 1 deep dive)
    ├── ML Engine Architecture.md         (Phase 2 deep dive)
    ├── API Layer Architecture.md         (Phase 3-4 deep dive)
    ├── Dashboard Deep Dive.md            (Phase 5 deep dive)
    ├── Daily Notes\
    │   └── Daily notes.md                (Phase 5 dev journal)
    └── Security Tests\
        ├── SECURITY_REPORT.md            (25-test audit report, 2026-04-22)
        ├── security_report.json          (machine-readable results)
        ├── SECURITY_TEST_SUMMARY.txt     (quick summary)
        └── security_tests.py             (25 automated security tests)
```

## 💡 Quick Tips

1. **AI session starting?** Read **[[../memory]]** before touching any code or docs
2. **New to the project?** Start with **[[Aegis AI Hub]]** for overview
3. **Checking progress?** See **[[Phase Progress]]** — all 6 phases complete
4. **Hit a bug?** Check **[[Bug Log]]** first — 7 pitfalls already documented
5. **Making a design decision?** See **[[Decisions & Rationale]]** and **[[Architecture Decisions]]**
6. **Updating the vault?** Follow the rules in **[[../memory]]** Part 4

## 🔗 External Links

- **Repository**: `c:\Rupalprojects\aegis-ai`
- **API Server**: `http://localhost:8000` (when running)
- **Dashboard**: `http://localhost:8501` (Docker or `streamlit run dashboard/app.py`)
- **MLflow**: `http://localhost:5000` (Docker)
- **GitHub**: `https://github.com/rupal2k/aegis-ai`

---

*This is a lightweight navigation index. Full content is in individual .md files.*

