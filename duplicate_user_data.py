#!/usr/bin/env python3
"""
Script to duplicate user 111's data for new test users
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add the backend_gateway to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend_gateway'))

from db_client import DatabaseClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# New users to create
NEW_USERS = [
    {'id': 'john-2', 'email': 'john2@example.com', 'name': 'John Test 2'},
    {'id': 'jane-3', 'email': 'jane3@example.com', 'name': 'Jane Test 3'},
    {'id': 'bob-4', 'email': 'bob4@example.com', 'name': 'Bob Test 4'},
    {'id': 'mike-5', 'email': 'mike5@example.com', 'name': 'Mike Test 5'},
    {'id': 'sarah-6', 'email': 'sarah6@example.com', 'name': 'Sarah Test 6'}
]

SOURCE_USER_ID = '111'

async def duplicate_user_data():
    """Duplicate all data from user 111 to new users"""
    db = DatabaseClient()
    
    try:
        # 1. Get user 111's data
        logger.info(f"Fetching data for user {SOURCE_USER_ID}")
        
        # Get user profile
        user_data = await db.fetch_one(
            "SELECT * FROM users WHERE user_id = $1",
            SOURCE_USER_ID
        )
        
        if not user_data:
            logger.error(f"User {SOURCE_USER_ID} not found!")
            return
        
        # 2. Create new users
        for new_user in NEW_USERS:
            logger.info(f"Creating user {new_user['id']}")
            
            # Check if user already exists
            existing = await db.fetch_one(
                "SELECT user_id FROM users WHERE user_id = $1",
                new_user['id']
            )
            
            if existing:
                logger.warning(f"User {new_user['id']} already exists, skipping user creation")
                continue
            
            # Insert new user
            await db.execute(
                """
                INSERT INTO users (user_id, email, full_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                new_user['id'],
                new_user['email'],
                new_user['name'],
                datetime.now(),
                datetime.now()
            )
        
        # 3. Duplicate pantry items
        logger.info("Duplicating pantry items...")
        pantry_items = await db.fetch_all(
            """
            SELECT pi.*, p.name as product_name, p.category, p.unit
            FROM pantry_items pi
            JOIN products p ON pi.product_id = p.product_id
            WHERE pi.user_id = $1
            """,
            SOURCE_USER_ID
        )
        
        for new_user in NEW_USERS:
            for item in pantry_items:
                # Check if item already exists
                existing_item = await db.fetch_one(
                    """
                    SELECT pantry_item_id FROM pantry_items 
                    WHERE user_id = $1 AND product_id = $2
                    """,
                    new_user['id'],
                    item['product_id']
                )
                
                if not existing_item:
                    await db.execute(
                        """
                        INSERT INTO pantry_items 
                        (user_id, product_id, quantity, expiration_date, location, added_date, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        new_user['id'],
                        item['product_id'],
                        item['quantity'],
                        item['expiration_date'],
                        item['location'],
                        datetime.now(),
                        datetime.now()
                    )
        
        # 4. Duplicate shopping list items
        logger.info("Duplicating shopping list items...")
        shopping_items = await db.fetch_all(
            """
            SELECT * FROM shopping_list_items
            WHERE user_id = $1
            """,
            SOURCE_USER_ID
        )
        
        for new_user in NEW_USERS:
            for item in shopping_items:
                # Check if item already exists
                existing_item = await db.fetch_one(
                    """
                    SELECT item_id FROM shopping_list_items 
                    WHERE user_id = $1 AND product_id = $2
                    """,
                    new_user['id'],
                    item['product_id']
                )
                
                if not existing_item:
                    await db.execute(
                        """
                        INSERT INTO shopping_list_items 
                        (user_id, product_id, quantity, is_checked, added_date, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        new_user['id'],
                        item['product_id'],
                        item['quantity'],
                        item['is_checked'],
                        datetime.now(),
                        datetime.now()
                    )
        
        # 5. Duplicate recipe completions
        logger.info("Duplicating recipe completions...")
        completions = await db.fetch_all(
            """
            SELECT * FROM recipe_completions
            WHERE user_id = $1
            """,
            SOURCE_USER_ID
        )
        
        for new_user in NEW_USERS:
            for completion in completions:
                await db.execute(
                    """
                    INSERT INTO recipe_completions 
                    (user_id, recipe_id, completed_at, rating, notes)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    new_user['id'],
                    completion['recipe_id'],
                    completion['completed_at'],
                    completion['rating'],
                    completion['notes']
                )
        
        # 6. Duplicate favorites
        logger.info("Duplicating favorite recipes...")
        favorites = await db.fetch_all(
            """
            SELECT * FROM recipe_favorites
            WHERE user_id = $1
            """,
            SOURCE_USER_ID
        )
        
        for new_user in NEW_USERS:
            for favorite in favorites:
                # Check if already favorited
                existing_fav = await db.fetch_one(
                    """
                    SELECT 1 FROM recipe_favorites 
                    WHERE user_id = $1 AND recipe_id = $2
                    """,
                    new_user['id'],
                    favorite['recipe_id']
                )
                
                if not existing_fav:
                    await db.execute(
                        """
                        INSERT INTO recipe_favorites 
                        (user_id, recipe_id, favorited_at)
                        VALUES ($1, $2, $3)
                        """,
                        new_user['id'],
                        favorite['recipe_id'],
                        datetime.now()
                    )
        
        logger.info("Data duplication completed successfully!")
        
        # Verify the duplication
        logger.info("\nVerifying duplicated data:")
        for new_user in NEW_USERS:
            pantry_count = await db.fetch_one(
                "SELECT COUNT(*) as count FROM pantry_items WHERE user_id = $1",
                new_user['id']
            )
            shopping_count = await db.fetch_one(
                "SELECT COUNT(*) as count FROM shopping_list_items WHERE user_id = $1",
                new_user['id']
            )
            completion_count = await db.fetch_one(
                "SELECT COUNT(*) as count FROM recipe_completions WHERE user_id = $1",
                new_user['id']
            )
            favorite_count = await db.fetch_one(
                "SELECT COUNT(*) as count FROM recipe_favorites WHERE user_id = $1",
                new_user['id']
            )
            
            logger.info(f"\nUser {new_user['id']}:")
            logger.info(f"  - Pantry items: {pantry_count['count']}")
            logger.info(f"  - Shopping list items: {shopping_count['count']}")
            logger.info(f"  - Recipe completions: {completion_count['count']}")
            logger.info(f"  - Favorite recipes: {favorite_count['count']}")
            
    except Exception as e:
        logger.error(f"Error duplicating user data: {e}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(duplicate_user_data())