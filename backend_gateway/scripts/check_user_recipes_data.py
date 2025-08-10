#!/usr/bin/env python3
"""
Check user recipes and favorites data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def check_user_recipes():
    """Check user recipes and favorites"""
    print("Checking user recipes and favorites...")

    # Get database service
    db_service = get_database_service()

    try:
        # Check if user_recipes table exists and has data for user 111
        user_recipes_query = """
            SELECT * FROM user_recipes
            WHERE user_id = 111
            ORDER BY created_at DESC
            LIMIT 10;
        """

        recipes = db_service.execute_query(user_recipes_query)
        if recipes:
            print(f"\nFound {len(recipes)} recipes for user 111:")
            for recipe in recipes:
                print(f"\n  Recipe ID: {recipe.get('recipe_id')}")
                print(f"  Name: {recipe.get('recipe_name', 'N/A')}")
                print(f"  Is Favorite: {recipe.get('is_favorite', False)}")
                print(f"  Rating: {recipe.get('rating', 'N/A')}")
                print(f"  Created: {recipe.get('created_at')}")
        else:
            print("\nNo recipes found for user 111")

        # Check table structure
        schema_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_recipes'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """

        columns = db_service.execute_query(schema_query)
        if columns:
            print("\n\nColumns in 'user_recipes' table:")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")

        # Check for any users with recipes
        users_with_recipes = """
            SELECT user_id, COUNT(*) as recipe_count
            FROM user_recipes
            GROUP BY user_id
            ORDER BY recipe_count DESC
            LIMIT 5;
        """

        user_counts = db_service.execute_query(users_with_recipes)
        if user_counts:
            print("\n\nUsers with saved recipes:")
            for user in user_counts:
                print(f"  - User {user['user_id']}: {user['recipe_count']} recipes")

        # Check specifically for favorites
        favorites_query = """
            SELECT * FROM user_recipes
            WHERE user_id = 111 AND is_favorite = true
            LIMIT 5;
        """

        favorites = db_service.execute_query(favorites_query)
        if favorites:
            print(f"\n\nUser 111 has {len(favorites)} favorite recipes:")
            for fav in favorites:
                print(f"  - {fav.get('recipe_name', 'Recipe ID: ' + str(fav.get('recipe_id')))}")

    except Exception as e:
        print(f"❌ Error checking recipes: {e}")


if __name__ == "__main__":
    check_user_recipes()
