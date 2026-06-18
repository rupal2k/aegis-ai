"""Translate Health Risk Score into a dynamic premium adjustment."""

# Derived from 200-corporate market quotes via ml_engine/training/calibrate_premium.py
# Re-run calibrate_premium.py after adding new quote data to update these tables.
INDUSTRY_RISK_MULTIPLIERS = {'Agriculture': 1.029, 'Automotive': 0.988, 'Construction': 0.876, 'Consulting': 1.016, 'Education': 1.011, 'Energy': 0.902, 'Finance': 0.994, 'Food & Beverages': 1.099, 'Healthcare': 1.034, 'Hospitality': 1.01, 'IT Services': 0.995, 'Logistics': 1.101, 'Manufacturing': 0.91, 'Media': 1.133, 'Mining': 0.986, 'Pharma': 0.997, 'Real Estate': 0.991, 'Retail': 1.045, 'Telecom': 1.135, 'Textiles': 1.115}

REGION_MULTIPLIERS = {'Central': 1.018, 'East': 0.934, 'North': 1.016, 'Northeast': 1.036, 'South': 0.965, 'West': 1.017}

SUM_ASSURED_BAND_MULTIPLIERS = {'1-3L': 0.944, '4-7L': 1.0, '8-15L': 1.202, '15L+': 1.0}


def _get_sum_assured_band(sum_assured_lakhs: float) -> str:
    if sum_assured_lakhs <= 3:
        return "1-3L"
    if sum_assured_lakhs <= 7:
        return "4-7L"
    if sum_assured_lakhs <= 15:
        return "8-15L"
    return "15L+"


def calculate_premium_adjustment(
    base_premium: float,
    hrs: float,
    industry: str = None,
    region: str = None,
    sum_assured_lakhs: float = 5.0,
) -> dict:
    """
    Dynamic premium pricing based on HRS with optional market multipliers.

    HRS 0-40  : discount zone (up to 15% off)
    HRS 41-60 : standard rate
    HRS 61-100: loading zone (up to 30% surcharge)

    Optional multipliers (applied to base_premium before HRS adjustment):
    - industry: industry-specific risk loading from Indian market data
    - region: regional cost-of-care factor (North/South/East/West/Central/Northeast)
    - sum_assured_lakhs: sum assured band adjustment
    """
    # Apply market multipliers to base premium
    multiplier = 1.0
    if industry and industry in INDUSTRY_RISK_MULTIPLIERS:
        multiplier *= INDUSTRY_RISK_MULTIPLIERS[industry]
    if region and region in REGION_MULTIPLIERS:
        multiplier *= REGION_MULTIPLIERS[region]
    band = _get_sum_assured_band(sum_assured_lakhs)
    multiplier *= SUM_ASSURED_BAND_MULTIPLIERS.get(band, 1.0)
    effective_base = base_premium * multiplier

    if hrs <= 40:
        discount = (40 - hrs) / 40 * 0.15
        adjusted = effective_base * (1 - discount)
        return {
            "base_premium":     base_premium,
            "adjusted_premium": round(adjusted, 2),
            "adjustment_pct":   round(-discount * 100, 2),
            "zone":             "discount",
            "recommendation":   "Low-risk group. Offer preferred rates to retain.",
        }

    if hrs <= 60:
        return {
            "base_premium":     base_premium,
            "adjusted_premium": round(effective_base, 2),
            "adjustment_pct":   round((multiplier - 1) * 100, 2),
            "zone":             "standard",
            "recommendation":   "Average risk. Price at book rate.",
        }

    loading  = (hrs - 60) / 40 * 0.30
    adjusted = effective_base * (1 + loading)
    return {
        "base_premium":     base_premium,
        "adjusted_premium": round(adjusted, 2),
        "adjustment_pct":   round(loading * 100, 2),
        "zone":             "loading",
        "recommendation":   "High risk. Apply surcharge or require wellness program.",
    }


def calculate_wellness_roi(
    base_premium: float,
    current_hrs: float,
    projected_hrs_after_program: float,
    industry: str = None,
    region: str = None,
    sum_assured_lakhs: float = 5.0,
) -> dict:
    """Estimates ROI of a wellness program based on projected HRS improvement."""
    current  = calculate_premium_adjustment(base_premium, current_hrs,
                                            industry, region, sum_assured_lakhs)
    improved = calculate_premium_adjustment(base_premium, projected_hrs_after_program,
                                            industry, region, sum_assured_lakhs)
    annual_savings = current["adjusted_premium"] - improved["adjusted_premium"]
    return {
        "current_premium":   current["adjusted_premium"],
        "projected_premium": improved["adjusted_premium"],
        "annual_savings":    round(annual_savings, 2),
        "hrs_improvement":   round(current_hrs - projected_hrs_after_program, 1),
        "current_zone":      current["zone"],
        "projected_zone":    improved["zone"],
    }
