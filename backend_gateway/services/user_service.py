"""Handles user persistence in BigQuery and related lookups."""

from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from ..models.user import UserCreate, UserInDB, UserResponse
from ..core.config import settings

class UserService:
    def __init__(self, bq_client=None):
        self.bq_client = bq_client or bigquery.Client()
        self.table_id = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.users"
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the users table exists in BigQuery"""
        query = f"""
        CREATE TABLE IF NOT EXISTS `{self.table_id}` (
            id STRING NOT NULL,
            email STRING NOT NULL,
            first_name STRING NOT NULL,
            last_name STRING NOT NULL,
            password_hash STRING NOT NULL,
            is_admin BOOL NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """
        self.bq_client.query(query).result()
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        """Create a new user in BigQuery"""
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # In a real app, you'd hash the password here
        password_hash = user.password  # TODO: Hash the password
        
        query = f"""
        INSERT INTO `{self.table_id}` 
        (id, email, first_name, last_name, password_hash, is_admin, created_at, updated_at)
        VALUES (@user_id, @email, @first_name, @last_name, @password_hash, @is_admin, @created_at, @updated_at)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("email", "STRING", user.email),
                bigquery.ScalarQueryParameter("first_name", "STRING", user.first_name),
                bigquery.ScalarQueryParameter("last_name", "STRING", user.last_name),
                bigquery.ScalarQueryParameter("password_hash", "STRING", password_hash),
                bigquery.ScalarQueryParameter("is_admin", "BOOL", user.is_admin),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", now),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
            ]
        )
        
        self.bq_client.query(query, job_config=job_config).result()
        
        # Return the created user
        return UserInDB(
            id=user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            created_at=now,
            updated_at=now
        )
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get a user by email"""
        query = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{self.table_id}`
        WHERE email = @email
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email),
            ]
        )
        
        query_job = self.bq_client.query(query, job_config=job_config)
        row = next(iter(query_job.result()), None)
        
        if not row:
            return None
            
        return UserInDB(
            id=row.id,
            email=row.email,
            first_name=row.first_name,
            last_name=row.last_name,
            is_admin=row.is_admin,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """Get all users with pagination"""
        query = f"""
            SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
            FROM `{self.table_id}`
            ORDER BY created_at DESC
            LIMIT @limit
            OFFSET @offset
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
                bigquery.ScalarQueryParameter("offset", "INT64", skip)
            ]
        )
        
        query_job = self.bq_client.query(query, job_config=job_config)
        rows = query_job.result()
        
        users = []
        for row in rows:
            users.append(UserInDB(
                id=row.id,
                email=row.email,
                first_name=row.first_name,
                last_name=row.last_name,
                is_admin=row.is_admin,
                created_at=row.created_at,
                updated_at=row.updated_at
            ))
        return users
        
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get a user by ID from BigQuery"""
        query = f"""
            SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
            FROM `{self.table_id}`
            WHERE id = @user_id
            LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        query_job = self.bq_client.query(query, job_config=job_config)
        result = query_job.result()
        
        for row in result:
            return UserInDB(
                id=row.id,
                email=row.email,
                first_name=row.first_name,
                last_name=row.last_name,
                is_admin=row.is_admin,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        return None
    
    async def create_default_user(self):
        """Create Samantha Smith as a default user if not exists"""
        default_email = "samantha.smith@example.com"
        existing_user = await self.get_user_by_email(default_email)
        
        if not existing_user:
            user_data = UserCreate(
                email=default_email,
                first_name="Samantha",
                last_name="Smith",
                password="defaultpassword",  # In a real app, use a secure password
                is_admin=True
            )
            return await self.create_user(user_data)
        return existing_user
