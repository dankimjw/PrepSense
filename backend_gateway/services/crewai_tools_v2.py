"""Custom tools for CrewAI agents - Version 2 using functional approach"""

from typing import List, Dict, Any
from crewai.tools.agent_tools import Tool
import logging
import json

logger = logging.getLogger(__name__)


def create_pantry_tool(db_service):
    """Create a tool for fetching pantry items"""
    
    def fetch_pantry_items(user_id: int) -> str:
        """Fetch pantry items for the user"""
        logger.info(f"Fetching pantry items for user {user_id}")
        
        query = """
        SELECT 
            pi.pantry_item_id,
            pi.product_name,
            pi.brand_name,
            pi.category,
            pi.quantity,
            pi.unit_of_measurement,
            pi.expiration_date,
            pi.status,
            CASE 
                WHEN expiration_date <= CURRENT_DATE THEN 'expired'
                WHEN expiration_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'expiring_soon'
                ELSE 'fresh'
            END as freshness_status
        FROM pantry_items pi
        WHERE pi.pantry_id = (
            SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s LIMIT 1
        )
        AND pi.status = 'available'
        ORDER BY pi.expiration_date ASC
        """
        
        try:
            results = db_service.execute_query(query, {"user_id": user_id})
            logger.info(f"Found {len(results)} pantry items")
            return json.dumps(results, default=str)
        except Exception as e:
            logger.error(f"Error fetching pantry items: {str(e)}")
            return json.dumps([])
    
    return Tool(
        name="fetch_pantry_items",
        func=fetch_pantry_items,
        description="Fetches current pantry items for a user from PostgreSQL database. Input: user_id (integer)"
    )


def create_preferences_tool(db_service):
    """Create a tool for fetching user preferences"""
    
    def fetch_user_preferences(user_id: int) -> str:
        """Fetch user preferences"""
        logger.info(f"Fetching preferences for user {user_id}")
        
        try:
            # Get dietary preferences
            dietary_query = """
            SELECT preference FROM user_dietary_preferences 
            WHERE user_id = %(user_id)s
            """
            dietary_results = db_service.execute_query(dietary_query, {"user_id": user_id})
            dietary_prefs = [row['preference'] for row in dietary_results]
            
            # Get allergens
            allergen_query = """
            SELECT allergen FROM user_allergens 
            WHERE user_id = %(user_id)s
            """
            allergen_results = db_service.execute_query(allergen_query, {"user_id": user_id})
            allergens = [row['allergen'] for row in allergen_results]
            
            # Get cuisine preferences
            cuisine_query = """
            SELECT cuisine FROM user_cuisine_preferences 
            WHERE user_id = %(user_id)s
            """
            cuisine_results = db_service.execute_query(cuisine_query, {"user_id": user_id})
            cuisines = [row['cuisine'] for row in cuisine_results]
            
            preferences = {
                'dietary_restrictions': dietary_prefs,
                'allergens': allergens,
                'cuisine_preferences': cuisines
            }
            
            return json.dumps(preferences)
        except Exception as e:
            logger.error(f"Error fetching preferences: {str(e)}")
            return json.dumps({
                'dietary_restrictions': [],
                'allergens': [],
                'cuisine_preferences': []
            })
    
    return Tool(
        name="fetch_user_preferences",
        func=fetch_user_preferences,
        description="Fetches dietary restrictions, allergens, and cuisine preferences for a user. Input: user_id (integer)"
    )


def create_spoonacular_tool(spoonacular_service):
    """Create a tool for fetching recipes from Spoonacular"""
    
    def search_spoonacular_recipes(ingredients: str, dietary_restrictions: str = "", allergens: str = "", number: int = 3) -> str:
        """Search for recipes from Spoonacular"""
        logger.info(f"Searching Spoonacular for recipes with ingredients: {ingredients}")
        
        try:
            # Parse inputs
            ingredient_list = [i.strip() for i in ingredients.split(',')]
            diet_list = [d.strip() for d in dietary_restrictions.split(',')] if dietary_restrictions else []
            allergen_list = [a.strip() for a in allergens.split(',')] if allergens else []
            
            # Map allergens to intolerances
            intolerances = []
            allergen_mapping = {
                'dairy': 'dairy',
                'eggs': 'egg',
                'gluten': 'gluten',
                'nuts': 'tree nut',
                'peanuts': 'peanut',
                'soy': 'soy',
                'shellfish': 'shellfish'
            }
            
            for allergen in allergen_list:
                if allergen.lower() in allergen_mapping:
                    intolerances.append(allergen_mapping[allergen.lower()])
            
            # Search for recipes
            import asyncio
            recipes = asyncio.run(spoonacular_service.search_recipes_by_ingredients(
                ingredients=ingredient_list,
                number=number,
                diet=','.join(diet_list) if diet_list else None,
                intolerances=','.join(intolerances) if intolerances else None
            ))
            
            # Get full details for each recipe
            detailed_recipes = []
            for recipe in recipes:
                try:
                    details = asyncio.run(spoonacular_service.get_recipe_details(
                        recipe_id=recipe['id'],
                        include_nutrition=True
                    ))
                    detailed_recipes.append(details)
                except Exception as e:
                    logger.error(f"Error getting recipe details: {str(e)}")
            
            return json.dumps(detailed_recipes, default=str)
            
        except Exception as e:
            logger.error(f"Error fetching Spoonacular recipes: {str(e)}")
            return json.dumps([])
    
    return Tool(
        name="search_spoonacular_recipes",
        func=search_spoonacular_recipes,
        description="Search for recipes from Spoonacular API. Inputs: ingredients (comma-separated string), dietary_restrictions (optional, comma-separated), allergens (optional, comma-separated), number (optional, default 3)"
    )


def create_openai_recipe_tool():
    """Create a tool for generating recipes with OpenAI"""
    
    def generate_openai_recipes(ingredients: str, expiring_items: str = "", dietary_restrictions: str = "", 
                               allergens: str = "", cuisine_preferences: str = "", number: int = 2) -> str:
        """Generate recipes using OpenAI"""
        import openai
        from backend_gateway.core.config_utils import get_openai_api_key
        
        logger.info(f"Generating {number} recipes with OpenAI")
        
        # Parse inputs
        ingredient_list = [i.strip() for i in ingredients.split(',')]
        expiring_list = [e.strip() for e in expiring_items.split(',')] if expiring_items else []
        diet_list = [d.strip() for d in dietary_restrictions.split(',')] if dietary_restrictions else []
        allergen_list = [a.strip() for a in allergens.split(',')] if allergens else []
        cuisine_list = [c.strip() for c in cuisine_preferences.split(',')] if cuisine_preferences else []
        
        prompt = f"""
        Create {number} different recipes using ONLY these available ingredients:
        {', '.join(ingredient_list)}
        
        {"PRIORITY: Use these expiring items: " + ', '.join(expiring_list) if expiring_list else ""}
        
        Requirements:
        - Dietary restrictions: {', '.join(diet_list) if diet_list else 'None'}
        - Must NOT contain: {', '.join(allergen_list) if allergen_list else 'None'}
        - Preferred cuisines: {', '.join(cuisine_list) if cuisine_list else 'Any'}
        
        Return a JSON array where each recipe has:
        - name: string
        - ingredients: array of strings with quantities
        - instructions: array of detailed steps
        - readyInMinutes: number
        - cuisineType: string
        - dietaryTags: array
        - nutrition: object with calories and protein per serving
        
        Only use ingredients from the provided list. Be creative but realistic.
        """
        
        try:
            client = openai.OpenAI(api_key=get_openai_api_key())
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative chef who generates recipes in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            recipes_text = response.choices[0].message.content.strip()
            if recipes_text.startswith('```'):
                recipes_text = recipes_text.split('```')[1]
                if recipes_text.startswith('json'):
                    recipes_text = recipes_text[4:]
                recipes_text = recipes_text.rstrip('```')
            
            recipes = json.loads(recipes_text)
            logger.info(f"Generated {len(recipes)} recipes")
            return json.dumps(recipes)
            
        except Exception as e:
            logger.error(f"Error generating OpenAI recipes: {str(e)}")
            return json.dumps([])
    
    return Tool(
        name="generate_openai_recipes",
        func=generate_openai_recipes,
        description="Generate creative recipes using OpenAI. Inputs: ingredients (comma-separated), expiring_items (optional), dietary_restrictions (optional), allergens (optional), cuisine_preferences (optional), number (optional, default 2)"
    )


def create_preference_analyzer_tool(preference_service):
    """Create a tool for analyzing user preferences"""
    
    def analyze_preferences(user_id: int) -> str:
        """Analyze user preferences from recipe history"""
        logger.info(f"Analyzing preferences for user {user_id}")
        
        try:
            analysis = preference_service.analyze_user_preferences(user_id)
            return json.dumps(analysis.get('insights', {}), default=str)
        except Exception as e:
            logger.error(f"Error analyzing preferences: {str(e)}")
            return json.dumps({})
    
    return Tool(
        name="analyze_preferences",
        func=analyze_preferences,
        description="Analyze user's recipe preferences based on their saved recipes and ratings. Input: user_id (integer)"
    )


def create_recipe_ranker_tool():
    """Create a tool for ranking recipes"""
    
    def rank_recipes(recipes_json: str, user_preferences_json: str = "{}", user_insights_json: str = "{}", pantry_items_json: str = "[]") -> str:
        """Rank recipes based on multiple factors. 
        
        Args:
            recipes_json: JSON string containing list of recipes to rank
            user_preferences_json: Optional JSON string with user preferences (default: empty object)
            user_insights_json: Optional JSON string with user insights (default: empty object)
            pantry_items_json: Optional JSON string with pantry items (default: empty list)
        """
        logger.info("Ranking recipes")
        
        try:
            # Parse JSON inputs with defaults
            recipes = json.loads(recipes_json) if isinstance(recipes_json, str) else recipes_json
            user_preferences = json.loads(user_preferences_json) if user_preferences_json else {}
            user_insights = json.loads(user_insights_json) if user_insights_json else {}
            pantry_items = json.loads(pantry_items_json) if pantry_items_json else []
            
            # Create pantry ingredient set
            pantry_ingredients = set()
            for item in pantry_items:
                if item.get('product_name'):
                    pantry_ingredients.add(item['product_name'].lower())
            
            # Score each recipe
            for recipe in recipes:
                score = 0.0
                
                # Pantry match score (40%)
                if 'ingredients' in recipe:
                    recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
                    matches = sum(1 for ing in recipe_ingredients if any(p in ing for p in pantry_ingredients))
                    match_ratio = matches / len(recipe_ingredients) if recipe_ingredients else 0
                    score += match_ratio * 0.4
                
                # User preference match (30%)
                cuisine_match = recipe.get('cuisineType', '').lower() in [c.lower() for c in user_preferences.get('cuisine_preferences', [])]
                if cuisine_match:
                    score += 0.3
                
                # Historical preference match (20%)
                favorite_ingredients = user_insights.get('favorite_ingredients', [])
                if favorite_ingredients and 'ingredients' in recipe:
                    recipe_ingredients = recipe.get('ingredients', [])
                    matches = sum(1 for ing in favorite_ingredients if any(ing.lower() in r.lower() for r in recipe_ingredients))
                    score += (matches / len(favorite_ingredients)) * 0.2 if favorite_ingredients else 0
                
                # Dietary compliance (10%)
                dietary_prefs = user_preferences.get('dietary_restrictions', [])
                if dietary_prefs and recipe.get('dietaryTags'):
                    if any(diet in recipe['dietaryTags'] for diet in dietary_prefs):
                        score += 0.1
                
                recipe['final_score'] = score
            
            # Sort by score
            ranked = sorted(recipes, key=lambda r: r.get('final_score', 0), reverse=True)
            
            logger.info(f"Ranking complete. Top recipe: {ranked[0]['name'] if ranked else 'None'}")
            return json.dumps(ranked, default=str)
            
        except Exception as e:
            logger.error(f"Error ranking recipes: {str(e)}")
            return json.dumps([])
    
    return Tool(
        name="rank_recipes",
        func=rank_recipes,
        description="Rank recipes based on pantry match, user preferences, and historical data. Inputs: recipes_json (JSON string), user_preferences_json (JSON string), user_insights_json (JSON string), pantry_items_json (JSON string)"
    )