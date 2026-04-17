"""Aegis AI — Ingestion + Prediction Service entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routers import health, ingest, predict

app = FastAPI(
    title="Aegis AI — Underwriting Platform API",
    description="Tier 1 + Tier 2: secure ingestion + ML-powered predictions.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(predict.router)


@app.get("/")
def root():
    return {
        "service": "Aegis AI Underwriting Platform",
        "docs":    "/docs",
        "health":  "/health",
        "endpoints": {
            "ingest":  ["/ingest/wearable", "/ingest/clinical", "/ingest/company"],
            "predict": [
                "/predict/employee",
                "/predict/company/{company_id}",
                "/predict/premium",
                "/predict/wellness-roi",
            ],
        },
    }
