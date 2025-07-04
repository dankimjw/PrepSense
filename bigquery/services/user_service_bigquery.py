import logging
import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

from backend_gateway.models.user import UserCreate, UserInDB, UserResponse, UserProfilePreference, UserProfileResponse
from backend_gateway.core.config import settings
from backend_gateway.config.database import get_database_service

# Load environment variables early
load_dotenv()

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db_service=None):
        if db_service:
            self.db_service = db_service
        else:
            self.db_service = get_database_service()
        
        self.users_table = "users"
        self.profile_table = "user_preference"
        logger.info("UserService initialized with database service")
    
    def _ensure_table_exists(self):
        """Ensure the users (credentials) table exists in BigQuery"""
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

    def _ensure_profile_table_exists(self):
        """Ensure the user (profile details) table exists in BigQuery"""
        query = f"""
        CREATE TABLE IF NOT EXISTS `{self.profile_table_id}` (
            user_id INT64 NOT NULL,
            user_name STRING,
            first_name STRING,
            last_name STRING,
            email STRING,
            password_hash STRING,
            role STRING,
            api_key_enc STRING,
            created_at TIMESTAMP
        )
        OPTIONS (
            description="Stores detailed user profile information."
        );
        """
        try:
            logger.info(f"Ensuring profile table '{self.profile_table_id}' exists...")
            self.bq_client.query(query).result()
            logger.info(f"Profile table '{self.profile_table_id}' ensured.")
        except Exception as e:
            logger.error(f"Failed to ensure profile table '{self.profile_table_id}': {e}", exc_info=True)
            raise

    def _ensure_user_preference_table_exists(self):
        """Ensure the user_preference table exists in BigQuery"""
        # Note: BigQuery doesn't enforce foreign keys in DDL like traditional SQL databases.
        # The FOREIGN KEY (user_id) REFERENCES ... is a logical representation.
        query = f"""
        CREATE TABLE IF NOT EXISTS `{self.user_preferences_table_id}` (
            user_id STRING NOT NULL,
            household_size INT64,
            dietary_preference STRING,
            allergens ARRAY<STRING>,
            cuisine_preference STRING,
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
        """Get a user by email, including their numeric_user_id."""
        # Step 1: Get basic user info from 'users' (plural) table (credentials table)
        query_users_table = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{self.table_id}` # self.table_id is ...project.dataset.users
        WHERE email = @email
        LIMIT 1
        """
        job_config_users = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )
        query_job_users = self.bq_client.query(query_users_table, job_config=job_config_users)
        user_row = next(iter(query_job_users.result()), None)

        if not user_row:
            return None

        # Special case: If this is Samantha's email, set numeric_user_id to 111
        if email.lower() == 'samantha.smith@example.com':  # Adjust email as needed
            numeric_user_id_val = 111
        else:
            # Step 2: For other users, get numeric user_id from 'user' (singular) table
            user_profile_table_id = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.user"
            
            query_user_profile_table = f"""
            SELECT user_id
            FROM `{user_profile_table_id}`
            WHERE email = @email
            LIMIT 1
            """
            job_config_profile = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
            )
            query_job_profile = self.bq_client.query(query_user_profile_table, job_config=job_config_profile)
            profile_row = next(iter(query_job_profile.result()), None)

            if profile_row and hasattr(profile_row, 'user_id') and profile_row.user_id is not None:
                try:
                    numeric_user_id_val = int(profile_row.user_id)
                except ValueError:
                    logger.error(f"Could not convert user_id '{profile_row.user_id}' to int for email {email}")
                    raise ValueError(f"Invalid user_id for email {email}")
            else:
                raise ValueError(f"No numeric user_id found for email {email}")

        return UserInDB(
            id=user_row.id, # String ID
            email=user_row.email,
            first_name=user_row.first_name,
            last_name=user_row.last_name,
            is_admin=user_row.is_admin,
            created_at=user_row.created_at,
            updated_at=user_row.updated_at,
            numeric_user_id=numeric_user_id_val # Populate the new field
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get a user by ID, including their numeric_user_id."""
        # Step 1: Get basic user info from 'users' (plural) table (credentials table)
        query_users_table = f"""
        SELECT id, email, first_name, last_name, is_admin, created_at, updated_at
        FROM `{self.table_id}`
        WHERE id = @user_id
        LIMIT 1
        """
        job_config_users = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
        )
        query_job_users = self.bq_client.query(query_users_table, job_config=job_config_users)
        user_row = next(iter(query_job_users.result()), None)

        if not user_row:
            return None

        # Special case: If this is Samantha's ID, set numeric_user_id to 111
        if user_id.lower() == 'samantha-smith-001':  # Adjust the ID as needed
            numeric_user_id_val = 111
        else:
            # Step 2: For other users, get numeric user_id from 'user' (singular) table
            user_profile_table_id = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.user"
            
            query_user_profile_table = f"""
            SELECT user_id
            FROM `{user_profile_table_id}`
            WHERE email = @email
            LIMIT 1
            """
            job_config_profile = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", user_row.email)]
            )
            query_job_profile = self.bq_client.query(query_user_profile_table, job_config=job_config_profile)
            profile_row = next(iter(query_job_profile.result()), None)

            if profile_row and hasattr(profile_row, 'user_id') and profile_row.user_id is not None:
                try:
                    numeric_user_id_val = int(profile_row.user_id)
                except ValueError:
                    logger.error(f"Could not convert user_id '{profile_row.user_id}' to int for user {user_id}")
                    raise ValueError(f"Invalid user_id for user {user_id}")
            else:
                raise ValueError(f"No numeric user_id found for user {user_id}")

        return UserInDB(
            id=user_row.id, # String ID
            email=user_row.email,
            first_name=user_row.first_name,
            last_name=user_row.last_name,
            is_admin=user_row.is_admin,
            created_at=user_row.created_at,
            updated_at=user_row.updated_at,
            numeric_user_id=numeric_user_id_val
        )

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """Get all users with pagination. Note: This version does NOT populate numeric_user_id for list items to keep focused."""
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

    async def get_user_profile_by_id(self, user_id_input: str) -> Optional[UserProfileResponse]:
        """Get a user's full profile including preferences by ID from BigQuery."""
        try:
            numeric_user_id: Optional[int] = None

            if user_id_input.lower() == 'samantha-smith-001':
                numeric_user_id = 111
                logger.info(f"Resolved '{user_id_input}' to numeric_user_id: {numeric_user_id}")
            elif user_id_input.isdigit():
                numeric_user_id = int(user_id_input)
                logger.info(f"Using provided numeric_user_id: {numeric_user_id}")
            else:
                # If it's not "samantha-smith-001" and not a digit, it's an unsupported format for direct profile lookup.
                # We might need to look up in the 'users' table if a string ID (like UUID) from authUser is passed.
                # For now, let's assume the frontend sends either "samantha-smith-001" or a numeric ID if directly known.
                logger.warning(f"Received non-numeric and non-samantha ID: {user_id_input}. Attempting lookup in 'users' table.")
                # This part handles if authUser.id (a string UUID) is passed from frontend
                # We need to find the associated numeric_user_id from the 'users' table (which should now store it)
                # or from the 'user' table by matching email if we assume email is unique and present in both.
                # This logic will need to be robust. For now, if not samantha or numeric, we can't directly query profile table.
                
                # Let's try to find the user by the string ID in the 'users' table first.
                # This assumes the 'users' table has an 'id' (string UUID) and also a 'numeric_user_id' column 
                # that links to the 'user' (profile) table's 'user_id'.
                # This requires schema modification for 'users' table if not already done.
                
                # Simplified: if we are here, it implies an ID like a UUID was passed.
                # We should have a mapping or a way to get from UUID to numeric_user_id.
                # For now, we'll log an error if we can't resolve it to 111 or a direct numeric ID.
                logger.error(f"Cannot resolve ID '{user_id_input}' to a numeric ID for profile lookup.")
                return None

            if numeric_user_id is None:
                 logger.error(f"Could not determine numeric_user_id for input: {user_id_input}")
                 return None

            logger.info(f"Fetching profile for numeric_user_id: {numeric_user_id}")
            query = f"""
            SELECT
                u.user_id, u.user_name, u.first_name, u.last_name, u.email, u.password_hash, 
                u.role, u.api_key_enc, u.created_at AS user_created_at,
                up.household_size, up.dietary_preference,
                up.allergens, up.cuisine_preference, up.created_at AS preference_created_at
            FROM
                `{self.profile_table_id}` AS u
            LEFT JOIN
                `{self.user_preferences_table_id}` AS up
            ON
                u.user_id = up.user_id # Assuming up.user_id is also INT64
            WHERE u.user_id = @numeric_user_id
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("numeric_user_id", "INT64", numeric_user_id)
                ]
            )
            query_job = self.bq_client.query(query, job_config=job_config)
            row = next(iter(query_job.result()), None)

            if not row:
                logger.error(f"No profile data found for numeric_user_id: {numeric_user_id}")
                return None

            logger.info(f"Successfully retrieved profile data for numeric_user_id: {numeric_user_id}")
            
            user_prefs_model = None
            if row.preference_created_at is not None: # Check if preference data exists
                preference_data = {
                    "household_size": row.household_size,
                    "dietary_preference": row.dietary_preference,
                    "allergens": list(row.allergens) if row.allergens is not None else [],
                    "cuisine_preference": row.cuisine_preference,
                    "preference_created_at": row.preference_created_at
                }
                user_prefs_model = UserProfilePreference(**preference_data)

            profile_response_data = {
                "id": str(row.user_id), # This should be the numeric ID as a string
                "user_name": row.user_name,
                "email": row.email,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "is_admin": row.role.lower() == "admin" if row.role else False,
                "password_hash": row.password_hash,
                "user_created_at": row.user_created_at.isoformat() if row.user_created_at else None,
                "user_updated_at": row.user_created_at.isoformat() if row.user_created_at else None, # Using created_at as no updated_at in schema
                "role": row.role,
                "api_key_enc": row.api_key_enc,
                "preferences": user_prefs_model
            }
            return UserProfileResponse(**profile_response_data)
        
        except Exception as e:
            logger.error(f"Error fetching user profile for input {user_id_input}: {str(e)}", exc_info=True)
            # Consider re-raising a more specific custom exception or returning None
            # For now, re-raising the generic exception to ensure visibility of failure
            raise # Re-raise the caught exception to propagate it

    async def upsert_user_preferences(self, user_id: str, preferences: UserProfilePreference) -> None:
        """
        Insert or update user preferences in BigQuery.
        """
        now = datetime.now(timezone.utc)
        
        # Ensure allergens is a list, even if None or empty, for BigQuery ARRAY<STRING>
        allergens_list = preferences.allergens if preferences.allergens is not None else []

        query = f"""
        MERGE `{self.user_preferences_table_id}` T
        USING (
            SELECT
                @user_id AS user_id,
                @household_size AS household_size,
                @dietary_preference AS dietary_preference,
                @allergens AS allergens,
                @cuisine_preference AS cuisine_preference,
                @now AS created_at,
                @now AS updated_at
        ) S
        ON T.user_id = S.user_id
        WHEN MATCHED THEN
            UPDATE SET
                T.household_size = S.household_size,
                T.dietary_preference = S.dietary_preference,
                T.allergens = S.allergens,
                T.cuisine_preference = S.cuisine_preference,
                T.updated_at = S.updated_at
        WHEN NOT MATCHED THEN
            INSERT (user_id, household_size, dietary_preference, allergens, cuisine_preference, created_at, updated_at)
            VALUES (
                S.user_id, S.household_size, S.dietary_preference, S.allergens, S.cuisine_preference, 
                S.created_at, S.updated_at
            )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("household_size", "INT64", preferences.household_size),
                bigquery.ScalarQueryParameter("dietary_preference", "STRING", preferences.dietary_preference),
                bigquery.ArrayQueryParameter("allergens", "STRING", allergens_list),
                bigquery.ScalarQueryParameter("cuisine_preference", "STRING", preferences.cuisine_preference),
                bigquery.ScalarQueryParameter("now", "TIMESTAMP", now),
            ]
        )
        
        try:
            logger.info(f"Attempting to upsert preferences for user_id: {user_id}")
            self.bq_client.query(query, job_config=job_config).result()  # Wait for the job to complete
            logger.info(f"Successfully upserted preferences for user_id: {user_id}")
        except Exception as e:
            logger.error(f"Error upserting preferences for user_id {user_id}: {e}")
            raise

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

    async def _populate_samantha_smith_preferences(self):
        """Populate Samantha Smith's preferences"""
        print("Attempting to populate Samantha Smith's preferences...")
        try:
            # Query to get default user (Samantha Smith) and preferences
            query = f"""
            SELECT
                user.id as user_id,
                user.email,
                user.first_name,
                user.last_name,
                pref.dietary_restrictions,
                pref.allergies,
                pref.favorite_cuisines,
                pref.cooking_skill_level,
                pref.meal_preferences,
                pref.spice_preference,
                pref.cooking_time_preference
            FROM `{self.table_id}` as user
            INNER JOIN `{self.user_preferences_table_id}` as pref
            ON user.id = pref.user_id
            WHERE user.email = 'samantha.smith@example.com'
            """
            
            job_config = bigquery.QueryJobConfig()
            query_job = self.bq_client.query(query, job_config=job_config)
            result = query_job.result()
            
            # Get the first (and should be only) result for Samantha
            row = next(iter(result), None)
            if not row:
                print("Default user (Samantha Smith) not found in database")
                return
                
            # Create preferences object for Samantha
            samantha_prefs = UserProfilePreference(
                user_id=row.user_id,
                dietary_restrictions=row.dietary_restrictions,
                allergies=row.allergies,
                favorite_cuisines=row.favorite_cuisines,
                cooking_skill_level=row.cooking_skill_level,
                meal_preferences=row.meal_preferences,
                spice_preference=row.spice_preference,
                cooking_time_preference=row.cooking_time_preference
            )
            
            print(f"Processing preferences for default user: {row.email}")
            await self.upsert_user_preferences(row.user_id, samantha_prefs)
            print(f"Successfully updated preferences for {row.email}")

        except DefaultCredentialsError as e:
            print(f"Authentication Error: Could not find default credentials. {e}")
            print("Please ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly.")
        except Exception as e:
            print(f"An error occurred while populating preferences: {e}")
            logger.error(f"Detailed error populating preferences: {e}", exc_info=True)

if __name__ == "__main__":
    import asyncio
    print("Checking environment for preference population script...")
    # This check ensures that the environment is set up for BigQuery client
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.getenv('BIGQUERY_PROJECT'):
        print("Environment variables found. Running temporary p`12reference population script...")
        user_service = UserService()
        asyncio.run(user_service._populate_samantha_smith_preferences())
    else:
        print("Skipping preference population script: GOOGLE_APPLICATION_CREDENTIALS or BIGQUERY_PROJECT not set.")
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("- GOOGLE_APPLICATION_CREDENTIALS is MISSING")
        if not os.getenv('BIGQUERY_PROJECT'):
            print("- BIGQUERY_PROJECT is MISSING")
