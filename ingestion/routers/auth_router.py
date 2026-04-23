"""POST /auth/token — issue JWT on valid credentials."""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from ingestion.auth.users import authenticate_user
from ingestion.auth.jwt import create_access_token
from ingestion.rate_limit import limiter
import logging

router = APIRouter(prefix="/auth", tags=["auth"])
_audit = logging.getLogger("aegis.audit")


@router.post(
    "/token",
    summary="Exchange credentials for a bearer token",
    description=(
        "Authenticate a dashboard or API user and return a JWT bearer token. "
        "Send the token in `Authorization: Bearer <token>` for all protected routes."
    ),
)
@limiter.limit("5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a signed JWT access token.

    Requests are rate limited to five attempts per minute per client IP.
    """
    # Log authentication attempt (without password)
    client_ip = request.client.host if request else "unknown"
    _audit.info(f"AUTH_ATTEMPT user={form.username} ip={client_ip}")
    
    user = authenticate_user(form.username, form.password)
    if not user:
        _audit.warning(f"AUTH_FAILED user={form.username} ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = {
        "sub":        user["email"],
        "role":       user["role"],
        "name":       user["name"],
        "org":        user["org"],
    }
    if user.get("company_id"):
        token_data["company_id"] = user["company_id"]

    token = create_access_token(token_data)
    _audit.info(f"AUTH_SUCCESS user={user['email']} role={user['role']} ip={client_ip}")
    
    return {"access_token": token, "token_type": "bearer"}
