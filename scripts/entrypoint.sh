#!/bin/bash
set -e

# Bootstrap (data generation + DB seed + model training) runs in the background
# so uvicorn can bind its port immediately — required for Render's port scanner.
# The API serves requests as soon as it starts; ML endpoints become fully
# functional once bootstrap completes (~3-5 min on first cold start).
python scripts/bootstrap.py &

exec uvicorn ingestion.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-server-header
