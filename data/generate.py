import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path
import hashlib
import os

fake = Faker("en_IN")
np.random.seed(42)
Faker.seed(42)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

N_COMPANIES = 20
N_EMPLOYEES = 5000
MONTHS = 12

COMPANY_NAMES = [
    "TechNova Solutions", "Bharat Steel Works", "QuickServe Retail",
    "MediPlus Hospitals", "GreenField Agriculture", "UrbanLogix Transport",
    "DataSpark Analytics", "ClearView Finance", "BuildRight Construction",
    "EduNext Learning", "SafeNet Insurance", "PrimeFood Industries",
    "CloudBridge IT", "SwiftBank Services", "AeroTech Manufacturing",
    "RetailMax Group", "Pinnacle Pharma", "HorizonEnergy", "MegaMart",
    "GlobalConnect BPO",
]

INDUSTRIES = [
    "IT/Software", "Manufacturing", "Retail", "Healthcare", "Agriculture",
    "Logistics", "Analytics", "Finance", "Construction", "Education",
    "Insurance", "Food Processing", "IT/Software", "Banking", "Manufacturing",
    "Retail", "Pharma", "Energy", "Retail", "BPO",
]


def anonymize_id(raw_id: str) -> str:
    salt = os.environ.get("HASH_SALT", "aegis_dev_salt_2024")
    return hashlib.sha256(f"{salt}{raw_id}".encode()).hexdigest()[:16]


def clamp(value, low, high):
    return max(low, min(high, value))


def generate_companies() -> pd.DataFrame:
    companies = []
    risk_map = {
        "Manufacturing": 0.70, "Construction": 0.75, "BPO": 0.65,
        "Logistics": 0.60, "Retail": 0.55, "Food Processing": 0.60,
        "Healthcare": 0.40, "IT/Software": 0.30, "Analytics": 0.28,
        "Finance": 0.35, "Banking": 0.38, "Insurance": 0.35,
        "Education": 0.42, "Agriculture": 0.50, "Pharma": 0.38,
        "Energy": 0.55,
    }
    for i, (name, industry) in enumerate(zip(COMPANY_NAMES, INDUSTRIES)):
        base_risk = risk_map.get(industry, 0.50)
        companies.append({
            "company_id":     f"COMP_{i+1:03d}",
            "company_name":   name,
            "industry":       industry,
            "city":           fake.city(),
            "employee_count": np.random.randint(80, 600),
            "risk_profile":   clamp(base_risk + np.random.normal(0, 0.07), 0.1, 0.95),
            "base_premium":   int(np.random.randint(4000, 12000)) * 100,
        })
    return pd.DataFrame(companies)


def generate_employees(companies: pd.DataFrame) -> pd.DataFrame:
    employees = []
    weights = companies["employee_count"] / companies["employee_count"].sum()
    counts = (weights * N_EMPLOYEES).round().astype(int)
    counts.iloc[-1] += N_EMPLOYEES - counts.sum()

    emp_id = 1
    for _, company in companies.iterrows():
        n = counts[company.name]
        rp = company["risk_profile"]

        for _ in range(n):
            age = int(clamp(np.random.normal(35 + rp * 10, 8), 22, 62))
            bmi = round(clamp(np.random.normal(22 + rp * 8, 3.5), 16.0, 42.0), 1)
            smoker = np.random.random() < (0.05 + rp * 0.35)
            diabetic = np.random.random() < (0.03 + rp * 0.25 + (0.05 if age > 45 else 0))
            hypertension = np.random.random() < (0.04 + rp * 0.30 + (0.06 if bmi > 28 else 0))

            employees.append({
                "employee_id":  anonymize_id(f"EMP_{emp_id:05d}"),
                "company_id":   company["company_id"],
                "age":          age,
                "gender":       np.random.choice(["M", "F"], p=[0.54, 0.46]),
                "bmi":          bmi,
                "smoker":       int(smoker),
                "diabetic":     int(diabetic),
                "hypertension": int(hypertension),
                "job_category": np.random.choice(
                    ["desk", "field", "manual"], p=[0.4, 0.35, 0.25]
                ),
            })
            emp_id += 1

    return pd.DataFrame(employees)


def generate_telemetry(employees: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    comp_lookup = companies.set_index("company_id")["risk_profile"].to_dict()
    records = []

    for _, emp in employees.iterrows():
        rp = comp_lookup[emp["company_id"]]
        fitness = clamp(1.0 - (rp * 0.5 + emp["bmi"] / 80 + emp["smoker"] * 0.1), 0.1, 1.0)

        for month in range(1, MONTHS + 1):
            seasonal = 1.0 - 0.12 * np.cos(2 * np.pi * month / 12)

            records.append({
                "employee_id":     emp["employee_id"],
                "company_id":      emp["company_id"],
                "month":           month,
                "avg_daily_steps": int(clamp(np.random.normal(4000 + fitness * 5000 * seasonal, 800), 500, 18000)),
                "resting_hr":      int(clamp(np.random.normal(58 + (1 - fitness) * 25 + emp["smoker"] * 5, 4), 45, 105)),
                "active_minutes":  int(clamp(np.random.normal(0, 5) + (4000 + fitness * 5000 * seasonal) / 120, 0, 120)),
                "sleep_hours":     round(clamp(np.random.normal(7.0 - (1 - fitness) * 1.5, 0.6), 4.0, 9.5), 1),
                "spo2":            round(clamp(np.random.normal(97.5 - emp["smoker"] * 1.2 - (1 - fitness) * 0.8, 0.5), 90.0, 100.0), 1),
            })

    return pd.DataFrame(records)


def generate_clinical_events(employees: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    comp_lookup = companies.set_index("company_id")["risk_profile"].to_dict()
    ICD10 = {
        "general_visit": ["Z00.00", "Z00.01"],
        "hypertension":  ["I10", "I11.9"],
        "diabetes":      ["E11.9", "E11.65"],
        "respiratory":   ["J06.9", "J45.909"],
        "injury":        ["S09.90XA", "M54.5"],
    }
    COSTS = {
        "general_visit": (800,  2500),
        "hypertension":  (2000, 8000),
        "diabetes":      (3000, 12000),
        "respiratory":   (1500, 6000),
        "injury":        (5000, 25000),
    }
    events = []
    event_id = 1

    for _, emp in employees.iterrows():
        rp = comp_lookup[emp["company_id"]]
        base_visits = int(np.random.poisson(
            1.5 + rp * 3 + emp["diabetic"] * 3 + emp["hypertension"] * 2
        ))

        for _ in range(base_visits):
            if emp["diabetic"] and np.random.random() < 0.4:
                etype = "diabetes"
            elif emp["hypertension"] and np.random.random() < 0.35:
                etype = "hypertension"
            elif emp["smoker"] and np.random.random() < 0.25:
                etype = "respiratory"
            elif rp > 0.6 and np.random.random() < 0.15:
                etype = "injury"
            else:
                etype = "general_visit"

            lo, hi = COSTS[etype]
            claim = round(float(np.random.uniform(lo, hi)), 2)

            events.append({
                "event_id":     f"EVT_{event_id:07d}",
                "employee_id":  emp["employee_id"],
                "company_id":   emp["company_id"],
                "month":        np.random.randint(1, 13),
                "event_type":   etype,
                "icd10_code":   np.random.choice(ICD10[etype]),
                "claim_amount": claim,
                "hospitalized": int(claim > 15000),
            })
            event_id += 1

    return pd.DataFrame(events)


def build_training_dataset(employees, telemetry, clinical, companies):
    tele_agg = telemetry.groupby("employee_id").agg(
        avg_daily_steps=("avg_daily_steps", "mean"),
        step_volatility=("avg_daily_steps", "std"),
        avg_resting_hr =("resting_hr",      "mean"),
        hr_trend       =("resting_hr",      lambda x: np.polyfit(range(len(x)), x, 1)[0]),
        avg_active_mins=("active_minutes",  "mean"),
        avg_sleep_hours=("sleep_hours",     "mean"),
        avg_spo2       =("spo2",            "mean"),
    ).reset_index()

    clin_agg = clinical.groupby("employee_id").agg(
        total_claims      =("claim_amount", "sum"),
        visit_count       =("event_id",     "count"),
        hospitalized_count=("hospitalized", "sum"),
    ).reset_index()

    df = employees.merge(tele_agg, on="employee_id", how="left")
    df = df.merge(clin_agg,  on="employee_id", how="left")

    df["total_claims"]       = df["total_claims"].fillna(0)
    df["visit_count"]        = df["visit_count"].fillna(0)
    df["hospitalized_count"] = df["hospitalized_count"].fillna(0)
    df["step_volatility"]    = df["step_volatility"].fillna(0)
    df["hr_trend"]           = df["hr_trend"].fillna(0)

    comp_premium = companies.set_index("company_id")["base_premium"]
    df["company_base_premium"] = df["company_id"].map(comp_premium)

    emp_counts = employees.groupby("company_id").size().rename("emp_count")
    df = df.merge(emp_counts, on="company_id")
    df["premium_share"] = df["company_base_premium"] / df["emp_count"]

    df["loss_ratio"]  = (df["total_claims"] / df["premium_share"]).round(4)
    df["high_risk"]   = (df["loss_ratio"] > 1.2).astype(int)
    df["chronic_count"] = df["diabetic"] + df["hypertension"]

    df.drop(columns=["company_base_premium", "emp_count"], inplace=True)
    return df


if __name__ == "__main__":
    print("Generating companies...")
    companies = generate_companies()
    companies.to_csv(OUTPUT_DIR / "companies.csv", index=False)
    print(f"  {len(companies)} companies")

    print("Generating employees...")
    employees = generate_employees(companies)
    employees.to_csv(OUTPUT_DIR / "employees.csv", index=False)
    print(f"  {len(employees)} employees")

    print("Generating telemetry (may take ~30 seconds)...")
    telemetry = generate_telemetry(employees, companies)
    telemetry.to_csv(OUTPUT_DIR / "telemetry.csv", index=False)
    print(f"  {len(telemetry):,} telemetry records")

    print("Generating clinical events...")
    clinical = generate_clinical_events(employees, companies)
    clinical.to_csv(OUTPUT_DIR / "clinical_events.csv", index=False)
    print(f"  {len(clinical):,} clinical events")

    print("Building ML training dataset...")
    training = build_training_dataset(employees, telemetry, clinical, companies)
    training.to_csv(OUTPUT_DIR / "training_dataset.csv", index=False)
    print(f"  {len(training):,} rows, {len(training.columns)} features")

    print("\n--- Sanity Check ---")
    print(f"Loss ratio range : {training['loss_ratio'].min():.3f} - {training['loss_ratio'].max():.3f}")
    print(f"Mean loss ratio  : {training['loss_ratio'].mean():.3f}")
    print(f"High-risk pct    : {training['high_risk'].mean()*100:.1f}%")
    print(f"Avg daily steps  : {training['avg_daily_steps'].mean():.0f}")
    print(f"Avg resting HR   : {training['avg_resting_hr'].mean():.1f} bpm")
    print(f"Diabetic pct     : {training['diabetic'].mean()*100:.1f}%")
    print("\nAll files saved to data/output/")