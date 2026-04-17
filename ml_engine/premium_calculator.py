"""Translate Health Risk Score into a dynamic premium adjustment."""


def calculate_premium_adjustment(base_premium: float, hrs: float) -> dict:
    """
    Dynamic premium pricing based on HRS.

    HRS 0-40  : discount zone (reward healthy groups, up to 15% off)
    HRS 41-60 : standard rate (no adjustment)
    HRS 61-100: loading zone (surcharge up to 30%)
    """
    if hrs <= 40:
        discount = (40 - hrs) / 40 * 0.15
        adjusted = base_premium * (1 - discount)
        return {
            "base_premium":      base_premium,
            "adjusted_premium":  round(adjusted, 2),
            "adjustment_pct":    round(-discount * 100, 2),
            "zone":              "discount",
            "recommendation":    "Low-risk group. Offer preferred rates to retain."
        }

    if hrs <= 60:
        return {
            "base_premium":      base_premium,
            "adjusted_premium":  base_premium,
            "adjustment_pct":    0.0,
            "zone":              "standard",
            "recommendation":    "Average risk. Price at book rate."
        }

    loading  = (hrs - 60) / 40 * 0.30
    adjusted = base_premium * (1 + loading)
    return {
        "base_premium":      base_premium,
        "adjusted_premium":  round(adjusted, 2),
        "adjustment_pct":    round(loading * 100, 2),
        "zone":              "loading",
        "recommendation":    "High risk. Apply surcharge or require wellness program."
    }


def calculate_wellness_roi(
    base_premium: float,
    current_hrs: float,
    projected_hrs_after_program: float,
) -> dict:
    """
    Estimates ROI of a wellness program based on projected HRS improvement.
    Used in Corporate HR dashboard.
    """
    current  = calculate_premium_adjustment(base_premium, current_hrs)
    improved = calculate_premium_adjustment(base_premium, projected_hrs_after_program)

    annual_savings = current["adjusted_premium"] - improved["adjusted_premium"]
    return {
        "current_premium":         current["adjusted_premium"],
        "projected_premium":       improved["adjusted_premium"],
        "annual_savings":          round(annual_savings, 2),
        "hrs_improvement":         round(current_hrs - projected_hrs_after_program, 1),
        "current_zone":            current["zone"],
        "projected_zone":          improved["zone"],
    }
