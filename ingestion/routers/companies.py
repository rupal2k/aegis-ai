"""Read-only company endpoints used by the dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ingestion.database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(db: Session = Depends(get_db)):
    """Returns all companies with basic metadata."""
    rows = db.execute(text("""
        SELECT company_id, company_name, industry, city,
               employee_count, base_premium
        FROM companies
        ORDER BY company_name
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{company_id}/employees")
def company_employees(company_id: str, db: Session = Depends(get_db)):
    """All employees with snapshot features for a given company."""
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
    return [dict(r) for r in rows]
