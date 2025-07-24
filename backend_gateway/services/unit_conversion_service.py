"""
AI-powered unit conversion and validation service
"""

import logging
from typing import Dict, Optional, Any, List, Tuple
from decimal import Decimal
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.constants.units import (
    normalize_unit, get_unit_category, convert_quantity,
    UnitCategory, UNIT_INFO
)
from crewai import Agent, Task, Crew
import openai
import os

logger = logging.getLogger(__name__)


class UnitConversionService:
    """
    Service for intelligent unit conversion and validation using both
    Spoonacular API and AI agents for complex cases
    """

    def __init__(self):
        self.spoonacular = SpoonacularService()
        self._setup_openai()

    def _setup_openai(self):
        """Setup OpenAI API key"""
        try:
            from backend_gateway.core.config_utils import get_openai_api_key
            os.environ['OPENAI_API_KEY'] = openai.api_key
        except Exception as e:
            logger.error(f"Failed to setup OpenAI: {e}")

    def convert_ingredient_with_fallback(
        self,
        ingredient_name: str,
        source_amount: Optional[float],
        source_unit: Optional[str],
        target_unit: str,
        pantry_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Convert ingredient amounts with multiple fallback strategies
        
        Args:
            ingredient_name: Name of the ingredient
            source_amount: Amount in source unit
            source_unit: Source unit (might be descriptive like "large")
            target_unit: Target unit from pantry
            pantry_context: Optional context about the pantry item
            
        Returns:
            Conversion result with confidence level
        """
        logger.info(f"Converting {source_amount} {source_unit} of {ingredient_name} to {target_unit}")

        # Handle None or missing amounts/units
        if source_amount is None or source_unit is None:
            return {
                "success": False,
                "method": "no_amount",
                "source_amount": source_amount,
                "source_unit": source_unit,
                "target_amount": 0,
                "target_unit": target_unit,
                "confidence": 0.0,
                "message": f"No amount specified for {ingredient_name} (e.g., 'to taste')",
                "warning": True
            }

        # Convert Decimal to float if needed
        if hasattr(source_amount, '__float__'):
            source_amount = float(source_amount)

        # Step 1: Handle descriptive units (large, medium, small, fresh)
        if source_unit and source_unit.lower() in ["large", "medium", "small", "fresh", "ripe"]:
            logger.info(f"Detected descriptive unit: {source_unit}")
            # For countable items with descriptive units, default to "each"
            if self._is_countable_item(ingredient_name):
                source_unit = "each"
                logger.info(f"Converting descriptive unit to 'each' for countable item")

        # Step 2: Try Spoonacular conversion first
        try:
            spoon_result = self.spoonacular.convert_amount(
                ingredient_name, source_amount, source_unit, target_unit
            )
            if spoon_result and spoon_result.get("targetAmount"):
                logger.info(f"Spoonacular conversion successful: {spoon_result}")
                return {
                    "success": True,
                    "method": "spoonacular",
                    "source_amount": source_amount,
                    "source_unit": source_unit,
                    "target_amount": spoon_result["targetAmount"],
                    "target_unit": target_unit,
                    "confidence": 0.95,
                    "message": spoon_result.get("answer", "")
                }
        except Exception as e:
            logger.warning(f"Spoonacular conversion failed: {e}")

        # Step 3: Try internal conversion system
        try:
            internal_result = self._try_internal_conversion(
                ingredient_name, source_amount, source_unit, target_unit
            )
            if internal_result:
                return internal_result
        except Exception as e:
            logger.warning(f"Internal conversion failed: {e}")

        # Step 4: Use AI agent for complex conversions
        try:
            ai_result = self._ai_conversion_agent(
                ingredient_name, source_amount, source_unit, target_unit, pantry_context
            )
            if ai_result:
                return ai_result
        except Exception as e:
            logger.error(f"AI conversion failed: {e}")

        # Step 5: Fallback - return original amount with warning
        return {
            "success": False,
            "method": "fallback",
            "source_amount": source_amount,
            "source_unit": source_unit,
            "target_amount": source_amount,
            "target_unit": source_unit,
            "confidence": 0.0,
            "message": f"Could not convert {source_unit} to {target_unit} for {ingredient_name}. Using original amount.",
            "warning": True
        }

    def _is_countable_item(self, ingredient_name: str) -> bool:
        """Check if an ingredient is typically counted as individual items"""
        countable_keywords = [
            "egg", "apple", "banana", "orange", "tomato", "potato", "onion",
            "pepper", "carrot", "lemon", "lime", "avocado", "berry", "grape",
            "peach", "pear", "plum", "clove", "chicken breast", "steak"
        ]
        ingredient_lower = ingredient_name.lower()
        return any(keyword in ingredient_lower for keyword in countable_keywords)

    def _try_internal_conversion(
        self,
        ingredient_name: str,
        source_amount: Optional[float],
        source_unit: Optional[str],
        target_unit: str
    ) -> Optional[Dict[str, Any]]:
        """Try conversion using internal unit system"""
        source_norm = normalize_unit(source_unit)
        target_norm = normalize_unit(target_unit)

        # Check if units are in the same category
        source_cat = get_unit_category(source_norm)
        target_cat = get_unit_category(target_norm)

        if source_cat and target_cat and source_cat == target_cat:
            converted = convert_quantity(source_amount, source_norm, target_norm)
            if converted is not None:
                return {
                    "success": True,
                    "method": "internal",
                    "source_amount": source_amount,
                    "source_unit": source_unit,
                    "target_amount": converted,
                    "target_unit": target_unit,
                    "confidence": 0.85,
                    "message": f"Converted using internal {source_cat} conversion"
                }

        return None

    def _ai_conversion_agent(
        self,
        ingredient_name: str,
        source_amount: float,
        source_unit: str,
        target_unit: str,
        pantry_context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Use AI agent for complex unit conversions"""

        # Create specialized conversion agent
        conversion_agent = Agent(
            role="Culinary Unit Conversion Expert",
            goal="Convert ingredient quantities between different units accurately",
            backstory="""You are an expert chef and food scientist with deep knowledge 
            of ingredient densities, common cooking measurements, and unit conversions. 
            You understand that different ingredients have different densities and that 
            some conversions require specific knowledge about the ingredient.""",
            verbose=False,
            allow_delegation=False
        )

        # Build context string
        context = f"Ingredient: {ingredient_name}\n"
        context += f"Convert: {source_amount} {source_unit} to {target_unit}\n"
        if pantry_context:
            context += f"Pantry item info: {pantry_context}\n"

        # Create conversion task
        conversion_task = Task(
            description=f"""
            Convert {source_amount} {source_unit} of {ingredient_name} to {target_unit}.
            
            Consider:
            1. If "{source_unit}" is a descriptor (large, medium, small), interpret it appropriately
            2. Common cooking conversions and typical ingredient densities
            3. Whether the ingredient is countable (like eggs) or measurable by weight/volume
            
            Return a JSON object with these exact fields:
            {{
                "target_amount": <number>,
                "explanation": "<brief explanation of conversion>",
                "confidence": <0.0 to 1.0>
            }}
            
            Be precise with the target_amount. If conversion is not possible, set target_amount to null.
            """,
            agent=conversion_agent,
            expected_output="JSON object with target_amount, explanation, and confidence"
        )

        try:
            # Execute conversion
            crew = Crew(
                agents=[conversion_agent],
                tasks=[conversion_task],
                verbose=False
            )

            result = crew.kickoff()

            # Parse AI response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', str(result), re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())

                if ai_data.get("target_amount") is not None:
                    return {
                        "success": True,
                        "method": "ai_agent",
                        "source_amount": source_amount,
                        "source_unit": source_unit,
                        "target_amount": float(ai_data["target_amount"]),
                        "target_unit": target_unit,
                        "confidence": float(ai_data.get("confidence", 0.7)),
                        "message": ai_data.get("explanation", "AI-powered conversion")
                    }

        except Exception as e:
            logger.error(f"AI conversion agent error: {e}")

        return None

    def validate_and_suggest_units(
        self,
        ingredient_name: str,
        current_unit: str,
        quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate if a unit is appropriate and suggest better alternatives
        
        Args:
            ingredient_name: Name of the ingredient
            current_unit: Current unit being used
            quantity: Optional quantity for context
            
        Returns:
            Validation result with suggestions
        """
        # First check with Spoonacular
        spoon_validation = self.spoonacular.validate_unit_for_ingredient(
            ingredient_name, current_unit
        )

        # Enhance with AI analysis for edge cases
        if not spoon_validation["is_valid"]:
            # Use AI to understand why the unit might be wrong
            ai_suggestion = self._ai_unit_suggestion(
                ingredient_name, current_unit, quantity
            )

            if ai_suggestion:
                spoon_validation["ai_suggestion"] = ai_suggestion
                spoon_validation["message"] = ai_suggestion.get("reasoning", spoon_validation["message"])

        return spoon_validation

    def _ai_unit_suggestion(
        self,
        ingredient_name: str,
        current_unit: str,
        quantity: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Get AI suggestions for better units"""

        suggestion_agent = Agent(
            role="Culinary Measurement Expert",
            goal="Suggest appropriate units for ingredients",
            backstory="""You are a professional chef who understands the best ways 
            to measure different ingredients for accuracy and convenience in cooking.""",
            verbose=False,
            allow_delegation=False
        )

        quantity_str = f"{quantity} " if quantity else ""

        suggestion_task = Task(
            description=f"""
            The user is trying to measure {quantity_str}{current_unit} of {ingredient_name}.
            
            Analyze if this is a reasonable unit for this ingredient and suggest better alternatives if needed.
            
            Return a JSON object with:
            {{
                "is_reasonable": <true/false>,
                "best_unit": "<most appropriate unit>",
                "alternatives": ["<unit1>", "<unit2>", ...],
                "reasoning": "<brief explanation>"
            }}
            """,
            agent=suggestion_agent,
            expected_output="JSON object with unit suggestions"
        )

        try:
            crew = Crew(
                agents=[suggestion_agent],
                tasks=[suggestion_task],
                verbose=False
            )

            result = crew.kickoff()

            # Parse response
            import json
            import re

            json_match = re.search(r'\{[^}]+\}', str(result), re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            logger.error(f"AI unit suggestion error: {e}")

        return None


# Singleton instance
_unit_conversion_service = None


def get_unit_conversion_service() -> UnitConversionService:
    """Get singleton instance of UnitConversionService"""
    global _unit_conversion_service
    if _unit_conversion_service is None:
        _unit_conversion_service = UnitConversionService()
    return _unit_conversion_service