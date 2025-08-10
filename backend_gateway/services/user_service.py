import logging
from datetime import datetime, timezone
from typing import Optional

from backend_gateway.config.database import get_database_service
from backend_gateway.core.security import get_password_hash
from backend_gateway.models.user import (
    UserCreate,
    UserInDB,
    UserProfilePreference,
    UserProfileResponse,
)

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db_service=None):
        if db_service:
            self.db_service = db_service
        else:
            self.db_service = get_database_service()

        self.users_table = "users"
        self.profile_table = "user_preferences"  # Note: plural form
        logger.info("UserService initialized with database service")

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get a user by email"""
        query = f"""
            SELECT user_id, email, first_name, last_name, role, created_at, updated_at
            FROM {self.users_table}
            WHERE email = %(email)s
            LIMIT 1
        """
        params = {"email": email}
        rows = self.db_service.execute_query(query, params)

        if not rows:
            return None

        row = rows[0]
        return UserInDB(
            id=str(row["user_id"]),  # Convert integer to string
            numeric_user_id=row["user_id"],  # Also include the numeric ID
            email=row["email"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            is_admin=row.get("role") == "admin",  # Check role for admin status
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get a user by ID"""
        query = f"""
            SELECT user_id, email, first_name, last_name, role, created_at, updated_at
            FROM {self.users_table}
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        params = {"user_id": int(user_id)}  # Convert string to integer
        rows = self.db_service.execute_query(query, params)

        if not rows:
            return None

        row = rows[0]
        return UserInDB(
            id=str(row["user_id"]),  # Convert integer to string
            numeric_user_id=row["user_id"],  # Also include the numeric ID
            email=row["email"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            is_admin=row.get("role") == "admin",  # Check role for admin status
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_user(self, user: UserCreate) -> UserInDB:
        """Create a new user"""
        now = datetime.now(timezone.utc)

        # Hash the password
        hashed_password = get_password_hash(user.password)

        # Generate username from email
        username = user.email.split("@")[0]

        query = f"""
            INSERT INTO {self.users_table}
            (username, email, first_name, last_name, password_hash, role, created_at, updated_at)
            VALUES (%(username)s, %(email)s, %(first_name)s, %(last_name)s, %(password_hash)s, %(role)s, %(created_at)s, %(updated_at)s)
            RETURNING user_id
        """
        params = {
            "username": username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "password_hash": hashed_password,
            "role": "admin" if user.is_admin else "user",
            "created_at": now,
            "updated_at": now,
        }

        rows = self.db_service.execute_query(query, params)
        user_id = rows[0]["user_id"] if rows else None

        if not user_id:
            raise Exception("Failed to create user")

        return UserInDB(
            id=str(user_id),
            numeric_user_id=user_id,  # Include numeric ID
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin or False,
            created_at=now,
            updated_at=now,
        )

    async def get_user_preferences(self, user_id: str) -> Optional[UserProfilePreference]:
        """Get user preferences"""
        query = f"""
            SELECT *
            FROM {self.profile_table}
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        params = {"user_id": int(user_id)}
        rows = self.db_service.execute_query(query, params)

        if not rows:
            return None

        row = rows[0]

        # Parse preferences JSON if it exists
        preferences_json = row.get("preferences", {}) or {}

        # Get household_size from either the column or the JSON
        household_size = preferences_json.get("household_size", row.get("household_size"))

        # Get values from JSON or fallback to columns
        dietary_preference = preferences_json.get(
            "dietary_restrictions", row.get("dietary_preference", [])
        )
        allergens = preferences_json.get("allergens", row.get("allergens", []))
        cuisine_preference = preferences_json.get(
            "cuisine_preferences", row.get("cuisine_preference", [])
        )

        return UserProfilePreference(
            household_size=household_size,
            dietary_preference=dietary_preference,
            allergens=allergens,
            cuisine_preference=cuisine_preference,
            preference_created_at=row.get("created_at"),
        )

    async def get_user_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get complete user profile including preferences"""
        # Get user info
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Get preferences
        preferences = await self.get_user_preferences(user_id)

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            user_created_at=user.created_at,
            user_updated_at=user.updated_at,
            password_hash=None,  # Don't expose password hash
            role="admin" if user.is_admin else "user",
            api_key_enc="",  # Add proper API key if needed
            preferences=preferences,
        )

    async def create_default_user(self) -> Optional[UserInDB]:
        """Create default test user if it doesn't exist"""
        default_email = "test@example.com"

        # Check if user already exists
        existing_user = await self.get_user_by_email(default_email)
        if existing_user:
            logger.info(f"Default user already exists: {default_email}")
            return existing_user

        # Create new user
        logger.info(f"Creating default user: {default_email}")
        user_data = UserCreate(
            email=default_email,
            first_name="Test",
            last_name="User",
            password="testpassword123",
            is_admin=False,
        )

        try:
            new_user = await self.create_user(user_data)
            logger.info(f"Default user created successfully: {new_user.id}")
            return new_user
        except Exception as e:
            logger.error(f"Failed to create default user: {e}")
            return None

    async def create_default_user_if_not_exists(self) -> Optional[UserInDB]:
        """Create default user if it doesn't exist (alias for create_default_user)"""
        return await self.create_default_user()
