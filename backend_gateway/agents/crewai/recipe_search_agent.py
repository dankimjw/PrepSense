"""RecipeSearch Agent for finding recipes using Spoonacular API."""

from typing import Dict, List, Any, Optional
import logging
from crewai import Agent
from langchain_openai import ChatOpenAI

from backend_gateway.tools.spoonacular_tool import create_spoonacular_tool
from backend_gateway.tools.database_tool import create_database_tool
from backend_gateway.core.config_utils import get_openai_api_key

logger = logging.getLogger(__name__)


class RecipeSearchAgent:
    """Agent specialized in searching for recipes using Spoonacular API."""
    
    def __init__(self):
        """Initialize the RecipeSearch agent."""
        self.spoonacular_tool = create_spoonacular_tool()
        self.database_tool = create_database_tool()
        
        # Initialize OpenAI LLM
        api_key = get_openai_api_key()
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0.1)
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Recipe Search Specialist",
            goal="Find the best recipes based on available ingredients, dietary preferences, and cooking constraints using the Spoonacular API",
            backstory=(
                "You are a skilled recipe researcher with extensive knowledge of cooking techniques, "
                "ingredient combinations, and dietary requirements. You excel at finding recipes that "
                "maximize the use of available ingredients while respecting dietary restrictions and "
                "preferences. Your expertise in recipe databases and API searches helps users discover "
                "new and exciting meal options that fit their pantry and lifestyle."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    async def search_recipes(self, user_id: int, search_strategy: str = "ingredients", **kwargs) -> Dict[str, Any]:
        """
        Search for recipes using different strategies.
        
        Args:
            user_id: The user's ID
            search_strategy: Strategy to use (ingredients, query, balanced, comprehensive)
            **kwargs: Additional parameters for search
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            logger.info(f"RecipeSearchAgent searching recipes for user {user_id}, strategy: {search_strategy}")
            
            if search_strategy == "ingredients":
                return await self._search_by_ingredients(user_id, **kwargs)
            elif search_strategy == "query":
                return await self._search_by_query(user_id, **kwargs)
            elif search_strategy == "balanced":
                return await self._search_balanced_recipes(user_id, **kwargs)
            elif search_strategy == "comprehensive":
                return await self._search_comprehensive(user_id, **kwargs)
            else:
                return await self._search_by_ingredients(user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"RecipeSearchAgent error: {str(e)}")
            return {"error": f"Recipe search failed: {str(e)}"}
    
    async def _search_by_ingredients(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Search recipes based on available ingredients."""
        ingredients = kwargs.get('ingredients', [])
        max_results = kwargs.get('max_results', 10)
        ranking = kwargs.get('ranking', 1)  # 1=maximize used ingredients, 2=minimize missing ingredients
        
        # If no ingredients provided, get from database
        if not ingredients:
            ingredients_data = self.database_tool._run("pantry_items", user_id)
            if "error" in ingredients_data:
                return ingredients_data
            
            # Extract ingredient names
            ingredients = [item['product_name'] for item in ingredients_data.get('items', [])]
        
        if not ingredients:
            return {"error": "No ingredients available for search"}
        
        # Search using Spoonacular
        search_result = await self.spoonacular_tool._run(
            "search_by_ingredients",
            ingredients=ingredients,
            number=max_results,
            ranking=ranking,
            ignore_pantry=True
        )
        
        if "error" in search_result:
            return search_result
        
        recipes = search_result.get('recipes', [])
        
        # Enhance recipes with additional analysis
        enhanced_recipes = []
        for recipe in recipes:
            enhanced_recipe = await self._enhance_recipe_data(recipe, user_id)
            enhanced_recipes.append(enhanced_recipe)
        
        return {
            "search_strategy": "ingredients",
            "user_id": user_id,
            "input_ingredients": ingredients,
            "recipes_found": len(enhanced_recipes),
            "recipes": enhanced_recipes,
            "search_metadata": {
                "ranking_strategy": ranking,
                "max_results": max_results
            }
        }
    
    async def _search_by_query(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Search recipes based on query string."""
        query = kwargs.get('query', '')
        max_results = kwargs.get('max_results', 10)
        cuisine = kwargs.get('cuisine', None)
        diet = kwargs.get('diet', None)
        intolerances = kwargs.get('intolerances', None)
        meal_type = kwargs.get('meal_type', None)
        
        if not query:
            return {"error": "No search query provided"}
        
        # Search using Spoonacular
        search_result = await self.spoonacular_tool._run(
            "search_by_query",
            query=query,
            number=max_results,
            cuisine=cuisine,
            diet=diet,
            intolerances=intolerances,
            type=meal_type
        )
        
        if "error" in search_result:
            return search_result
        
        recipes = search_result.get('recipes', [])
        
        # Enhance recipes with additional analysis
        enhanced_recipes = []
        for recipe in recipes:
            enhanced_recipe = await self._enhance_recipe_data(recipe, user_id)
            enhanced_recipes.append(enhanced_recipe)
        
        return {
            "search_strategy": "query",
            "user_id": user_id,
            "search_query": query,
            "recipes_found": len(enhanced_recipes),
            "recipes": enhanced_recipes,
            "search_metadata": {
                "cuisine": cuisine,
                "diet": diet,
                "intolerances": intolerances,
                "meal_type": meal_type,
                "max_results": max_results
            }
        }
    
    async def _search_balanced_recipes(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Search for recipes with balanced nutrition."""
        max_results = kwargs.get('max_results', 10)
        cuisine = kwargs.get('cuisine', None)
        diet = kwargs.get('diet', None)
        
        # Search for balanced meals
        search_result = await self.spoonacular_tool._run(
            "search_by_query",
            query="balanced healthy meal",
            number=max_results,
            cuisine=cuisine,
            diet=diet
        )
        
        if "error" in search_result:
            return search_result
        
        recipes = search_result.get('recipes', [])
        
        # Enhance and filter for nutritional balance
        enhanced_recipes = []
        for recipe in recipes:
            enhanced_recipe = await self._enhance_recipe_data(recipe, user_id)
            
            # Check if recipe meets balanced criteria
            if self._is_nutritionally_balanced(enhanced_recipe):
                enhanced_recipes.append(enhanced_recipe)
        
        return {
            "search_strategy": "balanced",
            "user_id": user_id,
            "recipes_found": len(enhanced_recipes),
            "recipes": enhanced_recipes,
            "search_metadata": {
                "cuisine": cuisine,
                "diet": diet,
                "max_results": max_results,
                "filter_criteria": "nutritionally_balanced"
            }
        }
    
    async def _search_comprehensive(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Comprehensive search combining multiple strategies."""
        max_results_per_strategy = kwargs.get('max_results_per_strategy', 5)
        
        # Get user's available ingredients
        ingredients_data = self.database_tool._run("pantry_items", user_id)
        ingredients = []
        if "items" in ingredients_data:
            ingredients = [item['product_name'] for item in ingredients_data['items']]
        
        # Get user preferences
        prefs_data = self.database_tool._run("user_preferences", user_id)
        preferences = prefs_data.get('preferences', {})
        
        all_recipes = []
        search_results = {}
        
        # Strategy 1: Ingredient-based search
        if ingredients:
            ingredient_results = await self._search_by_ingredients(
                user_id, 
                ingredients=ingredients,
                max_results=max_results_per_strategy
            )
            if "recipes" in ingredient_results:
                all_recipes.extend(ingredient_results['recipes'])
                search_results['ingredient_search'] = ingredient_results
        
        # Strategy 2: Cuisine preference search
        cuisine_prefs = preferences.get('cuisine_preference', [])
        if cuisine_prefs:
            for cuisine in cuisine_prefs[:2]:  # Limit to 2 cuisines
                cuisine_results = await self._search_by_query(
                    user_id,
                    query=f"{cuisine} cuisine",
                    max_results=max_results_per_strategy // 2,
                    cuisine=cuisine
                )
                if "recipes" in cuisine_results:
                    all_recipes.extend(cuisine_results['recipes'])
                    search_results[f'{cuisine}_cuisine'] = cuisine_results
        
        # Strategy 3: Dietary restriction search
        dietary_prefs = preferences.get('dietary_preference', [])
        if dietary_prefs:
            for diet in dietary_prefs[:2]:  # Limit to 2 diets
                diet_results = await self._search_by_query(
                    user_id,
                    query=f"{diet} recipes",
                    max_results=max_results_per_strategy // 2,
                    diet=diet
                )
                if "recipes" in diet_results:
                    all_recipes.extend(diet_results['recipes'])
                    search_results[f'{diet}_diet'] = diet_results
        
        # Remove duplicates based on recipe ID
        unique_recipes = []
        seen_ids = set()
        for recipe in all_recipes:
            recipe_id = recipe.get('id')
            if recipe_id and recipe_id not in seen_ids:
                unique_recipes.append(recipe)
                seen_ids.add(recipe_id)
        
        # Sort by relevance score
        unique_recipes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Limit final results
        final_recipes = unique_recipes[:kwargs.get('max_results', 15)]
        
        return {
            "search_strategy": "comprehensive",
            "user_id": user_id,
            "recipes_found": len(final_recipes),
            "recipes": final_recipes,
            "search_metadata": {
                "strategies_used": list(search_results.keys()),
                "total_searches": len(search_results),
                "deduplication_applied": True,
                "max_results": kwargs.get('max_results', 15)
            },
            "detailed_results": search_results
        }
    
    async def _enhance_recipe_data(self, recipe: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Enhance recipe data with additional analysis."""
        enhanced = recipe.copy()
        
        # Calculate ingredient match score
        enhanced['ingredient_match_score'] = self._calculate_ingredient_match_score(recipe)
        
        # Calculate cooking complexity score
        enhanced['complexity_score'] = self._calculate_complexity_score(recipe)
        
        # Calculate overall relevance score
        enhanced['relevance_score'] = self._calculate_relevance_score(recipe)
        
        # Add preparation insights
        enhanced['preparation_insights'] = self._generate_preparation_insights(recipe)
        
        return enhanced
    
    def _calculate_ingredient_match_score(self, recipe: Dict[str, Any]) -> float:
        """Calculate how well the recipe matches available ingredients."""
        used_ingredients = recipe.get('usedIngredients', [])
        missed_ingredients = recipe.get('missedIngredients', [])
        
        if not used_ingredients and not missed_ingredients:
            return 5.0  # Neutral score when no ingredient data
        
        total_ingredients = len(used_ingredients) + len(missed_ingredients)
        if total_ingredients == 0:
            return 5.0
        
        # Score based on percentage of available ingredients
        match_percentage = len(used_ingredients) / total_ingredients
        return round(match_percentage * 10, 1)
    
    def _calculate_complexity_score(self, recipe: Dict[str, Any]) -> float:
        """Calculate recipe complexity score (1-10, where 1 is simple)."""
        complexity_score = 1.0
        
        # Factor in cooking time
        ready_time = recipe.get('readyInMinutes', 0)
        if ready_time > 60:
            complexity_score += 2.0
        elif ready_time > 30:
            complexity_score += 1.0
        
        # Factor in number of ingredients
        total_ingredients = len(recipe.get('usedIngredients', [])) + len(recipe.get('missedIngredients', []))
        if total_ingredients > 15:
            complexity_score += 2.0
        elif total_ingredients > 10:
            complexity_score += 1.0
        
        # Factor in servings (larger servings might be more complex)
        servings = recipe.get('servings', 1)
        if servings > 6:
            complexity_score += 1.0
        
        return min(complexity_score, 10.0)
    
    def _calculate_relevance_score(self, recipe: Dict[str, Any]) -> float:
        """Calculate overall relevance score for the recipe."""
        # Combine multiple factors
        ingredient_score = self._calculate_ingredient_match_score(recipe)
        health_score = recipe.get('healthScore', 50) / 10  # Convert to 0-10 scale
        spoonacular_score = recipe.get('spoonacularScore', 50) / 10  # Convert to 0-10 scale
        
        # Weight the scores
        relevance = (
            ingredient_score * 0.4 +  # 40% weight on ingredient match
            health_score * 0.3 +      # 30% weight on health score
            spoonacular_score * 0.3   # 30% weight on Spoonacular score
        )
        
        return round(relevance, 1)
    
    def _generate_preparation_insights(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights about recipe preparation."""
        insights = {
            'difficulty_level': 'Easy',
            'time_commitment': 'Quick',
            'ingredient_availability': 'Good',
            'tips': []
        }
        
        # Determine difficulty level
        complexity = self._calculate_complexity_score(recipe)
        if complexity >= 7:
            insights['difficulty_level'] = 'Advanced'
        elif complexity >= 4:
            insights['difficulty_level'] = 'Intermediate'
        
        # Determine time commitment
        ready_time = recipe.get('readyInMinutes', 0)
        if ready_time > 60:
            insights['time_commitment'] = 'Long'
        elif ready_time > 30:
            insights['time_commitment'] = 'Medium'
        
        # Check ingredient availability
        used_ingredients = len(recipe.get('usedIngredients', []))
        missed_ingredients = len(recipe.get('missedIngredients', []))
        
        if missed_ingredients == 0:
            insights['ingredient_availability'] = 'Excellent'
        elif missed_ingredients <= 2:
            insights['ingredient_availability'] = 'Good'
        elif missed_ingredients <= 5:
            insights['ingredient_availability'] = 'Fair'
        else:
            insights['ingredient_availability'] = 'Poor'
        
        # Generate tips
        if missed_ingredients > 0:
            insights['tips'].append(f"You'll need to purchase {missed_ingredients} additional ingredients")
        
        if ready_time > 45:
            insights['tips'].append("Consider meal prep or starting early due to longer cooking time")
        
        if recipe.get('healthScore', 0) > 70:
            insights['tips'].append("This recipe is nutritionally balanced and healthy")
        
        return insights
    
    def _is_nutritionally_balanced(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is nutritionally balanced."""
        nutrition = recipe.get('nutrition', {})
        
        if not nutrition:
            return False
        
        # Check if has reasonable protein, carbs, and fats
        protein = nutrition.get('protein', 0)
        carbs = nutrition.get('carbs', 0)
        fat = nutrition.get('fat', 0)
        calories = nutrition.get('calories', 0)
        
        if calories == 0:
            return False
        
        # Calculate macro percentages
        protein_cals = protein * 4
        carb_cals = carbs * 4
        fat_cals = fat * 9
        
        total_macro_cals = protein_cals + carb_cals + fat_cals
        
        if total_macro_cals == 0:
            return False
        
        protein_pct = (protein_cals / total_macro_cals) * 100
        carb_pct = (carb_cals / total_macro_cals) * 100
        fat_pct = (fat_cals / total_macro_cals) * 100
        
        # Check if within reasonable ranges
        return (10 <= protein_pct <= 35 and 
                45 <= carb_pct <= 65 and 
                20 <= fat_pct <= 35)


def create_recipe_search_agent() -> RecipeSearchAgent:
    """Create and return a RecipeSearchAgent instance."""
    return RecipeSearchAgent()