"""POST /auth/token — issue JWT on valid credentials."""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from ingestion.auth.users import authenticate_user
from ingestion.auth.jwt import create_access_token
import logging

router = APIRouter(prefix="/auth", tags=["auth"])
_audit = logging.getLogger("aegis.audit")


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """
    Authenticate user and return JWT token.
    
    Rate limited to 5 requests per minute per IP address.
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
