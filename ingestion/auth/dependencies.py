"""FastAPI auth dependencies — inject into route handlers."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ingestion.auth.jwt import decode_token
from ingestion.auth.token_blacklist import is_token_revoked

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current user from token, checking if token is revoked."""
    # Check if token is revoked
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token)


def require_underwriter(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "underwriter":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Underwriter access required")
    return user


def require_company_access(company_id: str, user: dict = Depends(get_current_user)) -> dict:
    """Underwriters see all companies; HR admins only see their own."""
    if user.get("role") == "underwriter":
        return user
    if user.get("role") == "hr_admin" and user.get("company_id") == company_id:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this company")
