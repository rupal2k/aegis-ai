"""JWT token creation and verification."""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
import os
import logging

_logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
ALGORITHM = "HS256"  # Note: Consider using RS256 (asymmetric) for production
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Refuse to start with a missing or weak SECRET_KEY — an empty key lets anyone forge tokens.
_ENV = os.environ.get("ENV", "production")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if _ENV == "production":
        raise RuntimeError(
            "SECRET_KEY must be set to a random string of at least 32 characters. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    _logger.warning("SECRET_KEY missing or weak — acceptable in development only.")


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with expiration.
    
    Args:
        data: Dictionary containing token claims
        
    Returns:
        Encoded JWT token string
    """
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload["iat"] = datetime.now(timezone.utc)  # Issued at time
    
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    except Exception as e:
        _logger.error(f"Error creating token: {e}")
        raise


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Verify required claims
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing 'sub' claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as e:
        _logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

