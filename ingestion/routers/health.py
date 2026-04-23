"""Health check endpoints — used by Docker and monitoring tools."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ingestion.database import get_db

router = APIRouter(tags=["health"])
_logger = logging.getLogger(__name__)


@router.get(
    "/health",
    summary="Check service availability",
    description="Lightweight liveness probe for uptime checks, containers, and load balancers.",
)
def health():
    return {"status": "ok", "service": "aegis-ingestion"}


@router.get(
    "/health/db",
    summary="Check database connectivity",
    description="Run a minimal database probe to confirm the service can reach its configured database.",
)
def db_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        _logger.warning("Database health check failed: %s", e)
        return {
            "status": "error",
            "database": "unreachable",
            "detail": "Database connectivity check failed",
        }
