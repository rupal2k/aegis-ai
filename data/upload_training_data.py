"""
Aegis AI — Flexible training-data uploader.

Accepts ANY CSV that contains the training context (employee health/claims data).
Column names are matched via aliases (case/space/underscore-insensitive); missing
fields are filled from the existing dataset's medians/modes so partial datasets
still contribute to training. The canonical target (`loss_ratio`) — or enough
information to derive it — is the only hard requirement.

Usage:
    python data/upload_training_data.py <path/to/new_data.csv> [--retrain] [--no-backup] [--dry-run]
"""
import sys
import io
import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

OUTPUT_DIR    = Path("data/output")
DATASET_PATH  = OUTPUT_DIR / "training_dataset.csv"
BACKUP_DIR    = OUTPUT_DIR / "backups"

# Canonical schema (in canonical order). Anything outside this list is dropped.
CANONICAL_COLS = [
    "employee_id", "company_id", "age", "gender", "bmi",
    "smoker", "diabetic", "hypertension", "job_category",
    "avg_daily_steps", "step_volatility", "avg_resting_hr", "hr_trend",
    "avg_active_mins", "avg_sleep_hours", "avg_spo2",
    "total_claims", "visit_count", "hospitalized_count",
    "premium_share", "loss_ratio", "high_risk", "chronic_count",
    "lab_heart_flag", "lab_inflammation_flag", "lab_diabetes_flag",
    "lab_kidney_flag", "lab_liver_flag", "lab_iron_flag",
    "lab_thyroid_flag", "lab_bone_flag", "lab_vitamin_flag",
    "lab_domain_count", "lab_risk_score",
]

# Column-name aliases. Keys are canonical, values are accepted variants.
# Matching is normalized (lowercased, non-alphanumeric stripped).
ALIASES = {
    "employee_id":        ["employeeid", "empid", "id", "memberid", "personid", "uid"],
    "company_id":         ["companyid", "orgid", "employerid", "groupid"],
    "age":                ["years", "ageyears", "ageyrs"],
    "gender":             ["sex"],
    "bmi":                ["bodymassindex"],
    "smoker":             ["smokes", "tobacco", "tobaccouse", "issmoker"],
    "diabetic":           ["diabetes", "hasdiabetes", "isdiabetic", "dm"],
    "hypertension":       ["hypertensive", "highbp", "bp", "hbp"],
    "job_category":       ["job", "jobtype", "occupation", "role", "worktype"],
    "avg_daily_steps":    ["steps", "dailysteps", "stepsperday", "avgsteps"],
    "step_volatility":    ["stepvariance", "stepstddev"],
    "avg_resting_hr":     ["restinghr", "rhr", "heartrate", "avgheartrate"],
    "hr_trend":           ["heartratetrend", "hrslope"],
    "avg_active_mins":    ["activeminutes", "activemins", "exercisemins"],
    "avg_sleep_hours":    ["sleephours", "sleep", "avgsleep"],
    "avg_spo2":           ["spo2", "oxygensaturation", "avgoxygen"],
    "total_claims":       ["claims", "claimamount", "claimstotal", "totalclaim"],
    "visit_count":        ["visits", "doctorvisits", "opdvisits"],
    "hospitalized_count": ["hospitalizations", "admits", "ipdcount", "ipdvisits"],
    "premium_share":      ["premium", "annualpremium", "premiumpaid"],
    "loss_ratio":         ["lossratio", "lr", "claimsratio"],
    "high_risk":          ["highrisk", "isrisky", "riskflag"],
    "chronic_count":      ["chroniccount", "chronicconditions", "chroniccondcount"],
    "lab_heart_flag":     ["heartflag", "labheart", "cardiacflag"],
    "lab_inflammation_flag":["inflammationflag", "labinflammation", "crpflag"],
    "lab_diabetes_flag":  ["diabetesflag", "labdiabetes", "hba1cflag"],
    "lab_kidney_flag":    ["kidneyflag", "labkidney", "renalflag"],
    "lab_liver_flag":     ["liverflag", "labliver", "hepaticflag"],
    "lab_iron_flag":      ["ironflag", "labiron", "anemiaflag"],
    "lab_thyroid_flag":   ["thyroidflag", "labthyroid", "tshflag"],
    "lab_bone_flag":      ["boneflag", "labbone", "vitdflag"],
    "lab_vitamin_flag":   ["vitaminflag", "labvitamin", "vitb12flag"],
    "lab_domain_count":   ["labcount", "abnormallabs"],
    "lab_risk_score":     ["labrisk", "labscore"],
}

VALID_GENDER = {"M", "F", "O"}
VALID_JOB    = {"desk", "field", "manual"}

LAB_FLAGS = [c for c in CANONICAL_COLS if c.startswith("lab_") and c.endswith("_flag")]
LAB_WEIGHTS = {
    "lab_heart_flag": 0.20, "lab_inflammation_flag": 0.10, "lab_diabetes_flag": 0.25,
    "lab_kidney_flag": 0.18, "lab_liver_flag": 0.12, "lab_iron_flag": 0.05,
    "lab_thyroid_flag": 0.03, "lab_bone_flag": 0.04, "lab_vitamin_flag": 0.03,
}


def _norm(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, list]:
    """Rename columns to canonical names using alias matching. Returns (df, mapping, unmapped)."""
    norm_to_canonical: dict[str, str] = {}
    for canonical in CANONICAL_COLS:
        norm_to_canonical[_norm(canonical)] = canonical
        for alias in ALIASES.get(canonical, []):
            norm_to_canonical[_norm(alias)] = canonical

    rename_map: dict[str, str] = {}
    unmapped: list[str] = []
    for col in df.columns:
        canonical = norm_to_canonical.get(_norm(col))
        if canonical and canonical not in rename_map.values():
            rename_map[col] = canonical
        else:
            unmapped.append(col)

    return df.rename(columns=rename_map), rename_map, unmapped


def coerce_booleans(series: pd.Series) -> pd.Series:
    bool_map = {
        "true": 1, "false": 0, "yes": 1, "no": 0, "y": 1, "n": 0,
        "1": 1, "0": 0, "1.0": 1, "0.0": 0, "t": 1, "f": 0,
    }
    s = series.astype(str).str.strip().str.lower()
    mapped = s.map(bool_map)
    numeric = pd.to_numeric(series, errors="coerce")
    return mapped.fillna((numeric > 0).astype("Int64")).fillna(0).astype(int)


def derive_loss_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """If loss_ratio is missing but claims+premium exist, derive it."""
    if "loss_ratio" in df.columns:
        return df
    if "total_claims" in df.columns and "premium_share" in df.columns:
        prem = pd.to_numeric(df["premium_share"], errors="coerce").replace(0, np.nan)
        claims = pd.to_numeric(df["total_claims"], errors="coerce")
        df = df.copy()
        df["loss_ratio"] = (claims / prem).fillna(0).clip(0, 50).round(4)
        print("  Derived loss_ratio from total_claims / premium_share.")
    return df


def fill_defaults(df: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Fill any canonical column missing from df with reference dataset's median/mode."""
    df = df.copy()
    n = len(df)

    for col in CANONICAL_COLS:
        if col in df.columns:
            continue
        if col == "employee_id":
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            df[col] = [f"UPLOAD_{stamp}_{i:05d}" for i in range(n)]
        elif col == "company_id":
            df[col] = "UPLOAD"
        elif col in ("gender", "job_category"):
            df[col] = reference[col].mode().iloc[0]
        elif col in reference.columns and pd.api.types.is_numeric_dtype(reference[col]):
            df[col] = reference[col].median()
        else:
            df[col] = 0

    return df


def recompute_engineered(df: pd.DataFrame, user_supplied: set[str]) -> pd.DataFrame:
    df = df.copy()

    if "chronic_count" not in user_supplied:
        df["chronic_count"] = (
            df["diabetic"].astype(int) + df["hypertension"].astype(int)
        )

    if "lab_domain_count" not in user_supplied:
        df["lab_domain_count"] = df[LAB_FLAGS].sum(axis=1)
    if "lab_risk_score" not in user_supplied:
        df["lab_risk_score"] = sum(
            LAB_WEIGHTS[c] * df[c] for c in LAB_FLAGS
        ).round(4)

    if "high_risk" not in user_supplied:
        df["high_risk"] = (df["loss_ratio"] >= 1.5).astype(int)

    return df


def validate(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    if "loss_ratio" not in df.columns:
        errors.append(
            "Cannot find or derive `loss_ratio`. Provide a column matching loss_ratio/lr/claimsratio, "
            "or both total_claims and premium_share."
        )
        return errors

    lr = pd.to_numeric(df["loss_ratio"], errors="coerce")
    if lr.isna().any():
        errors.append(f"{int(lr.isna().sum())} row(s) have non-numeric loss_ratio")
    bad_lr = ~lr.between(0, 50)
    if bad_lr.any():
        errors.append(f"{int(bad_lr.sum())} row(s) with loss_ratio outside 0-50")

    return errors


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).str.upper().str[0]
        df.loc[~df["gender"].isin(VALID_GENDER), "gender"] = "O"

    if "job_category" in df.columns:
        df["job_category"] = df["job_category"].astype(str).str.lower()
        df.loc[~df["job_category"].isin(VALID_JOB), "job_category"] = "desk"

    for col in ("smoker", "diabetic", "hypertension", "high_risk"):
        if col in df.columns:
            df[col] = coerce_booleans(df[col])

    for col in LAB_FLAGS:
        if col in df.columns:
            df[col] = coerce_booleans(df[col])

    for col in CANONICAL_COLS:
        if col in df.columns and col not in (
            "employee_id", "company_id", "gender", "job_category"
        ):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def append_to_dataset(new_df: pd.DataFrame, backup: bool, dry_run: bool) -> int:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"{DATASET_PATH} not found — run the data pipeline first.")

    existing = pd.read_csv(DATASET_PATH)
    print(f"Existing dataset: {len(existing):,} rows, {len(existing.columns)} columns")

    aligned = new_df.copy()
    for col in existing.columns:
        if col not in aligned.columns:
            aligned[col] = 0
    aligned = aligned[existing.columns.tolist()]

    overlap = set(existing["employee_id"]) & set(aligned["employee_id"])
    if overlap:
        print(f"  WARNING: {len(overlap)} employee_id(s) already exist — those rows will appear twice.")

    if dry_run:
        print(f"DRY RUN — would append {len(aligned):,} rows (new total {len(existing) + len(aligned):,}). No file written.")
        return len(existing) + len(aligned)

    if backup:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"training_dataset_{stamp}.csv"
        shutil.copy2(DATASET_PATH, backup_path)
        print(f"  Backup saved -> {backup_path}")

    combined = pd.concat([existing, aligned], ignore_index=True)
    combined.to_csv(DATASET_PATH, index=False)
    print(f"Appended {len(aligned):,} rows. New total: {len(combined):,}")
    return len(combined)


def process(df: pd.DataFrame, reference: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pipeline used by both CLI and dashboard. Returns (canonical_df, report)."""
    df, mapping, unmapped = map_columns(df)
    df = derive_loss_ratio(df)

    errors = validate(df)
    if errors:
        return pd.DataFrame(), {"errors": errors, "mapping": mapping, "unmapped": unmapped}

    user_supplied = set(mapping.values())
    df = normalize(df)
    df = fill_defaults(df, reference)
    df = recompute_engineered(df, user_supplied)
    df = df[CANONICAL_COLS]

    filled = [c for c in CANONICAL_COLS if c not in mapping.values()]
    return df, {
        "errors": [],
        "mapping": mapping,
        "unmapped": unmapped,
        "filled_with_defaults": filled,
        "rows": len(df),
    }


def run_training() -> int:
    print("\nLaunching training pipeline...")
    proc = subprocess.run(
        [sys.executable, "-m", "ml_engine.training.train"],
        cwd=Path.cwd(),
    )
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Append flexible CSV data to the training dataset.")
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file to append.")
    parser.add_argument("--retrain", action="store_true", help="Run training after appending.")
    parser.add_argument("--no-backup", action="store_true", help="Skip backing up the existing dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without writing.")
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"ERROR: {args.csv_path} does not exist")
        sys.exit(1)
    if not DATASET_PATH.exists():
        print(f"ERROR: {DATASET_PATH} not found — run the data pipeline first.")
        sys.exit(1)

    print(f"Reading {args.csv_path}...")
    try:
        df = pd.read_csv(args.csv_path)
    except Exception as exc:
        print(f"ERROR: could not parse CSV — {exc}")
        sys.exit(1)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    reference = pd.read_csv(DATASET_PATH)
    canonical, report = process(df, reference)

    if report["mapping"]:
        print("\nColumn mapping:")
        for src, dst in report["mapping"].items():
            print(f"  {src!r} -> {dst}")
    if report["unmapped"]:
        print(f"\nIgnored {len(report['unmapped'])} unrecognized column(s): {report['unmapped'][:8]}{'...' if len(report['unmapped']) > 8 else ''}")
    if report["errors"]:
        print("\nValidation failed:")
        for err in report["errors"]:
            print(f"  - {err}")
        sys.exit(2)

    if report["filled_with_defaults"]:
        print(f"\nFilled {len(report['filled_with_defaults'])} missing column(s) from dataset defaults: "
              f"{report['filled_with_defaults'][:8]}{'...' if len(report['filled_with_defaults']) > 8 else ''}")

    print("Validation OK.")
    append_to_dataset(canonical, backup=not args.no_backup, dry_run=args.dry_run)

    if args.retrain and not args.dry_run:
        rc = run_training()
        if rc != 0:
            print(f"\nTraining exited with code {rc}")
            sys.exit(rc)

    print("\nDone.")


if __name__ == "__main__":
    main()
