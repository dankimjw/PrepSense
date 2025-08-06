#!/usr/bin/env python3
"""
Fix existing saved recipes that have empty recipe_data
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def fix_existing_recipes():
    """Fix existing recipes with empty recipe_data"""
    print("Fixing existing recipes with empty recipe_data...")

    # Get database service
    db_service = get_database_service()

    try:
        # Get recipes with empty recipe_data
        query = """
            SELECT id, recipe_id, recipe_title, recipe_image, recipe_data, source
            FROM user_recipes
            WHERE user_id = 111 
            AND source = 'spoonacular'
            AND (recipe_data = '{}' OR recipe_data IS NULL)
        """

        recipes = db_service.execute_query(query)
        print(f"Found {len(recipes)} recipes to fix")

        for recipe in recipes:
            # Extract recipe ID from image URL if possible
            # Image URLs are like: https://img.spoonacular.com/recipes/633594-556x370.jpg
            image_url = recipe.get("recipe_image", "")
            external_recipe_id = None

            if "spoonacular.com/recipes/" in image_url:
                try:
                    # Extract ID from URL
                    parts = image_url.split("/recipes/")[1].split("-")[0]
                    external_recipe_id = int(parts)
                    print(f"Extracted recipe ID {external_recipe_id} from image URL")
                except:
                    print(f"Could not extract recipe ID from URL: {image_url}")

            if external_recipe_id:
                # Create minimal recipe_data with external_recipe_id
                recipe_data = {
                    "id": external_recipe_id,
                    "external_recipe_id": external_recipe_id,
                    "title": recipe["recipe_title"],
                    "image": recipe["recipe_image"],
                }

                # Update the recipe
                update_query = """
                    UPDATE user_recipes
                    SET recipe_data = %(recipe_data)s
                    WHERE id = %(id)s
                """

                db_service.execute_query(
                    update_query, {"recipe_data": json.dumps(recipe_data), "id": recipe["id"]}
                )

                print(f"✅ Fixed recipe {recipe['id']}: {recipe['recipe_title']}")
            else:
                print(
                    f"❌ Could not fix recipe {recipe['id']}: {recipe['recipe_title']} - no recipe ID found"
                )

        print("\n✅ Done fixing existing recipes!")

    except Exception as e:
        print(f"❌ Error fixing recipes: {e}")


if __name__ == "__main__":
    fix_existing_recipes()
