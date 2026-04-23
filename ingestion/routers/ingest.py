"""Three POST endpoints for data ingestion."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from ingestion.database import get_db
from ingestion.models.schemas import (
    WearablePayload, ClinicalEventPayload, CompanyBatchUpload, IngestResponse,
)
from ingestion.normalizer import (
    normalize_wearable, normalize_clinical, normalize_employee,
)
from ingestion.auth.dependencies import get_current_user, require_company_access

router = APIRouter(prefix="/ingest", tags=["ingest"])
_audit = logging.getLogger("aegis.audit")


def _company_exists(db: Session, company_id: str) -> bool:
    result = db.execute(
        text("SELECT 1 FROM companies WHERE company_id = :cid"),
        {"cid": company_id}
    ).first()
    return result is not None


@router.post(
    "/wearable",
    response_model=IngestResponse,
    status_code=201,
    summary="Ingest wearable telemetry for one employee",
    description=(
        "Store a normalized monthly wearable payload for an employee after validating "
        "company access and employee existence."
    ),
)
def ingest_wearable(
    payload: WearablePayload,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_company_access(payload.company_id, user)
    if not _company_exists(db, payload.company_id):
        raise HTTPException(status_code=404, detail=f"Unknown company: {payload.company_id}")

    record = normalize_wearable(payload.model_dump(by_alias=False))

    employee_check = db.execute(
        text("SELECT 1 FROM employees WHERE employee_id = :eid"),
        {"eid": record["employee_id"]}
    ).first()
    if not employee_check:
        raise HTTPException(
            status_code=404,
            detail="Employee not found. Roster must be uploaded to /ingest/company first."
        )

    db.execute(text("""
        INSERT INTO telemetry (employee_id, company_id, month, avg_daily_steps,
                               resting_hr, active_minutes, sleep_hours, spo2)
        VALUES (:employee_id, :company_id, :month, :avg_daily_steps,
                :resting_hr, :active_minutes, :sleep_hours, :spo2)
    """), record)
    db.commit()

    _audit.info(
        "INGEST_WEARABLE user=%s company=%s employee=%s",
        user["sub"], payload.company_id, record["employee_id"],
    )
    return IngestResponse(
        status="success",
        records_received=1,
        records_stored=1,
        anonymized_id=record["employee_id"],
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/clinical",
    response_model=IngestResponse,
    status_code=201,
    summary="Ingest one clinical event",
    description=(
        "Store a normalized clinical or claims event for an existing employee within "
        "the authenticated company scope."
    ),
)
def ingest_clinical(
    payload: ClinicalEventPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_company_access(payload.company_id, user)
    if not _company_exists(db, payload.company_id):
        raise HTTPException(status_code=404, detail=f"Unknown company: {payload.company_id}")

    record = normalize_clinical(payload.model_dump())

    employee_check = db.execute(
        text("SELECT 1 FROM employees WHERE employee_id = :eid"),
        {"eid": record["employee_id"]}
    ).first()
    if not employee_check:
        raise HTTPException(
            status_code=404,
            detail="Employee not found. Upload roster first."
        )

    db.execute(text("""
        INSERT INTO clinical_events
            (event_id, employee_id, company_id, month, event_type,
             icd10_code, claim_amount, hospitalized)
        VALUES (:event_id, :employee_id, :company_id, :month, :event_type,
                :icd10_code, :claim_amount, :hospitalized)
    """), record)
    db.commit()

    _audit.info(
        "INGEST_CLINICAL user=%s company=%s employee=%s event_type=%s",
        user["sub"], payload.company_id, record["employee_id"], payload.event_type,
    )
    return IngestResponse(
        status="success",
        records_received=1,
        records_stored=1,
        anonymized_id=record["employee_id"],
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/company",
    response_model=IngestResponse,
    status_code=201,
    summary="Upload or update a company roster batch",
    description=(
        "Create or update employee roster records for a company. This endpoint is typically "
        "used before wearable or clinical payloads are ingested."
    ),
)
def ingest_company_roster(
    payload: CompanyBatchUpload,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_company_access(payload.company_id, user)
    if not _company_exists(db, payload.company_id):
        raise HTTPException(status_code=404, detail=f"Unknown company: {payload.company_id}")

    errors = []
    stored = 0
    for emp in payload.employees:
        try:
            record = normalize_employee(payload.company_id, emp.model_dump())
            db.execute(text("""
                INSERT INTO employees (employee_id, company_id, age, gender, bmi,
                                       smoker, diabetic, hypertension, job_category)
                VALUES (:employee_id, :company_id, :age, :gender, :bmi,
                        :smoker, :diabetic, :hypertension, :job_category)
                ON CONFLICT (employee_id) DO UPDATE SET
                    age          = EXCLUDED.age,
                    bmi          = EXCLUDED.bmi,
                    smoker       = EXCLUDED.smoker,
                    diabetic     = EXCLUDED.diabetic,
                    hypertension = EXCLUDED.hypertension
            """), record)
            stored += 1
        except Exception as e:
            errors.append(f"row_{stored + len(errors) + 1}: {str(e)[:80]}")

    db.commit()

    _audit.info(
        "INGEST_COMPANY user=%s company=%s stored=%d errors=%d",
        user["sub"], payload.company_id, stored, len(errors),
    )
    return IngestResponse(
        status="success" if stored == len(payload.employees) else "partial",
        records_received=len(payload.employees),
        records_stored=stored,
        errors=errors,
        timestamp=datetime.now(timezone.utc),
    )
