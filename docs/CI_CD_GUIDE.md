# Aegis AI — Continuous Integration & Continuous Deployment (CI/CD) Guide

This guide details the automated CI/CD pipeline powering **Aegis AI**, from code commits to production deployments on **Render** (FastAPI backend) and **Hugging Face Spaces** (Streamlit dashboard).

---

## 1. Pipeline Architecture Overview

The CI/CD pipeline is orchestrated via [GitHub Actions](.github/workflows/ci.yml). Every push to `main` and pull request triggers a cascade of quality and security checks, followed by automated deployments upon successful merge to `main`.

```mermaid
flowchart TD
    A[Code Push / PR] --> B[Job 1: Security & SAST Audit]
    B --> C[Bandit Code Scan & Pip-Audit CVE Scan]
    C --> D[Job 2: Database, ML & API Tests]
    
    subgraph TestEnvironment [Ephemeral Test Runner]
        D --> E[PostgreSQL 15 Container]
        E --> F[Synthetic Data Generation]
        F --> G[Database Seed & Migration]
        G --> H[Fast Model Fit - AEGIS_CI_FAST]
        H --> I[Pytest Suite: Data, ML & API]
    end
    
    I --> J[Job 3: Container Build Verification]
    J --> K[Docker Buildx: API, Dashboard & Nginx]
    
    K --> L{Branch == main?}
    L -- Yes --> M[Job 4: Deploy to Render]
    L -- Yes --> N[Job 5: Deploy to Hugging Face Spaces]
    L -- No (PR) --> O[CI Passed - Ready for Review]
    
    M --> P[Render Web Service Triggered via Webhook]
    N --> Q[Hugging Face Space Synced via Git LFS]
```

---

## 2. Pipeline Stages

### Stage 1: Security & SAST Audit (`security`)
- **Bandit SAST**: Scans `ingestion/`, `ml_engine/`, and `dashboard/` for insecure coding patterns (e.g. hardcoded secrets, dangerous deserialization). Generates `bandit-report.json` and uploads it as an artifact.
- **Pip-Audit**: Performs automated CVE vulnerability checks across pinned production dependencies (`requirements.docker.txt`). Publishes human-readable findings directly into the GitHub Actions Step Summary and uploads `pip-audit-report.json`.

### Stage 2: Database, ML & Contract Tests (`test`)
- **Ephemeral PostgreSQL 15**: Deploys a clean, health-checked Postgres database service within the runner.
- **Data Generation**: Executes `python data/generate.py` to create deterministic test fixtures.
- **Database Loader**: Ingests tables, constraints, and mock corporate accounts via `python data/load_to_db.py`.
- **Fast ML Fitting**: Invokes `python -m ml_engine.training.train --no-hf` with `AEGIS_CI_FAST=1` to train a lightweight XGBoost model artifact for pipeline integration tests.
- **Automated Pytest Suite**: Executes:
  - Data & Normalizer tests (`tests/test_data.py`, `tests/test_normalizer.py`, `tests/test_excel_loader.py`)
  - ML Engine & Calibration tests (`tests/test_ml_engine.py`, `tests/test_calibrate_premium.py`, `tests/test_training_pipeline.py`)
  - API & Contract tests (`tests/test_api.py`, `tests/test_predict_api.py`)

### Stage 3: Container Build Verification (`docker-build`)
- Compiles multi-stage production Docker images using `docker/build-push-action@v5` with GitHub Actions layer caching (`type=gha`):
  - API image (`Dockerfile.api`)
  - Dashboard image (`Dockerfile.dashboard`)
  - Nginx reverse-proxy image (`nginx/Dockerfile`)

### Stage 4: Continuous Deployment to Render (`deploy-render`)
- **Trigger**: Runs exclusively on `push` to `main` (or manual `workflow_dispatch`) after builds and tests pass.
- **Mechanism**: Issues an authenticated HTTP POST request to Render's Deploy Hook endpoint:
  ```bash
  curl -s -X POST "$RENDER_DEPLOY_HOOK_URL"
  ```
- **Fallback**: If `RENDER_DEPLOY_HOOK_URL` is omitted, logs an informational notice explaining that Render native Git auto-deploy is active.

### Stage 5: Continuous Deployment to Hugging Face Spaces (`deploy-huggingface`)
- **Trigger**: Runs exclusively on `push` to `main` after builds and tests pass.
- **Mechanism**: Clones repository with Git LFS support (`*.pkl` model binaries) and pushes `main` directly to Hugging Face Spaces:
  ```bash
  git remote add hf-space "https://Rupa2k:$HF_TOKEN@huggingface.co/spaces/Rupa2k/aegis-ai"
  git push --force hf-space main:main
  ```
- **Fallback**: If `HF_TOKEN` is omitted, provides diagnostic guidance on registering the secret.

---

## 3. GitHub Secrets Configuration

To enable automatic continuous deployments, configure the following secrets under **Repository Settings → Secrets and variables → Actions**:

| Secret Name | Required For | Description | Example / How to Obtain |
| :--- | :---: | :--- | :--- |
| `RENDER_DEPLOY_HOOK_URL` | **Render CD** | Instant webhook trigger URL for the `aegis-api` web service. | In Render Dashboard: `aegis-api` → *Settings* → *Deploy Hook* → *Copy URL* (`https://api.render.com/deploy/srv-...`). |
| `HF_TOKEN` | **Hugging Face CD** | Personal access token with **Write** permissions to push to the Space. | In Hugging Face: *Settings* → *Access Tokens* → *Create new token* (Role: Write). |
| `AEGIS_USERS_JSON` | **API Production Auth** | JSON payload defining user roles and salted bcrypt hashes. | See `config/users.example.json` or `.env.example`. |
| `HASH_SALT` | **Privacy Guard** | Secret salt for employee ID pseudonymization (SHA-256). | Random 32+ byte hex string. |
| `SECRET_KEY` | **JWT Token Signing** | Cryptographic secret for signing API bearer JWT tokens. | Random 32+ byte string generated via `openssl rand -hex 32`. |

> [!NOTE]
> In pull requests or test environments where secrets are not exposed to untrusted forks, the CI test job automatically substitutes safe, 32-byte ephemeral dummy secrets (`ci_test_salt...`, `ci_test_jwt...`) to guarantee tests pass without leaking production secrets.

---

## 4. Manual Triggers and Workflow Dispatch

The workflow supports manual execution at any time:
1. Navigate to the **Actions** tab on GitHub.
2. Select **CI/CD Pipeline** from the left sidebar.
3. Click **Run workflow**, choose the `main` branch, and click the green button.
