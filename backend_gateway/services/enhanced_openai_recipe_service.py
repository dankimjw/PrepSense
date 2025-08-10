"""Enhanced OpenAI Recipe Service
Generates Spoonacular-compatible rich recipe data using OpenAI API.
Creates recipes with comprehensive nutrition, structured ingredients, and detailed instructions.
"""

import json
import logging
import re
from typing import Any, Optional

from openai import OpenAI

from backend_gateway.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EnhancedOpenAIRecipeService:
    """Service for generating Spoonacular-compatible recipes using OpenAI"""

    def __init__(self):
        """Initialize the service with OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.recipe_id_counter = 3000  # Start from 3000 for OpenAI-generated recipes

    def generate_enhanced_recipe(
        self,
        recipe_name: str,
        available_ingredients: list[str],
        dietary_restrictions: Optional[list[str]] = None,
        allergens: Optional[list[str]] = None,
        cuisine_type: Optional[str] = None,
        cooking_time: Optional[int] = None,
        servings: Optional[int] = None,
    ) -> dict[str, Any]:
        """Generate a Spoonacular-compatible recipe with rich data structure

        Args:
            recipe_name: Name of the recipe to generate
            available_ingredients: List of available ingredients
            dietary_restrictions: User dietary preferences (vegetarian, vegan, etc.)
            allergens: User allergens to avoid
            cuisine_type: Preferred cuisine type
            cooking_time: Maximum cooking time in minutes
            servings: Number of servings

        Returns:
            Dict containing rich recipe data compatible with Spoonacular format
        """
        if not self.client:
            logger.warning("OpenAI API key not configured, returning fallback recipe")
            return self._create_fallback_recipe(recipe_name, available_ingredients)

        try:
            # Generate the structured recipe using OpenAI
            structured_recipe = self._generate_structured_recipe(
                recipe_name=recipe_name,
                available_ingredients=available_ingredients,
                dietary_restrictions=dietary_restrictions or [],
                allergens=allergens or [],
                cuisine_type=cuisine_type,
                cooking_time=cooking_time,
                servings=servings,
            )

            # Validate and enhance the recipe
            enhanced_recipe = self._enhance_recipe_structure(structured_recipe)

            # Add metadata and compatibility fields
            final_recipe = self._add_recipe_metadata(enhanced_recipe, available_ingredients)

            return final_recipe

        except Exception as e:
            logger.error(f"Error generating enhanced recipe: {str(e)}")
            return self._create_fallback_recipe(recipe_name, available_ingredients)

    def _generate_structured_recipe(
        self,
        recipe_name: str,
        available_ingredients: list[str],
        dietary_restrictions: list[str],
        allergens: list[str],
        cuisine_type: Optional[str],
        cooking_time: Optional[int],
        servings: Optional[int],
    ) -> dict[str, Any]:
        """Generate structured recipe using OpenAI with detailed prompt"""

        # Create comprehensive prompt for structured recipe generation
        prompt = self._create_recipe_prompt(
            recipe_name,
            available_ingredients,
            dietary_restrictions,
            allergens,
            cuisine_type,
            cooking_time,
            servings,
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional chef and recipe developer. Generate detailed, structured recipes in JSON format that match the Spoonacular API schema exactly. Include comprehensive nutrition data, detailed instructions, and proper ingredient measurements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_completion_tokens=2500,
            )

            recipe_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            recipe_json = self._extract_json_from_response(recipe_text)

            if recipe_json:
                return recipe_json
            else:
                logger.warning(
                    "Failed to extract JSON from OpenAI response, creating structured fallback"
                )
                return self._create_structured_fallback(recipe_name, available_ingredients)

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return self._create_structured_fallback(recipe_name, available_ingredients)

    def _create_recipe_prompt(
        self,
        recipe_name: str,
        available_ingredients: list[str],
        dietary_restrictions: list[str],
        allergens: list[str],
        cuisine_type: Optional[str],
        cooking_time: Optional[int],
        servings: Optional[int],
    ) -> str:
        """Create comprehensive prompt for recipe generation"""

        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text += f"\nDietary restrictions: {', '.join(dietary_restrictions)}"
        if allergens:
            restrictions_text += f"\nAllergens to avoid: {', '.join(allergens)}"

        constraints_text = ""
        if cooking_time:
            constraints_text += f"\nMaximum cooking time: {cooking_time} minutes"
        if servings:
            constraints_text += f"\nServings: {servings}"
        if cuisine_type:
            constraints_text += f"\nCuisine type: {cuisine_type}"

        prompt = f"""
Create a detailed recipe for "{recipe_name}" using these available ingredients: {', '.join(available_ingredients)}

{restrictions_text}
{constraints_text}

Return ONLY a valid JSON object with this EXACT structure:

{{
  "title": "Recipe Name",
  "summary": "Brief appetizing description of the dish",
  "readyInMinutes": 30,
  "servings": 4,
  "cuisines": ["cuisine_type"],
  "dishTypes": ["main course", "dinner"],
  "diets": ["vegetarian"],
  "occasions": ["casual", "weeknight"],
  "extendedIngredients": [
    {{
      "name": "ingredient_name",
      "original": "2 cups ingredient_name, diced",
      "amount": 2.0,
      "unit": "cups",
      "aisle": "Produce",
      "meta": ["diced"],
      "measures": {{
        "us": {{"amount": 2.0, "unitShort": "cups", "unitLong": "cups"}},
        "metric": {{"amount": 473.0, "unitShort": "ml", "unitLong": "milliliters"}}
      }}
    }}
  ],
  "analyzedInstructions": [{{
    "steps": [
      {{
        "number": 1,
        "step": "Detailed cooking instruction with specific techniques",
        "ingredients": [{{"name": "ingredient_used", "id": 1}}],
        "equipment": [{{"name": "equipment_needed", "id": 1}}],
        "length": {{"number": 5, "unit": "minutes"}}
      }}
    ]
  }}],
  "nutrition": {{
    "nutrients": [
      {{"name": "Calories", "amount": 420, "unit": "kcal"}},
      {{"name": "Protein", "amount": 32, "unit": "g"}},
      {{"name": "Fat", "amount": 12, "unit": "g"}},
      {{"name": "Carbohydrates", "amount": 45, "unit": "g"}},
      {{"name": "Fiber", "amount": 8, "unit": "g"}},
      {{"name": "Sugar", "amount": 6, "unit": "g"}},
      {{"name": "Sodium", "amount": 800, "unit": "mg"}},
      {{"name": "Saturated Fat", "amount": 4, "unit": "g"}}
    ],
    "caloricBreakdown": {{
      "percentProtein": 30,
      "percentFat": 26,
      "percentCarbs": 44
    }}
  }}
}}

Requirements:
- Use realistic cooking times and techniques
- Provide accurate nutritional estimates
- Include 6-8 detailed cooking steps
- Specify equipment needed for each step
- Use proper ingredient measurements and units
- Include meta information (chopped, diced, etc.)
- Ensure cuisine/diet tags match the recipe content
- Make instructions clear and actionable
"""
        return prompt

    def _extract_json_from_response(self, response_text: str) -> Optional[dict[str, Any]]:
        """Extract JSON from OpenAI response text"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                return json.loads(json_text)

            # If no JSON found, try parsing the entire response
            return json.loads(response_text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            return None

    def _enhance_recipe_structure(self, recipe_data: dict[str, Any]) -> dict[str, Any]:
        """Enhance and validate recipe structure"""
        enhanced_recipe = recipe_data.copy()

        # Ensure required fields exist with defaults
        enhanced_recipe.setdefault("title", "Generated Recipe")
        enhanced_recipe.setdefault("summary", "A delicious recipe generated for you")
        enhanced_recipe.setdefault("readyInMinutes", 30)
        enhanced_recipe.setdefault("servings", 4)
        enhanced_recipe.setdefault("cuisines", ["American"])
        enhanced_recipe.setdefault("dishTypes", ["main course"])
        enhanced_recipe.setdefault("diets", [])
        enhanced_recipe.setdefault("occasions", ["casual"])

        # Validate and enhance ingredients
        if "extendedIngredients" not in enhanced_recipe:
            enhanced_recipe["extendedIngredients"] = []

        for i, ingredient in enumerate(enhanced_recipe["extendedIngredients"]):
            ingredient.setdefault("id", i + 1)
            ingredient.setdefault("aisle", "Unknown")
            ingredient.setdefault("meta", [])

            # Ensure measures exist
            if "measures" not in ingredient:
                amount = ingredient.get("amount", 1)
                unit = ingredient.get("unit", "item")
                ingredient["measures"] = {
                    "us": {"amount": amount, "unitShort": unit, "unitLong": unit},
                    "metric": {"amount": amount, "unitShort": unit, "unitLong": unit},
                }

        # Validate and enhance instructions
        if "analyzedInstructions" not in enhanced_recipe:
            enhanced_recipe["analyzedInstructions"] = [{"steps": []}]

        for instruction_set in enhanced_recipe["analyzedInstructions"]:
            if "steps" not in instruction_set:
                instruction_set["steps"] = []

            for step in instruction_set["steps"]:
                step.setdefault("ingredients", [])
                step.setdefault("equipment", [])
                step.setdefault("length", {"number": 5, "unit": "minutes"})

        # Validate and enhance nutrition
        if "nutrition" not in enhanced_recipe:
            enhanced_recipe["nutrition"] = self._create_default_nutrition()

        nutrition = enhanced_recipe["nutrition"]
        if "nutrients" not in nutrition:
            nutrition["nutrients"] = self._create_default_nutrients()

        if "caloricBreakdown" not in nutrition:
            nutrition["caloricBreakdown"] = {
                "percentProtein": 25,
                "percentFat": 30,
                "percentCarbs": 45,
            }

        # Add convenience fields from nutrients
        nutrients_dict = {n["name"]: n["amount"] for n in nutrition["nutrients"]}
        nutrition["calories"] = nutrients_dict.get("Calories", 400)
        nutrition["protein"] = nutrients_dict.get("Protein", 20)
        nutrition["carbs"] = nutrients_dict.get("Carbohydrates", 45)
        nutrition["carbohydrates"] = nutrients_dict.get("Carbohydrates", 45)
        nutrition["fat"] = nutrients_dict.get("Fat", 15)
        nutrition["fiber"] = nutrients_dict.get("Fiber", 5)
        nutrition["sugar"] = nutrients_dict.get("Sugar", 8)

        return enhanced_recipe

    def _add_recipe_metadata(
        self, recipe: dict[str, Any], available_ingredients: list[str]
    ) -> dict[str, Any]:
        """Add metadata and compatibility fields"""
        # Generate unique ID
        self.recipe_id_counter += 1
        recipe["id"] = self.recipe_id_counter

        # Add compatibility fields for both formats
        recipe["name"] = recipe.get("title", "Generated Recipe")  # For chat format compatibility

        # Generate image URL (placeholder for now)
        recipe["image"] = f"https://spoonacular.com/recipeImages/{recipe['id']}-556x370.jpg"

        # Add ingredient matching data
        recipe_ingredients = [ing["name"].lower() for ing in recipe.get("extendedIngredients", [])]
        available_lower = [ing.lower() for ing in available_ingredients]

        matched_ingredients = [ing for ing in recipe_ingredients if ing in available_lower]
        missing_ingredients = [ing for ing in recipe_ingredients if ing not in available_lower]

        recipe["available_ingredients"] = matched_ingredients
        recipe["missing_ingredients"] = missing_ingredients
        recipe["available_count"] = len(matched_ingredients)
        recipe["missing_count"] = len(missing_ingredients)
        recipe["match_score"] = (
            len(matched_ingredients) / len(recipe_ingredients) if recipe_ingredients else 0
        )

        # Add source information
        recipe["source"] = "openai_enhanced"
        recipe["sourceUrl"] = f"https://prepsense.app/recipes/{recipe['id']}"

        # Add safety status (will be validated by safety service)
        recipe["safety_status"] = "SAFE"
        recipe["safety_violations"] = []
        recipe["safety_warnings"] = []
        recipe["allergen_risks"] = []

        return recipe

    def _create_default_nutrition(self) -> dict[str, Any]:
        """Create default nutrition data"""
        return {
            "nutrients": self._create_default_nutrients(),
            "caloricBreakdown": {"percentProtein": 25, "percentFat": 30, "percentCarbs": 45},
            "calories": 400,
            "protein": 20,
            "carbs": 45,
            "carbohydrates": 45,
            "fat": 15,
            "fiber": 5,
            "sugar": 8,
        }

    def _create_default_nutrients(self) -> list[dict[str, Any]]:
        """Create default nutrient list"""
        return [
            {"name": "Calories", "amount": 400, "unit": "kcal"},
            {"name": "Protein", "amount": 20, "unit": "g"},
            {"name": "Fat", "amount": 15, "unit": "g"},
            {"name": "Carbohydrates", "amount": 45, "unit": "g"},
            {"name": "Fiber", "amount": 5, "unit": "g"},
            {"name": "Sugar", "amount": 8, "unit": "g"},
            {"name": "Sodium", "amount": 600, "unit": "mg"},
            {"name": "Saturated Fat", "amount": 5, "unit": "g"},
        ]

    def _create_structured_fallback(
        self, recipe_name: str, available_ingredients: list[str]
    ) -> dict[str, Any]:
        """Create a structured fallback recipe when OpenAI fails"""
        return {
            "title": recipe_name,
            "summary": f"A simple {recipe_name.lower()} recipe using available ingredients",
            "readyInMinutes": 30,
            "servings": 4,
            "cuisines": ["American"],
            "dishTypes": ["main course"],
            "diets": [],
            "occasions": ["casual"],
            "extendedIngredients": [
                {
                    "id": i + 1,
                    "name": ingredient.lower(),
                    "original": f"1 cup {ingredient}",
                    "amount": 1.0,
                    "unit": "cup",
                    "aisle": "Unknown",
                    "meta": [],
                    "measures": {
                        "us": {"amount": 1.0, "unitShort": "cup", "unitLong": "cup"},
                        "metric": {"amount": 240, "unitShort": "ml", "unitLong": "milliliters"},
                    },
                }
                for i, ingredient in enumerate(available_ingredients[:6])
            ],
            "analyzedInstructions": [
                {
                    "steps": [
                        {
                            "number": 1,
                            "step": f"Prepare all ingredients for {recipe_name.lower()}.",
                            "ingredients": [],
                            "equipment": [],
                            "length": {"number": 10, "unit": "minutes"},
                        },
                        {
                            "number": 2,
                            "step": "Combine ingredients according to your preferred method.",
                            "ingredients": [],
                            "equipment": [],
                            "length": {"number": 20, "unit": "minutes"},
                        },
                    ]
                }
            ],
            "nutrition": self._create_default_nutrition(),
        }

    def _create_fallback_recipe(
        self, recipe_name: str, available_ingredients: list[str]
    ) -> dict[str, Any]:
        """Create a basic fallback recipe when all else fails"""
        fallback = self._create_structured_fallback(recipe_name, available_ingredients)
        return self._add_recipe_metadata(fallback, available_ingredients)

    def batch_generate_recipes(
        self, recipe_requests: list[dict[str, Any]], max_concurrent: int = 3
    ) -> list[dict[str, Any]]:
        """Generate multiple recipes with rate limiting

        Args:
            recipe_requests: List of recipe request dictionaries
            max_concurrent: Maximum concurrent OpenAI requests

        Returns:
            List of generated recipes
        """
        import concurrent.futures

        results = []

        # Process in batches to respect rate limits
        for i in range(0, len(recipe_requests), max_concurrent):
            batch = recipe_requests[i : i + max_concurrent]

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [
                    executor.submit(self.generate_enhanced_recipe, **request) for request in batch
                ]

                for future in concurrent.futures.as_completed(futures):
                    try:
                        recipe = future.result()
                        results.append(recipe)
                    except Exception as e:
                        logger.error(f"Error in batch recipe generation: {str(e)}")
                        # Add a fallback recipe for failed generations
                        failed_request = batch[len(results) % len(batch)]
                        fallback_recipe = self._create_fallback_recipe(
                            failed_request.get("recipe_name", "Failed Recipe"),
                            failed_request.get("available_ingredients", []),
                        )
                        results.append(fallback_recipe)

        return results

    def validate_recipe_structure(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Validate that a recipe matches the expected Spoonacular structure

        Args:
            recipe: Recipe dictionary to validate

        Returns:
            Validation result with status and issues
        """
        issues = []

        # Check required top-level fields
        required_fields = [
            "id",
            "title",
            "extendedIngredients",
            "analyzedInstructions",
            "nutrition",
        ]
        for field in required_fields:
            if field not in recipe:
                issues.append(f"Missing required field: {field}")

        # Validate extendedIngredients structure
        if "extendedIngredients" in recipe:
            for i, ingredient in enumerate(recipe["extendedIngredients"]):
                if not isinstance(ingredient, dict):
                    issues.append(f"Ingredient {i} is not a dictionary")
                else:
                    required_ing_fields = ["name", "original", "amount", "unit"]
                    for field in required_ing_fields:
                        if field not in ingredient:
                            issues.append(f"Ingredient {i} missing field: {field}")

        # Validate analyzedInstructions structure
        if "analyzedInstructions" in recipe:
            if not isinstance(recipe["analyzedInstructions"], list):
                issues.append("analyzedInstructions must be a list")
            else:
                for i, instruction_set in enumerate(recipe["analyzedInstructions"]):
                    if "steps" not in instruction_set:
                        issues.append(f"Instruction set {i} missing 'steps'")
                    else:
                        for j, step in enumerate(instruction_set["steps"]):
                            if "step" not in step:
                                issues.append(f"Step {j} missing 'step' text")

        # Validate nutrition structure
        if "nutrition" in recipe:
            nutrition = recipe["nutrition"]
            if "nutrients" not in nutrition:
                issues.append("Nutrition missing 'nutrients' array")
            if "caloricBreakdown" not in nutrition:
                issues.append("Nutrition missing 'caloricBreakdown'")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10),  # Simple scoring system
        }


# Export the service
__all__ = ["EnhancedOpenAIRecipeService"]
