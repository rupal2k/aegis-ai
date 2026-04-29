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
    "gcc-insurance-intelligence-lab-dev/gcc-insurance-underwriting-risk",
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


def load_from_huggingface(dataset_name: str = HF_DATASET_NAME):
    """Load dataset from Hugging Face and map it into the Aegis feature schema.
    
    Maps the insurance underwriting dataset to Aegis AI health telemetry format.
    """
    print(f"Loading dataset from Hugging Face ({dataset_name})...")
    try:
        from datasets import load_dataset
    except ImportError:
        raise RuntimeError("'datasets' package not found. Install with: pip install datasets") from None
    
    ds = load_dataset(dataset_name)
    print(f"  Loaded {len(ds['train'])} training rows from HF")
    
    # Convert to pandas DataFrame
    df = ds['train'].to_pandas()
    rng = np.random.default_rng(RANDOM_STATE)
    
    # Map HF columns to Aegis AI format
    df_mapped = pd.DataFrame()
    df_mapped['age'] = df['applicant_age']
    df_mapped['gender'] = df['gender']
    df_mapped['bmi'] = df['bmi']
    df_mapped['smoker'] = df['smoker'].astype(int)
    
    # Map health_score to estimated health features
    # health_score (0-100) -> estimate other telemetry
    health_normalized = df['health_score'] / 100.0
    df_mapped['avg_daily_steps'] = (health_normalized * 10000 + rng.normal(0, 500, len(df))).clip(3000, 15000)
    df_mapped['step_volatility'] = (1 - health_normalized) * 1500 + rng.normal(0, 200, len(df))
    df_mapped['avg_resting_hr'] = 60 + (1 - health_normalized) * 25 + rng.normal(0, 3, len(df))
    df_mapped['hr_trend'] = (rng.random(len(df)) - 0.5) * 5
    df_mapped['avg_active_mins'] = health_normalized * 60 + rng.normal(0, 10, len(df))
    df_mapped['avg_sleep_hours'] = 6.5 + health_normalized * 1.5 + rng.normal(0, 0.5, len(df))
    df_mapped['avg_spo2'] = 96 + health_normalized * 2 + rng.normal(0, 0.5, len(df))
    
    # Occupation risk to chronic conditions
    risk_map = {'Low': 0, 'Medium': 1, 'High': 2}
    occupation_risk_encoded = df['occupation_risk'].map(risk_map).fillna(1)
    df_mapped['diabetic'] = (occupation_risk_encoded > 1).astype(int)
    df_mapped['hypertension'] = (occupation_risk_encoded > 0).astype(int)
    df_mapped['chronic_count'] = occupation_risk_encoded
    
    # Clinical events from claims history
    df_mapped['visit_count'] = df['previous_claims_count'].clip(0, 10)
    df_mapped['hospitalized_count'] = (df['previous_claims_count'] > 3).astype(int)
    
    # Lab features (estimated from health_score)
    low_health = health_normalized < 0.5
    df_mapped['lab_heart_flag'] = (low_health & (occupation_risk_encoded > 0)).astype(int)
    df_mapped['lab_diabetes_flag'] = df_mapped['diabetic']
    df_mapped['lab_kidney_flag'] = (low_health & (df['bmi'] > 28)).astype(int)
    df_mapped['lab_liver_flag'] = (low_health & df['smoker']).astype(int)
    df_mapped['lab_inflammation_flag'] = (low_health & (occupation_risk_encoded > 1)).astype(int)
    df_mapped['lab_iron_flag'] = (rng.random(len(df)) > 0.8).astype(int)
    df_mapped['lab_thyroid_flag'] = (rng.random(len(df)) > 0.85).astype(int)
    df_mapped['lab_bone_flag'] = (df_mapped['age'] > 55).astype(int)
    df_mapped['lab_vitamin_flag'] = (rng.random(len(df)) > 0.7).astype(int)
    
    # Target: Use premium_calculated as proxy for loss_ratio
    # Normalize premium to 0-1 loss ratio scale
    df_mapped['loss_ratio'] = np.clip(df['premium_calculated'] / df['premium_calculated'].max() * 2, 0.1, 10)
    
    return df_mapped


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
