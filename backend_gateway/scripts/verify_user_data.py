#!/usr/bin/env python3
"""
Verify the duplicated user data
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import logging

from backend_gateway.core.config import settings
from backend_gateway.services.postgres_service import PostgresService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_users():
    """Check all users that were created"""

    # Setup database connection
    connection_params = {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "database": settings.POSTGRES_DATABASE,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
    }

    db = PostgresService(connection_params)

    try:
        # Get all users with usernames matching our test users
        users = db.execute_query(
            """
            SELECT user_id, username, email, first_name, last_name, created_at
            FROM users 
            WHERE username IN (@u1, @u2, @u3, @u4, @u5) OR user_id = @source_id
            ORDER BY user_id
            """,
            {
                "u1": "john2",
                "u2": "jane3",
                "u3": "bob4",
                "u4": "mike5",
                "u5": "sarah6",
                "source_id": 111,
            },
        )

        logger.info("Users found:")
        for user in users:
            logger.info(
                f"  ID: {user['user_id']}, Username: {user['username']}, Email: {user['email']}"
            )

            # Check pantry
            pantry = db.execute_query(
                "SELECT pantry_id, pantry_name FROM pantries WHERE user_id = @user_id",
                {"user_id": user["user_id"]},
            )

            if pantry:
                pantry_id = pantry[0]["pantry_id"]
                logger.info(f"    - Pantry: {pantry[0]['pantry_name']} (ID: {pantry_id})")

                # Count pantry items
                item_count = db.execute_query(
                    "SELECT COUNT(*) as count FROM pantry_items WHERE pantry_id = @pantry_id",
                    {"pantry_id": pantry_id},
                )
                logger.info(f"    - Pantry items: {item_count[0]['count']}")

            # Count other data - check if tables exist first
            try:
                shopping_count = db.execute_query(
                    "SELECT COUNT(*) as count FROM shopping_list_items WHERE user_id = @user_id",
                    {"user_id": user["user_id"]},
                )[0]["count"]
                logger.info(f"    - Shopping list items: {shopping_count}")
            except:
                logger.info(f"    - Shopping list items: N/A (table may not exist)")

            try:
                # Check for user_recipes table instead
                recipe_count = db.execute_query(
                    "SELECT COUNT(*) as count FROM user_recipes WHERE user_id = @user_id",
                    {"user_id": user["user_id"]},
                )[0]["count"]
                logger.info(f"    - User recipes: {recipe_count}")
            except:
                logger.info(f"    - User recipes: N/A (table may not exist)")
            logger.info("")

    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        raise


if __name__ == "__main__":
    verify_users()
