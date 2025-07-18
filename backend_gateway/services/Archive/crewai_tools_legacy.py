"""Legacy tools for CrewAI 0.1.32 - simplified implementation"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
import logging
import os
import openai

logger = logging.getLogger(__name__)


def create_pantry_tool(db_service):
    """Create a tool that fetches pantry items"""
    
    def fetch_pantry_items(user_id: str) -> str:
        """Fetch pantry items for the user"""
        try:
            user_id_int = int(user_id)
            query = """
            SELECT 
                pi.product_name,
                pi.category,
                pi.quantity,
                pi.unit_of_measurement,
                pi.expiration_date,
                CASE 
                    WHEN expiration_date <= CURRENT_DATE THEN 'expired'
                    WHEN expiration_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'expiring_soon'
                    ELSE 'fresh'
                END as freshness_status
            FROM pantry_items pi
            WHERE pi.pantry_id IN (
                SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s
            )
            AND pi.status = 'available'
            ORDER BY pi.expiration_date ASC
            """
            
            items = db_service.execute_query(query, {"user_id": user_id_int})
            
            # Format as readable text
            if not items:
                return "No pantry items found"
            
            expiring = [i for i in items if i.get('freshness_status') == 'expiring_soon']
            fresh = [i for i in items if i.get('freshness_status') == 'fresh']
            
            result = f"Found {len(items)} pantry items:\n"
            if expiring:
                result += f"\nExpiring Soon ({len(expiring)} items):\n"
                for item in expiring[:5]:
                    result += f"- {item['product_name']} ({item['quantity']} {item['unit_of_measurement']})\n"
            
            result += f"\nFresh Items ({len(fresh)} items):\n"
            for item in fresh[:10]:
                result += f"- {item['product_name']} ({item['quantity']} {item['unit_of_measurement']})\n"
            
            return result
        except Exception as e:
            logger.error(f"Error fetching pantry: {e}")
            return f"Error fetching pantry items: {str(e)}"
    
    return Tool(
        name="fetch_pantry_items",
        func=fetch_pantry_items,
        description="Fetch current pantry items for a user. Input should be the user_id as a string."
    )


def create_preferences_tool(db_service):
    """Create a tool that fetches user preferences"""
    
    def fetch_preferences(user_id: str) -> str:
        """Fetch user preferences and dietary restrictions"""
        try:
            user_id_int = int(user_id)
            
            # Get dietary preferences
            dietary_query = """
            SELECT preference FROM user_dietary_preferences 
            WHERE user_id = %(user_id)s
            """
            dietary_results = db_service.execute_query(dietary_query, {"user_id": user_id_int})
            dietary_prefs = [row['preference'] for row in dietary_results]
            
            # Get allergens
            allergen_query = """
            SELECT allergen FROM user_allergens 
            WHERE user_id = %(user_id)s
            """
            allergen_results = db_service.execute_query(allergen_query, {"user_id": user_id_int})
            allergens = [row['allergen'] for row in allergen_results]
            
            # Get cuisine preferences
            cuisine_query = """
            SELECT cuisine FROM user_cuisine_preferences 
            WHERE user_id = %(user_id)s
            """
            cuisine_results = db_service.execute_query(cuisine_query, {"user_id": user_id_int})
            cuisines = [row['cuisine'] for row in cuisine_results]
            
            result = "User Preferences:\n"
            
            if dietary_prefs:
                result += f"Dietary Restrictions: {', '.join(dietary_prefs)}\n"
            else:
                result += "Dietary Restrictions: None\n"
                
            if allergens:
                result += f"Allergens: {', '.join(allergens)}\n"
            else:
                result += "Allergens: None\n"
                
            if cuisines:
                result += f"Cuisine Preferences: {', '.join(cuisines)}\n"
            else:
                result += "Cuisine Preferences: None specified\n"
            
            # Return both formatted text and structured data for other tools
            import json
            preferences_json = json.dumps({
                'allergens': allergens, 
                'dietary_restrictions': dietary_prefs
            })
            return result + f"\n[JSON]{preferences_json}[/JSON]"
            
        except Exception as e:
            logger.error(f"Error fetching preferences: {e}")
            return f"Error fetching preferences: {str(e)}"
    
    return Tool(
        name="fetch_preferences",
        func=fetch_preferences,
        description="Fetch user dietary preferences and allergens. Input should be the user_id as a string."
    )


def create_saved_recipes_tool(user_recipes_service):
    """Create a tool that fetches saved recipes"""
    
    async def fetch_saved_recipes(user_id_and_pantry: str) -> str:
        """Fetch saved recipes that match pantry items"""
        try:
            # Parse input (expecting "user_id|pantry_items")
            parts = user_id_and_pantry.split("|", 1)
            if len(parts) != 2:
                return "Invalid input format. Expected: 'user_id|pantry_items'"
            
            user_id = int(parts[0])
            # For simplicity, just get all saved recipes
            recipes = await user_recipes_service.get_user_recipes(user_id)
            
            if not recipes:
                return "No saved recipes found"
            
            result = f"Found {len(recipes)} saved recipes:\n\n"
            for i, recipe in enumerate(recipes[:5], 1):
                result += f"{i}. {recipe.get('name', 'Unknown')}\n"
                result += f"   Cuisine: {recipe.get('cuisine_type', 'Unknown')}\n"
                if recipe.get('user_rating'):
                    result += f"   Your Rating: {recipe['user_rating']}\n"
                result += "\n"
            
            return result
        except Exception as e:
            logger.error(f"Error fetching saved recipes: {e}")
            return f"Error fetching saved recipes: {str(e)}"
    
    # Note: This is a sync wrapper for the async function
    import asyncio
    
    def sync_wrapper(user_id_and_pantry: str) -> str:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(fetch_saved_recipes(user_id_and_pantry))
        finally:
            loop.close()
    
    return Tool(
        name="fetch_saved_recipes",
        func=sync_wrapper,
        description="Fetch user's saved recipes. Input format: 'user_id|pantry_items'"
    )


def create_openai_recipe_tool():
    """Create a tool that generates recipes using OpenAI"""
    
    def generate_recipe(ingredients: str) -> str:
        """Generate a recipe using OpenAI based on ingredients"""
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""Create a practical, well-known recipe using these ingredients: {ingredients}

Requirements:
- Use common cooking techniques
- Create familiar dishes that people actually cook
- Include clear measurements
- Provide step-by-step instructions
- Keep it simple and realistic

Format:
Recipe Name: [name]
Cooking Time: [time]
Ingredients:
- [list ingredients with amounts]
Instructions:
1. [step by step]"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a practical home chef who creates simple, delicious recipes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return f"Error generating recipe: {str(e)}"
    
    return Tool(
        name="generate_recipe",
        func=generate_recipe,
        description="Generate a practical recipe using OpenAI. Input should be a list of ingredients."
    )


def create_recipe_ranker_tool():
    """Create a tool that ranks recipes with allergen filtering"""
    
    def rank_recipes(recipes_and_preferences_json: str) -> str:
        """Rank recipes based on various factors including allergen filtering"""
        try:
            import json
            data = json.loads(recipes_and_preferences_json)
            
            # Extract recipes and preferences
            if isinstance(data, list):
                # Legacy format - just recipes
                recipes = data
                user_allergens = []
                dietary_restrictions = []
            else:
                # New format with preferences
                recipes = data.get('recipes', [])
                preferences = data.get('preferences', {})
                user_allergens = preferences.get('allergens', [])
                dietary_restrictions = preferences.get('dietary_restrictions', [])
            
            # Convert allergens to lowercase for comparison
            user_allergens_lower = [a.lower() for a in user_allergens]
            
            # Filter and score recipes
            safe_recipes = []
            excluded_recipes = []
            
            for recipe in recipes:
                # Check for allergens
                recipe_allergens = recipe.get('allergens_present', [])
                recipe_ingredients = recipe.get('ingredients', [])
                
                # Check if recipe contains any user allergens
                contains_allergen = False
                allergen_found = None
                
                # Check explicit allergens
                for allergen in recipe_allergens:
                    if allergen.lower() in user_allergens_lower:
                        contains_allergen = True
                        allergen_found = allergen
                        break
                
                # Also check ingredients for allergen keywords
                if not contains_allergen:
                    for ingredient in recipe_ingredients:
                        ingredient_lower = ingredient.lower()
                        for user_allergen in user_allergens_lower:
                            if user_allergen in ingredient_lower:
                                contains_allergen = True
                                allergen_found = user_allergen
                                break
                        if contains_allergen:
                            break
                
                # If recipe contains allergens, exclude it
                if contains_allergen:
                    excluded_recipes.append({
                        'name': recipe.get('name', 'Unknown'),
                        'reason': f'Contains {allergen_found}'
                    })
                    continue
                
                # Score the recipe
                score = 50  # Base score
                
                # Bonus for saved recipes
                if recipe.get('source') == 'saved':
                    score += 20
                    if recipe.get('user_rating') == 'thumbs_up':
                        score += 25
                    elif recipe.get('is_favorite'):
                        score += 30
                
                # Bonus for fewer missing ingredients
                missing = len(recipe.get('missing_ingredients', []))
                if missing == 0:
                    score += 30
                elif missing <= 2:
                    score += 20
                elif missing <= 5:
                    score += 10
                
                # Bonus for matching dietary preferences
                if recipe.get('dietary_tags'):
                    for tag in recipe['dietary_tags']:
                        if tag.lower() in [dr.lower() for dr in dietary_restrictions]:
                            score += 15
                
                # Penalty for long cooking time
                cook_time = recipe.get('time', 0)
                if cook_time > 60:
                    score -= 10
                elif cook_time > 90:
                    score -= 20
                
                recipe['score'] = score
                safe_recipes.append(recipe)
            
            # Sort by score
            safe_recipes.sort(key=lambda x: x['score'], reverse=True)
            
            result = "Recipe Rankings:\n\n"
            
            if user_allergens:
                result += f"User Allergens: {', '.join(user_allergens)}\n"
                result += f"Excluded {len(excluded_recipes)} recipes containing allergens\n\n"
            
            if not safe_recipes:
                result += "No safe recipes found after allergen filtering!\n"
                if excluded_recipes:
                    result += "\nExcluded recipes:\n"
                    for exc in excluded_recipes[:5]:
                        result += f"- {exc['name']} ({exc['reason']})\n"
            else:
                result += f"Safe Recipes ({len(safe_recipes)} found):\n\n"
                for i, recipe in enumerate(safe_recipes[:5], 1):
                    result += f"{i}. {recipe.get('name', 'Unknown')} (Score: {recipe['score']})\n"
                    result += f"   Source: {recipe.get('source', 'unknown')}\n"
                    if recipe.get('missing_ingredients'):
                        result += f"   Missing: {len(recipe['missing_ingredients'])} ingredients\n"
                    if recipe.get('time'):
                        result += f"   Time: {recipe['time']} minutes\n"
                    result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error ranking recipes: {e}")
            return f"Error ranking recipes: {str(e)}"
    
    return Tool(
        name="rank_recipes",
        func=rank_recipes,
        description="Rank recipes based on match score and user preferences, filtering out allergens. Input should be JSON with recipes and preferences."
    )