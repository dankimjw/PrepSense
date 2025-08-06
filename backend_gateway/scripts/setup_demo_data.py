#!/usr/bin/env python3
"""
Setup demo data for testing recipe completion with ingredient subtraction
This script creates mock recipes and pantry items for demonstration purposes
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Activate virtual environment if available
venv_path = Path(__file__).parent.parent.parent / "venv"
if venv_path.exists():
    activate_this = venv_path / "bin" / "activate_this.py"
    if activate_this.exists():
        exec(open(activate_this).read(), {"__file__": str(activate_this)})

try:
    from backend_gateway.config.database import get_database_service
    from backend_gateway.services.pantry_service import PantryService
    from backend_gateway.services.user_recipes_service import UserRecipesService
except ImportError:
    print("❌ Error: Unable to import required modules.")
    print("   Make sure you're running this from the PrepSense root directory")
    print("   and that the virtual environment is activated:")
    print("   $ source venv/bin/activate")
    sys.exit(1)

# Demo user ID
DEMO_USER_ID = 111


def setup_demo_pantry_items(db_service, pantry_service):
    """Create demo pantry items with various units for testing"""
    print("🥘 Setting up demo pantry items...")

    # First, get or create pantry for user
    pantry_query = """
    SELECT pantry_id FROM pantries 
    WHERE user_id = %(user_id)s
    LIMIT 1
    """

    result = db_service.execute_query(pantry_query, {"user_id": DEMO_USER_ID})

    if not result:
        # Create pantry if doesn't exist
        create_pantry = """
        INSERT INTO pantries (user_id, name, created_at, updated_at)
        VALUES (%(user_id)s, %(name)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING pantry_id
        """
        result = db_service.execute_query(
            create_pantry, {"user_id": DEMO_USER_ID, "name": "My Pantry"}
        )

    pantry_id = result[0]["pantry_id"]

    # Demo items with various units for testing conversions
    demo_items = [
        # Liquids - for volume conversion testing
        {
            "product_name": "Whole Milk",
            "quantity": 2000,  # 2 liters
            "unit_of_measurement": "ml",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=7)).date(),
        },
        {
            "product_name": "Olive Oil",
            "quantity": 750,  # 750ml
            "unit_of_measurement": "ml",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=180)).date(),
        },
        # Dry goods - for weight conversion testing
        {
            "product_name": "All-Purpose Flour",
            "quantity": 2.5,  # 2.5 kg
            "unit_of_measurement": "kg",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=365)).date(),
        },
        {
            "product_name": "Granulated Sugar",
            "quantity": 1000,  # 1kg in grams
            "unit_of_measurement": "g",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=730)).date(),
        },
        {
            "product_name": "Pasta",
            "quantity": 500,  # 500g to ensure enough for recipe
            "unit_of_measurement": "g",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=365)).date(),
        },
        # Count items
        {
            "product_name": "Eggs",
            "quantity": 12,
            "unit_of_measurement": "each",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=21)).date(),
        },
        {
            "product_name": "Roma Tomatoes",
            "quantity": 6,
            "unit_of_measurement": "each",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=5)).date(),
        },
        # Items with different units for testing
        {
            "product_name": "Butter",
            "quantity": 1,  # 1 pound
            "unit_of_measurement": "lb",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=30)).date(),
        },
        {
            "product_name": "Chicken Breast",
            "quantity": 2,  # 2 pounds
            "unit_of_measurement": "lb",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=3)).date(),
        },
        # Spices and small quantities
        {
            "product_name": "Salt",
            "quantity": 500,
            "unit_of_measurement": "g",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=1095)).date(),
        },
        {
            "product_name": "Black Pepper",
            "quantity": 100,
            "unit_of_measurement": "g",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=1095)).date(),
        },
        {
            "product_name": "Vanilla Extract",
            "quantity": 4,  # 4 fl oz
            "unit_of_measurement": "fl oz",
            "category": "Test",
            "expiration_date": (datetime.now() + timedelta(days=730)).date(),
        },
    ]

    # Insert or update demo items
    # First check if item exists
    for item in demo_items:
        item["pantry_id"] = pantry_id

        # Check if item exists
        check_query = """
        SELECT pantry_item_id FROM pantry_items 
        WHERE pantry_id = %(pantry_id)s AND product_name = %(product_name)s
        """
        existing = db_service.execute_query(
            check_query, {"pantry_id": pantry_id, "product_name": item["product_name"]}
        )

        if existing:
            # Update existing item
            update_query = """
            UPDATE pantry_items SET
                quantity = %(quantity)s,
                unit_of_measurement = %(unit_of_measurement)s,
                expiration_date = %(expiration_date)s,
                category = %(category)s,
                used_quantity = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE pantry_id = %(pantry_id)s AND product_name = %(product_name)s
            """
            db_service.execute_query(update_query, item)
            print(
                f"  ✅ Updated: {item['product_name']} - {item['quantity']} {item['unit_of_measurement']}"
            )
        else:
            # Insert new item
            insert_query = """
            INSERT INTO pantry_items (
                pantry_id, product_name, quantity, unit_of_measurement, 
                category, expiration_date, created_at, updated_at
            ) VALUES (
                %(pantry_id)s, %(product_name)s, %(quantity)s, %(unit_of_measurement)s,
                %(category)s, %(expiration_date)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
            db_service.execute_query(insert_query, item)
            print(
                f"  ✅ Added: {item['product_name']} - {item['quantity']} {item['unit_of_measurement']}"
            )

    return len(demo_items)


def setup_demo_recipes(db_service):
    """Create demo recipes for testing"""
    print("\n📚 Setting up demo recipes...")

    # Initialize service
    recipes_service = UserRecipesService(db_service)

    # Demo Recipe 1: Simple Pasta (tests weight and volume conversions)
    recipe1 = {
        "id": "demo-pasta-recipe",
        "title": "Simple Pasta with Olive Oil",
        "image": "https://img.spoonacular.com/recipes/715769-556x370.jpg",
        "readyInMinutes": 20,
        "servings": 4,
        "sourceUrl": "https://demo.recipe",
        "summary": "A simple pasta dish that uses exact pantry items for testing",
        "instructions": [
            {
                "number": 1,
                "step": "Bring a large pot of salted water to boil and cook pasta according to package directions.",
            },
            {"number": 2, "step": "Drain pasta and toss with olive oil."},
            {"number": 3, "step": "Season with salt and black pepper to taste."},
            {"number": 4, "step": "Serve immediately while hot."},
        ],
        "extendedIngredients": [
            {"id": 1, "name": "Pasta", "original": "400g pasta", "amount": 400, "unit": "g"},
            {
                "id": 2,
                "name": "Olive Oil",
                "original": "60ml olive oil",
                "amount": 60,
                "unit": "ml",
            },
            {"id": 3, "name": "Salt", "original": "5g salt", "amount": 5, "unit": "g"},
            {
                "id": 4,
                "name": "Black Pepper",
                "original": "2g black pepper",
                "amount": 2,
                "unit": "g",
            },
        ],
    }

    # Demo Recipe 2: Baking recipe (tests cups to ml, different weight units)
    recipe2 = {
        "id": "demo-cookies-recipe",
        "title": "Chocolate Chip Cookies",
        "image": "https://img.spoonacular.com/recipes/247012-556x370.jpg",
        "readyInMinutes": 45,
        "servings": 24,
        "sourceUrl": "https://demo.recipe",
        "summary": "Classic cookies to test baking ingredient conversions",
        "instructions": [
            {"number": 1, "step": "Preheat oven to 375°F (190°C)."},
            {"number": 2, "step": "Cream butter and sugars until fluffy."},
            {"number": 3, "step": "Beat in eggs and vanilla."},
            {"number": 4, "step": "Mix in flour, baking soda, and salt."},
            {"number": 5, "step": "Fold in chocolate chips."},
            {"number": 6, "step": "Drop dough on baking sheets and bake 9-11 minutes."},
        ],
        "extendedIngredients": [
            {
                "id": 1,
                "name": "flour",
                "original": "2 1/4 cups all-purpose flour",
                "amount": 2.25,
                "unit": "cup",
            },
            {
                "id": 2,
                "name": "butter",
                "original": "1 cup butter, softened",
                "amount": 1,
                "unit": "cup",
            },
            {
                "id": 3,
                "name": "sugar",
                "original": "3/4 cup granulated sugar",
                "amount": 0.75,
                "unit": "cup",
            },
            {"id": 4, "name": "eggs", "original": "2 large eggs", "amount": 2, "unit": "each"},
            {
                "id": 5,
                "name": "vanilla extract",
                "original": "1 teaspoon vanilla extract",
                "amount": 1,
                "unit": "tsp",
            },
            {"id": 6, "name": "salt", "original": "1 teaspoon salt", "amount": 1, "unit": "tsp"},
        ],
    }

    # Demo Recipe 3: Mixed units recipe
    recipe3 = {
        "id": "demo-chicken-recipe",
        "title": "Simple Roasted Chicken",
        "image": "https://img.spoonacular.com/recipes/638420-556x370.jpg",
        "readyInMinutes": 60,
        "servings": 4,
        "sourceUrl": "https://demo.recipe",
        "summary": "A simple roasted chicken using exact pantry items",
        "instructions": [
            {"number": 1, "step": "Preheat oven to 425°F (220°C)."},
            {"number": 2, "step": "Season chicken with salt and pepper."},
            {"number": 3, "step": "Drizzle with olive oil."},
            {"number": 4, "step": "Roast for 45-50 minutes until golden."},
        ],
        "extendedIngredients": [
            {
                "id": 1,
                "name": "Chicken Breast",
                "original": "1.5 pounds chicken breast",
                "amount": 1.5,
                "unit": "lb",
            },
            {
                "id": 2,
                "name": "Olive Oil",
                "original": "1/4 cup olive oil",
                "amount": 0.25,
                "unit": "cup",
            },
            {"id": 3, "name": "Salt", "original": "10g salt", "amount": 10, "unit": "g"},
            {
                "id": 4,
                "name": "Black Pepper",
                "original": "5g black pepper",
                "amount": 5,
                "unit": "g",
            },
        ],
    }

    # Save recipes
    recipes = [recipe1, recipe2, recipe3]
    saved_count = 0

    for recipe in recipes:
        try:
            result = recipes_service.save_recipe(
                user_id=DEMO_USER_ID,
                recipe_id=None,  # External recipe
                recipe_title=recipe["title"],
                recipe_image=recipe["image"],
                recipe_data=recipe,
                source="spoonacular",  # Marking as spoonacular for testing
                rating="neutral",
                is_favorite=True,  # Make them favorites for easy access
            )
            print(f"  ✅ Added recipe: {recipe['title']}")
            saved_count += 1
        except Exception as e:
            print(f"  ⚠️  Error adding recipe {recipe['title']}: {str(e)}")

    return saved_count


def reset_demo_data():
    """Reset pantry quantities to original demo values"""
    print("\n🔄 Resetting demo data to original values...")

    db_service = get_database_service()
    pantry_service = PantryService(db_service)

    # Clear existing demo items first (optional)
    # This ensures clean state

    # Re-setup demo items
    items_count = setup_demo_pantry_items(db_service, pantry_service)
    recipes_count = setup_demo_recipes(db_service)

    print(f"\n✅ Demo setup complete!")
    print(f"   - {items_count} pantry items")
    print(f"   - {recipes_count} recipes")
    print(f"\n📱 Ready for testing in the app!")


def show_current_quantities():
    """Display current pantry quantities"""
    print("\n📊 Current Pantry Quantities:")

    db_service = get_database_service()

    query = """
    SELECT 
        product_name,
        quantity,
        unit_of_measurement,
        used_quantity
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE p.user_id = %(user_id)s
    ORDER BY product_name
    """

    items = db_service.execute_query(query, {"user_id": DEMO_USER_ID})

    for item in items:
        used = item.get("used_quantity", 0) or 0
        print(
            f"  • {item['product_name']}: {item['quantity']} {item['unit_of_measurement']} "
            f"(used: {used})"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup demo data for recipe testing")
    parser.add_argument("--reset", action="store_true", help="Reset all demo data")
    parser.add_argument("--show", action="store_true", help="Show current quantities")

    args = parser.parse_args()

    if args.show:
        show_current_quantities()
    else:
        reset_demo_data()
        if not args.reset:
            print("\n💡 Tip: Use --show to see current quantities")
            print("💡 Tip: Use --reset to restore original quantities")
