"""Security helpers for authentication and password management."""

from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend_gateway.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

# OAuth2 scheme for token authentication
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

# Optional OAuth2 scheme for endpoints that don't require authentication
class OAuth2PasswordBearerOptional(OAuth2PasswordBearer):
    def __init__(self):
        super().__init__(tokenUrl=f"{settings.API_V1_STR}/login/access-token", auto_error=False)

    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None

oauth2_scheme_optional = OAuth2PasswordBearerOptional()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> dict:
    """Get current user from token"""
    token = credentials.credentials
    
    # Development mode: accept mock token
    if token == "mock-admin-token-for-prototype":
        # Check for DEMO_USER_ID environment variable
        import os
        demo_user_id = os.getenv("DEMO_USER_ID", "samantha-1")
        
        # Map demo user IDs to user data
        demo_users = {
            "samantha-1": {
                "user_id": 1,
                "email": "samantha@prepsense.com",
                "first_name": "Samantha",
                "last_name": "Smith",
                "is_admin": True
            },
            "john-2": {
                "user_id": 2,
                "email": "john@prepsense.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_admin": False
            },
            "jane-3": {
                "user_id": 3,
                "email": "jane@prepsense.com",
                "first_name": "Jane",
                "last_name": "Johnson",
                "is_admin": False
            },
            "bob-4": {
                "user_id": 4,
                "email": "bob@prepsense.com",
                "first_name": "Bob",
                "last_name": "Wilson",
                "is_admin": False
            }
        }
        
        # Return the demo user based on environment variable
        return demo_users.get(demo_user_id, demo_users["samantha-1"])
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_email: str = payload.get("sub")
        user_id: int = payload.get("user_id", 111)  # Default to Samantha's ID
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        return {
            "user_id": user_id,
            "email": user_email,
            "first_name": payload.get("first_name", "User"),
            "last_name": payload.get("last_name", ""),
            "is_admin": payload.get("is_admin", False)
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
