"""Custom tools for CrewAI agents"""

from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class PostgresPantryToolInput(BaseModel):
    user_id: int = Field(..., description="The user ID for whom to fetch pantry items")


class PostgresPantryTool(BaseTool):
    """Fetches pantry items from PostgreSQL"""
    name: str = "PostgresPantryTool"
    description: str = "Fetches current pantry items for a user from PostgreSQL database"
    args_schema: Type[BaseModel] = PostgresPantryToolInput
    db_service: Any = None
    
    def __init__(self, db_service):
        super().__init__()
        self.db_service = db_service

    def _run(self, user_id: int) -> List[Dict[str, Any]]:
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
        AND pi.status = 'active'
        ORDER BY pi.expiration_date ASC
        """
        
        try:
            results = self.db_service.execute_query(query, {"user_id": user_id})
            logger.info(f"Found {len(results)} pantry items")
            return results
        except Exception as e:
            logger.error(f"Error fetching pantry items: {str(e)}")
            return []


class UserPreferencesToolInput(BaseModel):
    user_id: int = Field(..., description="The user ID for whom to fetch preferences")


class UserPreferencesTool(BaseTool):
    """Fetches user dietary preferences and allergens"""
    name: str = "UserPreferencesTool"
    description: str = "Fetches dietary restrictions, allergens, and cuisine preferences for a user"
    args_schema: Type[BaseModel] = UserPreferencesToolInput
    db_service: Any = None
    
    def __init__(self, db_service):
        super().__init__()
        self.db_service = db_service

    def _run(self, user_id: int) -> Dict[str, Any]:
        """Fetch user preferences"""
        logger.info(f"Fetching preferences for user {user_id}")
        
        query = """
        SELECT 
            preferences
        FROM user_preferences
        WHERE user_id = %(user_id)s
        LIMIT 1
        """
        
        try:
            results = self.db_service.execute_query(query, {"user_id": user_id})
            if results and results[0].get('preferences'):
                prefs = results[0]['preferences']
                return {
                    'dietary_restrictions': prefs.get('dietary_restrictions', []),
                    'allergens': prefs.get('allergens', []),
                    'cuisine_preferences': prefs.get('cuisine_preferences', [])
                }
            return {
                'dietary_restrictions': [],
                'allergens': [],
                'cuisine_preferences': []
            }
        except Exception as e:
            logger.error(f"Error fetching preferences: {str(e)}")
            return {
                'dietary_restrictions': [],
                'allergens': [],
                'cuisine_preferences': []
            }


class SavedRecipeMatchToolInput(BaseModel):
    user_id: int = Field(..., description="The user ID")
    pantry_items: List[Dict[str, Any]] = Field(..., description="Current pantry items")


class SavedRecipeMatchTool(BaseTool):
    """Matches saved recipes with current pantry"""
    name: str = "SavedRecipeMatchTool"
    description: str = "Finds user's saved recipes that can be made with current pantry items"
    args_schema: Type[BaseModel] = SavedRecipeMatchToolInput
    user_recipes_service: Any = None
    
    def __init__(self, user_recipes_service):
        super().__init__()
        self.user_recipes_service = user_recipes_service

    def _run(self, user_id: int, pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match saved recipes with pantry"""
        logger.info(f"Matching saved recipes for user {user_id}")
        
        try:
            matched_recipes = self.user_recipes_service.match_recipes_with_pantry(
                user_id=user_id,
                pantry_items=pantry_items,
                limit=10
            )
            
            # Filter to get top matches
            high_match_recipes = [
                recipe for recipe in matched_recipes 
                if recipe['match_score'] > 0.5 or recipe['can_make']
            ]
            
            logger.info(f"Found {len(high_match_recipes)} matching saved recipes")
            return high_match_recipes[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error matching recipes: {str(e)}")
            return []


class SpoonacularRecipeToolInput(BaseModel):
    ingredients: List[str] = Field(..., description="List of available ingredients")
    number: int = Field(default=2, description="Number of recipes to fetch")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    exclude_allergens: List[str] = Field(default=[], description="Allergens to exclude")


class SpoonacularRecipeTool(BaseTool):
    """Fetches recipes from Spoonacular API"""
    name: str = "SpoonacularRecipeTool"
    description: str = "Fetches recipes from Spoonacular API based on available ingredients"
    args_schema: Type[BaseModel] = SpoonacularRecipeToolInput
    spoonacular_service: Any = None
    
    def __init__(self, spoonacular_service):
        super().__init__()
        self.spoonacular_service = spoonacular_service

    def _run(self, ingredients: List[str], number: int = 2, 
             dietary_restrictions: List[str] = [], 
             exclude_allergens: List[str] = []) -> List[Dict[str, Any]]:
        """Fetch recipes from Spoonacular"""
        logger.info(f"Fetching {number} recipes from Spoonacular")
        
        try:
            # Convert allergens to intolerances for Spoonacular
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
            
            for allergen in exclude_allergens:
                if allergen.lower() in allergen_mapping:
                    intolerances.append(allergen_mapping[allergen.lower()])
            
            # Search for recipes
            recipes = self.spoonacular_service.search_by_ingredients(
                ingredients=ingredients,
                number=number,
                diet=','.join(dietary_restrictions) if dietary_restrictions else None,
                intolerances=','.join(intolerances) if intolerances else None
            )
            
            # Get full recipe details for each
            detailed_recipes = []
            for recipe in recipes:
                try:
                    details = self.spoonacular_service.get_recipe_details(
                        recipe_id=recipe['id'],
                        include_nutrition=True
                    )
                    detailed_recipes.append(details)
                except Exception as e:
                    logger.error(f"Error getting recipe details: {str(e)}")
            
            return detailed_recipes
            
        except Exception as e:
            logger.error(f"Error fetching Spoonacular recipes: {str(e)}")
            return []


class OpenAIRecipeToolInput(BaseModel):
    ingredients: List[str] = Field(..., description="List of available ingredients")
    expiring_items: List[str] = Field(default=[], description="Items expiring soon")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    exclude_allergens: List[str] = Field(default=[], description="Allergens to exclude")
    cuisine_preferences: List[str] = Field(default=[], description="Preferred cuisines")
    number: int = Field(default=2, description="Number of recipes to generate")


class OpenAIRecipeTool(BaseTool):
    """Generates recipes using OpenAI"""
    name: str = "OpenAIRecipeTool"
    description: str = "Generates creative recipes using OpenAI based on available ingredients"
    args_schema: Type[BaseModel] = OpenAIRecipeToolInput
    
    def _run(self, ingredients: List[str], expiring_items: List[str] = [],
             dietary_restrictions: List[str] = [], exclude_allergens: List[str] = [],
             cuisine_preferences: List[str] = [], number: int = 2) -> List[Dict[str, Any]]:
        """Generate recipes using OpenAI"""
        import openai
        import json
        
        logger.info(f"Generating {number} recipes with OpenAI")
        
        # Build prompt
        prompt = f"""
        Create {number} different recipes using ONLY these available ingredients:
        {', '.join(ingredients)}
        
        {"PRIORITY: Use these expiring items: " + ', '.join(expiring_items) if expiring_items else ""}
        
        Requirements:
        - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
        - Must NOT contain: {', '.join(exclude_allergens) if exclude_allergens else 'None'}
        - Preferred cuisines: {', '.join(cuisine_preferences) if cuisine_preferences else 'Any'}
        
        Return a JSON array where each recipe has:
        - name: string
        - ingredients: array of strings with quantities
        - instructions: array of detailed steps
        - time: total minutes
        - cuisine_type: string
        - dietary_tags: array
        - nutrition: object with calories and protein
        
        Only use ingredients from the provided list. Be creative but realistic.
        """
        
        try:
            response = openai.ChatCompletion.create(
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
            
            recipes = json.loads(recipes_text)
            logger.info(f"Generated {len(recipes)} recipes")
            return recipes
            
        except Exception as e:
            logger.error(f"Error generating OpenAI recipes: {str(e)}")
            return []


class PreferenceAnalyzerToolInput(BaseModel):
    user_id: int = Field(..., description="The user ID to analyze preferences for")


class PreferenceAnalyzerTool(BaseTool):
    """Analyzes user preferences from recipe history"""
    name: str = "PreferenceAnalyzerTool"
    description: str = "Analyzes user's recipe preferences based on their saved recipes and ratings"
    args_schema: Type[BaseModel] = PreferenceAnalyzerToolInput
    preference_service: Any = None
    
    def __init__(self, preference_service):
        super().__init__()
        self.preference_service = preference_service

    def _run(self, user_id: int) -> Dict[str, Any]:
        """Analyze user preferences"""
        logger.info(f"Analyzing preferences for user {user_id}")
        
        try:
            analysis = self.preference_service.analyze_user_preferences(user_id)
            return analysis.get('insights', {})
        except Exception as e:
            logger.error(f"Error analyzing preferences: {str(e)}")
            return {}


class RecipeRankerToolInput(BaseModel):
    recipes: List[Dict[str, Any]] = Field(..., description="List of recipes to rank")
    user_preferences: Dict[str, Any] = Field(..., description="User preferences")
    user_insights: Dict[str, Any] = Field(..., description="User preference insights")
    pantry_items: List[Dict[str, Any]] = Field(..., description="Current pantry items")


class RecipeRankerTool(BaseTool):
    """Ranks recipes based on multiple factors"""
    name: str = "RecipeRankerTool"
    description: str = "Ranks recipes based on pantry match, user preferences, and historical data"
    args_schema: Type[BaseModel] = RecipeRankerToolInput
    
    def _run(self, recipes: List[Dict[str, Any]], user_preferences: Dict[str, Any],
             user_insights: Dict[str, Any], pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank recipes"""
        logger.info(f"Ranking {len(recipes)} recipes")
        
        # Create pantry ingredient set for matching
        pantry_ingredients = set()
        for item in pantry_items:
            if item.get('product_name'):
                pantry_ingredients.add(item['product_name'].lower())
        
        # Score each recipe
        for recipe in recipes:
            score = 0.0
            
            # Pantry match score (40%)
            if 'match_score' in recipe:
                score += recipe['match_score'] * 0.4
            
            # User preference match (30%)
            cuisine_match = recipe.get('cuisine_type') in user_preferences.get('cuisine_preferences', [])
            if cuisine_match:
                score += 0.3
            
            # Historical preference match (20%)
            favorite_ingredients = user_insights.get('favorite_ingredients', [])
            if favorite_ingredients:
                recipe_ingredients = recipe.get('ingredients', [])
                matches = sum(1 for ing in favorite_ingredients if any(ing in r.lower() for r in recipe_ingredients))
                score += (matches / len(favorite_ingredients)) * 0.2 if favorite_ingredients else 0
            
            # Saved recipe boost (10%)
            if recipe.get('source') == 'saved' and recipe.get('rating') == 'thumbs_up':
                score += 0.1
            
            recipe['final_score'] = score
        
        # Sort by score
        ranked = sorted(recipes, key=lambda r: r.get('final_score', 0), reverse=True)
        
        logger.info(f"Ranking complete. Top recipe: {ranked[0]['name'] if ranked else 'None'}")
        return ranked