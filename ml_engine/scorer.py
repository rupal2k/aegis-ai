"""Convert raw loss_ratio predictions into interpretable Health Risk Scores (0-100)."""
import numpy as np


class HRSScorer:
    """
    Converts log-loss-ratio predictions into a 0-100 Health Risk Score.

    Lower HRS = healthier (discount zone)
    Higher HRS = riskier (loading zone)

    Calibration: fit() learns the distribution bounds from training data.
    """

    def __init__(self):
        self.p05 = None
        self.p95 = None
        self.fitted = False

    def fit(self, log_loss_ratio_array):
        """Calibrate bounds from training predictions."""
        self.p05 = float(np.percentile(log_loss_ratio_array, 5))
        self.p95 = float(np.percentile(log_loss_ratio_array, 95))
        self.fitted = True
        return self

    def _normalize(self, arr):
        """Normalize values into a 0-1 range, handling degenerate calibration safely."""
        if not self.fitted:
            raise RuntimeError("Scorer not fitted. Call .fit() first.")

        scale = self.p95 - self.p05
        if not np.isfinite(scale) or abs(scale) < 1e-12:
            return np.full_like(np.asarray(arr, dtype=float), 0.5, dtype=float)
        return (np.asarray(arr, dtype=float) - self.p05) / scale

    def score(self, log_loss_ratio):
        """Convert one log-loss-ratio value to 0-100."""
        normalized = self._normalize(log_loss_ratio)
        return float(np.clip(normalized * 100, 0, 100))

    def score_batch(self, log_loss_ratio_array):
        """Vectorized scoring."""
        normalized = self._normalize(log_loss_ratio_array)
        return np.clip(normalized * 100, 0, 100).round(1)

    def risk_band(self, hrs: float) -> str:
        """Human-readable risk tier."""
        if hrs < 30:  return "Low"
        if hrs < 60:  return "Moderate"
        if hrs < 80:  return "High"
        return "Critical"

    def to_dict(self):
        return {"p05": self.p05, "p95": self.p95, "fitted": self.fitted}

    @classmethod
    def from_dict(cls, d: dict):
        inst = cls()
        inst.p05 = d["p05"]
        inst.p95 = d["p95"]
        inst.fitted = d["fitted"]
        return inst
