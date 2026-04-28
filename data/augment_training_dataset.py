"""
Augment training_dataset.csv with:
  1. Synthetic lab features for the existing 5,000 synthetic employees.
  2. 237 real-user rows from real_user_training.csv.

Outputs:
  data/output/training_dataset.csv  (replaces the existing file)

Run: python data/augment_training_dataset.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

OUTPUT_DIR = Path("data/output")


def add_synthetic_lab_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate plausible lab domain flags for synthetic employees.
    Uses existing health features as probability drivers.
    Rates calibrated to real-world distributions from uploaded data.
    """
    rng_lab = np.random.default_rng(seed=99)
    n = len(df)

    steps  = df["avg_daily_steps"].values
    smoker = df["smoker"].values.astype(float)
    diab   = df["diabetic"].values.astype(float)
    htn    = df["hypertension"].values.astype(float)
    bmi    = df["bmi"].values
    age    = df["age"].values
    female = (df["gender"].values == "F").astype(float)

    df["lab_heart_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.40 + htn * 0.28 + smoker * 0.18 + (bmi > 28).astype(float) * 0.12, 0.05, 0.95
    )).astype(int)

    df["lab_inflammation_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.28 + smoker * 0.22 + htn * 0.12 + (bmi > 30).astype(float) * 0.12, 0.05, 0.92
    )).astype(int)

    df["lab_diabetes_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.06 + diab * 0.78 + (bmi > 30).astype(float) * 0.08 + (age > 45).astype(float) * 0.05,
        0.02, 0.95
    )).astype(int)

    df["lab_kidney_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.12 + diab * 0.22 + htn * 0.18 + (age > 50).astype(float) * 0.08, 0.03, 0.88
    )).astype(int)

    df["lab_liver_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.28 + smoker * 0.18 + (bmi > 28).astype(float) * 0.14 + diab * 0.12, 0.05, 0.92
    )).astype(int)

    df["lab_iron_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.13 + female * 0.14 + (age < 35).astype(float) * 0.04, 0.03, 0.72
    )).astype(int)

    df["lab_thyroid_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.06 + female * 0.05 + (age > 45).astype(float) * 0.03, 0.02, 0.38
    )).astype(int)

    df["lab_bone_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.05 + female * 0.04 + (age > 50).astype(float) * 0.06, 0.02, 0.32
    )).astype(int)

    df["lab_vitamin_flag"] = (rng_lab.uniform(size=n) < np.clip(
        0.76 + smoker * 0.08 + (steps < 4000).astype(float) * 0.06, 0.50, 0.98
    )).astype(int)

    lab_flags   = ["lab_heart_flag","lab_inflammation_flag","lab_diabetes_flag",
                   "lab_kidney_flag","lab_liver_flag","lab_iron_flag",
                   "lab_thyroid_flag","lab_bone_flag","lab_vitamin_flag"]
    lab_weights = [0.20, 0.10, 0.25, 0.18, 0.12, 0.05, 0.03, 0.04, 0.03]

    df["lab_domain_count"] = df[lab_flags].sum(axis=1)
    df["lab_risk_score"]   = sum(
        w * df[col] for w, col in zip(lab_weights, lab_flags)
    ).round(4)

    return df


def main():
    # ── Load existing synthetic training data ───────────────────────────────
    synth_path = OUTPUT_DIR / "training_dataset.csv"
    print(f"Loading {synth_path}...")
    df_synth = pd.read_csv(synth_path)
    print(f"  {len(df_synth):,} synthetic rows, {len(df_synth.columns)} columns")

    if "lab_heart_flag" in df_synth.columns:
        print("  Lab features already present — skipping re-generation")
    else:
        print("  Adding synthetic lab features...")
        df_synth = add_synthetic_lab_features(df_synth)
        print(f"  Added lab features. Now {len(df_synth.columns)} columns.")

    # ── Load real-user rows ─────────────────────────────────────────────────
    real_path = OUTPUT_DIR / "real_user_training.csv"
    print(f"\nLoading {real_path}...")
    df_real = pd.read_csv(real_path)
    print(f"  {len(df_real)} real-user rows")

    # ── Align columns before concatenating ─────────────────────────────────
    all_cols = df_synth.columns.tolist()
    for col in all_cols:
        if col not in df_real.columns:
            df_real[col] = 0
    df_real = df_real[all_cols]

    # ── Combine and save ────────────────────────────────────────────────────
    df_combined = pd.concat([df_synth, df_real], ignore_index=True)
    print(f"\nCombined dataset: {len(df_combined):,} rows, {len(df_combined.columns)} columns")

    df_combined.to_csv(synth_path, index=False)
    print(f"Saved -> {synth_path}")

    # ── Sanity check ────────────────────────────────────────────────────────
    print("\n--- Sanity Check ---")
    print(f"Loss ratio      : mean={df_combined['loss_ratio'].mean():.3f}, "
          f"max={df_combined['loss_ratio'].max():.3f}")
    print(f"High-risk pct   : {df_combined['high_risk'].mean()*100:.1f}%")
    print(f"Lab domain count: {df_combined['lab_domain_count'].mean():.2f} avg")
    print(f"Lab risk score  : {df_combined['lab_risk_score'].mean():.3f} avg")
    print(f"Heart flag rate : {df_combined['lab_heart_flag'].mean()*100:.1f}%")
    print(f"Diabetes flag   : {df_combined['lab_diabetes_flag'].mean()*100:.1f}%")
    print(f"Vitamin flag    : {df_combined['lab_vitamin_flag'].mean()*100:.1f}%")


if __name__ == "__main__":
    main()
