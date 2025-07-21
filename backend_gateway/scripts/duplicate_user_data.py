#!/usr/bin/env python3
"""
Script to duplicate user 111's data for new test users
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime
from typing import List, Dict, Any

import logging

from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# New users to create
NEW_USERS = [
    {'username': 'john2', 'email': 'john2@example.com', 'first_name': 'John', 'last_name': 'Test2'},
    {'username': 'jane3', 'email': 'jane3@example.com', 'first_name': 'Jane', 'last_name': 'Test3'},
    {'username': 'bob4', 'email': 'bob4@example.com', 'first_name': 'Bob', 'last_name': 'Test4'},
    {'username': 'mike5', 'email': 'mike5@example.com', 'first_name': 'Mike', 'last_name': 'Test5'},
    {'username': 'sarah6', 'email': 'sarah6@example.com', 'first_name': 'Sarah', 'last_name': 'Test6'}
]

SOURCE_USER_ID = 111

def duplicate_user_data():
    """Duplicate all data from user 111 to new users"""
    
    # Setup database connection
    connection_params = {
        'host': settings.POSTGRES_HOST,
        'port': settings.POSTGRES_PORT,
        'database': settings.POSTGRES_DATABASE,
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD
    }
    
    db = PostgresService(connection_params)
    
    try:
        # 1. Get user 111's data
        logger.info(f"Fetching data for user {SOURCE_USER_ID}")
        
        # Get user profile
        user_data = db.execute_query(
            "SELECT * FROM users WHERE user_id = @user_id",
            {"user_id": SOURCE_USER_ID}
        )
        
        if not user_data:
            logger.error(f"User {SOURCE_USER_ID} not found!")
            return
        
        # 2. Create new users and collect their IDs
        user_id_map = {}
        for new_user in NEW_USERS:
            logger.info(f"Creating user {new_user['username']}")
            
            # Check if user already exists
            existing = db.execute_query(
                "SELECT user_id FROM users WHERE username = @username OR email = @email",
                {"username": new_user['username'], "email": new_user['email']}
            )
            
            if existing:
                logger.warning(f"User {new_user['username']} already exists")
                user_id_map[new_user['username']] = existing[0]['user_id']
                continue
            
            # Insert new user - using data from source user for password
            result = db.execute_query(
                """
                INSERT INTO users (username, email, first_name, last_name, password_hash, role, created_at, updated_at)
                VALUES (@username, @email, @first_name, @last_name, @password_hash, @role, @created_at, @updated_at)
                RETURNING user_id
                """,
                {"username": new_user['username'], "email": new_user['email'], 
                 "first_name": new_user['first_name'], "last_name": new_user['last_name'],
                 "password_hash": user_data[0]['password_hash'], "role": 'user',
                 "created_at": datetime.now(), "updated_at": datetime.now()}
            )
            user_id_map[new_user['username']] = result[0]['user_id']
            logger.info(f"Created user {new_user['username']} with ID {result[0]['user_id']}")
        
        # 3. First create pantries for new users
        logger.info("Creating pantries for new users...")
        pantry_id_map = {}
        for username, new_user_id in user_id_map.items():
            # Check if pantry exists
            existing_pantry = db.execute_query(
                "SELECT pantry_id FROM pantries WHERE user_id = @user_id",
                {"user_id": new_user_id}
            )
            
            if existing_pantry:
                pantry_id_map[new_user_id] = existing_pantry[0]['pantry_id']
            else:
                # Create pantry
                result = db.execute_query(
                    """
                    INSERT INTO pantries (user_id, pantry_name, created_at)
                    VALUES (@user_id, @pantry_name, @created_at)
                    RETURNING pantry_id
                    """,
                    {"user_id": new_user_id, "pantry_name": f"{username}'s Pantry",
                     "created_at": datetime.now()}
                )
                pantry_id_map[new_user_id] = result[0]['pantry_id']
        
        # 4. Duplicate pantry items
        logger.info("Duplicating pantry items...")
        # Get source user's pantry
        source_pantry = db.execute_query(
            "SELECT pantry_id FROM pantries WHERE user_id = @user_id",
            {"user_id": SOURCE_USER_ID}
        )
        
        if source_pantry:
            source_pantry_id = source_pantry[0]['pantry_id']
            pantry_items = db.execute_query(
                """
                SELECT * FROM pantry_items
                WHERE pantry_id = @pantry_id
                """,
                {"pantry_id": source_pantry_id}
            )
        
            for username, new_user_id in user_id_map.items():
                new_pantry_id = pantry_id_map.get(new_user_id)
                if not new_pantry_id:
                    continue
                    
                for item in pantry_items:
                    # Check if item already exists by product name
                    existing_item = db.execute_query(
                        """
                        SELECT pantry_item_id FROM pantry_items 
                        WHERE pantry_id = @pantry_id AND product_name = @product_name
                        """,
                        {"pantry_id": new_pantry_id, "product_name": item['product_name']}
                    )
                    
                    if not existing_item:
                        # Handle JSONB metadata column
                        metadata = item.get('metadata', {})
                        if isinstance(metadata, dict):
                            import json
                            metadata_str = json.dumps(metadata)
                        else:
                            metadata_str = metadata if metadata else '{}'
                        
                        db.execute_query(
                            """
                            INSERT INTO pantry_items 
                            (pantry_id, product_name, brand_name, category, quantity, 
                             unit_of_measurement, expiration_date, unit_price, total_price,
                             source, status, metadata, created_at, updated_at)
                            VALUES (@pantry_id, @product_name, @brand_name, @category, @quantity,
                                    @unit_of_measurement, @expiration_date, @unit_price, @total_price,
                                    @source, @status, @metadata::jsonb, @created_at, @updated_at)
                            """,
                            {
                                "pantry_id": new_pantry_id,
                                "product_name": item.get('product_name'),
                                "brand_name": item.get('brand_name'),
                                "category": item.get('category', 'Uncategorized'),
                                "quantity": item.get('quantity', 0),
                                "unit_of_measurement": item.get('unit_of_measurement'),
                                "expiration_date": item.get('expiration_date'),
                                "unit_price": item.get('unit_price'),
                                "total_price": item.get('total_price'),
                                "source": item.get('source', 'manual'),
                                "status": item.get('status', 'available'),
                                "metadata": metadata_str,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
        
        # 4. Duplicate shopping list items
        logger.info("Duplicating shopping list items...")
        shopping_items = db.execute_query(
            """
            SELECT * FROM shopping_list_items
            WHERE user_id = @user_id
            """,
            {"user_id": SOURCE_USER_ID}
        )
        
        for username, new_user_id in user_id_map.items():
            for item in shopping_items:
                # Check if item already exists
                existing_item = db.execute_query(
                    """
                    SELECT item_id FROM shopping_list_items 
                    WHERE user_id = @user_id AND product_id = @product_id
                    """,
                    {"user_id": new_user_id, "product_id": item['product_id']}
                )
                
                if not existing_item:
                    db.execute_query(
                        """
                        INSERT INTO shopping_list_items 
                        (user_id, product_id, quantity, is_checked, added_date, updated_at)
                        VALUES (@user_id, @product_id, @quantity, @is_checked, @added_date, @updated_at)
                        """,
                        {"user_id": new_user_id, "product_id": item['product_id'],
                         "quantity": item['quantity'], "is_checked": item['is_checked'],
                         "added_date": datetime.now(), "updated_at": datetime.now()}
                    )
        
        # 5. Duplicate recipe completions
        logger.info("Duplicating recipe completions...")
        completions = db.execute_query(
            """
            SELECT * FROM recipe_completions
            WHERE user_id = @user_id
            """,
            {"user_id": SOURCE_USER_ID}
        )
        
        for username, new_user_id in user_id_map.items():
            for completion in completions:
                db.execute_query(
                    """
                    INSERT INTO recipe_completions 
                    (user_id, recipe_id, completed_at, rating, notes)
                    VALUES (@user_id, @recipe_id, @completed_at, @rating, @notes)
                    """,
                    {"user_id": new_user_id, "recipe_id": completion['recipe_id'],
                     "completed_at": completion['completed_at'], "rating": completion['rating'],
                     "notes": completion['notes']}
                )
        
        # 6. Duplicate favorites
        logger.info("Duplicating favorite recipes...")
        favorites = db.execute_query(
            """
            SELECT * FROM recipe_favorites
            WHERE user_id = @user_id
            """,
            {"user_id": SOURCE_USER_ID}
        )
        
        for username, new_user_id in user_id_map.items():
            for favorite in favorites:
                # Check if already favorited
                existing_fav = db.execute_query(
                    """
                    SELECT 1 FROM recipe_favorites 
                    WHERE user_id = @user_id AND recipe_id = @recipe_id
                    """,
                    {"user_id": new_user_id, "recipe_id": favorite['recipe_id']}
                )
                
                if not existing_fav:
                    db.execute_query(
                        """
                        INSERT INTO recipe_favorites 
                        (user_id, recipe_id, favorited_at)
                        VALUES (@user_id, @recipe_id, @favorited_at)
                        """,
                        {"user_id": new_user_id, "recipe_id": favorite['recipe_id'], 
                         "favorited_at": datetime.now()}
                    )
        
        logger.info("Data duplication completed successfully!")
        
        # Verify the duplication
        logger.info("\nVerifying duplicated data:")
        for username, new_user_id in user_id_map.items():
            pantry_id = pantry_id_map.get(new_user_id)
            pantry_count = {'count': 0}
            if pantry_id:
                pantry_count = db.execute_query(
                    "SELECT COUNT(*) as count FROM pantry_items WHERE pantry_id = @pantry_id",
                    {"pantry_id": pantry_id}
                )[0]
            shopping_count = db.execute_query(
                "SELECT COUNT(*) as count FROM shopping_list_items WHERE user_id = @user_id",
                {"user_id": new_user_id}
            )[0]
            completion_count = db.execute_query(
                "SELECT COUNT(*) as count FROM recipe_completions WHERE user_id = @user_id",
                {"user_id": new_user_id}
            )[0]
            favorite_count = db.execute_query(
                "SELECT COUNT(*) as count FROM recipe_favorites WHERE user_id = @user_id",
                {"user_id": new_user_id}
            )[0]
            
            logger.info(f"\nUser {username} (ID: {new_user_id}):")
            logger.info(f"  - Pantry items: {pantry_count['count']}")
            logger.info(f"  - Shopping list items: {shopping_count['count']}")
            logger.info(f"  - Recipe completions: {completion_count['count']}")
            logger.info(f"  - Favorite recipes: {favorite_count['count']}")
            
    except Exception as e:
        logger.error(f"Error duplicating user data: {e}")
        raise

if __name__ == "__main__":
    duplicate_user_data()