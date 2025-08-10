#!/usr/bin/env python3
"""
Simple script to add mock recipes and ingredients directly to database
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
load_dotenv(os.path.join(parent_dir, ".env"))

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# User ID for demo user
USER_ID = 111  # samantha-1
PANTRY_ID = 1011  # pantry_id for user 111


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def add_pantry_items():
    """Add all ingredients to pantry"""
    ingredients = [
        # Italian ingredients
        ("chicken breast", "1600g", 14, "Meat"),
        ("eggs", "2 dozen", 21, "Dairy"),
        ("breadcrumbs", "200g", 90, "Bakery"),
        ("parmesan cheese", "300g", 30, "Dairy"),
        ("mozzarella cheese", "600g", 14, "Dairy"),
        ("marinara sauce", "1000ml", 180, "Canned Goods"),
        ("cottage cheese", "400g", 14, "Dairy"),
        ("protein pasta", "800g", 365, "Pasta"),
        ("chicken thighs", "1200g", 7, "Meat"),
        ("cannellini beans", "4 cans", 730, "Canned Goods"),
        ("spinach", "500g", 7, "Produce"),
        ("sun-dried tomatoes", "200g", 180, "Canned Goods"),
        ("garlic", "10 cloves", 21, "Produce"),
        ("chicken broth", "1000ml", 365, "Canned Goods"),
        ("fresh basil", "2 bunches", 7, "Produce"),
        ("lemon", "4", 14, "Produce"),
        ("ground turkey", "1000g", 3, "Meat"),
        ("lasagna noodles", "1 box", 365, "Pasta"),
        ("ricotta cheese", "500g", 14, "Dairy"),
        ("Greek yogurt", "1kg", 21, "Dairy"),
        ("tomato sauce", "800ml", 365, "Canned Goods"),
        # Mexican ingredients
        ("flank steak", "800g", 5, "Meat"),
        ("black beans", "6 cans", 730, "Canned Goods"),
        ("quinoa", "600g", 365, "Rice & Grains"),
        ("lime", "8", 14, "Produce"),
        ("cilantro", "3 bunches", 7, "Produce"),
        ("avocado", "4", 7, "Produce"),
        ("jalapeños", "6", 14, "Produce"),
        ("chipotle peppers in adobo", "2 cans", 730, "International"),
        ("diced tomatoes", "2 cans", 730, "Canned Goods"),
        ("refried beans", "4 cans", 730, "Canned Goods"),
        ("corn tortillas", "24", 14, "Bakery"),
        ("queso fresco", "400g", 14, "Dairy"),
        ("red onion", "3", 21, "Produce"),
        ("egg whites", "16", 14, "Dairy"),
        ("turkey sausage", "400g", 7, "Meat"),
        ("flour tortillas", "8 large", 14, "Bakery"),
        ("pepper jack cheese", "200g", 21, "Dairy"),
        ("salsa", "500ml", 90, "Condiments"),
        ("green onions", "1 bunch", 7, "Produce"),
        # Indian ingredients
        ("chicken drumsticks", "1600g", 7, "Meat"),
        ("tandoori masala", "100g", 365, "Spices"),
        ("black lentils", "600g", 365, "Rice & Grains"),
        ("heavy cream", "600ml", 14, "Dairy"),
        ("butter", "300g", 30, "Dairy"),
        ("ginger", "4 inch piece", 21, "Produce"),
        ("paneer cheese", "800g", 14, "Dairy"),
        ("chickpea flour", "600g", 365, "Rice & Grains"),
        ("onion", "8", 21, "Produce"),
        ("garam masala", "100g", 365, "Spices"),
        ("basmati rice", "1kg", 365, "Rice & Grains"),
        ("biryani masala", "100g", 365, "Spices"),
        ("saffron", "1g", 730, "Spices"),
        ("milk", "500ml", 7, "Dairy"),
        ("cucumber", "3", 7, "Produce"),
        ("ground lamb", "800g", 3, "Meat"),
        ("green peas", "400g", 365, "Frozen"),
        ("tomatoes", "8", 7, "Produce"),
        ("bread flour", "800g", 180, "Bakery"),
    ]

    conn = get_connection()
    cur = conn.cursor()

    try:
        for name, quantity, days_until_expiry, category in ingredients:
            expiration_date = datetime.now() + timedelta(days=days_until_expiry)

            # Convert quantity to numeric and unit
            if " " in quantity:
                parts = quantity.split(" ", 1)
                qty_value = float(parts[0]) if parts[0].replace(".", "").isdigit() else 1.0
                unit = parts[1] if len(parts) > 1 else "unit"
            else:
                qty_value = float(quantity) if quantity.replace(".", "").isdigit() else 1.0
                unit = "unit"

            # Check if item already exists
            cur.execute(
                """
                SELECT pantry_item_id FROM pantry_items
                WHERE pantry_id = %s AND product_name = %s
            """,
                (PANTRY_ID, name),
            )

            existing = cur.fetchone()

            if existing:
                # Update existing item
                cur.execute(
                    """
                    UPDATE pantry_items
                    SET quantity = %s,
                        unit_of_measurement = %s,
                        expiration_date = %s,
                        category = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE pantry_item_id = %s
                """,
                    (qty_value, unit, expiration_date, category, existing["pantry_item_id"]),
                )
            else:
                # Insert new item
                cur.execute(
                    """
                    INSERT INTO pantry_items (
                        pantry_id, product_name, quantity, unit_of_measurement,
                        expiration_date, category, status, source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        PANTRY_ID,
                        name,
                        qty_value,
                        unit,
                        expiration_date,
                        category,
                        "available",
                        "manual",
                    ),
                )

            print(f"Added/Updated: {name} - {quantity}")

        conn.commit()
        print(f"\nSuccessfully added {len(ingredients)} ingredients to pantry")

    except Exception as e:
        conn.rollback()
        print(f"Error adding ingredients: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def add_recipes():
    """Add mock recipes to user's saved recipes"""
    recipes = [
        {
            "id": 1001,
            "title": "Chicken Parmesan with Protein-Packed Marinara",
            "image": "https://img.spoonacular.com/recipes/632003-556x370.jpg",
            "cuisine": "Italian",
            "protein": 48,
            "ingredients_count": 8,
        },
        {
            "id": 1002,
            "title": "Tuscan White Bean and Chicken Skillet",
            "image": "https://img.spoonacular.com/recipes/715769-556x370.jpg",
            "cuisine": "Italian",
            "protein": 42,
            "ingredients_count": 8,
        },
        {
            "id": 1003,
            "title": "High-Protein Lasagna with Turkey and Ricotta",
            "image": "https://img.spoonacular.com/recipes/633344-556x370.jpg",
            "cuisine": "Italian",
            "protein": 38,
            "ingredients_count": 8,
        },
        {
            "id": 1004,
            "title": "Carne Asada Protein Bowl",
            "image": "https://img.spoonacular.com/recipes/641893-556x370.jpg",
            "cuisine": "Mexican",
            "protein": 45,
            "ingredients_count": 8,
        },
        {
            "id": 1005,
            "title": "Chicken Tinga Tacos with Refried Beans",
            "image": "https://img.spoonacular.com/recipes/663050-556x370.jpg",
            "cuisine": "Mexican",
            "protein": 36,
            "ingredients_count": 8,
        },
        {
            "id": 1006,
            "title": "Mexican Egg White Breakfast Burrito",
            "image": "https://img.spoonacular.com/recipes/636228-556x370.jpg",
            "cuisine": "Mexican",
            "protein": 40,
            "ingredients_count": 8,
        },
        {
            "id": 1007,
            "title": "Tandoori Chicken with Dal Makhani",
            "image": "https://img.spoonacular.com/recipes/663175-556x370.jpg",
            "cuisine": "Indian",
            "protein": 44,
            "ingredients_count": 8,
        },
        {
            "id": 1008,
            "title": "Palak Paneer with Chickpea Flour Roti",
            "image": "https://img.spoonacular.com/recipes/641906-556x370.jpg",
            "cuisine": "Indian",
            "protein": 35,
            "ingredients_count": 8,
        },
        {
            "id": 1009,
            "title": "Chicken Biryani with Raita",
            "image": "https://img.spoonacular.com/recipes/654928-556x370.jpg",
            "cuisine": "Indian",
            "protein": 38,
            "ingredients_count": 8,
        },
        {
            "id": 1010,
            "title": "Lamb Keema with Protein Naan",
            "image": "https://img.spoonacular.com/recipes/640119-556x370.jpg",
            "cuisine": "Indian",
            "protein": 42,
            "ingredients_count": 8,
        },
    ]

    conn = get_connection()
    cur = conn.cursor()

    try:
        for recipe in recipes:
            # First, insert into recipes table if not exists
            cur.execute(
                """
                INSERT INTO recipes (recipe_id, recipe_name, cuisine_type, prep_time, servings, recipe_data)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (recipe_id) DO NOTHING
            """,
                (
                    recipe["id"],
                    recipe["title"],
                    recipe["cuisine"],
                    45,  # prep_time
                    4,  # servings
                    json.dumps(
                        {
                            "protein": recipe["protein"],
                            "ingredients_count": recipe["ingredients_count"],
                        }
                    ),
                ),
            )

            # Create recipe data with all ingredients marked as available
            recipe_data = {
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe["image"],
                "cuisines": [recipe["cuisine"]],
                "readyInMinutes": 45,
                "servings": 4,
                "dishTypes": ["main course"],
                "nutrition": {
                    "nutrients": [{"name": "Protein", "amount": recipe["protein"], "unit": "g"}]
                },
                "summary": f"High-protein {recipe['cuisine']} recipe perfect for your dietary preferences.",
                "usedIngredientCount": recipe["ingredients_count"],
                "missedIngredientCount": 0,
                "unusedIngredientCount": 0,
                "likes": random.randint(50, 500),
            }

            # Check if recipe already exists
            cur.execute(
                """
                SELECT id FROM user_recipes
                WHERE user_id = %s AND recipe_id = %s
            """,
                (USER_ID, recipe["id"]),
            )

            existing = cur.fetchone()

            if existing:
                # Update existing recipe
                cur.execute(
                    """
                    UPDATE user_recipes
                    SET recipe_title = %s,
                        recipe_image = %s,
                        recipe_data = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """,
                    (recipe["title"], recipe["image"], json.dumps(recipe_data), existing["id"]),
                )
                print(f"Updated recipe: {recipe['title']}")
            else:
                # Insert new recipe
                cur.execute(
                    """
                    INSERT INTO user_recipes (
                        user_id, recipe_id, recipe_title, recipe_image,
                        recipe_data, source, rating, is_favorite
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        USER_ID,
                        recipe["id"],
                        recipe["title"],
                        recipe["image"],
                        json.dumps(recipe_data),
                        "mock_high_protein",
                        "neutral",
                        False,
                    ),
                )
                print(f"Added recipe: {recipe['title']}")

        conn.commit()
        print(f"\nSuccessfully added {len(recipes)} recipes")

    except Exception as e:
        conn.rollback()
        print(f"Error adding recipes: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_data():
    """Verify the data was added correctly"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Count pantry items
        cur.execute("SELECT COUNT(*) as count FROM pantry_items WHERE pantry_id = %s", (PANTRY_ID,))
        pantry_count = cur.fetchone()["count"]
        print(f"\nPantry items for pantry {PANTRY_ID} (user {USER_ID}): {pantry_count}")

        # Count recipes
        cur.execute("SELECT COUNT(*) as count FROM user_recipes WHERE user_id = %s", (USER_ID,))
        recipe_count = cur.fetchone()["count"]
        print(f"Saved recipes for user {USER_ID}: {recipe_count}")

        # Show a few pantry items
        cur.execute(
            """
            SELECT product_name, quantity, unit_of_measurement, category, expiration_date
            FROM pantry_items
            WHERE pantry_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """,
            (PANTRY_ID,),
        )

        print("\nSample pantry items:")
        for item in cur.fetchall():
            print(
                f"  - {item['product_name']}: {item['quantity']} {item['unit_of_measurement']} ({item['category']}) - expires {item['expiration_date'].strftime('%Y-%m-%d')}"
            )

        # Show recipes
        cur.execute(
            """
            SELECT recipe_title, recipe_data->>'cuisines' as cuisine
            FROM user_recipes
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """,
            (USER_ID,),
        )

        print("\nAdded recipes:")
        for recipe in cur.fetchall():
            print(f"  - {recipe['recipe_title']} ({recipe['cuisine']})")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("Adding mock high-protein recipes and ingredients...")
    print(f"Database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
    print(f"User ID: {USER_ID}\n")

    try:
        add_pantry_items()
        add_recipes()
        verify_data()
        print("\n✅ All mock data added successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
