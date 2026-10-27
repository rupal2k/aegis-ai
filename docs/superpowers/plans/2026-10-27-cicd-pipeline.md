# CI/CD Pipeline Implementation Plan (Render & Hugging Face Spaces)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish an end-to-end automated CI/CD pipeline for Aegis AI that unbreaks CI validation, tests the complete stack, and automatically deploys the FastAPI backend to Render and the Streamlit dashboard to Hugging Face Spaces on merges to `main`.

**Architecture:** A unified, resilient GitHub Actions workflow structure consisting of three core stages:
1. **CI Quality & Security Gate**: SAST analysis (Bandit), dependency vulnerability audit (pip-audit with report artifact upload), ephemeral PostgreSQL 15 integration tests with synthetic data generation and fast model training, and multi-stage Docker build verification.
2. **CD - Render Web Service**: Automated trigger of Render's deploy hook for the FastAPI backend service (`aegis-api`) defined in `render.yaml`, with fallback status logging.
3. **CD - Hugging Face Space**: Automated git synchronization of the repository and Streamlit dashboard (`Dockerfile`) to `https://huggingface.co/spaces/Rupa2k/aegis-ai` using `HF_TOKEN`.

**Tech Stack:** GitHub Actions, Docker Buildx, PostgreSQL 15, FastAPI, Streamlit, Render Webhook API, Hugging Face Spaces Git LFS, Pytest.

**Spec:** Automated CI/CD pipeline targeting Render (`aegis-api` / `Dockerfile.api`) and Hugging Face Spaces (`Rupa2k/aegis-ai` / `Dockerfile`), fixing existing pipeline failures and securing test credentials.

## Global Constraints

- Workflow files must reside in `.github/workflows/`.
- CI must run on `push: [main, develop]` and `pull_request: [main]`.
- CD jobs must only execute on `push: [main]` after CI jobs succeed.
- Missing deployment secrets (`RENDER_DEPLOY_HOOK_URL`, `HF_TOKEN`) must never crash or block CI; they must emit clear diagnostic instructions.
- CI tests must use secure fallback defaults for `HASH_SALT` and `SECRET_KEY` when repository secrets are absent in test runners.

## Review Focus

1. **Non-fatal pip-audit CVE reporting**: New or low-severity CVEs in pinned packages should upload artifacts and warn without halting the entire build.
2. **Missing GitHub Secrets in CI**: Ephemeral test jobs must execute successfully even if `HASH_SALT` or `SECRET_KEY` secrets are omitted from the repo.
3. **Deployment Secrets Validation**: Missing `HF_TOKEN` or `RENDER_DEPLOY_HOOK_URL` in PRs or forks must not mark the build as failed.
4. **Hugging Face Git Authentication**: Must handle remote synchronization without exposing auth tokens in action logs.
5. **Fast vs Full Test Coverage**: Ensure all unit and integration tests run in CI while keeping runtime under 5 minutes.

---

### Task 1: Harden and Unbreak GitHub Actions CI Workflow

**Files:**
- Modify: `.github/workflows/ci.yml`
- Test: GitHub Actions local simulation / YAML schema validation

**Interfaces:**
- Consumes: `requirements.docker.txt`, `data/generate.py`, `data/load_to_db.py`, `tests/`
- Produces: `bandit-report` artifact, `pip-audit-report` artifact, passing test & docker build jobs

- [ ] **Step 1: Inspect and fix pip-audit failure in `.github/workflows/ci.yml`**
  Add `--desc` for readable logging and ensure the command outputs `pip-audit-report.json` and uploads it as an artifact without exiting with code 1 on non-breaking dependency advisories (`pip-audit ... || true`).

- [ ] **Step 2: Add fallback test environment secrets in `test` job**
  Update `HASH_SALT` and `SECRET_KEY` env declarations to use repository secrets when present, and secure 32-byte default strings for CI when absent.

- [ ] **Step 3: Expand test job to run comprehensive test suite**
  Update `pytest` step to run data, normalizer, ML engine, and API tests (`pytest tests/ -v`).

- [ ] **Step 4: Verify YAML syntax and test execution locally**
  Run schema validation on `.github/workflows/ci.yml` and verify python test commands.

- [ ] **Step 5: Commit changes**
  ```bash
  git add .github/workflows/ci.yml
  git commit -m "ci: harden security scan reporting and provide fallback test secrets"
  ```

---

### Task 2: Implement CD Deployment Job for Render

**Files:**
- Modify: `.github/workflows/ci.yml` (or create `.github/workflows/cd.yml`)
- Create: `scripts/deploy_render.sh` (or inline shell step)

**Interfaces:**
- Consumes: `secrets.RENDER_DEPLOY_HOOK_URL`
- Produces: Webhook POST to Render API triggering container redeployment

- [ ] **Step 1: Define `deploy-render` job in workflow**
  Add `deploy-render` job depending on `docker-build`, conditioned on `github.ref == 'refs/heads/main' && github.event_name == 'push'`.

- [ ] **Step 2: Implement webhook trigger logic with diagnostic fallback**
  If `secrets.RENDER_DEPLOY_HOOK_URL` is set:
  Trigger `curl -s -S -X POST "$RENDER_DEPLOY_HOOK_URL"`.
  If not set:
  Output an informative notice explaining that Render native Git auto-deploy (from `render.yaml`) is handling the deployment.

- [ ] **Step 3: Verify job definition and dependencies**
  Ensure execution only triggers when previous build and test jobs pass.

- [ ] **Step 4: Commit changes**
  ```bash
  git add .github/workflows/ci.yml
  git commit -m "cd: add automated Render deploy hook trigger job"
  ```

---

### Task 3: Implement CD Deployment Job for Hugging Face Spaces

**Files:**
- Modify: `.github/workflows/ci.yml`
- Test: Git remote synchronization logic

**Interfaces:**
- Consumes: `secrets.HF_TOKEN`
- Produces: Git push to `https://huggingface.co/spaces/Rupa2k/aegis-ai`

- [ ] **Step 1: Define `deploy-huggingface` job in workflow**
  Add `deploy-huggingface` job depending on `docker-build`, conditioned on `github.ref == 'refs/heads/main' && github.event_name == 'push'`.

- [ ] **Step 2: Implement safe repository push to Hugging Face Spaces**
  Fetch full git history (`actions/checkout@v4` with `fetch-depth: 0`).
  If `secrets.HF_TOKEN` is present:
  Authenticate and push `main` branch to `https://Rupa2k:${{ secrets.HF_TOKEN }}@huggingface.co/spaces/Rupa2k/aegis-ai`.
  If not present:
  Log a helpful status notice directing how to configure `HF_TOKEN`.

- [ ] **Step 3: Test git remote command format and secret masking**
  Confirm secret masking prevents credential leakage in GitHub Actions runners.

- [ ] **Step 4: Commit changes**
  ```bash
  git add .github/workflows/ci.yml
  git commit -m "cd: add automated Hugging Face Spaces deployment job"
  ```

---

### Task 4: Add CI/CD Documentation and Configuration Guide

**Files:**
- Create: `docs/CI_CD_GUIDE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Workflow details from Task 1-3
- Produces: Step-by-step setup documentation and badge updates

- [ ] **Step 1: Write `docs/CI_CD_GUIDE.md`**
  Document the entire CI/CD pipeline lifecycle, list all GitHub Secrets (`HF_TOKEN`, `RENDER_DEPLOY_HOOK_URL`, `AEGIS_USERS_JSON`, `HASH_SALT`, `SECRET_KEY`), and provide instructions for generating tokens.

- [ ] **Step 2: Update `README.md` badges and CI/CD section**
  Ensure CI/CD status badges and deployment links in `README.md` accurately link to the new pipeline.

- [ ] **Step 3: Commit and push changes**
  ```bash
  git add docs/CI_CD_GUIDE.md README.md
  git commit -m "docs: add comprehensive CI/CD deployment guide and pipeline badges"
  ```
