"""Service for interacting with Spoonacular API"""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SpoonacularService:
    """Service for interacting with Spoonacular API"""
    
    def __init__(self):
        self.api_key = os.getenv('SPOONACULAR_API_KEY')
        if not self.api_key:
            # Try to read from file
            try:
                with open('config/spoonacular_key.txt', 'r') as f:
                    self.api_key = f.read().strip()
            except FileNotFoundError:
                logger.warning("Spoonacular API key not found in environment or config file")
        
        self.base_url = "https://api.spoonacular.com"
        self.timeout = 30.0
    
    async def search_recipes_by_ingredients(
        self, 
        ingredients: List[str], 
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for recipes by ingredients
        
        Args:
            ingredients: List of ingredients to search with
            number: Number of recipes to return
            ranking: 0 = maximize used ingredients, 1 = minimize missing ingredients
            ignore_pantry: Whether to ignore typical pantry items
            
        Returns:
            List of recipe dictionaries
        """
        if not self.api_key:
            raise ValueError("Spoonacular API key not configured")
        
        params = {
            "apiKey": self.api_key,
            "ingredients": ",".join(ingredients),
            "number": number,
            "ranking": ranking,
            "ignorePantry": ignore_pantry
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/findByIngredients",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error searching recipes: {str(e)}")
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
        
        params = {
            "apiKey": self.api_key,
            "includeNutrition": include_nutrition
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/recipes/{recipe_id}/information",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error getting recipe info: {str(e)}")
                raise
    
    async def search_recipes_complex(
        self,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        include_ingredients: Optional[List[str]] = None,
        exclude_ingredients: Optional[List[str]] = None,
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