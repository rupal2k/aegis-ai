"""Prediction endpoints — wraps the ML engine with HTTP."""
import logging
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
from ingestion.auth.dependencies import get_current_user, require_company_access

router = APIRouter(prefix="/predict", tags=["predict"])
_audit = logging.getLogger("aegis.audit")


def _enrich_driver(model, driver: dict) -> FeatureDriver:
    return FeatureDriver(
        feature     = driver["feature"],
        value       = driver["value"],
        shap_value  = driver["shap_value"],
        direction   = driver["direction"],
        explanation = model.explainer.plain_language(driver),
    )


@router.post(
    "/employee",
    response_model=EmployeePredictionResponse,
    summary="Score a single employee record",
    description=(
        "Return predicted loss ratio, Health Risk Score, risk band, and SHAP-enriched "
        "feature drivers for one employee payload."
    ),
)
def predict_employee(
    payload: EmployeePredictionRequest,
    user: dict = Depends(get_current_user),
):
    model = get_model()
    emp = payload.model_dump()
    if emp.get("chronic_count") is None:
        emp["chronic_count"] = int(emp["diabetic"]) + int(emp["hypertension"])

    result = model.predict_one(emp)
    enriched = [_enrich_driver(model, d) for d in result["top_drivers"]]

    _audit.info("PREDICT_EMPLOYEE user=%s risk_band=%s", user["sub"], result["risk_band"])
    return EmployeePredictionResponse(
        predicted_loss_ratio = result["predicted_loss_ratio"],
        health_risk_score    = result["health_risk_score"],
        risk_band            = result["risk_band"],
        top_drivers          = enriched,
    )


@router.get(
    "/company/{company_id}",
    response_model=CompanyPredictionResponse,
    summary="Summarize company risk and HRS distribution",
    description=(
        "Aggregate employee feature snapshots for one company and return mean HRS, "
        "risk-band distribution, and top portfolio drivers."
    ),
)
def predict_company(
    company_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_company_access),
):
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

    _audit.info("PREDICT_COMPANY user=%s company=%s employees=%d", user["sub"], company_id, result["employee_count"])
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


@router.post(
    "/premium",
    response_model=PremiumResponse,
    summary="Calculate premium adjustment from HRS",
    description=(
        "Translate a base premium and Health Risk Score into adjusted premium guidance "
        "and zone classification."
    ),
)
def predict_premium(
    payload: PremiumRequest,
    user: dict = Depends(get_current_user),
):
    _audit.info("PREDICT_PREMIUM user=%s hrs=%s", user["sub"], payload.hrs)
    result = calculate_premium_adjustment(payload.base_premium, payload.hrs)
    return PremiumResponse(**result)


@router.post(
    "/wellness-roi",
    response_model=WellnessROIResponse,
    summary="Estimate wellness program ROI",
    description=(
        "Compare current and projected company HRS values to estimate premium savings, "
        "program lift, and expected ROI."
    ),
)
def predict_wellness_roi(
    payload: WellnessROIRequest,
    user: dict = Depends(get_current_user),
):
    _audit.info("PREDICT_WELLNESS_ROI user=%s", user["sub"])
    result = calculate_wellness_roi(
        payload.base_premium,
        payload.current_hrs,
        payload.projected_hrs_after_program,
    )
    return WellnessROIResponse(**result)
