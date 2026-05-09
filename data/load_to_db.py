"""Loads all generated CSVs into PostgreSQL."""
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
OUTPUT = Path("data/output")

print("Creating schema...")
with engine.connect() as conn:
    schema_sql = open("data/schema.sql").read()
    for statement in schema_sql.split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()
print("  Schema ready.")

tables = [
    ("companies.csv",       "companies"),
    ("employees.csv",       "employees"),
    ("telemetry.csv",       "telemetry"),
    ("clinical_events.csv", "clinical_events"),
    ("training_dataset.csv","training_snapshots"),
]

for filename, table in tables:
    filepath = OUTPUT / filename
    if not filepath.exists():
        print(f"  SKIP: {filename} not found — run generate.py first")
        continue
    df = pd.read_csv(filepath)
    df.to_sql(table, engine, if_exists="append", index=False,
              method="multi", chunksize=500)
    print(f"  Loaded {len(df):,} rows -> {table}")

print("\nAll data loaded successfully.")