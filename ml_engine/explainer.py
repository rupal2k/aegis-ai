"""SHAP wrapper for model explainability."""
import shap
import numpy as np


class AegisExplainer:
    """Wraps SHAP TreeExplainer with business-friendly outputs."""

    def __init__(self, model, feature_names: list):
        self.model = model
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(model)

    def explain_one(self, x_row, top_n: int = 5) -> list:
        """
        Returns top N feature contributors for a single prediction.

        Each contributor: { feature, value, shap_value, direction }
        direction = "increases risk" or "reduces risk"
        """
        shap_values = self.explainer.shap_values(x_row.reshape(1, -1))[0]

        contributions = []
        for i, feat in enumerate(self.feature_names):
            contributions.append({
                "feature":    feat,
                "value":      float(x_row[i]),
                "shap_value": float(shap_values[i]),
                "direction":  "increases risk" if shap_values[i] > 0 else "reduces risk"
            })

        contributions.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
        return contributions[:top_n]

    def explain_batch(self, X):
        """Returns mean absolute SHAP per feature — global feature importance."""
        shap_values = self.explainer.shap_values(X)
        mean_abs = np.abs(shap_values).mean(axis=0)

        importance = [
            {"feature": f, "importance": float(v)}
            for f, v in zip(self.feature_names, mean_abs)
        ]
        importance.sort(key=lambda c: c["importance"], reverse=True)
        return importance

    def plain_language(self, contribution: dict) -> str:
        """Convert SHAP contribution to an HR-friendly explanation."""
        feat = contribution["feature"]
        val  = contribution["value"]
        direction = contribution["direction"]

        friendly = {
            "age":                  f"Employee age ({val:.0f} years)",
            "bmi":                  f"BMI ({val:.1f})",
            "smoker":               "Smoking status",
            "diabetic":             "Diabetes diagnosis",
            "hypertension":         "Hypertension diagnosis",
            "chronic_count":        f"Number of chronic conditions ({val:.0f})",
            "avg_daily_steps":      f"Average daily steps ({val:.0f})",
            "step_volatility":      "Irregular activity pattern",
            "avg_resting_hr":       f"Resting heart rate ({val:.0f} bpm)",
            "hr_trend":             "Heart rate trend over time",
            "avg_active_mins":      f"Daily active minutes ({val:.0f})",
            "avg_sleep_hours":      f"Average sleep ({val:.1f} hours)",
            "avg_spo2":             f"Blood oxygen ({val:.1f}%)",
            "visit_count":          f"Clinical visits ({val:.0f})",
            "hospitalized_count":   f"Hospitalizations ({val:.0f})",
            "activity_score":       f"Overall activity score ({val:.1f})",
            "health_composite":     "Combined chronic health burden",
        }

        label = friendly.get(feat, feat)
        return f"{label} {direction}"
