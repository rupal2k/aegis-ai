# Aegis AI — LLM Quick Reference

**This is a session-start cheat sheet. All rules live in [[../memory]] — read that first.**

---

## Pre-Flight (every session)

```
1. git status && git log --oneline -5
2. Check [[Phase Progress]] and [[Bug Log]]
3. docker-compose ps  (if touching API or dashboard)
4. Read the file before editing it
```

---

## Health Check

Run all at once after `docker-compose up -d` to confirm the stack is healthy.

### 1 — Service status
```bash
docker-compose ps
```
Expected: all 4 services (db, mlflow, api, dashboard) Up / healthy.

### 2 — API health
```bash
curl -s http://localhost:8000/health
# Expected: {"status":"ok","service":"aegis-ingestion"}
```

### 3 — Database row counts
```bash
docker exec aegis-db psql -U aegis_user -d aegis_db \
  -c "SELECT COUNT(*) as companies FROM companies;" \
  -c "SELECT COUNT(*) as employees FROM employees;" \
  -c "SELECT COUNT(*) as telemetry FROM telemetry;"
# Expected: 20 | 5002 | 60003
```

### 4 — API endpoints
```bash
# Company list
curl -s http://localhost:8000/companies | python -c \
  "import sys,json; d=json.load(sys.stdin); print(f'Companies: {len(d)}')"

# ML prediction
curl -s http://localhost:8000/predict/company/COMP_001 | python -c \
  "import sys,json; d=json.load(sys.stdin); \
   print(f'mean_hrs={d[\"mean_hrs\"]}, employees={d[\"employee_count\"]}, risk_band={d[\"risk_band\"]}')"

# Premium calc
curl -s -X POST http://localhost:8000/predict/premium \
  -H "Content-Type: application/json" \
  -d '{"company_id":"COMP_001","mean_hrs":24.1,"employee_count":156,"currency":"USD","base_premium":500,"hrs":24.1}' | \
  python -c "import sys,json; d=json.load(sys.stdin); \
   print(f'adjusted_premium={d[\"adjusted_premium\"]}, zone={d[\"zone\"]}')"
```
Expected: Companies=20 · risk_band=Low · zone=discount

### 5 — Dashboard & MLflow
```bash
curl -s -o /dev/null -w "Dashboard: %{http_code}\n" http://localhost:8501
curl -s -o /dev/null -w "MLflow:    %{http_code}\n" http://localhost:5000
# Expected: 200 for both
```

### 6 — Full test suite
```bash
python -m pytest tests/ -q --tb=no
# Expected: 63 passed
```

**Last verified:** 2026-04-19 — all checks passed.

---

## Rules by Topic

| Topic | Location |
|-------|----------|
| Universal LLM principles (Karpathy) | [[../memory]] Part 1 |
| Python, CSS/Streamlit, Docker, Git rules | [[../memory]] Part 2 |
| Known pitfalls — BUG-001 to BUG-007 | [[../memory]] Part 3 |
| Vault maintenance rules | [[../memory]] Part 4 |
| Response style | [[../memory]] Part 5 |
| Constants (ports, credentials, dark mode palette) | [[../memory]] Part 6 |

---

## Vault Update Targets

| Change | Update |
|--------|--------|
| Bug fixed | `Bug Log.md` + `memory.md` Part 3 |
| Phase / feature work | `Phase Progress.md` (relevant section) |
| Architecture decision | `Architecture Decisions.md` or `Decisions & Rationale.md` |
| New pitfall | `Bug Log.md` + `memory.md` Part 3 |
| Constants changed | `memory.md` Part 6 |
| Graph View / vault config changed | `Claude Memory.md` → Graph View Color Scheme section |

*No separate daily notes for phase work — merge into `Phase Progress.md`.*
*Vault is the persistent brain — record all session decisions before closing.*
