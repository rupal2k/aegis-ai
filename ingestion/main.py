"""Aegis AI — Ingestion + Prediction Service entry point."""
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from ingestion.routers import health, ingest, predict, companies, auth_router
from ingestion.rate_limit import (
    limiter,
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

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

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["Server"] = "AegisAI"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Swagger UI loads scripts/styles from CDN — relax CSP for doc routes in dev
    is_doc_path = request.url.path in ("/docs", "/redoc", "/openapi.json")
    if _ENV == "development" and is_doc_path:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data:; "
            "worker-src blob:;"
        )
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        )
    return response

# CORS Configuration - Stricter validation
_ALLOWED_ORIGINS_LIST = _ALLOWED_ORIGINS if _ALLOWED_ORIGINS else ["http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # Cache CORS preflight for 1 hour
)

# Register routers with rate limiting applied
app.include_router(auth_router.router)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(predict.router)
app.include_router(companies.router)


@app.get("/")
def root():
    return {
        "service": "Aegis AI Underwriting Platform",
        "version": "1.1.0",
        "health": "/health",
        "docs": "/docs",
        "endpoints": {
            "auth": ["/auth/token"],
            "ingest": ["/ingest/wearable", "/ingest/clinical", "/ingest/company"],
            "predict": [
                "/predict/employee",
                "/predict/company/{company_id}",
                "/predict/premium",
                "/predict/wellness-roi"
            ],
            "companies": ["/companies", "/companies/{company_id}/employees"]
        }
    }
