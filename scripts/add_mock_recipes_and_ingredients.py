#!/usr/bin/env python3
"""
Add mock recipes and corresponding pantry ingredients for user preferences:
- Allergens: Shellfish (avoid)
- Dietary: High-Protein
- Cuisines: Italian, Mexican, Indian
"""

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import logging

from backend_gateway.core.config import settings
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.user_recipes_service import UserRecipesService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# High-protein recipes matching user preferences
MOCK_RECIPES = [
    # Italian Recipes (High Protein)
    {
        "id": 1001,
        "title": "Chicken Parmesan with Protein-Packed Marinara",
        "image": "https://img.spoonacular.com/recipes/632003-556x370.jpg",
        "cuisine": "Italian",
        "readyInMinutes": 45,
        "servings": 4,
        "protein": 48,
        "summary": "Classic Italian chicken parmesan with extra protein from added cottage cheese in the marinara sauce.",
        "instructions": [
            "Pound chicken breasts to even thickness",
            "Dredge in flour, egg, and breadcrumb mixture with parmesan",
            "Pan-fry until golden brown",
            "Top with marinara sauce mixed with cottage cheese",
            "Add mozzarella and bake until melted",
            "Serve over high-protein pasta",
        ],
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 4, "unit": "pieces", "aisle": "Meat"},
            {"name": "eggs", "amount": 3, "unit": "", "aisle": "Dairy"},
            {"name": "breadcrumbs", "amount": 200, "unit": "g", "aisle": "Bakery"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g", "aisle": "Dairy"},
            {"name": "mozzarella cheese", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "marinara sauce", "amount": 500, "unit": "ml", "aisle": "Canned Goods"},
            {"name": "cottage cheese", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "protein pasta", "amount": 400, "unit": "g", "aisle": "Pasta"},
        ],
    },
    {
        "id": 1002,
        "title": "Tuscan White Bean and Chicken Skillet",
        "image": "https://img.spoonacular.com/recipes/715769-556x370.jpg",
        "cuisine": "Italian",
        "readyInMinutes": 30,
        "servings": 4,
        "protein": 42,
        "summary": "Hearty Tuscan-style skillet with chicken, white beans, and spinach for maximum protein.",
        "instructions": [
            "Season and sear chicken thighs in olive oil",
            "Remove chicken, sauté garlic and sun-dried tomatoes",
            "Add white beans, chicken broth, and spinach",
            "Return chicken to pan and simmer",
            "Finish with fresh basil and lemon juice",
        ],
        "extendedIngredients": [
            {"name": "chicken thighs", "amount": 6, "unit": "pieces", "aisle": "Meat"},
            {"name": "cannellini beans", "amount": 2, "unit": "cans", "aisle": "Canned Goods"},
            {"name": "spinach", "amount": 200, "unit": "g", "aisle": "Produce"},
            {"name": "sun-dried tomatoes", "amount": 100, "unit": "g", "aisle": "Canned Goods"},
            {"name": "garlic", "amount": 4, "unit": "cloves", "aisle": "Produce"},
            {"name": "chicken broth", "amount": 500, "unit": "ml", "aisle": "Canned Goods"},
            {"name": "fresh basil", "amount": 1, "unit": "bunch", "aisle": "Produce"},
            {"name": "lemon", "amount": 1, "unit": "", "aisle": "Produce"},
        ],
    },
    {
        "id": 1003,
        "title": "High-Protein Lasagna with Turkey and Ricotta",
        "image": "https://img.spoonacular.com/recipes/633344-556x370.jpg",
        "cuisine": "Italian",
        "readyInMinutes": 60,
        "servings": 8,
        "protein": 38,
        "summary": "Traditional lasagna made healthier with lean ground turkey and protein-enriched ricotta filling.",
        "instructions": [
            "Brown ground turkey with Italian seasonings",
            "Mix ricotta with eggs, Greek yogurt, and spinach",
            "Layer pasta sheets, meat sauce, and ricotta mixture",
            "Top with mozzarella and parmesan",
            "Bake until golden and bubbly",
        ],
        "extendedIngredients": [
            {"name": "ground turkey", "amount": 1000, "unit": "g", "aisle": "Meat"},
            {"name": "lasagna noodles", "amount": 1, "unit": "box", "aisle": "Pasta"},
            {"name": "ricotta cheese", "amount": 500, "unit": "g", "aisle": "Dairy"},
            {"name": "Greek yogurt", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "eggs", "amount": 2, "unit": "", "aisle": "Dairy"},
            {"name": "spinach", "amount": 300, "unit": "g", "aisle": "Produce"},
            {"name": "mozzarella cheese", "amount": 400, "unit": "g", "aisle": "Dairy"},
            {"name": "tomato sauce", "amount": 800, "unit": "ml", "aisle": "Canned Goods"},
        ],
    },
    # Mexican Recipes (High Protein)
    {
        "id": 1004,
        "title": "Carne Asada Protein Bowl",
        "image": "https://img.spoonacular.com/recipes/641893-556x370.jpg",
        "cuisine": "Mexican",
        "readyInMinutes": 35,
        "servings": 4,
        "protein": 45,
        "summary": "Marinated grilled steak over black beans and quinoa with all the Mexican fixings.",
        "instructions": [
            "Marinate flank steak in lime juice, garlic, and spices",
            "Grill steak to medium-rare and let rest",
            "Prepare quinoa and mix with black beans",
            "Slice steak thinly against the grain",
            "Serve over quinoa-bean mixture with toppings",
        ],
        "extendedIngredients": [
            {"name": "flank steak", "amount": 800, "unit": "g", "aisle": "Meat"},
            {"name": "black beans", "amount": 2, "unit": "cans", "aisle": "Canned Goods"},
            {"name": "quinoa", "amount": 300, "unit": "g", "aisle": "Rice & Grains"},
            {"name": "lime", "amount": 4, "unit": "", "aisle": "Produce"},
            {"name": "cilantro", "amount": 1, "unit": "bunch", "aisle": "Produce"},
            {"name": "avocado", "amount": 2, "unit": "", "aisle": "Produce"},
            {"name": "Greek yogurt", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "jalapeños", "amount": 2, "unit": "", "aisle": "Produce"},
        ],
    },
    {
        "id": 1005,
        "title": "Chicken Tinga Tacos with Refried Beans",
        "image": "https://img.spoonacular.com/recipes/663050-556x370.jpg",
        "cuisine": "Mexican",
        "readyInMinutes": 40,
        "servings": 6,
        "protein": 36,
        "summary": "Smoky shredded chicken tacos with protein-rich refried beans and queso fresco.",
        "instructions": [
            "Simmer chicken breasts in chipotle-tomato sauce",
            "Shred chicken and mix back with sauce",
            "Warm refried beans with cumin",
            "Heat corn tortillas",
            "Assemble tacos with chicken, beans, and toppings",
        ],
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 1000, "unit": "g", "aisle": "Meat"},
            {
                "name": "chipotle peppers in adobo",
                "amount": 1,
                "unit": "can",
                "aisle": "International",
            },
            {"name": "diced tomatoes", "amount": 1, "unit": "can", "aisle": "Canned Goods"},
            {"name": "refried beans", "amount": 2, "unit": "cans", "aisle": "Canned Goods"},
            {"name": "corn tortillas", "amount": 12, "unit": "", "aisle": "Bakery"},
            {"name": "queso fresco", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "red onion", "amount": 1, "unit": "", "aisle": "Produce"},
            {"name": "cilantro", "amount": 1, "unit": "bunch", "aisle": "Produce"},
        ],
    },
    {
        "id": 1006,
        "title": "Mexican Egg White Breakfast Burrito",
        "image": "https://img.spoonacular.com/recipes/636228-556x370.jpg",
        "cuisine": "Mexican",
        "readyInMinutes": 20,
        "servings": 2,
        "protein": 40,
        "summary": "High-protein breakfast burrito with egg whites, turkey sausage, and black beans.",
        "instructions": [
            "Cook turkey sausage until browned",
            "Scramble egg whites with a splash of milk",
            "Warm black beans with cumin and garlic",
            "Warm large flour tortillas",
            "Fill with all ingredients and roll tightly",
        ],
        "extendedIngredients": [
            {"name": "egg whites", "amount": 8, "unit": "", "aisle": "Dairy"},
            {"name": "turkey sausage", "amount": 200, "unit": "g", "aisle": "Meat"},
            {"name": "black beans", "amount": 1, "unit": "can", "aisle": "Canned Goods"},
            {"name": "flour tortillas", "amount": 2, "unit": "large", "aisle": "Bakery"},
            {"name": "pepper jack cheese", "amount": 100, "unit": "g", "aisle": "Dairy"},
            {"name": "salsa", "amount": 200, "unit": "ml", "aisle": "Condiments"},
            {"name": "Greek yogurt", "amount": 100, "unit": "g", "aisle": "Dairy"},
            {"name": "green onions", "amount": 2, "unit": "", "aisle": "Produce"},
        ],
    },
    # Indian Recipes (High Protein)
    {
        "id": 1007,
        "title": "Tandoori Chicken with Dal Makhani",
        "image": "https://img.spoonacular.com/recipes/663175-556x370.jpg",
        "cuisine": "Indian",
        "readyInMinutes": 50,
        "servings": 4,
        "protein": 44,
        "summary": "Classic tandoori chicken served with creamy high-protein black lentil dal.",
        "instructions": [
            "Marinate chicken in yogurt and tandoori spices overnight",
            "Grill or bake chicken until charred and cooked through",
            "Cook black lentils until tender",
            "Prepare dal makhani with cream and butter",
            "Serve chicken over dal with naan bread",
        ],
        "extendedIngredients": [
            {"name": "chicken drumsticks", "amount": 8, "unit": "pieces", "aisle": "Meat"},
            {"name": "Greek yogurt", "amount": 400, "unit": "g", "aisle": "Dairy"},
            {"name": "tandoori masala", "amount": 3, "unit": "tbsp", "aisle": "Spices"},
            {"name": "black lentils", "amount": 300, "unit": "g", "aisle": "Rice & Grains"},
            {"name": "heavy cream", "amount": 200, "unit": "ml", "aisle": "Dairy"},
            {"name": "butter", "amount": 100, "unit": "g", "aisle": "Dairy"},
            {"name": "ginger", "amount": 2, "unit": "inch piece", "aisle": "Produce"},
            {"name": "garlic", "amount": 6, "unit": "cloves", "aisle": "Produce"},
        ],
    },
    {
        "id": 1008,
        "title": "Palak Paneer with Chickpea Flour Roti",
        "image": "https://img.spoonacular.com/recipes/641906-556x370.jpg",
        "cuisine": "Indian",
        "readyInMinutes": 40,
        "servings": 4,
        "protein": 35,
        "summary": "Creamy spinach curry with high-protein paneer cheese and chickpea flour flatbread.",
        "instructions": [
            "Blanch and puree spinach",
            "Fry paneer cubes until golden",
            "Prepare spinach gravy with onions and spices",
            "Add paneer and cream to spinach",
            "Make chickpea flour roti on griddle",
        ],
        "extendedIngredients": [
            {"name": "paneer cheese", "amount": 400, "unit": "g", "aisle": "Dairy"},
            {"name": "spinach", "amount": 500, "unit": "g", "aisle": "Produce"},
            {"name": "heavy cream", "amount": 100, "unit": "ml", "aisle": "Dairy"},
            {"name": "chickpea flour", "amount": 300, "unit": "g", "aisle": "Rice & Grains"},
            {"name": "onion", "amount": 2, "unit": "", "aisle": "Produce"},
            {"name": "garam masala", "amount": 2, "unit": "tbsp", "aisle": "Spices"},
            {"name": "ginger", "amount": 1, "unit": "inch piece", "aisle": "Produce"},
            {"name": "garlic", "amount": 4, "unit": "cloves", "aisle": "Produce"},
        ],
    },
    {
        "id": 1009,
        "title": "Chicken Biryani with Raita",
        "image": "https://img.spoonacular.com/recipes/654928-556x370.jpg",
        "cuisine": "Indian",
        "readyInMinutes": 60,
        "servings": 6,
        "protein": 38,
        "summary": "Fragrant basmati rice layered with spiced chicken and served with protein-rich yogurt raita.",
        "instructions": [
            "Marinate chicken in yogurt and biryani spices",
            "Partially cook basmati rice with whole spices",
            "Cook marinated chicken until tender",
            "Layer rice and chicken in pot",
            "Steam cook until rice is fluffy",
            "Prepare raita with yogurt and cucumber",
        ],
        "extendedIngredients": [
            {"name": "chicken thighs", "amount": 1000, "unit": "g", "aisle": "Meat"},
            {"name": "basmati rice", "amount": 500, "unit": "g", "aisle": "Rice & Grains"},
            {"name": "Greek yogurt", "amount": 500, "unit": "g", "aisle": "Dairy"},
            {"name": "biryani masala", "amount": 3, "unit": "tbsp", "aisle": "Spices"},
            {"name": "onions", "amount": 3, "unit": "", "aisle": "Produce"},
            {"name": "saffron", "amount": 1, "unit": "pinch", "aisle": "Spices"},
            {"name": "milk", "amount": 100, "unit": "ml", "aisle": "Dairy"},
            {"name": "cucumber", "amount": 1, "unit": "", "aisle": "Produce"},
        ],
    },
    {
        "id": 1010,
        "title": "Lamb Keema with Protein Naan",
        "image": "https://img.spoonacular.com/recipes/640119-556x370.jpg",
        "cuisine": "Indian",
        "readyInMinutes": 45,
        "servings": 4,
        "protein": 42,
        "summary": "Spiced ground lamb curry with peas, served with high-protein naan made with Greek yogurt.",
        "instructions": [
            "Brown ground lamb with onions and ginger-garlic",
            "Add spices and cook until fragrant",
            "Add tomatoes and peas, simmer until thick",
            "Make naan dough with flour, Greek yogurt, and eggs",
            "Cook naan on hot griddle or oven",
            "Garnish keema with fresh cilantro",
        ],
        "extendedIngredients": [
            {"name": "ground lamb", "amount": 800, "unit": "g", "aisle": "Meat"},
            {"name": "green peas", "amount": 200, "unit": "g", "aisle": "Frozen"},
            {"name": "onions", "amount": 2, "unit": "", "aisle": "Produce"},
            {"name": "tomatoes", "amount": 3, "unit": "", "aisle": "Produce"},
            {"name": "bread flour", "amount": 400, "unit": "g", "aisle": "Bakery"},
            {"name": "Greek yogurt", "amount": 200, "unit": "g", "aisle": "Dairy"},
            {"name": "eggs", "amount": 2, "unit": "", "aisle": "Dairy"},
            {"name": "garam masala", "amount": 2, "unit": "tbsp", "aisle": "Spices"},
        ],
    },
]


async def add_mock_data():
    """Add mock recipes and pantry ingredients"""
    # Create connection parameters
    connection_params = {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "database": settings.POSTGRES_DATABASE,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
    }

    db = PostgresService(connection_params)
    recipes_service = UserRecipesService(db)

    try:
        # Connect to database
        await db.connect()
        logger.info("Connected to database")

        # Demo user ID (using the one from .env)
        user_id = 111  # samantha-1 maps to user_id 111

        # First, add all ingredients to pantry
        logger.info("Adding ingredients to pantry...")

        # Collect all unique ingredients
        all_ingredients = {}
        for recipe in MOCK_RECIPES:
            for ingredient in recipe["extendedIngredients"]:
                key = ingredient["name"].lower()
                if key not in all_ingredients:
                    all_ingredients[key] = {
                        "name": ingredient["name"],
                        "amount": ingredient["amount"],
                        "unit": ingredient["unit"],
                        "aisle": ingredient.get("aisle", "Other"),
                    }
                # Accumulate quantities if ingredient appears in multiple recipes
                elif isinstance(all_ingredients[key]["amount"], (int, float)) and isinstance(
                    ingredient["amount"], (int, float)
                ):
                    all_ingredients[key]["amount"] += ingredient["amount"]

        # Add ingredients to pantry with expiration dates
        for _ingredient_key, ingredient_data in all_ingredients.items():
            # Set expiration dates based on food type
            if any(x in ingredient_data["aisle"].lower() for x in ["meat", "dairy", "produce"]):
                days_until_expiry = random.randint(7, 14)  # Perishables
            elif "frozen" in ingredient_data["aisle"].lower():
                days_until_expiry = random.randint(30, 60)  # Frozen items
            else:
                days_until_expiry = random.randint(60, 180)  # Pantry items

            expiration_date = datetime.now() + timedelta(days=days_until_expiry)

            # Format quantity based on unit
            if ingredient_data["unit"] == "":
                quantity_str = str(ingredient_data["amount"])
            else:
                quantity_str = f"{ingredient_data['amount']} {ingredient_data['unit']}"

            # Add to pantry
            query = """
                INSERT INTO pantry_items (user_id, product_name, quantity, expiration_date, category)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, product_name)
                DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    expiration_date = EXCLUDED.expiration_date,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            try:
                result = await db.fetch_one(
                    query,
                    user_id,
                    ingredient_data["name"],
                    quantity_str,
                    expiration_date,
                    ingredient_data["aisle"],
                )
                logger.info(
                    f"Added/Updated pantry item: {ingredient_data['name']} - {quantity_str}"
                )
            except Exception as e:
                logger.error(f"Error adding {ingredient_data['name']}: {e}")

        logger.info(f"Added {len(all_ingredients)} ingredients to pantry")

        # Now add the recipes to user's saved recipes
        logger.info("Adding recipes to user's saved recipes...")

        for recipe in MOCK_RECIPES:
            # Transform to match the expected format
            recipe_data = {
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe["image"],
                "readyInMinutes": recipe["readyInMinutes"],
                "servings": recipe["servings"],
                "summary": recipe["summary"],
                "instructions": recipe["instructions"],
                "extendedIngredients": recipe["extendedIngredients"],
                "cuisines": [recipe["cuisine"]],
                "dishTypes": ["main course"],
                "nutrition": {
                    "nutrients": [{"name": "Protein", "amount": recipe["protein"], "unit": "g"}]
                },
                # Mark all ingredients as available in pantry
                "usedIngredientCount": len(recipe["extendedIngredients"]),
                "missedIngredientCount": 0,
                "usedIngredients": recipe["extendedIngredients"],
                "missedIngredients": [],
            }

            # Save the recipe
            result = await recipes_service.save_recipe(
                user_id=user_id,
                recipe_id=recipe["id"],
                recipe_title=recipe["title"],
                recipe_image=recipe["image"],
                recipe_data=recipe_data,
                source="mock_data",
            )

            if result:
                logger.info(f"Saved recipe: {recipe['title']}")
            else:
                logger.info(f"Recipe already exists: {recipe['title']}")

        logger.info(f"Successfully added {len(MOCK_RECIPES)} recipes")

        # Verify pantry items
        pantry_query = """
            SELECT COUNT(*) as count FROM pantry_items WHERE user_id = $1
        """
        pantry_count = await db.fetch_one(pantry_query, user_id)
        logger.info(f"Total pantry items for user {user_id}: {pantry_count['count']}")

        # Verify saved recipes
        recipes_query = """
            SELECT COUNT(*) as count FROM user_recipes WHERE user_id = $1
        """
        recipes_count = await db.fetch_one(recipes_query, user_id)
        logger.info(f"Total saved recipes for user {user_id}: {recipes_count['count']}")

    except Exception as e:
        logger.error(f"Error adding mock data: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(add_mock_data())
