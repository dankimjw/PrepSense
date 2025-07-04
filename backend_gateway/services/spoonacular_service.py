"""Service for interacting with Spoonacular API"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from backend_gateway.core.config import settings

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
    
