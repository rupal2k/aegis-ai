# Aegis AI â€” Project Index

**Last Updated**: 2026-04-29

## ðŸ“ Main Navigation

### LLM Guidelines (Read First)
- **[[../memory]]** â€” Master LLM guide: Karpathy principles + all project rules (START HERE FOR ANY AI SESSION)
- **[[behaviour]]** â€” Aegis AI-specific quick-reference (subset of memory.md)

### Project Management
- **[[Aegis AI Hub]]** - Overview, status, metrics
- **[[User Manual Cheat Sheet]]** - Quick operational guide: startup, login, dashboard use, training, and health checks
- **[[Phase Progress]]** - Detailed checklist for all 6 phases + post-capstone additions
- **[[Bug Log]]** - 9 bugs, root causes, fixes, prevention
- **[[Claude Memory]]** - Claude's persistent memory: user profile, feedback rules, project state
- **[[Commit Log]]** - Auto-appended git commit history (hook-driven)
- **[[Daily Notes/Daily notes]]** - Phase 5 dev journal
- **[[Daily notes]]** - Legacy root working notes and dashboard retheme log

### Presentation
- **[[Aegis AI - Presentation]]** - Full project slide deck (Advanced Slides, 16 slides, reveal.js)

### Security
- **[[Security Tests/SECURITY_REPORT]]** - Full 25-test security audit report (2026-04-22, 25/25 passing)
- **[[Security Tests/TEST_REPORT]]** - Comprehensive functional test report and verification log

### Deep Dives (from actual code)
- **[[Data Generation & Pipeline]]** â€” How 5K employees + 60K telemetry rows were built
- **[[ML Engine Architecture]]** â€” XGBoost, Optuna, SHAP, HRSScorer â€” full internals
- **[[API Layer Architecture]]** â€” FastAPI endpoints, Pydantic validation, routing
- **[[Dashboard Deep Dive]]** â€” Streamlit views, currency module, PDF generator
- **[[System End-to-End Flow]]** â€” Full data journey from raw CSV to PDF download

### Decision Documentation
- **[[Decisions & Rationale]]** â€” 10 logical decisions with tradeoff analysis
- **[[Architecture Decisions]]** â€” 15 ADRs (final design choices)

### Deployment
- **[[Aegis AI - Free Deployment Plan]]** â€” Neon + Render + Hugging Face Spaces (â‚¹0/month)

## ðŸš€ Status

| Item | Status |
|------|--------|
| All 6 Phases | âœ… Complete |
| Docker Stack | âœ… 5 services (+ nginx TLS), one `docker-compose up -d` |
| CI/CD | âœ… GitHub Actions (security scan â†’ test â†’ docker-build) |
| Dashboard | âœ… Live (dark mode, multi-currency) |
| Tests | ✅ 75 passed, 5 skipped (latest full pytest) |
| Bugs | âœ… All 9 resolved |
| Auth | âœ… JWT + bcrypt, 30-min timeout |
| Security | âœ… HSTS, CSP, rate limiting, non-root container |

## ðŸ“‚ File Structure

```
C:\Rupalprojects\Rupal\                   â† vault root
â”œâ”€â”€ memory.md                             (master LLM guide â€” read first)
â””â”€â”€ Aegis AI\                             â† project notebook
    â”œâ”€â”€ INDEX.md                          (this file â€” navigation)
    â”œâ”€â”€ behaviour.md                      (Aegis AI-specific LLM rules)
    â”œâ”€â”€ Aegis AI Hub.md                   (project overview + status)
    â”œâ”€â”€ Phase Progress.md                 (phase checklists + dev logs)
    â”œâ”€â”€ Bug Log.md                        (7 bugs, root causes, fixes)
    â”œâ”€â”€ Claude Memory.md                  (Claude auto-memory â€” user profile, feedback, project state)
    â”œâ”€â”€ Commit Log.md                     (auto-appended git commit history via hook)
    â”œâ”€â”€ Aegis AI - Presentation.md        (full project slide deck â€” Advanced Slides, 16 slides)
    â”œâ”€â”€ Decisions & Rationale.md          (10 logical decisions)
    â”œâ”€â”€ Architecture Decisions.md         (18 ADRs â€” includes JWT, rate limiting, security headers)
    â”œâ”€â”€ Aegis AI - Free Deployment Plan.md (Neon + Render + HF Spaces deployment)
    â”œâ”€â”€ System End-to-End Flow.md         (full data journey)
    â”œâ”€â”€ Data Generation & Pipeline.md     (Phase 1 deep dive)
    â”œâ”€â”€ ML Engine Architecture.md         (Phase 2 deep dive)
    â”œâ”€â”€ API Layer Architecture.md         (Phase 3-4 deep dive)
    â”œâ”€â”€ Dashboard Deep Dive.md            (Phase 5 deep dive)
    â”œâ”€â”€ Daily Notes\
    â”‚   â””â”€â”€ Daily notes.md                (Phase 5 dev journal)
    â””â”€â”€ Security Tests\
        â”œâ”€â”€ SECURITY_REPORT.md            (25-test audit report, 2026-04-22)
        â”œâ”€â”€ security_report.json          (machine-readable results)
        â”œâ”€â”€ SECURITY_TEST_SUMMARY.txt     (quick summary)
        â””â”€â”€ security_tests.py             (25 automated security tests)
```

## ðŸ’¡ Quick Tips

1. **AI session starting?** Read **[[../memory]]** before touching any code or docs
2. **New to the project?** Start with **[[Aegis AI Hub]]** for overview
3. **Checking progress?** See **[[Phase Progress]]** â€” all 6 phases complete
4. **Hit a bug?** Check **[[Bug Log]]** first â€” 7 pitfalls already documented
5. **Making a design decision?** See **[[Decisions & Rationale]]** and **[[Architecture Decisions]]**
6. **Updating the vault?** Follow the rules in **[[../memory]]** Part 4

## ðŸ”— External Links

- **Repository**: `c:\Rupalprojects\aegis-ai`
- **API Server**: `http://localhost:8000` (when running)
- **Dashboard**: `http://localhost:8501` (Docker or `streamlit run dashboard/app.py`)
- **MLflow**: `http://localhost:5000` (Docker)
- **GitHub**: `https://github.com/rupal2k/aegis-ai`

---

*This is a lightweight navigation index. Full content is in individual .md files.*


