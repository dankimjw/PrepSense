"""Service for generating and managing recipe images using OpenAI DALL-E"""

import os
import logging
from typing import Optional, Dict, Any
import openai
from backend_gateway.services.gcs_service import GCSService
from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)


class RecipeImageService:
    """Service for generating recipe images using DALL-E and storing them in GCS"""
    
    def __init__(self):
        # Initialize OpenAI
        self.openai_api_key = self._get_openai_api_key()
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize GCS service
        self.gcs_service = GCSService()
    
    def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from file or environment"""
        try:
            # Try to read from file first
            if os.path.exists(settings.OPENAI_API_KEY_FILE):
                with open(settings.OPENAI_API_KEY_FILE, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading OpenAI API key from file: {e}")
        
        # Fall back to environment variable
        return os.getenv('OPENAI_API_KEY')
    
    def create_recipe_image_prompt(self, recipe_title: str, ingredients: list, cuisine: str = None) -> str:
        """
        Create an optimized prompt for DALL-E to generate appetizing recipe images
        
        Args:
            recipe_title: Name of the recipe
            ingredients: List of main ingredients
            cuisine: Type of cuisine (optional)
            
        Returns:
            Formatted prompt for DALL-E
        """
        # Base prompt for food photography style
        base_prompt = "Professional food photography, appetizing presentation, natural lighting, shallow depth of field"
        
        # Add recipe details
        recipe_prompt = f"{recipe_title}"
        
        # Add cuisine style if provided
        if cuisine:
            recipe_prompt += f", {cuisine} cuisine style"
        
        # Add key ingredients (limit to 3-4 main ones)
        if ingredients:
            main_ingredients = ", ".join(ingredients[:3])
            recipe_prompt += f", featuring {main_ingredients}"
        
        # Combine prompts
        full_prompt = f"{base_prompt}, {recipe_prompt}, on a beautiful plate, restaurant quality, highly detailed, 4K"
        
        # Ensure prompt isn't too long (DALL-E has a limit)
        if len(full_prompt) > 400:
            full_prompt = full_prompt[:397] + "..."
        
        return full_prompt
    
    async def generate_and_store_recipe_image(
        self, 
        recipe_id: str,
        recipe_title: str,
        ingredients: list = None,
        cuisine: str = None,
        force_regenerate: bool = False
    ) -> Optional[str]:
        """
        Generate a recipe image using DALL-E and store it in GCS
        
        Args:
            recipe_id: Unique identifier for the recipe
            recipe_title: Name of the recipe
            ingredients: List of ingredients (optional)
            cuisine: Type of cuisine (optional)
            force_regenerate: Force generation even if image exists
            
        Returns:
            Public URL of the stored image or None if failed
        """
        try:
            # Check if image already exists in GCS
            if not force_regenerate:
                existing_url = self.gcs_service.get_recipe_image_url(recipe_id)
                if existing_url:
                    logger.info(f"Image already exists for recipe {recipe_id}: {existing_url}")
                    return existing_url
            
            # Check if OpenAI API key is available
            if not self.openai_api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            # Create optimized prompt
            prompt = self.create_recipe_image_prompt(recipe_title, ingredients or [], cuisine)
            logger.info(f"Generating image for recipe {recipe_id} with prompt: {prompt}")
            
            # Generate image using DALL-E 3
            response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            # Get the generated image URL
            image_url = response.data[0].url
            
            # Upload to GCS
            stored_url = await self.gcs_service.upload_image_from_url(
                image_url,
                recipe_id,
                recipe_title
            )
            
            return stored_url
            
        except Exception as e:
            # Handle any OpenAI-related errors
            if hasattr(e, '__class__') and 'openai' in str(type(e)).lower():
                logger.error(f"OpenAI API error generating image for recipe {recipe_id}: {str(e)}")
            else:
                logger.error(f"Error generating image for recipe {recipe_id}: {str(e)}")
            return None
    
    async def generate_batch_recipe_images(self, recipes: list[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate images for multiple recipes
        
        Args:
            recipes: List of recipe dictionaries with id, title, ingredients, cuisine
            
        Returns:
            Dictionary mapping recipe_id to image URL
        """
        results = {}
        
        for recipe in recipes:
            recipe_id = str(recipe.get('id', ''))
            recipe_title = recipe.get('title', '')
            ingredients = recipe.get('ingredients', [])
            cuisine = recipe.get('cuisine', '')
            
            if recipe_id and recipe_title:
                image_url = await self.generate_and_store_recipe_image(
                    recipe_id,
                    recipe_title,
                    ingredients,
                    cuisine
                )
                if image_url:
                    results[recipe_id] = image_url
        
        return results
    
    def get_recipe_image(self, recipe_id: str) -> Optional[str]:
        """
        Get the stored image URL for a recipe if it exists
        
        Args:
            recipe_id: ID of the recipe
            
        Returns:
            URL of the stored image or None if not found
        """
        return self.gcs_service.get_recipe_image_url(recipe_id)
