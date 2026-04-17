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


class EmployeePredictionRequest(BaseModel):
    """Features for a single employee prediction."""
    age:          int   = Field(..., ge=18, le=70)
    gender:       Literal["M","F","O"]
    bmi:          float = Field(..., ge=10, le=60)
    smoker:       bool  = False
    diabetic:     bool  = False
    hypertension: bool  = False
    chronic_count:Optional[int]   = None
    avg_daily_steps:   float = Field(..., ge=0, le=30000)
    step_volatility:   float = Field(0, ge=0)
    avg_resting_hr:    float = Field(..., ge=40, le=120)
    hr_trend:          float = 0
    avg_active_mins:   float = Field(30, ge=0, le=240)
    avg_sleep_hours:   float = Field(7.0, ge=3, le=12)
    avg_spo2:          float = Field(97.0, ge=85, le=100)
    visit_count:       int   = Field(0, ge=0)
    hospitalized_count:int   = Field(0, ge=0)


class FeatureDriver(BaseModel):
    feature:    str
    value:      float
    shap_value: float
    direction:  str
    explanation:Optional[str] = None


class EmployeePredictionResponse(BaseModel):
    predicted_loss_ratio: float
    health_risk_score:    float
    risk_band:            str
    top_drivers:          List[FeatureDriver]


class CompanyPredictionResponse(BaseModel):
    company_id:        str
    company_name:      str
    employee_count:    int
    mean_loss_ratio:   float
    mean_hrs:          float
    risk_band:         str
    low_risk_pct:      float
    moderate_risk_pct: float
    high_risk_pct:     float
    critical_risk_pct: float
    top_risk_drivers:  List[dict]


class PremiumRequest(BaseModel):
    base_premium: float = Field(..., gt=0)
    hrs:          float = Field(..., ge=0, le=100)


class PremiumResponse(BaseModel):
    base_premium:      float
    adjusted_premium:  float
    adjustment_pct:    float
    zone:              str
    recommendation:    str


class WellnessROIRequest(BaseModel):
    base_premium:               float = Field(..., gt=0)
    current_hrs:                float = Field(..., ge=0, le=100)
    projected_hrs_after_program:float = Field(..., ge=0, le=100)


class WellnessROIResponse(BaseModel):
    current_premium:   float
    projected_premium: float
    annual_savings:    float
    hrs_improvement:   float
    current_zone:      str
    projected_zone:    str
