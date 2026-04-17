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

    def score(self, log_loss_ratio):
        """Convert one log-loss-ratio value to 0-100."""
        if not self.fitted:
            raise RuntimeError("Scorer not fitted. Call .fit() first.")
        normalized = (log_loss_ratio - self.p05) / (self.p95 - self.p05)
        return float(np.clip(normalized * 100, 0, 100))

    def score_batch(self, log_loss_ratio_array):
        """Vectorized scoring."""
        arr = np.asarray(log_loss_ratio_array)
        normalized = (arr - self.p05) / (self.p95 - self.p05)
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
