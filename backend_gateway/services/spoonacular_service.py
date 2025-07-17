"""Service for interacting with Spoonacular API"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from backend_gateway.core.config import settings
from backend_gateway.services.openai_recipe_service import OpenAIRecipeService

logger = logging.getLogger(__name__)


class SpoonacularService:
    """Service for interacting with Spoonacular API"""
    
    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        if not self.api_key:
            # Try to read from file as fallback
            try:
                with open('config/spoonacular_key.txt', 'r') as f:
                    self.api_key = f.read().strip()
            except FileNotFoundError:
                logger.warning("Spoonacular API key not found in environment or config file")
        
        self.base_url = "https://api.spoonacular.com"
        self.timeout = httpx.Timeout(120.0, connect=60.0)  # 2 minute timeout with 1 minute connect timeout
        self.max_retries = 3
        self.openai_service = OpenAIRecipeService()
    
    async def search_recipes_by_ingredients_with_allergen_filter(
        self,
        ingredients: List[str],
        intolerances: List[str],
        number: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Use complexSearch for better allergen filtering when searching by ingredients.
        This is more reliable than findByIngredients for allergen filtering.
        
        Args:
            ingredients: List of ingredients to include
            intolerances: List of allergens to exclude
            number: Number of recipes to return
            
        Returns:
            List of recipe dictionaries
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        # Use complexSearch with includeIngredients for better allergen filtering
        results = await self.search_recipes_complex(
            include_ingredients=ingredients,
            intolerances=intolerances,
            number=number,
            sort="min-missing-ingredients"
        )
        
        # Extract recipes from results
        recipes = results.get('results', [])
        
        # Add compatibility fields to match findByIngredients format
        for recipe in recipes:
            # Count used and missed ingredients (approximation)
            recipe['usedIngredientCount'] = len([ing for ing in ingredients if any(ing.lower() in recipe.get('title', '').lower() for ing in ingredients)])
            recipe['missedIngredientCount'] = max(0, 5 - recipe['usedIngredientCount'])  # Rough estimate
            
        return recipes
    
    async def search_recipes_by_ingredients(
        self, 
        ingredients: List[str], 
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = False,
        intolerances: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for recipes by ingredients
        
        Args:
            ingredients: List of ingredients to search with
            number: Number of recipes to return
            ranking: 0 = maximize used ingredients, 1 = minimize missing ingredients
            ignore_pantry: Whether to ignore typical pantry items
            intolerances: List of allergens/intolerances to exclude (e.g., ['dairy', 'gluten', 'peanut'])
            
        Returns:
            List of recipe dictionaries
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        # If intolerances are specified, use complexSearch for better filtering
        if intolerances:
            logger.info(f"Using complexSearch for allergen filtering: {intolerances}")
            return await self.search_recipes_by_ingredients_with_allergen_filter(
                ingredients=ingredients,
                intolerances=intolerances,
                number=number
            )
        
        # Otherwise use the standard findByIngredients endpoint
        params = {
            "apiKey": self.api_key,
            "ingredients": ",".join(ingredients),
            "number": number,
            "ranking": ranking,
            "ignorePantry": ignore_pantry
        }
        
        # Continue with standard findByIngredients without allergen filtering
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} for ingredient search")
                    
                    response = await client.get(
                        f"{self.base_url}/recipes/findByIngredients",
                        params=params
                    )
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.ReadTimeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries} for ingredient search")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except httpx.HTTPError as e:
                logger.error(f"Error searching recipes: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error searching recipes: {type(e).__name__}: {str(e)}")
                raise
    
    async def get_recipe_information(
        self, 
        recipe_id: int,
        include_nutrition: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information about a recipe
        
        Args:
            recipe_id: The ID of the recipe
            include_nutrition: Whether to include nutrition information
            
        Returns:
            Recipe information dictionary
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        logger.info(f"Getting recipe info for ID {recipe_id}, API key present: {bool(self.api_key)}")
        
        params = {
            "apiKey": self.api_key,
            "includeNutrition": include_nutrition
        }
        
        # Add retry logic for timeouts
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} for recipe {recipe_id}")
                    
                    response = await client.get(
                        f"{self.base_url}/recipes/{recipe_id}/information",
                        params=params
                    )
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.ReadTimeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries} for recipe {recipe_id}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts failed for recipe {recipe_id}")
                    raise
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)
                
            except httpx.HTTPError as e:
                logger.error(f"Error getting recipe info: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                    # For 500 errors, don't retry as it's a server issue
                    if e.response.status_code >= 500:
                        raise Exception(f"Spoonacular server error (status {e.response.status_code})")
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error getting recipe info: {type(e).__name__}: {str(e)}")
                raise
    
    async def search_recipes_complex(
        self,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        include_ingredients: Optional[List[str]] = None,
        exclude_ingredients: Optional[List[str]] = None,
        intolerances: Optional[List[str]] = None,
        max_ready_time: Optional[int] = None,
        sort: Optional[str] = None,
        number: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Complex recipe search with multiple filters
        
        Args:
            query: Natural language search query
            cuisine: Cuisine type (italian, mexican, etc.)
            diet: Diet type (vegetarian, vegan, etc.)
            include_ingredients: Ingredients that must be included
            exclude_ingredients: Ingredients to exclude
            intolerances: List of allergens/intolerances to exclude
            max_ready_time: Maximum time in minutes
            sort: Sort by (popularity, time, etc.)
            number: Number of results
            offset: Results offset for pagination
            
        Returns:
            Search results with recipes and metadata
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        params = {
            "apiKey": self.api_key,
            "number": number,
            "offset": offset,
            "addRecipeInformation": True,
            "fillIngredients": True
        }
        
        if query:
            params["query"] = query
        if cuisine:
            params["cuisine"] = cuisine
        if diet:
            params["diet"] = diet
        if include_ingredients:
            params["includeIngredients"] = ",".join(include_ingredients)
        if exclude_ingredients:
            params["excludeIngredients"] = ",".join(exclude_ingredients)
        if intolerances:
            # Map common allergen names to Spoonacular format
            intolerance_mapping = {
                'milk': 'dairy',
                'eggs': 'egg',
                'nuts': 'tree nut',
                'peanuts': 'peanut', 
                'wheat': 'gluten',
                'soy': 'soy',
                'fish': 'seafood',
                'shellfish': 'shellfish',
                'sesame': 'sesame'
            }
            
            mapped_intolerances = []
            for intol in intolerances:
                mapped = intolerance_mapping.get(intol.lower(), intol.lower())
                mapped_intolerances.append(mapped)
            
            params["intolerances"] = ",".join(mapped_intolerances)
        if max_ready_time:
            params["maxReadyTime"] = max_ready_time
        if sort:
            params["sort"] = sort
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/complexSearch",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error in complex search: {str(e)}")
                raise
    
    def _check_recipe_for_allergens(self, recipe_title: str, intolerances: List[str]) -> bool:
        """
        Check if a recipe title contains common allergen indicators
        
        Returns:
            True if recipe contains allergens, False otherwise
        """
        title_lower = recipe_title.lower()
        
        # Comprehensive allergen keyword mapping
        allergen_keywords = {
            'dairy': ['milk', 'cheese', 'cream', 'butter', 'yogurt', 'custard', 'ice cream', 'whey', 'casein', 'lactose'],
            'egg': ['egg', 'eggs', 'mayonnaise', 'meringue', 'custard', 'eggplant'],  # Note: eggplant is false positive
            'gluten': ['wheat', 'bread', 'pasta', 'flour', 'cake', 'cookie', 'muffin', 'pastry', 'pie', 'pizza', 'noodle'],
            'peanut': ['peanut', 'peanuts'],
            'tree nut': ['almond', 'cashew', 'walnut', 'pecan', 'pistachio', 'hazelnut', 'macadamia'],
            'soy': ['soy', 'tofu', 'edamame', 'miso', 'tempeh'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'shellfish', 'seafood'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'clam', 'oyster', 'mussel', 'scallop'],
            'sesame': ['sesame', 'tahini']
        }
        
        for intolerance in intolerances:
            intol_lower = intolerance.lower().replace('_', ' ')
            keywords = allergen_keywords.get(intol_lower, [intol_lower])
            
            for keyword in keywords:
                if keyword in title_lower:
                    # Special case: "eggplant" shouldn't trigger egg allergy
                    if keyword == 'egg' and 'eggplant' in title_lower:
                        continue
                    return True
        
        return False
    
    async def get_random_recipes(
        self,
        number: int = 10,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get random recipes
        
        Args:
            number: Number of random recipes
            tags: Optional tags to filter by
            
        Returns:
            Random recipes
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        params = {
            "apiKey": self.api_key,
            "number": number
        }
        
        if tags:
            params["tags"] = ",".join(tags)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/random",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error getting random recipes: {str(e)}")
                raise
    
