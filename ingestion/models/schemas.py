"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from datetime import datetime


class WearablePayload(BaseModel):
    """Raw payload from Apple HealthKit / Google Fit style sources."""
    external_employee_id: str = Field(..., description="Raw ID from source system, will be hashed")
    company_id:           str = Field(..., pattern=r"^COMP_\d{3}$")
    month:                int = Field(..., ge=1, le=12)

    daily_steps:      Optional[int]   = Field(None, alias="steps")
    heart_rate_rest:  Optional[int]   = Field(None, alias="restingHR")
    active_mins:      Optional[int]   = Field(None, alias="activeMinutes")
    sleep_hrs:        Optional[float] = Field(None, alias="sleepHours")
    oxygen_saturation:Optional[float] = Field(None, alias="SpO2")

    model_config = {"populate_by_name": True}

    @field_validator("daily_steps")
    @classmethod
    def steps_sanity(cls, v):
        if v is not None and (v < 0 or v > 100_000):
            raise ValueError(f"Step count out of sensor range: {v}")
        return v

    @field_validator("heart_rate_rest")
    @classmethod
    def hr_sanity(cls, v):
        if v is not None and (v < 30 or v > 220):
            raise ValueError(f"Heart rate out of physiological range: {v}")
        return v


class ClinicalEventPayload(BaseModel):
    """Raw clinical event from EHR system."""
    external_employee_id: str
    company_id:   str = Field(..., pattern=r"^COMP_\d{3}$")
    event_type:   Literal["general_visit","hypertension","diabetes",
                          "respiratory","injury","cardiac"]
    icd10_code:   str = Field(..., max_length=10)
    claim_amount: float = Field(..., ge=0, le=5_000_000)
    month:        int   = Field(..., ge=1, le=12)
    hospitalized: bool  = False


class EmployeeRecord(BaseModel):
    external_employee_id: str
    age:          int   = Field(..., ge=18, le=70)
    gender:       Literal["M","F","O"]
    bmi:          float = Field(..., ge=10, le=60)
    smoker:       bool  = False
    diabetic:     bool  = False
    hypertension: bool  = False
    job_category: Literal["desk","field","manual"]


class CompanyBatchUpload(BaseModel):
    """Bulk employee roster upload from HR systems."""
    company_id: str = Field(..., pattern=r"^COMP_\d{3}$")
    employees:  List[EmployeeRecord] = Field(..., min_length=1, max_length=1000)


class IngestResponse(BaseModel):
    status:          Literal["success","partial","failed"]
    records_received:int
    records_stored:  int
    anonymized_id:   Optional[str] = None
    errors:          List[str] = []
    timestamp:       datetime
