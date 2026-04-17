"""Aegis AI — Ingestion Service entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routers import health, ingest

app = FastAPI(
    title="Aegis AI — Ingestion API",
    description="Tier 1: secure data ingestion for wearable, clinical, and HR sources.",
    version="1.0.0",
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


@app.get("/")
def root():
    return {
        "service": "Aegis AI Ingestion Layer",
        "docs":    "/docs",
        "health":  "/health",
    }
