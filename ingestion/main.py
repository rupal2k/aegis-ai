"""Aegis AI — Ingestion + Prediction Service entry point."""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routers import health, ingest, predict, companies
from ingestion.routers.auth_router import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

_ENV = os.environ.get("ENV", "production")
_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app = FastAPI(
    title="Aegis AI — Underwriting Platform API",
    description="Tier 1 + Tier 2: secure ingestion + ML-powered predictions.",
    version="1.1.0",
    docs_url="/docs" if _ENV == "development" else None,
    redoc_url="/redoc" if _ENV == "development" else None,
    openapi_url="/openapi.json" if _ENV == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS or ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(predict.router)
app.include_router(companies.router)


@app.get("/")
def root():
    return {
        "service": "Aegis AI Underwriting Platform",
        "health":  "/health",
    }
