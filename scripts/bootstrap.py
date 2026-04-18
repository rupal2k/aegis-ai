"""
One-time bootstrap script.

Runs inside the api container on first launch to:
  1. Generate synthetic data (if CSVs don't exist)
  2. Load CSVs into Postgres (if tables are empty)
  3. Train the XGBoost model (if artifacts don't exist)

Idempotent — safe to run multiple times.
"""
import sys
from pathlib import Path
import subprocess
from sqlalchemy import create_engine, text
import os
import time


DATA_OUTPUT = Path("data/output")
ARTIFACTS   = Path("ml_engine/artifacts")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://aegis_user:aegis_pass@db:5432/aegis_db"
)


def wait_for_db(max_wait: int = 60):
    print("Waiting for database...", flush=True)
    engine = create_engine(DATABASE_URL)
    for i in range(max_wait):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("  Database ready.", flush=True)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"Database not reachable after {max_wait}s")


def data_csvs_exist() -> bool:
    required = ["companies.csv", "employees.csv", "telemetry.csv",
                "clinical_events.csv", "training_dataset.csv"]
    return all((DATA_OUTPUT / f).exists() for f in required)


def db_already_seeded() -> bool:
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            return r is not None and r > 0
    except Exception:
        return False


def artifacts_exist() -> bool:
    required = ["xgb_model.pkl", "hrs_scorer.pkl", "feature_names.pkl"]
    return all((ARTIFACTS / f).exists() for f in required)


def run(cmd: list):
    print(f"\n-> Running: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr}", flush=True)
        raise RuntimeError(f"Command failed: {cmd}")
    print(result.stdout, flush=True)


def main():
    wait_for_db()

    if not data_csvs_exist():
        print("\n[1/3] Generating synthetic data...", flush=True)
        run([sys.executable, "data/generate.py"])
    else:
        print("\n[1/3] Data CSVs exist — skipping generation.", flush=True)

    if not db_already_seeded():
        print("\n[2/3] Loading data into Postgres...", flush=True)
        run([sys.executable, "data/load_to_db.py"])
    else:
        print("\n[2/3] Database already seeded — skipping load.", flush=True)

    if not artifacts_exist():
        print("\n[3/3] Training model...", flush=True)
        run([sys.executable, "-m", "ml_engine.training.train"])
    else:
        print("\n[3/3] Model artifacts exist — skipping training.", flush=True)

    print("\nBootstrap complete.", flush=True)


if __name__ == "__main__":
    main()
