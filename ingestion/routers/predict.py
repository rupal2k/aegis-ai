"""Prediction endpoints — wraps the ML engine with HTTP."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import numpy as np

from ingestion.database import get_db
from ingestion.models.schemas import (
    EmployeePredictionRequest, EmployeePredictionResponse, FeatureDriver,
    CompanyPredictionResponse,
    PremiumRequest, PremiumResponse,
    WellnessROIRequest, WellnessROIResponse,
)
from ml_engine import get_model
from ml_engine.explainer import AegisExplainer
from ml_engine.premium_calculator import (
    calculate_premium_adjustment, calculate_wellness_roi,
)

router = APIRouter(prefix="/predict", tags=["predict"])


def _enrich_driver(model, driver: dict) -> FeatureDriver:
    """Attach plain-language explanation to a SHAP driver."""
    return FeatureDriver(
        feature     = driver["feature"],
        value       = driver["value"],
        shap_value  = driver["shap_value"],
        direction   = driver["direction"],
        explanation = model.explainer.plain_language(driver),
    )


@router.post("/employee", response_model=EmployeePredictionResponse)
def predict_employee(payload: EmployeePredictionRequest):
    """Predict HRS for a single employee given their features."""
    model = get_model()

    emp = payload.model_dump()
    if emp.get("chronic_count") is None:
        emp["chronic_count"] = int(emp["diabetic"]) + int(emp["hypertension"])

    result = model.predict_one(emp)

    enriched = [_enrich_driver(model, d) for d in result["top_drivers"]]

    return EmployeePredictionResponse(
        predicted_loss_ratio = result["predicted_loss_ratio"],
        health_risk_score    = result["health_risk_score"],
        risk_band            = result["risk_band"],
        top_drivers          = enriched,
    )


@router.get("/company/{company_id}", response_model=CompanyPredictionResponse)
def predict_company(company_id: str, db: Session = Depends(get_db)):
    """
    Aggregate HRS across all employees in a company.
    Pulls aggregated features from training_snapshots table.
    """
    company = db.execute(
        text("SELECT company_id, company_name FROM companies WHERE company_id = :cid"),
        {"cid": company_id}
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Unknown company: {company_id}")

    rows = db.execute(text("""
        SELECT age, gender, bmi, smoker, diabetic, hypertension, chronic_count,
               avg_daily_steps, step_volatility, avg_resting_hr, hr_trend,
               avg_active_mins, avg_sleep_hours, avg_spo2,
               visit_count, hospitalized_count
        FROM training_snapshots
        WHERE company_id = :cid
    """), {"cid": company_id}).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No employee data found. Run feature snapshot generation first."
        )

    df = pd.DataFrame(rows)
    df = df.apply(lambda col: pd.to_numeric(col, errors="coerce").fillna(col) if col.dtype == object else col)
    model  = get_model()
    result = model.predict_company(df)

    hrs_array = np.array(result["hrs_distribution"])
    low      = float((hrs_array < 30).mean() * 100)
    moderate = float(((hrs_array >= 30) & (hrs_array < 60)).mean() * 100)
    high     = float(((hrs_array >= 60) & (hrs_array < 80)).mean() * 100)
    critical = float((hrs_array >= 80).mean() * 100)

    return CompanyPredictionResponse(
        company_id        = company.company_id,
        company_name      = company.company_name,
        employee_count    = result["employee_count"],
        mean_loss_ratio   = round(result["mean_loss_ratio"], 4),
        mean_hrs          = result["mean_hrs"],
        risk_band         = result["risk_band"],
        low_risk_pct      = round(low, 1),
        moderate_risk_pct = round(moderate, 1),
        high_risk_pct     = round(high, 1),
        critical_risk_pct = round(critical, 1),
        top_risk_drivers  = result["top_risk_drivers"],
    )


@router.post("/premium", response_model=PremiumResponse)
def predict_premium(payload: PremiumRequest):
    """Convert a Health Risk Score into a dynamic premium adjustment."""
    result = calculate_premium_adjustment(payload.base_premium, payload.hrs)
    return PremiumResponse(**result)


@router.post("/wellness-roi", response_model=WellnessROIResponse)
def predict_wellness_roi(payload: WellnessROIRequest):
    """Calculate projected ROI of a wellness program for Corporate HR."""
    result = calculate_wellness_roi(
        payload.base_premium,
        payload.current_hrs,
        payload.projected_hrs_after_program,
    )
    return WellnessROIResponse(**result)
