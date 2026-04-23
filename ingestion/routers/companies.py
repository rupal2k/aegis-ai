"""Read-only company endpoints used by the dashboard."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ingestion.database import get_db
from ingestion.auth.dependencies import get_current_user, require_company_access

router = APIRouter(prefix="/companies", tags=["companies"])
_audit = logging.getLogger("aegis.audit")


@router.get(
    "",
    summary="List companies available to the dashboard",
    description=(
        "Return company metadata and base premium inputs used by the dashboard selectors, "
        "portfolio views, and role-based workflows."
    ),
)
def list_companies(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rows = db.execute(text("""
        SELECT company_id, company_name, industry, city,
               employee_count, base_premium
        FROM companies
        ORDER BY company_name
    """)).mappings().all()
    _audit.info("LIST_COMPANIES user=%s role=%s count=%d", user["sub"], user.get("role"), len(rows))
    return [dict(r) for r in rows]


@router.get(
    "/{company_id}/employees",
    summary="List employees for a company view",
    description=(
        "Return employee-level feature, health, and claims fields used by the workforce "
        "dashboard for the requested company."
    ),
)
def company_employees(
    company_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_company_access),
):
    rows = db.execute(text("""
        SELECT s.employee_id, s.age, s.gender, s.bmi,
               s.smoker, s.diabetic, s.hypertension, s.chronic_count,
               s.avg_daily_steps, s.avg_resting_hr, s.avg_sleep_hours,
               s.visit_count, s.hospitalized_count, s.loss_ratio, s.high_risk,
               e.job_category
        FROM training_snapshots s
        JOIN employees e ON e.employee_id = s.employee_id
        WHERE s.company_id = :cid
    """), {"cid": company_id}).mappings().all()
    _audit.info(
        "ACCESS_EMPLOYEES user=%s role=%s company=%s records=%d",
        user["sub"], user.get("role"), company_id, len(rows),
    )
    return [dict(r) for r in rows]
