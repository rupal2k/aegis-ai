"""
Aegis AI — Model training pipeline.

Run: python -m ml_engine.training.train
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

from ml_engine.features import engineer_features, get_feature_matrix, TARGET_LOG
from ml_engine.scorer   import HRSScorer

load_dotenv()

DATA_PATH    = Path("data/output/training_dataset.csv")
ARTIFACTS    = Path("ml_engine/artifacts")
ARTIFACTS.mkdir(exist_ok=True)

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("aegis-underwriting")

N_OPTUNA_TRIALS = 30
RANDOM_STATE    = 42

optuna.logging.set_verbosity(optuna.logging.WARNING)


def load_and_prepare():
    print(f"Loading {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"  {len(df):,} rows loaded")

    df = engineer_features(df)
    X, y, feature_names = get_feature_matrix(df)
    print(f"  {X.shape[1]} features prepared: {feature_names}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    return X_train, X_test, y_train, y_test, feature_names


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


def tune_and_train(X_train, y_train, X_test, y_test, feature_names):
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
    best_params.update({"random_state": RANDOM_STATE, "verbosity": 0, "tree_method": "hist"})

    with mlflow.start_run(run_name="final_xgb_with_optuna") as run:
        mlflow.log_params(best_params)
        mlflow.log_param("optuna_trials", N_OPTUNA_TRIALS)
        mlflow.log_param("target", "loss_ratio_log")
        mlflow.log_param("n_features", len(feature_names))

        model = xgb.XGBRegressor(**best_params)
        model.fit(X_train, y_train)

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


if __name__ == "__main__":
    X_train, X_test, y_train, y_test, feature_names = load_and_prepare()
    model, scorer, metrics = tune_and_train(X_train, y_train, X_test, y_test, feature_names)
    sanity_check(model, scorer, X_test, y_test, feature_names)
    print("\nTraining complete.")
