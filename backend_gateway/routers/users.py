import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Optional, List, Dict
from datetime import timedelta, datetime, timezone
import jwt
import uuid
import logging

from ..models.user import UserCreate, UserInDB, UserResponse, UserProfileResponse, UserProfilePreference
from ..services.bigquery_service import BigQueryService
from ..services.recipe_service import RecipeService
from ..services.user_service import UserService
from ..core.security import create_access_token, reusable_oauth2, get_password_hash, verify_password, oauth2_scheme_optional
from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize BigQuery service
def get_bigquery_service():
    return BigQueryService(
        project_id=settings.BIGQUERY_PROJECT,
        dataset_id=settings.BIGQUERY_DATASET,
        credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )

# Dependency to get UserService instance
def get_user_service():
    # UserService now handles its own BigQuery client initialization
    return UserService()

# OAuth2 scheme
oauth2_scheme = HTTPBearer()

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
USERS_TABLE = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.users"
USER_PREFS_TABLE = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.user_preference"

router = APIRouter()

# Helper functions
async def get_user_by_email(email: str, bq: BigQueryService) -> Optional[UserInDB]:
    """Get a user by email from BigQuery"""
    query = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{USERS_TABLE}`
        WHERE email = @email
        LIMIT 1
    """
    params = [{"name": "email", "type": "STRING", "value": email}]
    rows = bq.execute_query(query, params)
    
    if not rows:
        return None
    
    row = rows[0]
    return UserInDB(
        id=row['id'],
        email=row['email'],
        first_name=row['first_name'],
        last_name=row['last_name'],
        is_admin=row['is_admin'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

async def get_user_by_id(user_id: str, bq: BigQueryService) -> Optional[UserInDB]:
    """Get a user by ID from BigQuery"""
    query = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{USERS_TABLE}`
        WHERE id = @user_id
        LIMIT 1
    """
    params = [{"name": "user_id", "type": "STRING", "value": user_id}]
    rows = bq.execute_query(query, params)
    
    if not rows:
        return None
    
    row = rows[0]
    return UserInDB(
        id=row['id'],
        email=row['email'],
        first_name=row['first_name'],
        last_name=row['last_name'],
        is_admin=row['is_admin'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

async def create_user(user: UserCreate, bq: BigQueryService) -> UserInDB:
    """Create a new user in BigQuery"""
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    query = f"""
        INSERT INTO `{USERS_TABLE}` 
        (id, email, first_name, last_name, password_hash, is_admin, created_at, updated_at)
        VALUES (@user_id, @email, @first_name, @last_name, @password_hash, @is_admin, @created_at, @updated_at)
    """
    params = [
        {"name": "user_id", "type": "STRING", "value": user_id},
        {"name": "email", "type": "STRING", "value": user.email},
        {"name": "first_name", "type": "STRING", "value": user.first_name},
        {"name": "last_name", "type": "STRING", "value": user.last_name},
        {"name": "password_hash", "type": "STRING", "value": hashed_password},
        {"name": "is_admin", "type": "BOOL", "value": user.is_admin or False},
        {"name": "created_at", "type": "TIMESTAMP", "value": now},
        {"name": "updated_at", "type": "TIMESTAMP", "value": now}
    ]
    
    bq.execute_query(query, params)
    
    return UserInDB(
        id=user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.is_admin or False,
        created_at=now,
        updated_at=now
    )

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def read_user_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get a specific user's full profile. Authentication removed for prototype."""

    logger.info(f"Read_user_profile (No Auth): Request for user_id: {user_id}")

    profile_data = await user_service.get_user_profile_by_id(user_id)
    
    if profile_data is None:
        logger.error(f"Read_user_profile (No Auth): Profile data not found for user_id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile not found for ID: {user_id}"
        )
    
    logger.info(f"Read_user_profile (No Auth): Successfully fetched profile for user_id: {user_id}, email: {profile_data.email}")
    return profile_data

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """OAuth2 compatible token login, get an access token for future requests"""
    # Get user by email
    user = await user_service.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dependencies
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme_optional),
    user_service: UserService = Depends(get_user_service)
) -> Optional[UserInDB]:
    if credentials is None:
        logger.info("Get_current_user: No token provided.")
        return None

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (token invalid or expired)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Get_current_user: Token payload missing email (sub).")
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        logger.warning("Get_current_user: Token has expired.")
        raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"Get_current_user: Token validation error: {e}")
        raise credentials_exception
    
    user = await user_service.get_user_by_email(email=email)
    if user is None:
        logger.warning(f"Get_current_user: User not found for email from token: {email}")
        raise credentials_exception
    return user

# If get_current_active_user was used by other endpoints and relied on get_current_user,
# it would also be affected. For simplicity, if it's only for profile, it can be removed or adapted.
async def get_current_active_user(
    current_user: Optional[UserInDB] = Depends(get_current_user),
) -> Optional[UserInDB]:
    if current_user is None and os.getenv("REQUIRE_AUTH", "true").lower() == "true":
        pass
    return current_user

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user. This endpoint implies authentication."""
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user

@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0, 
    limit: int = 100,
    bq: BigQueryService = Depends(get_bigquery_service),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    query = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{USERS_TABLE}`
        ORDER BY created_at DESC
        LIMIT @limit
        OFFSET @offset
    """
    params = [
        {"name": "limit", "type": "INT64", "value": limit},
        {"name": "offset", "type": "INT64", "value": skip}
    ]
    
    rows = bq.execute_query(query, params)
    users = [
        UserInDB(
            id=row['id'],
            email=row['email'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            is_admin=row['is_admin'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        for row in rows
    ]
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str, 
    bq: BigQueryService = Depends(get_bigquery_service),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific user by ID"""
    # Non-admin users can only view their own profile
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user"
        )
        
    user = await get_user_by_id(user_id, bq)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
