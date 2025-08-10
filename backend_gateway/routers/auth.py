"""Authentication and token endpoints."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm

from backend_gateway.core.config import settings
from backend_gateway.core.security import create_access_token, get_current_user
from backend_gateway.models.user import UserInDB
from backend_gateway.services.user_service import UserService

# OAuth2 scheme
oauth2_scheme = HTTPBearer()

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["auth"])


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), user_service: UserService = Depends()
):
    """OAuth2 compatible token login, get an access token for future requests"""
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserInDB)
async def read_current_user(current_user: UserInDB = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user
