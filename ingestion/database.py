"""SQLAlchemy database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

# Engine and session are created lazily so uvicorn can bind its port even
# if DATABASE_URL is missing — the error surfaces on the first DB request.
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,          # recycle connections every 5 min before Render drops them
    pool_pre_ping=False,       # startup warmup handles connection validity; skip per-request ping
    connect_args={"connect_timeout": 10},
) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session per request, closes after."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not configured — service is not ready."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
