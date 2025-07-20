"""
Spoonacular API client wrapper for centralized API interaction.
"""
import os
import httpx
from typing import List, Dict, Any, Optional, Union
import time
from urllib.parse import quote


class SpoonacularClient:
    """Client wrapper for Spoonacular API interactions."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.spoonacular.com"):
        """
        Initialize Spoonacular client.
        
        Args:
            api_key: Spoonacular API key. If not provided, will use SPOONACULAR_API_KEY env var.
            base_url: Base URL for Spoonacular API.
        
        Raises:
            ValueError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("SPOONACULAR_API_KEY")
        if not self.api_key:
            raise ValueError("Spoonacular API key not provided")
        
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            timeout=30.0,
            headers={
                "User-Agent": "PrepSense/1.0"
            }
        )
    
    def search_recipes_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = True,
        retry_count: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for recipes by ingredients.
        
        Args:
            ingredients: List of ingredients to search with.
            number: Number of results to return (default: 10).
            ranking: Whether to maximize used ingredients (1) or minimize missing ingredients (2).
            ignore_pantry: Whether to ignore typical pantry ingredients.
            retry_count: Number of retries for transient failures.
        
        Returns:
            List of recipe dictionaries.
        """
        params = {
            "ingredients": ",".join(ingredients),
            "number": number,
            "ranking": ranking,
            "ignorePantry": str(ignore_pantry).lower(),
            "apiKey": self.api_key
        }
        
        return self._make_request(
            method="GET",
            endpoint="/recipes/findByIngredients",
            params=params,
            retry_count=retry_count
        )
    
    def get_recipe_information(
        self,
        recipe_id: int,
        include_nutrition: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific recipe.
        
        Args:
            recipe_id: The ID of the recipe.
            include_nutrition: Whether to include nutritional information.
        
        Returns:
            Recipe information dictionary.
        """
        params = {
            "includeNutrition": str(include_nutrition).lower(),
            "apiKey": self.api_key
        }
        
        return self._make_request(
            method="GET",
            endpoint=f"/recipes/{recipe_id}/information",
            params=params
        )
    
    def analyze_recipe_instructions(self, recipe_id: int) -> List[Dict[str, Any]]:
        """
        Get analyzed recipe instructions with steps broken down.
        
        Args:
            recipe_id: The ID of the recipe.
        
        Returns:
            List of instruction sections with detailed steps.
        """
        params = {"apiKey": self.api_key}
        
        return self._make_request(
            method="GET",
            endpoint=f"/recipes/{recipe_id}/analyzedInstructions",
            params=params
        )
    
    def get_similar_recipes(self, recipe_id: int, number: int = 10) -> List[Dict[str, Any]]:
        """
        Get similar recipes to a given recipe.
        
        Args:
            recipe_id: The ID of the recipe to find similar recipes for.
            number: Number of similar recipes to return.
        
        Returns:
            List of similar recipe dictionaries.
        """
        params = {
            "number": number,
            "apiKey": self.api_key
        }
        
        return self._make_request(
            method="GET",
            endpoint=f"/recipes/{recipe_id}/similar",
            params=params
        )
    
    def substitute_ingredients(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Get ingredient substitutes.
        
        Args:
            ingredient_name: Name of the ingredient to find substitutes for.
        
        Returns:
            Dictionary with substitution information.
        """
        params = {
            "ingredientName": ingredient_name,
            "apiKey": self.api_key
        }
        
        return self._make_request(
            method="GET",
            endpoint="/food/ingredients/substitutes",
            params=params
        )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make HTTP request to Spoonacular API.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: Query parameters.
            data: Request body data.
            retry_count: Number of retries for transient failures.
        
        Returns:
            Response data as dictionary or list.
        
        Raises:
            httpx.HTTPStatusError: For HTTP errors.
            httpx.ConnectError: For connection errors.
            httpx.ConnectTimeout: For timeout errors.
        """
        retries = 0
        last_exception = None
        
        while retries <= retry_count:
            try:
                response = self.client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.ConnectTimeout as e:
                last_exception = e
                retries += 1
                if retries <= retry_count:
                    time.sleep(1 * retries)  # Exponential backoff
                    continue
                raise
                
            except (httpx.HTTPStatusError, httpx.ConnectError) as e:
                # Don't retry on HTTP errors (4xx, 5xx) or other connection errors
                raise
        
        # If we've exhausted retries, raise the last exception
        if last_exception:
            raise last_exception
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()