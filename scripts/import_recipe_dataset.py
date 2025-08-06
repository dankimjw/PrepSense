#!/usr/bin/env python3
"""
Import Kaggle recipe dataset into PostgreSQL database
Matches images with our selected 256 recipes and uploads to GCS
"""

import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from google.cloud import storage
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "sslmode": "require",
}

# GCS configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "prepsense_recipe_images")
DATASET_PATH = "/Users/danielkim/_Capstone/PrepSense/Food Data/kaggle-recipes-with-images"
SELECTED_RECIPES_PATH = (
    "/Users/danielkim/_Capstone/PrepSense/Food Data/recipe-dataset-main/final_256_recipes.json"
)


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def initialize_gcs_client():
    """Initialize Google Cloud Storage client"""
    # Skip GCS for now - store images locally
    print("Images will be stored locally")
    return None, None


def clean_filename(name: str) -> str:
    """Convert recipe title to filename format"""
    # Remove special characters and convert to lowercase
    clean = re.sub(r"[^\w\s-]", "", name.lower())
    # Replace spaces with hyphens
    clean = re.sub(r"[-\s]+", "-", clean)
    return clean.strip("-")


def find_matching_image(title: str, image_dir: Path) -> Optional[str]:
    """Find image file matching recipe title"""
    clean_title = clean_filename(title)

    # Try exact match first
    for img_file in image_dir.glob("*.jpg"):
        if clean_title in str(img_file).lower():
            return str(img_file)

    # Try partial match (first 20 chars)
    title_start = clean_title[:20]
    for img_file in image_dir.glob("*.jpg"):
        if title_start in str(img_file).lower():
            return str(img_file)

    return None


def upload_to_gcs(bucket, local_path: str, gcs_path: str) -> str:
    """Upload image to Google Cloud Storage"""
    if not bucket:
        return f"local://{local_path}"

    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        # Make publicly accessible
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return f"local://{local_path}"


def categorize_recipe(recipe: Dict) -> Dict:
    """Categorize recipe by meal type, cuisine, and dietary restrictions"""
    title = recipe["title"].lower()
    ingredients = recipe["ingredients"].lower()

    # Meal type detection
    meal_type = "dinner"  # default
    if any(
        word in title or word in ingredients
        for word in ["breakfast", "pancake", "waffle", "oatmeal", "toast", "muffin"]
    ):
        meal_type = "breakfast"
    elif any(
        word in title or word in ingredients
        for word in ["lunch", "sandwich", "salad", "soup", "wrap"]
    ):
        meal_type = "lunch"

    # Dietary detection
    dietary_tags = []
    if "vegan" in title or "vegan" in ingredients:
        dietary_tags.append("vegan")
    elif "vegetarian" in title or "vegetarian" in ingredients:
        dietary_tags.append("vegetarian")
    if "gluten-free" in title or "gluten free" in title:
        dietary_tags.append("gluten-free")
    if "dairy-free" in title or "dairy free" in title:
        dietary_tags.append("dairy-free")
    if "keto" in title or "low-carb" in title:
        dietary_tags.append("keto")

    # Allergen detection
    allergens = []
    if any(word in ingredients for word in ["milk", "cheese", "butter", "cream", "yogurt"]):
        allergens.append("dairy")
    if any(word in ingredients for word in ["nuts", "almond", "walnut", "pecan", "cashew"]):
        allergens.append("nuts")
    if any(word in ingredients for word in ["shrimp", "crab", "lobster", "shellfish"]):
        allergens.append("shellfish")
    if "egg" in ingredients:
        allergens.append("eggs")
    if any(word in ingredients for word in ["flour", "bread", "pasta", "wheat"]):
        allergens.append("gluten")
    if any(word in ingredients for word in ["soy sauce", "tofu", "tempeh", "miso"]):
        allergens.append("soy")

    return {"meal_type": meal_type, "dietary_tags": dietary_tags, "allergens": allergens}


def process_ingredients(ingredients_str: str) -> List[Dict]:
    """Parse ingredients string into structured format"""
    try:
        # Try to parse as Python list
        ingredients_list = eval(ingredients_str)
        if isinstance(ingredients_list, list):
            return [{"name": ing, "amount": "", "unit": ""} for ing in ingredients_list]
    except:
        # Fallback: split by common delimiters
        ingredients = re.split(r"[,;]\s*", ingredients_str)
        return [
            {"name": ing.strip(), "amount": "", "unit": ""} for ing in ingredients if ing.strip()
        ]


def import_recipes():
    """Import selected recipes with images into database"""
    # Load selected recipes
    with open(SELECTED_RECIPES_PATH, "r") as f:
        selected_recipes = json.load(f)

    print(f"Loading {len(selected_recipes)} selected recipes...")

    # Initialize GCS
    _, bucket = initialize_gcs_client()

    # Connect to database
    conn = get_connection()
    cur = conn.cursor()

    # Image directory
    image_dir = Path(DATASET_PATH) / "Food Images" / "Food Images"

    # Create local image directory if needed
    local_image_dir = Path(
        "/Users/danielkim/_Capstone/PrepSense/backend_gateway/static/recipe_images"
    )
    local_image_dir.mkdir(parents=True, exist_ok=True)

    imported_count = 0

    try:
        # Start recipe ID from 10001 to avoid conflicts
        recipe_id = 10001

        for i, recipe in enumerate(selected_recipes):
            # Find matching image
            image_path = find_matching_image(recipe["title"], image_dir)
            image_url = None

            if image_path:
                # Copy to local directory
                local_filename = f"recipe_{recipe_id}.jpg"
                local_path = local_image_dir / local_filename
                shutil.copy2(image_path, local_path)

                # Upload to GCS if available
                if bucket:
                    gcs_path = f"recipes/{local_filename}"
                    image_url = upload_to_gcs(bucket, str(local_path), gcs_path)
                else:
                    image_url = f"/static/recipe_images/{local_filename}"

                print(f"✓ Found image for: {recipe['title'][:50]}...")
            else:
                print(f"✗ No image for: {recipe['title'][:50]}...")

            # Categorize recipe
            categories = categorize_recipe(recipe)

            # Process ingredients
            ingredients_data = process_ingredients(recipe["ingredients"])

            # Prepare recipe data
            recipe_data = {
                "id": recipe_id,
                "title": recipe["title"],
                "image": image_url
                or f"https://via.placeholder.com/400x300?text={recipe['title'][:20]}",
                "imageType": "jpg",
                "servings": 4,
                "readyInMinutes": 45,
                "instructions": recipe["instructions"],
                "cuisines": [recipe["cuisine"]],
                "dishTypes": [categories["meal_type"]],
                "diets": categories["dietary_tags"],
                "extendedIngredients": ingredients_data,
                "nutrition": {
                    "nutrients": [
                        {"name": "Calories", "amount": 350, "unit": "kcal"},
                        {"name": "Protein", "amount": 25, "unit": "g"},
                        {"name": "Carbohydrates", "amount": 40, "unit": "g"},
                        {"name": "Fat", "amount": 12, "unit": "g"},
                    ]
                },
                "analyzedInstructions": [
                    {
                        "steps": [
                            {"step": step.strip()}
                            for step in recipe["instructions"].split(".")
                            if step.strip()
                        ]
                    }
                ],
                "allergens": categories["allergens"],
                "sourceUrl": "https://www.epicurious.com",
                "creditsText": "Epicurious",
            }

            # First check if recipe already exists
            cur.execute(
                """
                SELECT id FROM user_recipes 
                WHERE user_id = %s AND recipe_id = %s
            """,
                (111, recipe_id),
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
                    (recipe["title"], image_url, json.dumps(recipe_data), existing["id"]),
                )
            else:
                # Insert new recipe
                cur.execute(
                    """
                    INSERT INTO user_recipes (
                        user_id, recipe_id, recipe_title, recipe_image, 
                        recipe_data, source, rating, is_favorite, created_at, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        111,  # User ID 111
                        recipe_id,
                        recipe["title"],
                        image_url,
                        json.dumps(recipe_data),
                        "kaggle_dataset",
                        "neutral",
                        False,
                        datetime.now(),
                        "saved",  # status field - must be 'saved' or 'cooked'
                    ),
                )

            imported_count += 1
            recipe_id += 1

            # Progress update
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(selected_recipes)} recipes imported...")
                conn.commit()

        # Final commit
        conn.commit()
        print(f"\n✅ Successfully imported {imported_count} recipes!")

        # Verify import
        cur.execute(
            """
            SELECT COUNT(*) as count 
            FROM user_recipes 
            WHERE user_id = 111 AND source = 'kaggle_dataset'
        """
        )
        result = cur.fetchone()
        print(f"Verified: {result['count']} recipes in database for user 111")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("🍳 Recipe Dataset Import Tool")
    print("=" * 50)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Selected recipes: {SELECTED_RECIPES_PATH}")
    print(f"Database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
    print()

    # Check for --auto flag
    import sys

    if "--auto" in sys.argv:
        print("Running in auto mode...")
        import_recipes()
    else:
        # Confirm before proceeding
        response = input("Import 256 recipes with images to database? (y/n): ")
        if response.lower() == "y":
            import_recipes()
        else:
            print("Import cancelled.")
