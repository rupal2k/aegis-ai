"""
Aegis AI — Model training pipeline.

Run: python -m ml_engine.training.train [OPTIONS]

Options:
  --use-local         Use only local CSV dataset
  --use-hf            Use only Hugging Face dataset  
  --use-both          Use both local CSV and HF dataset (default - recommended)
  --no-hf             Alias for --use-local (skip HF dataset)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import xgboost as xgb
import optuna
import mlflow
import mlflow.xgboost
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from dotenv import load_dotenv
import os
import argparse
from typing import Dict, Tuple

from ml_engine.features import engineer_features, get_feature_matrix, TARGET_LOG
from ml_engine.scorer   import HRSScorer

load_dotenv()

DATA_PATH    = Path("data/output/training_dataset.csv")
ARTIFACTS    = Path("ml_engine/artifacts")
ARTIFACTS.mkdir(exist_ok=True)

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
HF_DATASET_NAME = os.environ.get(
    "AEGIS_HF_DATASET",
    "ayush0205/clinical_data_rf",
)
DEFAULT_DATA_MODE = "both"
N_OPTUNA_TRIALS = 5 if os.environ.get("AEGIS_CI_FAST") == "1" else 30
RANDOM_STATE    = 42

optuna.logging.set_verbosity(optuna.logging.WARNING)


def configure_mlflow():
    """Configure MLflow lazily so importing this module stays side-effect free."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("aegis-underwriting")


def load_local_dataset():
    """Load the synthetic/local training CSV."""
    print(f"Loading local dataset from {DATA_PATH}...")
    return pd.read_csv(DATA_PATH)


def _parse_clinical_note(text: str) -> dict:
    """Extract structured fields from one clinical discharge note."""
    import re

    # Strip the instruction wrapper
    idx = text.find("### Instruction:")
    end = text.find("### Response:")
    if idx > -1:
        text = text[idx + len("### Instruction:"):end if end > -1 else None].strip()

    def flag(*patterns) -> int:
        return int(any(re.search(p, text, re.IGNORECASE) for p in patterns))

    # ── Demographics ─────────────────────────────────────────────
    age = 45.0
    for pat in (
        r"(\d{1,3})[- ]year[s]?[- ]old",
        r"\bAge:\s*(\d{1,3})",
        r"\bage[d]?\s+(\d{1,3})\b",
        r"\b(\d{1,3})[- ]yo\b",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 0 < val < 120:
                age = float(val)
                break

    female_hits = len(re.findall(r"\b(female|woman|women|she\b|her\b)", text, re.IGNORECASE))
    male_hits   = len(re.findall(r"\b(male|man\b|men\b|he\b|his\b)", text, re.IGNORECASE))
    gender = "F" if female_hits > male_hits else "M"

    # BMI — extract if stated, otherwise default
    bmi = 26.0
    m = re.search(r"\bBMI\s*(?:of\s*|=\s*|:\s*)?(\d{1,2}(?:\.\d)?)\b", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if 10 < val < 70:
            bmi = val

    # ── Conditions ───────────────────────────────────────────────
    smoker      = flag(r"\bsmok(?:er|ing|ed)\b", r"\bcurrent smoker\b", r"\btobacco\b")
    diabetic    = flag(r"\bdiabet(?:es|ic|ics)\b", r"\bDM\b", r"\binsulin[- ]dependent\b", r"\bT2DM\b", r"\bT1DM\b")
    hypertension= flag(r"\bhypertension\b", r"\bhigh blood pressure\b", r"\bHTN\b")
    cancer      = flag(r"\bcancer\b", r"\bmalignant\b", r"\bcarcinoma\b", r"\blymphoma\b", r"\bleukemia\b", r"\bneoplasm\b", r"\btumou?r\b")
    heart_dis   = flag(r"\bcardiac\b", r"\bheart failure\b", r"\bmyocardial infarction\b", r"\bcoronary\b", r"\batrial fibr", r"\bangina\b")
    renal       = flag(r"\brenal failure\b", r"\bkidney failure\b", r"\bCKD\b", r"\bdialysis\b", r"\bnephrop", r"\bcreatinine elevated\b")
    liver_dis   = flag(r"\bliver failure\b", r"\bhepat(?:itis|ic encephalopathy|orenal)\b", r"\bcirrhosis\b", r"\belevated.*(?:AST|ALT|LFT)\b", r"\bbilirubin\b")
    respiratory = flag(r"\bCOPD\b", r"\basthma\b", r"\bARDS\b", r"\bpneumonia\b", r"\brespiratory failure\b", r"\bmechanical ventilation\b")
    sepsis      = flag(r"\bsepsis\b", r"\bseptic shock\b", r"\bbacteremia\b")
    stroke      = flag(r"\bstroke\b", r"\bcerebral infarct\b", r"\bTIA\b", r"\bischemic.*brain\b")
    mental      = flag(r"\bdepression\b", r"\banxiety disorder\b", r"\bschizophrenia\b", r"\bbipolar\b", r"\bpsychiat")
    osteo       = flag(r"\bosteoporosis\b", r"\bosteopenia\b", r"\bone fracture\b", r"\bfragility fracture\b")
    anemia      = flag(r"\banemia\b", r"\banaemia\b", r"\biron deficiency\b", r"\bhemoglobin\b.*\blow\b")
    thyroid_dis = flag(r"\bhypothyroid\b", r"\bhyperthyroid\b", r"\bthyroid\b")
    vitamin_def = flag(r"\bvitamin D deficiency\b", r"\bvitamin B12\b", r"\bvitamin deficiency\b")

    chronic_conditions = [diabetic, hypertension, cancer, heart_dis, renal, liver_dis,
                          respiratory, sepsis, stroke, mental, osteo, anemia, thyroid_dis]
    chronic_count = sum(chronic_conditions)

    # ── Clinical events ──────────────────────────────────────────
    icu          = flag(r"\bICU\b", r"\bintensive care unit\b", r"\bcritical care\b")
    ventilated   = flag(r"\bmechanical ventilation\b", r"\bintubat", r"\bventilat")
    hospitalized_count = 1 + icu  # all records are hospitalisations; ICU adds complexity
    visit_count  = min(2 + chronic_count + icu * 2, 10)

    # ── SpO2 ─────────────────────────────────────────────────────
    avg_spo2 = 97.0
    for pat in (
        r"(?:oxygen saturation|SpO2|O2 sat)[^0-9]*(\d{2,3})%",
        r"(\d{2,3})%\s*to\s*(\d{2,3})%",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # If two values (before→after), take the later one
            val = float(m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1))
            if 70 <= val <= 100:
                avg_spo2 = val
                break

    # ── Target: loss_ratio ───────────────────────────────────────
    # Built from clinical severity so the model can learn meaningful signal.
    age_risk        = max(age - 18, 0) / 80 * 0.4          # 0.0 – 0.40
    condition_risk  = chronic_count * 0.08                   # 0.08 per condition
    serious_risk    = (cancer * 0.30 + icu * 0.20 + renal * 0.18
                       + heart_dis * 0.15 + sepsis * 0.15 + ventilated * 0.15
                       + stroke * 0.12 + liver_dis * 0.10 + respiratory * 0.08)
    lifestyle_risk  = smoker * 0.10 + (max(bmi - 30, 0) / 10) * 0.10
    loss_ratio = 0.20 + age_risk + condition_risk + serious_risk + lifestyle_risk

    return {
        "age":               age,
        "gender":            gender,
        "bmi":               bmi,
        "smoker":            smoker,
        "diabetic":          diabetic,
        "hypertension":      hypertension,
        "chronic_count":     float(chronic_count),
        "avg_daily_steps":   None,   # synthesised below
        "step_volatility":   None,
        "avg_resting_hr":    None,
        "hr_trend":          None,
        "avg_active_mins":   None,
        "avg_sleep_hours":   None,
        "avg_spo2":          avg_spo2,
        "visit_count":       float(visit_count),
        "hospitalized_count":float(hospitalized_count),
        "lab_heart_flag":    int(heart_dis),
        "lab_diabetes_flag": int(diabetic),
        "lab_kidney_flag":   int(renal),
        "lab_liver_flag":    int(liver_dis),
        "lab_inflammation_flag": int(sepsis or respiratory),
        "lab_iron_flag":     int(anemia),
        "lab_thyroid_flag":  int(thyroid_dis),
        "lab_bone_flag":     int(osteo or age > 60),
        "lab_vitamin_flag":  int(vitamin_def),
        "loss_ratio":        loss_ratio,
        "_severity":         age_risk + condition_risk + serious_risk,  # used for telemetry synthesis
    }


def load_from_huggingface(dataset_name: str = HF_DATASET_NAME):
    """Parse clinical discharge notes from HF Hub into the Aegis feature schema.

    The dataset (`ayush0205/clinical_data_rf`) contains free-text hospital
    course / discharge notes.  Each note is parsed with regex to extract age,
    gender, BMI, conditions, clinical events, and lab abnormalities.
    Wearable telemetry (steps, HR, sleep) is synthesised from extracted clinical
    severity so the model receives coherent, correlated features.
    """
    print(f"Loading dataset from Hugging Face ({dataset_name})...")
    try:
        from datasets import load_dataset
    except ImportError:
        raise RuntimeError("'datasets' package not found. Install with: pip install datasets") from None

    ds = load_dataset(dataset_name)
    split = list(ds.keys())[0]
    raw = ds[split].to_pandas()
    n = len(raw)
    print(f"  Loaded {n:,} clinical notes from split '{split}'")

    print("  Parsing notes…")
    records = [_parse_clinical_note(row["text"]) for _, row in raw.iterrows()]
    df = pd.DataFrame(records)

    # ── Synthesise wearable telemetry from severity ───────────────────────────
    # severity ≈ 0 (healthy) → 1+ (very ill)  |  cap at 1 for normalisation
    rng = np.random.default_rng(RANDOM_STATE)
    sev = np.clip(df["_severity"].values, 0, 1.2)
    health = np.clip(1.0 - sev / 1.2, 0.0, 1.0)   # 1 = healthy, 0 = critical

    noise = lambda scale, size=n: rng.normal(0, scale, size)
    df["avg_daily_steps"]  = np.clip(health * 9000 + 1000 + noise(600),  1000, 15000)
    df["step_volatility"]  = np.clip((1 - health) * 1400 + 100 + noise(150), 50, 3000)
    df["avg_resting_hr"]   = np.clip(65 + (1 - health) * 22 + noise(3),  45, 110)
    df["hr_trend"]         = (rng.random(n) - 0.5) * 6
    df["avg_active_mins"]  = np.clip(health * 55 + 5 + noise(8),          0,  90)
    df["avg_sleep_hours"]  = np.clip(6.0 + health * 2.0 + noise(0.5),     3,  10)

    # SpO2 already extracted per-note; blend with synthesised baseline where missing
    df["avg_spo2"] = np.clip(df["avg_spo2"] + noise(0.3), 80, 100)

    df.drop(columns=["_severity"], inplace=True)

    # Add log-normal noise to loss_ratio for realistic variance
    lr_noise = rng.lognormal(0, 0.25, n)
    df["loss_ratio"] = np.clip(df["loss_ratio"] * lr_noise, 0.10, 6.0)

    print(f"  loss_ratio  mean={df['loss_ratio'].mean():.3f}  "
          f"std={df['loss_ratio'].std():.3f}  "
          f"p5={df['loss_ratio'].quantile(0.05):.3f}  "
          f"p95={df['loss_ratio'].quantile(0.95):.3f}")
    return df


def load_training_dataframe(
    dataset_mode: str = DEFAULT_DATA_MODE,
    hf_dataset_name: str = HF_DATASET_NAME,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Load one or both training sources into a single dataframe."""
    if dataset_mode not in {"local", "hf", "both"}:
        raise ValueError(f"Unsupported dataset mode: {dataset_mode}")

    selected_sources = []
    if dataset_mode in {"local", "both"}:
        selected_sources.append(("local", load_local_dataset))
    if dataset_mode in {"hf", "both"}:
        selected_sources.append(("huggingface", lambda: load_from_huggingface(hf_dataset_name)))

    frames = []
    source_counts: Dict[str, int] = {}
    errors = []

    for source_name, loader in selected_sources:
        try:
            df = loader().copy()
        except Exception as exc:
            if dataset_mode != "both":
                raise
            errors.append((source_name, exc))
            print(f"WARNING: Failed to load {source_name} dataset: {exc}")
            continue

        df["dataset_source"] = source_name
        frames.append(df)
        source_counts[source_name] = len(df)

    if not frames:
        details = "; ".join(f"{name}: {exc}" for name, exc in errors) or "no sources selected"
        raise RuntimeError(f"Unable to load any training data ({details})")

    df = pd.concat(frames, ignore_index=True, sort=False)
    print(f"Using dataset mode: {dataset_mode}")
    for source_name, row_count in source_counts.items():
        print(f"  {source_name:>11s}: {row_count:,} rows")
    print(f"  {'combined':>11s}: {len(df):,} rows")
    return df, source_counts


def load_and_prepare(
    dataset_mode: str = DEFAULT_DATA_MODE,
    return_source_counts: bool = False,
    hf_dataset_name: str = HF_DATASET_NAME,
):
    df, source_counts = load_training_dataframe(dataset_mode, hf_dataset_name=hf_dataset_name)

    df = engineer_features(df)
    X, y, feature_names = get_feature_matrix(df)
    print(f"  {X.shape[1]} features prepared: {feature_names}")

    # Stratified split on loss_ratio quartiles so test set is representative
    y_strata = pd.qcut(y, q=4, labels=False, duplicates="drop")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y_strata
    )
    result = (X_train, X_test, y_train, y_test, feature_names)
    if return_source_counts:
        return result + (source_counts,)
    return result


def objective(trial, X_train, y_train):
    """Optuna objective — minimize MAE via 3-fold CV."""
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 100, 500),
        "max_depth":         trial.suggest_int("max_depth", 3, 10),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight":  trial.suggest_int("min_child_weight", 1, 10),
        "gamma":             trial.suggest_float("gamma", 0, 5),
        "reg_alpha":         trial.suggest_float("reg_alpha", 0, 5),
        "reg_lambda":        trial.suggest_float("reg_lambda", 0, 5),
        "random_state":      RANDOM_STATE,
        "verbosity":         0,
        "tree_method":       "hist",
    }
    model = xgb.XGBRegressor(**params)
    scores = cross_val_score(
        model, X_train, y_train,
        cv=3, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    return -scores.mean()


def tune_and_train(
    X_train,
    y_train,
    X_test,
    y_test,
    feature_names,
    dataset_mode=DEFAULT_DATA_MODE,
    source_counts=None,
    hf_dataset_name: str = HF_DATASET_NAME,
):
    print("\n[1/3] Tuning hyperparameters with Optuna...")
    study = optuna.create_study(direction="minimize", study_name="aegis_xgb")
    study.optimize(
        lambda t: objective(t, X_train, y_train),
        n_trials=N_OPTUNA_TRIALS,
        show_progress_bar=True,
    )
    print(f"\n  Best CV MAE: {study.best_value:.4f}")
    print(f"  Best params: {study.best_params}")

    print("\n[2/3] Training final model with best params...")
    best_params = study.best_params.copy()
    # Use a large n_estimators — early stopping will find the optimal number
    best_params["n_estimators"] = 2000
    best_params.update({"random_state": RANDOM_STATE, "verbosity": 0, "tree_method": "hist",
                        "early_stopping_rounds": 50})

    # 10% of training data held out for early stopping validation
    val_size = int(len(X_train) * 0.10)
    X_tr, X_val = X_train[:-val_size], X_train[-val_size:]
    y_tr, y_val = y_train[:-val_size], y_train[-val_size:]

    configure_mlflow()
    with mlflow.start_run(run_name="final_xgb_with_optuna") as run:
        mlflow.log_params(best_params)
        mlflow.log_param("optuna_trials", N_OPTUNA_TRIALS)
        mlflow.log_param("target", "loss_ratio_log")
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("dataset_mode", dataset_mode)
        mlflow.log_param("hf_dataset_name", hf_dataset_name)
        if source_counts:
            for source_name, row_count in source_counts.items():
                mlflow.log_param(f"rows_{source_name}", row_count)

        model = xgb.XGBRegressor(**best_params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        print(f"  Best iteration: {model.best_iteration}")
        mlflow.log_param("best_iteration", model.best_iteration)

        train_preds = model.predict(X_train)
        test_preds  = model.predict(X_test)

        metrics = {
            "train_mae":  mean_absolute_error(y_train, train_preds),
            "test_mae":   mean_absolute_error(y_test, test_preds),
            "train_rmse": np.sqrt(mean_squared_error(y_train, train_preds)),
            "test_rmse":  np.sqrt(mean_squared_error(y_test, test_preds)),
            "train_r2":   r2_score(y_train, train_preds),
            "test_r2":    r2_score(y_test, test_preds),
        }
        for name, val in metrics.items():
            mlflow.log_metric(name, val)

        print("\n  Metrics:")
        for k, v in metrics.items():
            print(f"    {k:12s} {v:.4f}")

        print("\n[3/3] Calibrating HRS scorer...")
        scorer = HRSScorer()
        scorer.fit(train_preds)
        mlflow.log_metric("hrs_p05", scorer.p05)
        mlflow.log_metric("hrs_p95", scorer.p95)

        model_path  = ARTIFACTS / "xgb_model.pkl"
        scorer_path = ARTIFACTS / "hrs_scorer.pkl"
        feats_path  = ARTIFACTS / "feature_names.pkl"

        joblib.dump(model,  model_path)
        joblib.dump(scorer.to_dict(), scorer_path)
        joblib.dump(feature_names,     feats_path)

        mlflow.log_artifact(str(model_path),  artifact_path="model")
        mlflow.log_artifact(str(scorer_path), artifact_path="model")
        mlflow.log_artifact(str(feats_path),  artifact_path="model")

        print(f"\n  Saved: {model_path}")
        print(f"  Saved: {scorer_path}")
        print(f"  Saved: {feats_path}")
        print(f"  MLflow run: {run.info.run_id}")

    return model, scorer, metrics


def sanity_check(model, scorer, X_test, y_test, feature_names):
    print("\n[Sanity check on 5 test predictions]")
    preds_log = model.predict(X_test[:5])
    preds_actual = np.expm1(preds_log)
    actual_log   = y_test[:5]
    actual       = np.expm1(actual_log)
    hrs_scores   = scorer.score_batch(preds_log)

    print(f"  {'Pred LR':>10s} {'Actual LR':>10s} {'HRS':>6s} {'Band':>10s}")
    for p, a, h in zip(preds_actual, actual, hrs_scores):
        print(f"  {p:10.3f} {a:10.3f} {h:6.1f} {scorer.risk_band(h):>10s}")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Train Aegis AI underwriting model")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-local",
        action="store_true",
        help="Load data from the local CSV only"
    )
    group.add_argument(
        "--use-hf",
        dest="use_hf",
        action="store_true",
        help=f"Load data from Hugging Face ({HF_DATASET_NAME}) only"
    )
    group.add_argument(
        "--use-hf-dataset",
        dest="use_hf",
        action="store_true",
        help="Alias for --use-hf"
    )
    group.add_argument(
        "--use-both",
        action="store_true",
        help="Combine local CSV and Hugging Face rows into one training run"
    )
    group.add_argument(
        "--no-hf",
        action="store_true",
        help="Alias for --use-local"
    )
    parser.add_argument(
        "--hf-dataset",
        default=HF_DATASET_NAME,
        help="Hugging Face dataset ID to load for HF-based training"
    )
    return parser


def resolve_dataset_mode(args) -> str:
    if getattr(args, "use_local", False) or getattr(args, "no_hf", False):
        return "local"
    if getattr(args, "use_hf", False):
        return "hf"
    if getattr(args, "use_both", False):
        return "both"
    return DEFAULT_DATA_MODE


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    dataset_mode = resolve_dataset_mode(args)

    X_train, X_test, y_train, y_test, feature_names, source_counts = load_and_prepare(
        dataset_mode=dataset_mode,
        return_source_counts=True,
        hf_dataset_name=args.hf_dataset,
    )
    model, scorer, metrics = tune_and_train(
        X_train,
        y_train,
        X_test,
        y_test,
        feature_names,
        dataset_mode=dataset_mode,
        source_counts=source_counts,
        hf_dataset_name=args.hf_dataset,
    )
    sanity_check(model, scorer, X_test, y_test, feature_names)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
