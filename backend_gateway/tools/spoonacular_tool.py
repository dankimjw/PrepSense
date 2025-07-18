"""Spoonacular API tool for CrewAI agents."""

from typing import Dict, List, Any, Optional
import logging
# from crewai_tools import BaseTool  # Not available in CrewAI 0.5.0

from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


class SpoonacularTool:
    """Tool for searching recipes using Spoonacular API."""
    
    name: str = "spoonacular_tool"
    description: str = (
        "A tool for searching recipes using the Spoonacular API. Can search by ingredients, "
        "dietary restrictions, cuisine type, and other parameters."
    )
    
    def __init__(self):
        self.spoonacular_service = SpoonacularService()
    
    def _run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a Spoonacular API action.
        
        Args:
            action: The action to perform (search_by_ingredients, search_by_query, etc.)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Dict containing the API results
        """
        try:
            if action == "search_by_ingredients":
                return self._search_by_ingredients(**kwargs)
            elif action == "search_by_query":
                return self._search_by_query(**kwargs)
            elif action == "get_recipe_details":
                return self._get_recipe_details(**kwargs)
            elif action == "search_with_filters":
                return self._search_with_filters(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Spoonacular tool error: {str(e)}")
            return {"error": f"Spoonacular API call failed: {str(e)}"}
    
    async def _search_by_ingredients(self, **kwargs) -> Dict[str, Any]:
        """Search recipes by ingredients."""
        ingredients = kwargs.get('ingredients', [])
        number = kwargs.get('number', 10)
        ranking = kwargs.get('ranking', 1)
        ignore_pantry = kwargs.get('ignore_pantry', True)
        intolerances = kwargs.get('intolerances', None)
        
        if not ingredients:
            return {"error": "No ingredients provided"}
        
        # Convert ingredients list to string if needed
        if isinstance(ingredients, list):
            ingredients_str = ','.join(ingredients)
        else:
            ingredients_str = ingredients
        
        try:
            recipes = await self.spoonacular_service.search_recipes_by_ingredients(
                ingredients=ingredients_str,
                number=number,
                ranking=ranking,
                ignore_pantry=ignore_pantry,
                intolerances=intolerances
            )
            
            return {
                "action": "search_by_ingredients",
                "ingredients": ingredients_str,
                "count": len(recipes),
                "recipes": recipes
            }
            
        except Exception as e:
            logger.error(f"Error searching by ingredients: {str(e)}")
            return {"error": f"Failed to search by ingredients: {str(e)}"}
    
    async def _search_by_query(self, **kwargs) -> Dict[str, Any]:
        """Search recipes by query string."""
        query = kwargs.get('query', '')
        number = kwargs.get('number', 10)
        cuisine = kwargs.get('cuisine', None)
        diet = kwargs.get('diet', None)
        intolerances = kwargs.get('intolerances', None)
        type_param = kwargs.get('type', None)
        
        if not query:
            return {"error": "No query provided"}
        
        try:
            recipes = await self.spoonacular_service.search_recipes(
                query=query,
                number=number,
                cuisine=cuisine,
                diet=diet,
                intolerances=intolerances,
                type_param=type_param
            )
            
            return {
                "action": "search_by_query",
                "query": query,
                "count": len(recipes),
                "recipes": recipes
            }
            
        except Exception as e:
            logger.error(f"Error searching by query: {str(e)}")
            return {"error": f"Failed to search by query: {str(e)}"}
    
    async def _get_recipe_details(self, **kwargs) -> Dict[str, Any]:
        """Get detailed recipe information."""
        recipe_id = kwargs.get('recipe_id')
        include_nutrition = kwargs.get('include_nutrition', True)
        
        if not recipe_id:
            return {"error": "No recipe ID provided"}
        
        try:
            recipe_details = await self.spoonacular_service.get_recipe_information(
                recipe_id=recipe_id,
                include_nutrition=include_nutrition
            )
            
            return {
                "action": "get_recipe_details",
                "recipe_id": recipe_id,
                "recipe": recipe_details
            }
            
        except Exception as e:
            logger.error(f"Error getting recipe details: {str(e)}")
            return {"error": f"Failed to get recipe details: {str(e)}"}
    
    async def _search_with_filters(self, **kwargs) -> Dict[str, Any]:
        """Search recipes with comprehensive filters."""
        # Extract parameters
        ingredients = kwargs.get('ingredients', [])
        query = kwargs.get('query', '')
        cuisine = kwargs.get('cuisine', None)
        diet = kwargs.get('diet', None)
        intolerances = kwargs.get('intolerances', None)
        type_param = kwargs.get('type', None)
        max_ready_time = kwargs.get('max_ready_time', None)
        number = kwargs.get('number', 10)
        
        # Decide which search method to use
        if ingredients:
            # Search by ingredients with additional filters
            return await self._search_by_ingredients(
                ingredients=ingredients,
                number=number,
                intolerances=intolerances
            )
        elif query:
            # Search by query with filters
            return await self._search_by_query(
                query=query,
                number=number,
                cuisine=cuisine,
                diet=diet,
                intolerances=intolerances,
                type_param=type_param
            )
        else:
            # Generic search with filters
            return await self._search_by_query(
                query="",
                number=number,
                cuisine=cuisine,
                diet=diet,
                intolerances=intolerances,
                type_param=type_param
            )
    
    def format_recipes_for_agents(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format recipes for use by agents."""
        formatted_recipes = []
        
        for recipe in recipes:
            formatted_recipe = {
                'id': recipe.get('id'),
                'name': recipe.get('title', 'Unknown Recipe'),
                'image': recipe.get('image', ''),
                'ready_in_minutes': recipe.get('readyInMinutes', 0),
                'servings': recipe.get('servings', 1),
                'source_url': recipe.get('sourceUrl', ''),
                'summary': recipe.get('summary', ''),
                'cuisines': recipe.get('cuisines', []),
                'dish_types': recipe.get('dishTypes', []),
                'diets': recipe.get('diets', []),
                'used_ingredients': recipe.get('usedIngredients', []),
                'missed_ingredients': recipe.get('missedIngredients', []),
                'unused_ingredients': recipe.get('unusedIngredients', []),
                'spoonacular_score': recipe.get('spoonacularScore', 0),
                'health_score': recipe.get('healthScore', 0)
            }
            
            # Extract nutrition if available
            if 'nutrition' in recipe:
                nutrition = recipe['nutrition']
                formatted_recipe['nutrition'] = {
                    'calories': self._extract_nutrient_value(nutrition, 'Calories'),
                    'protein': self._extract_nutrient_value(nutrition, 'Protein'),
                    'carbs': self._extract_nutrient_value(nutrition, 'Carbohydrates'),
                    'fat': self._extract_nutrient_value(nutrition, 'Fat'),
                    'fiber': self._extract_nutrient_value(nutrition, 'Fiber'),
                    'sugar': self._extract_nutrient_value(nutrition, 'Sugar'),
                    'sodium': self._extract_nutrient_value(nutrition, 'Sodium')
                }
            
            formatted_recipes.append(formatted_recipe)
        
        return formatted_recipes
    
    def _extract_nutrient_value(self, nutrition: Dict[str, Any], nutrient_name: str) -> float:
        """Extract nutrient value from nutrition data."""
        nutrients = nutrition.get('nutrients', [])
        for nutrient in nutrients:
            if nutrient.get('name') == nutrient_name:
                return nutrient.get('amount', 0)
        return 0


# Helper function to create the tool
def create_spoonacular_tool() -> SpoonacularTool:
    """Create and return a SpoonacularTool instance."""
    return SpoonacularTool()