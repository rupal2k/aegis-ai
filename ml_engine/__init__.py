"""Aegis ML Engine — public inference API."""
import joblib
import numpy as np
from pathlib import Path

from ml_engine.features  import engineer_features, FEATURE_COLUMNS
from ml_engine.scorer    import HRSScorer
from ml_engine.explainer import AegisExplainer
from ml_engine.premium_calculator import (
    calculate_premium_adjustment, calculate_wellness_roi,
)

ARTIFACTS = Path(__file__).parent / "artifacts"


class AegisModel:
    """Loaded, inference-ready bundle: model + scorer + explainer."""

    def __init__(self):
        self.model = joblib.load(ARTIFACTS / "xgb_model.pkl")
        self.feature_names = joblib.load(ARTIFACTS / "feature_names.pkl")
        self.scorer = HRSScorer.from_dict(joblib.load(ARTIFACTS / "hrs_scorer.pkl"))
        self.explainer = AegisExplainer(self.model, self.feature_names)

    def predict_one(self, employee_row: dict) -> dict:
        """
        Takes a dict of features for one employee.
        Returns: {loss_ratio, hrs, risk_band, top_drivers}
        """
        import pandas as pd
        df = pd.DataFrame([employee_row])
        df = engineer_features(df)
        X = df[self.feature_names].values

        log_pred = float(self.model.predict(X)[0])
        pred_lr  = float(np.expm1(log_pred))
        hrs      = self.scorer.score(log_pred)

        drivers = self.explainer.explain_one(X[0], top_n=5)
        return {
            "predicted_loss_ratio": round(pred_lr, 4),
            "health_risk_score":    round(hrs, 1),
            "risk_band":            self.scorer.risk_band(hrs),
            "top_drivers":          drivers,
        }

    def predict_company(self, employees_df) -> dict:
        """Aggregate all employees in a company to a company-level HRS."""
        df = engineer_features(employees_df)
        X = df[self.feature_names].values

        log_preds = self.model.predict(X)
        pred_lrs  = np.expm1(log_preds)
        hrs_array = self.scorer.score_batch(log_preds)

        mean_hrs = float(np.mean(hrs_array))
        global_importance = self.explainer.explain_batch(X)

        return {
            "employee_count":    len(employees_df),
            "mean_loss_ratio":   float(np.mean(pred_lrs)),
            "mean_hrs":          round(mean_hrs, 1),
            "risk_band":         self.scorer.risk_band(mean_hrs),
            "hrs_distribution":  hrs_array.tolist(),
            "top_risk_drivers":  global_importance[:5],
        }


_MODEL_INSTANCE = None

def get_model() -> AegisModel:
    """Singleton loader — avoids re-reading .pkl on every request."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = AegisModel()
    return _MODEL_INSTANCE
