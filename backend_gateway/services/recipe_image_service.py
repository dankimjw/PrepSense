"""Service for generating and managing recipe images using OpenAI GPT-4"""

import os
import logging
from typing import Optional, Dict, Any
from backend_gateway.services.gcs_service import GCSService
from backend_gateway.core.config import settings
from backend_gateway.core.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class RecipeImageService:
    """Service for generating recipe images using GPT-4 and storing them in GCS"""

    def __init__(self):
        # Initialize OpenAI client
        try:
            self.client = get_openai_client()
        except ValueError as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
            self.client = None

        # Initialize GCS service
        self.gcs_service = GCSService()


    def create_recipe_image_prompt(self, recipe_title: str, ingredients: list, cuisine: str = None) -> str:
        """
        Create an optimized prompt for GPT-4 to generate appetizing recipe images
        
        Args:
            recipe_title: Name of the recipe
            ingredients: List of main ingredients
            cuisine: Type of cuisine (optional)
            
        Returns:
            Formatted prompt for GPT-4
        """
        # Analyze dish type from title
        title_lower = recipe_title.lower()
        
        # Determine appropriate presentation style
        if "soup" in title_lower or "stew" in title_lower or "chowder" in title_lower:
            presentation = "in an elegant bowl, garnished beautifully, steam rising"
            style = "overhead angle showing the soup's texture and color"
        elif "appetizer" in title_lower or "starter" in title_lower:
            presentation = "on a modern appetizer plate, elegant small portions"
            style = "45-degree angle showcasing presentation"
        elif "salad" in title_lower:
            presentation = "in a modern salad bowl or plate, fresh and vibrant"
            style = "natural lighting emphasizing freshness"
        elif "dessert" in title_lower or "cake" in title_lower:
            presentation = "on a dessert plate with elegant plating"
            style = "close-up showing texture and details"
        else:
            presentation = "on a beautiful plate"
            style = "appetizing presentation"
        
        # Base prompt for food photography style
        base_prompt = f"Professional food photography, {style}, natural soft lighting, shallow depth of field"

        # Build the dish description more carefully
        recipe_prompt = f"beautifully plated {recipe_title}"

        # Add cuisine style if provided
        if cuisine:
            recipe_prompt = f"{cuisine} cuisine {recipe_prompt}"

        # Handle ingredients more thoughtfully
        if ingredients:
            # Skip generic ingredients and focus on visual ones
            visual_ingredients = []
            skip_words = ['salt', 'pepper', 'oil', 'water', 'stock', 'broth']
            for ing in ingredients[:3]:
                if not any(skip in ing.lower() for skip in skip_words):
                    visual_ingredients.append(ing)
            
            if visual_ingredients:
                recipe_prompt += f", garnished with fresh herbs"

        # Combine prompts with better structure
        full_prompt = f"{base_prompt}, {recipe_prompt}, {presentation}, restaurant quality, warm inviting colors, highly detailed, 4K, no text or labels"

        # Ensure prompt isn't too long (GPT-4 has a limit)
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
        Generate a recipe image using GPT-4 and store it in GCS
        
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
            if not self.client:
                logger.error("OpenAI API key not configured")
                return None

            # Create optimized prompt
            prompt = self.create_recipe_image_prompt(recipe_title, ingredients or [], cuisine)
            logger.info(f"Generating image for recipe {recipe_id} with prompt: {prompt}")

            # Generate image using DALL-E 3 with new API syntax
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )

            # Log the full OpenAI response for debugging
            print(f"\n🤖 OpenAI Image Generation Response:")
            print(f"   Recipe ID: {recipe_id}")
            print(f"   Model: dall-e-3")
            print(f"   Response data: {response.data}")
            print(f"   Full response: {response}")
            
            # Get the generated image URL
            image_url = response.data[0].url
            print(f"   Generated Image URL: {image_url}\n")

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
