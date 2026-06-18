"""
One-time script to derive premium multiplier tables from corporate insurance quotes.

Run:
    python -m ml_engine.training.calibrate_premium

Copy the printed dict literals into ml_engine/premium_calculator.py.
"""
from pathlib import Path
import pandas as pd
import numpy as np

CORPORATE_FILE = Path("Traning Assets/group_health_insurance_quotes_200_corporates.xlsx")
PREMIUM_COL    = "estimated_annual_premium_per_employee_inr"


def _load_corporate_df(path: Path = CORPORATE_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Corporate quotes file not found: {path}")
    return pd.read_excel(path)


def compute_industry_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per industry normalised to overall median."""
    overall = df[PREMIUM_COL].median()
    by_industry = df.groupby("industry")[PREMIUM_COL].median()
    return {k: round(float(v / overall), 3) for k, v in by_industry.items()}


def compute_region_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per region (North/South/East/West) normalised to overall median."""
    overall = df[PREMIUM_COL].median()
    by_region = df.groupby("region")[PREMIUM_COL].median()
    return {k: round(float(v / overall), 3) for k, v in by_region.items()}


def compute_sum_assured_multipliers(df: pd.DataFrame) -> dict:
    """Median premium per sum-assured band normalised to 4-7L band."""
    bins   = [0, 3, 7, 15, 10000]
    labels = ["1-3L", "4-7L", "8-15L", "15L+"]
    df = df.copy()
    df["_band"] = pd.cut(df["sum_assured_lakhs"], bins=bins, labels=labels)
    by_band  = df.groupby("_band", observed=True)[PREMIUM_COL].median()
    base     = float(by_band.get("4-7L", by_band.median()))
    result   = {k: round(float(v / base), 3) for k, v in by_band.items()}
    # Fill any missing bands with 1.0 (neutral — no data to calibrate from)
    for label in labels:
        if label not in result:
            result[label] = 1.0
    return result


def main():
    df = _load_corporate_df()
    print(f"Loaded {len(df):,} corporate quotes.\n")

    industry = compute_industry_multipliers(df)
    region   = compute_region_multipliers(df)
    bands    = compute_sum_assured_multipliers(df)

    print("# Paste these into ml_engine/premium_calculator.py\n")
    print(f"INDUSTRY_RISK_MULTIPLIERS = {industry!r}\n")
    print(f"REGION_MULTIPLIERS = {region!r}\n")
    print(f"SUM_ASSURED_BAND_MULTIPLIERS = {bands!r}\n")


if __name__ == "__main__":
    main()
