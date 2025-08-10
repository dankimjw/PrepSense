#!/usr/bin/env python3
"""
Simple script to add mock ingredients and recipes to PrepSense database
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.config.database import get_database_service
from backend_gateway.services.user_recipes_service import UserRecipesService

# Mock ingredients that should appear in pantry with favorites
MOCK_INGREDIENTS = [
    # High-protein ingredients (marked as favorites)
    {"name": "chicken breast", "amount": "2 lbs", "category": "Meat", "is_favorite": True, "days_until_expiry": 5},
    {"name": "ground turkey", "amount": "1 lb", "category": "Meat", "is_favorite": True, "days_until_expiry": 3},
    {"name": "eggs", "amount": "12 count", "category": "Dairy", "is_favorite": True, "days_until_expiry": 14},
    {"name": "Greek yogurt", "amount": "32 oz", "category": "Dairy", "is_favorite": True, "days_until_expiry": 7},
    {"name": "cottage cheese", "amount": "16 oz", "category": "Dairy", "is_favorite": True, "days_until_expiry": 10},
    {"name": "quinoa", "amount": "2 cups", "category": "Grains", "is_favorite": True, "days_until_expiry": 365},
    {"name": "black beans", "amount": "2 cans", "category": "Canned Goods", "is_favorite": True, "days_until_expiry": 730},
    {"name": "cannellini beans", "amount": "2 cans", "category": "Canned Goods", "is_favorite": True, "days_until_expiry": 730},

    # Regular ingredients
    {"name": "spinach", "amount": "5 oz bag", "category": "Produce", "is_favorite": False, "days_until_expiry": 5},
    {"name": "tomatoes", "amount": "4 count", "category": "Produce", "is_favorite": False, "days_until_expiry": 7},
    {"name": "onions", "amount": "3 lbs", "category": "Produce", "is_favorite": False, "days_until_expiry": 30},
    {"name": "garlic", "amount": "1 bulb", "category": "Produce", "is_favorite": False, "days_until_expiry": 21},
    {"name": "olive oil", "amount": "500 ml", "category": "Pantry", "is_favorite": False, "days_until_expiry": 365},
    {"name": "pasta", "amount": "1 lb", "category": "Pasta", "is_favorite": False, "days_until_expiry": 730},
    {"name": "rice", "amount": "2 lbs", "category": "Grains", "is_favorite": False, "days_until_expiry": 365},
    {"name": "parmesan cheese", "amount": "8 oz", "category": "Dairy", "is_favorite": False, "days_until_expiry": 60},
    {"name": "mozzarella cheese", "amount": "8 oz", "category": "Dairy", "is_favorite": False, "days_until_expiry": 14},
    {"name": "marinara sauce", "amount": "24 oz jar", "category": "Canned Goods", "is_favorite": False, "days_until_expiry": 365},
]

# Mock recipes for My Recipes section
MOCK_RECIPES = [
    {
        "id": 1001,
        "title": "High-Protein Chicken Parmesan",
        "image": "https://img.spoonacular.com/recipes/632003-556x370.jpg",
        "readyInMinutes": 45,
        "servings": 4,
        "summary": "Classic Italian chicken parmesan with extra protein from cottage cheese in the marinara sauce.",
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 4, "unit": "pieces"},
            {"name": "eggs", "amount": 3, "unit": ""},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"},
            {"name": "mozzarella cheese", "amount": 200, "unit": "g"},
            {"name": "marinara sauce", "amount": 500, "unit": "ml"},
            {"name": "cottage cheese", "amount": 200, "unit": "g"},
        ]
    },
    {
        "id": 1002,
        "title": "Protein-Packed Turkey Quinoa Bowl",
        "image": "https://img.spoonacular.com/recipes/715769-556x370.jpg",
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Healthy quinoa bowl with ground turkey, black beans, and Greek yogurt.",
        "extendedIngredients": [
            {"name": "ground turkey", "amount": 1, "unit": "lb"},
            {"name": "quinoa", "amount": 1, "unit": "cup"},
            {"name": "black beans", "amount": 1, "unit": "can"},
            {"name": "spinach", "amount": 2, "unit": "cups"},
            {"name": "Greek yogurt", "amount": 0.5, "unit": "cup"},
        ]
    },
    {
        "id": 1003,
        "title": "Mediterranean Egg White Scramble",
        "image": "https://img.spoonacular.com/recipes/633344-556x370.jpg",
        "readyInMinutes": 15,
        "servings": 2,
        "summary": "Light and protein-rich breakfast with egg whites, spinach, and cottage cheese.",
        "extendedIngredients": [
            {"name": "eggs", "amount": 6, "unit": "whites"},
            {"name": "spinach", "amount": 2, "unit": "cups"},
            {"name": "cottage cheese", "amount": 0.5, "unit": "cup"},
            {"name": "tomatoes", "amount": 1, "unit": ""},
            {"name": "olive oil", "amount": 1, "unit": "tbsp"},
        ]
    }
]

async def add_mock_data():
    """Add mock ingredients and recipes to database"""
    db = get_database_service()
    recipes_service = UserRecipesService(db)

    print("Adding mock data to PrepSense database...")

    # Demo user ID
    user_id = 111  # samantha-1 maps to user_id 111

    try:
        # Add mock ingredients to pantry
        print("Adding mock ingredients to pantry...")

        for ingredient in MOCK_INGREDIENTS:
            expiration_date = datetime.now() + timedelta(days=ingredient["days_until_expiry"])

            # Add to pantry_items table
            query = """
                INSERT INTO pantry_items (user_id, product_name, quantity, expiration_date, category, is_favorite)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, product_name)
                DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    expiration_date = EXCLUDED.expiration_date,
                    is_favorite = EXCLUDED.is_favorite,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            try:
                with db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            query,
                            (user_id, ingredient["name"], ingredient["amount"],
                             expiration_date, ingredient["category"], ingredient["is_favorite"])
                        )
                        conn.commit()
                        print(f"✓ Added {ingredient['name']} ({'⭐ favorite' if ingredient['is_favorite'] else 'regular'})")
            except Exception as e:
                print(f"✗ Error adding {ingredient['name']}: {e}")

        print(f"Added {len(MOCK_INGREDIENTS)} ingredients to pantry")

        # Add mock recipes to user's saved recipes
        print("Adding mock recipes to My Recipes...")

        for recipe in MOCK_RECIPES:
            # Transform to match expected format
            recipe_data = {
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe["image"],
                "readyInMinutes": recipe["readyInMinutes"],
                "servings": recipe["servings"],
                "summary": recipe["summary"],
                "extendedIngredients": recipe["extendedIngredients"],
                "cuisines": ["High-Protein"],
                "dishTypes": ["main course"],
                "nutrition": {
                    "nutrients": [
                        {"name": "Protein", "amount": 35, "unit": "g"}
                    ]
                },
                "usedIngredientCount": len(recipe["extendedIngredients"]),
                "missedIngredientCount": 0,
                "usedIngredients": recipe["extendedIngredients"],
                "missedIngredients": []
            }

            # Save the recipe
            result = await recipes_service.save_recipe(
                user_id=user_id,
                recipe_id=recipe["id"],
                recipe_title=recipe["title"],
                recipe_image=recipe["image"],
                recipe_data=recipe_data,
                source="mock_data"
            )

            if result:
                print(f"✓ Saved recipe: {recipe['title']}")
            else:
                print(f"✓ Recipe already exists: {recipe['title']}")

        print(f"Added {len(MOCK_RECIPES)} recipes to My Recipes")

        # Verify data
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check pantry items
                cursor.execute("SELECT COUNT(*) FROM pantry_items WHERE user_id = %s", (user_id,))
                pantry_count = cursor.fetchone()[0]

                # Check favorite items
                cursor.execute("SELECT COUNT(*) FROM pantry_items WHERE user_id = %s AND is_favorite = true", (user_id,))
                favorites_count = cursor.fetchone()[0]

                # Check saved recipes
                cursor.execute("SELECT COUNT(*) FROM user_recipes WHERE user_id = %s", (user_id,))
                recipes_count = cursor.fetchone()[0]

                print("\n📊 Summary:")
                print(f"   Total pantry items: {pantry_count}")
                print(f"   Favorite items: {favorites_count}")
                print(f"   Saved recipes: {recipes_count}")

        print("\n✅ Mock data added successfully!")
        print("🔥 Favorites will appear first in pantry with ⭐ icon")
        print("📖 Recipes will appear in My Recipes section")

    except Exception as e:
        print(f"❌ Error adding mock data: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_mock_data())
