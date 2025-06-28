"""Logic for generating recipes using OpenAI based on pantry items."""

import os
import pandas as pd
from fastapi import HTTPException
from pydantic import BaseModel
import openai  # Ensure OpenAI API is properly configured
from ..core.config_utils import get_openai_api_key

class RecipeService:
    """
    Service class for generating recipes and associated images.
    """

    def __init__(self):
        # Initialize any required configurations, e.g., OpenAI API key
        try:
            openai.api_key = get_openai_api_key()
            print(f"Using OpenAI model: gpt-4")
        except ValueError as e:
            raise ValueError(f"OpenAI configuration error: {e}")

    def generate_recipe_from_pantry(self, pantry_db: pd.DataFrame) -> str:
        """
        Generates a recipe based on the provided pantry items.

        Args:
            pantry_db (pd.DataFrame): A DataFrame containing pantry items.

        Returns:
            str: A generated recipe as a string.
        """
        try:
            # Convert pantry items to a list for the prompt
            pantry_items = pantry_db["Item Name"].tolist()
            prompt = (
                f"Generate a recipe using the following ingredients: {', '.join(pantry_items)}. "
                "Provide detailed instructions and include a dish name."
            )

            # Call OpenAI API to generate the recipe
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Updated model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            recipe_text = response.choices[0].message["content"].strip()
            return recipe_text

        except openai.APIError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def generate_recipe_image(self, dish_name: str) -> str:
        """
        Generates an image for the given dish name.

        Args:
            dish_name (str): The name of the dish.

        Returns:
            str: The file path or URL of the generated image.
        """
        try:
            print("Processing image...")
            # Use OpenAI's DALL-E or another image generation API
            response = openai.Image.create(
                prompt=f"An appetizing dish of {dish_name}",
                n=1,
                size="512x512",
            )

            # Save the image locally or return the URL
            image_url = response["data"][0]["url"]
            return image_url

        except openai.APIError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def process_image(self, file):
        try:
            # API key is already set in __init__
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Test message to OpenAI"}
                ],
                max_tokens=100,
                temperature=0.7,
            )
            print(response)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error
            raise RuntimeError(f"Error communicating with OpenAI API: {str(e)}")