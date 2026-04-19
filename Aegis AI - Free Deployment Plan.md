# Aegis AI — Free Deployment Plan

**Date:** 2026-04-18
**Status:** Planned
**Related:** [[Aegis AI Hub]]

## Goal
Deploy the full Aegis AI stack (Dashboard + API + Postgres) on a completely free, permanent URL for the capstone demo.

## The Three-Platform Split

| Layer | Platform | Free allowance | Catch |
|-------|----------|----------------|-------|
| Dashboard | Hugging Face Spaces | Always-on, 16 GB RAM | Public code |
| API | Render | 750 hrs/month, sleeps after 15 min idle | 30-60s cold start |
| Postgres | Neon | 0.5 GB, never sleeps | Serverless only |

**Total cost:** ₹0/month forever

## Architecture
- Visitor → Hugging Face Spaces (Streamlit)
- Streamlit → Render (FastAPI)
- FastAPI → Neon (Postgres)

## Deployment Steps

### 1. Neon Postgres
- Sign up at neon.tech (GitHub login)
- Create project `aegis-ai`
- Save connection string: `postgresql://...neon.tech/aegis_db?sslmode=require`

### 2. Seed Remote DB (from local)
```powershell
$env:DATABASE_URL = "postgresql://...neon.tech/..."
python data\load_to_db.py
```

### 3. Render API
- Simplified `render.yaml` — only API service, no Render Postgres
- Set `DATABASE_URL` manually in Render dashboard (Neon string)
- Simplify `entrypoint.sh` to skip bootstrap (Neon already seeded)
- Deploy via Blueprint — get URL `https://aegis-api.onrender.com`

### 4. Hugging Face Dashboard
- New Space → Docker SDK → port 7860
- Separate git repo (not main aegis-ai repo)
- Copy: dashboard/, ml_engine/, ingestion/, requirements.txt
- Dockerfile uses port 7860
- README.md needs YAML front matter (title, sdk, app_port)
- Secrets: AEGIS_API_URL, DATABASE_URL
- Push → auto-builds → `https://USERNAME-aegis-dashboard.hf.space`

## Key Files to Modify

### render.yaml
- Remove Render Postgres service
- Remove dashboard service (moves to HF)
- `DATABASE_URL` uses `sync: false` (manual entry)

### scripts/entrypoint.sh
- Remove bootstrap call (Neon already has data)
- Just `exec uvicorn ingestion.main:app --host 0.0.0.0 --port ${PORT:-8000}`

### Dockerfile (HF version)
- Change `EXPOSE 8501` → `EXPOSE 7860`
- Update CMD to use port 7860

### HF README.md front matter
```yaml
---
title: Aegis AI Dashboard
emoji: 🛡️
sdk: docker
app_port: 7860
---
```

## Pre-Demo Checklist
- [ ] Neon project + connection string saved
- [ ] 20 companies loaded in Neon (verify with COUNT query)
- [ ] Render `/health` returns OK
- [ ] Render `/predict/company/COMP_001` returns data
- [ ] HF Space builds successfully
- [ ] HF secrets set (AEGIS_API_URL, DATABASE_URL)
- [ ] Login works end-to-end on HF URL
- [ ] README updated with live URLs
- [ ] **Warm-up test 15 min before presentation**

## Risks & Mitigations
- **API cold start** → Warn faculty "first load takes 30s"
- **Free tier changes** → Test 1 week before demo
- **Neon connection limits** → 0.5 GB is plenty; no concern

## Tags
#deployment #capstone #aegis-ai #free-tier
