#!/bin/bash
set -e

python scripts/bootstrap.py

exec uvicorn ingestion.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-server-header
