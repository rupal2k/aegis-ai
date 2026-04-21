"""POST /auth/token — issue JWT on valid credentials."""
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from ingestion.auth.users import authenticate_user
from ingestion.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
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

    return {"access_token": create_access_token(token_data), "token_type": "bearer"}
