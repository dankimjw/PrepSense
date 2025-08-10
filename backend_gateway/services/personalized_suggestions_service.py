"""
Personalized Suggestions Service for generating user-specific chat suggestions
based on dietary preferences, allergens, and pantry contents.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text

from backend_gateway.services.postgres_service import PostgresService

logger = logging.getLogger(__name__)


class PersonalizedSuggestionsService:
    """Service for generating personalized chat suggestions based on user preferences and pantry"""

    def __init__(self):
        self.db_service = PostgresService()

        # Base suggestion templates categorized by type
        self.suggestion_templates = {
            "dietary_specific": {
                "vegetarian": [
                    "What vegetarian recipes can I make tonight?",
                    "Show me plant-based dinner ideas",
                    "What can I cook with my vegetables?",
                    "Vegetarian recipes with protein alternatives",
                ],
                "vegan": [
                    "What vegan meals can I prepare?",
                    "Show me dairy-free and egg-free recipes",
                    "Plant-based dinner options for tonight",
                    "Vegan recipes using my ingredients",
                ],
                "gluten-free": [
                    "What gluten-free recipes can I make?",
                    "Show me wheat-free dinner options",
                    "Gluten-free meals with my pantry items",
                    "Safe recipes without gluten",
                ],
                "keto": [
                    "What low-carb keto recipes can I make?",
                    "High-fat, low-carb dinner ideas",
                    "Keto-friendly meals tonight",
                    "Show me ketogenic recipes",
                ],
                "paleo": [
                    "What paleo-friendly recipes can I cook?",
                    "Show me grain-free dinner options",
                    "Paleo meals with my ingredients",
                    "Whole foods recipes for tonight",
                ],
            },
            "allergen_safe": {
                "nuts": [
                    "What nut-free recipes are safe for me?",
                    "Show me allergy-safe dinner options",
                    "Recipes without nuts or nut oils",
                ],
                "dairy": [
                    "What dairy-free recipes can I make?",
                    "Show me lactose-free dinner ideas",
                    "Recipes without milk, cheese, or butter",
                ],
                "shellfish": [
                    "What shellfish-free seafood recipes are safe?",
                    "Show me fish recipes without shellfish",
                    "Safe seafood options for my allergy",
                ],
                "eggs": [
                    "What egg-free recipes can I cook?",
                    "Show me dinner options without eggs",
                    "Recipes safe for egg allergy",
                ],
            },
            "cuisine_specific": {
                "italian": [
                    "What Italian dishes can I make tonight?",
                    "Show me pasta and Italian recipes",
                    "Mediterranean dinner ideas",
                ],
                "mexican": [
                    "What Mexican recipes can I prepare?",
                    "Show me Latin American dinner ideas",
                    "Spicy Mexican dishes for tonight",
                ],
                "asian": [
                    "What Asian recipes can I cook?",
                    "Show me stir-fry and Asian dinner ideas",
                    "Oriental cuisine with my ingredients",
                ],
                "indian": [
                    "What Indian curry recipes can I make?",
                    "Show me spiced Indian dinner options",
                    "Flavorful Indian dishes tonight",
                ],
            },
            "expiring_items": [
                "What can I make with expiring ingredients?",
                "Help me use items that expire soon",
                "Recipes to prevent food waste",
                "Use my expiring pantry items",
            ],
            "quick_meals": [
                "What can I make in 20 minutes?",
                "Quick and easy dinner ideas",
                "Fast recipes for busy nights",
                "Simple meals under 30 minutes",
            ],
            "pantry_based": [
                "What can I make with ingredients I have?",
                "Show me recipes using my pantry",
                "Dinner ideas without shopping",
                "Use only what I have available",
            ],
            "healthy": [
                "What healthy recipes can I make tonight?",
                "Show me nutritious dinner options",
                "Low-calorie meals with my ingredients",
                "Balanced and wholesome recipes",
            ],
        }

    async def get_personalized_suggestions(self, user_id: int, limit: int = 6) -> list[str]:
        """
        Generate personalized chat suggestions based on user preferences and pantry

        Args:
            user_id: The user's ID
            limit: Maximum number of suggestions to return

        Returns:
            List of personalized suggestion strings
        """
        try:
            # Fetch user preferences
            user_preferences = await self._fetch_user_preferences(user_id)

            # Check for expiring items
            expiring_items = await self._check_expiring_items(user_id)

            # Generate suggestions based on user profile
            suggestions = []

            # Priority 1: Expiring items (highest priority for food safety)
            if expiring_items:
                suggestions.extend(self.suggestion_templates["expiring_items"][:2])
                logger.info(f"Added expiring items suggestions for user {user_id}")

            # Priority 2: Allergen-safe suggestions (critical for safety)
            allergen_suggestions = self._get_allergen_safe_suggestions(user_preferences)
            if allergen_suggestions:
                suggestions.extend(allergen_suggestions[:2])
                logger.info(f"Added allergen-safe suggestions for user {user_id}")

            # Priority 3: Dietary preference suggestions
            dietary_suggestions = self._get_dietary_suggestions(user_preferences)
            if dietary_suggestions:
                suggestions.extend(dietary_suggestions[:2])
                logger.info(f"Added dietary preference suggestions for user {user_id}")

            # Priority 4: Cuisine preference suggestions
            cuisine_suggestions = self._get_cuisine_suggestions(user_preferences)
            if cuisine_suggestions:
                suggestions.extend(cuisine_suggestions[:1])
                logger.info(f"Added cuisine preference suggestions for user {user_id}")

            # Fill remaining slots with general helpful suggestions
            remaining_slots = limit - len(suggestions)
            if remaining_slots > 0:
                general_suggestions = [
                    *self.suggestion_templates["pantry_based"][:1],
                    *self.suggestion_templates["quick_meals"][:1],
                    *self.suggestion_templates["healthy"][:1],
                ]
                suggestions.extend(general_suggestions[:remaining_slots])
                logger.info(f"Added general suggestions for user {user_id}")

            # Ensure we don't exceed the limit and remove duplicates
            unique_suggestions = []
            seen = set()
            for suggestion in suggestions:
                if suggestion not in seen and len(unique_suggestions) < limit:
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion)

            logger.info(
                f"Generated {len(unique_suggestions)} personalized suggestions for user {user_id}"
            )
            return unique_suggestions

        except Exception as e:
            logger.error(f"Error generating personalized suggestions for user {user_id}: {str(e)}")
            # Fallback to generic suggestions
            return self._get_fallback_suggestions(limit)

    async def _fetch_user_preferences(self, user_id: int) -> dict[str, Any]:
        """Fetch user dietary preferences and allergens"""
        try:
            query = text(
                """
                SELECT
                    dietary_preferences,
                    allergies,
                    cuisine_preferences,
                    household_size,
                    cooking_skill_level
                FROM user_preferences
                WHERE user_id = :user_id
            """
            )

            with self.db_service.get_session() as session:
                result = session.execute(query, {"user_id": user_id}).fetchone()

                if result:
                    return {
                        "dietary_preferences": result.dietary_preferences or [],
                        "allergens": result.allergies or [],
                        "cuisine_preferences": result.cuisine_preferences or [],
                        "household_size": result.household_size,
                        "cooking_skill_level": result.cooking_skill_level,
                    }
                else:
                    return {
                        "dietary_preferences": [],
                        "allergens": [],
                        "cuisine_preferences": [],
                        "household_size": None,
                        "cooking_skill_level": None,
                    }
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return {"dietary_preferences": [], "allergens": [], "cuisine_preferences": []}

    async def _check_expiring_items(self, user_id: int) -> list[dict[str, Any]]:
        """Check for items expiring in the next 7 days"""
        try:
            query = text(
                """
                SELECT
                    pi.name as product_name,
                    pi.expiration_date,
                    pi.quantity,
                    pi.quantity_consumed
                FROM pantry_items pi
                WHERE pi.user_id = :user_id
                    AND pi.expiration_date IS NOT NULL
                    AND pi.expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                    AND pi.quantity > COALESCE(pi.quantity_consumed, 0)
                    AND pi.is_deleted = false
                ORDER BY pi.expiration_date ASC
            """
            )

            with self.db_service.get_session() as session:
                result = session.execute(query, {"user_id": user_id})
                expiring_items = []

                for row in result:
                    days_until_expiry = (row.expiration_date - datetime.now().date()).days
                    expiring_items.append(
                        {
                            "product_name": row.product_name,
                            "expiration_date": row.expiration_date,
                            "days_until_expiry": days_until_expiry,
                            "quantity": row.quantity,
                            "quantity_consumed": row.quantity_consumed or 0,
                        }
                    )

                return expiring_items[:5]  # Limit to 5 most urgent items

        except Exception as e:
            logger.error(f"Error checking expiring items: {str(e)}")
            return []

    def _get_allergen_safe_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate allergen-safe suggestions based on user allergens"""
        allergens = user_preferences.get("allergens", [])
        if not allergens:
            return []

        suggestions = []
        for allergen in allergens[:2]:  # Limit to top 2 allergens to avoid overwhelming
            allergen_lower = allergen.lower()
            if allergen_lower in self.suggestion_templates["allergen_safe"]:
                suggestions.extend(self.suggestion_templates["allergen_safe"][allergen_lower][:1])
            else:
                # Generic allergen-safe suggestion
                suggestions.append(f"What {allergen}-free recipes are safe for me?")

        return suggestions

    def _get_dietary_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate dietary preference-based suggestions"""
        dietary_prefs = user_preferences.get("dietary_preferences", [])
        if not dietary_prefs:
            return []

        suggestions = []
        for diet in dietary_prefs[:2]:  # Limit to top 2 dietary preferences
            diet_lower = diet.lower()
            if diet_lower in self.suggestion_templates["dietary_specific"]:
                suggestions.extend(self.suggestion_templates["dietary_specific"][diet_lower][:1])
            else:
                # Generic dietary suggestion
                suggestions.append(f"What {diet} recipes can I make tonight?")

        return suggestions

    def _get_cuisine_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate cuisine preference-based suggestions"""
        cuisine_prefs = user_preferences.get("cuisine_preferences", [])
        if not cuisine_prefs:
            return []

        suggestions = []
        for cuisine in cuisine_prefs[:1]:  # Limit to 1 cuisine to keep suggestions diverse
            cuisine_lower = cuisine.lower()
            if cuisine_lower in self.suggestion_templates["cuisine_specific"]:
                suggestions.extend(self.suggestion_templates["cuisine_specific"][cuisine_lower][:1])
            else:
                # Generic cuisine suggestion
                suggestions.append(f"What {cuisine} recipes can I cook tonight?")

        return suggestions

    def _get_fallback_suggestions(self, limit: int) -> list[str]:
        """Fallback suggestions when personalization fails"""
        fallback = [
            "What can I make for dinner?",
            "What can I make with ingredients I have?",
            "Show me healthy recipes",
            "Quick meals under 20 minutes",
            "What should I cook tonight?",
            "Help me use expiring ingredients",
        ]
        return fallback[:limit]

    async def get_suggestion_context(self, user_id: int, suggestion: str) -> dict[str, Any]:
        """
        Get context about why a suggestion was made for the user

        Args:
            user_id: The user's ID
            suggestion: The suggestion text

        Returns:
            Dict with context about the suggestion
        """
        try:
            user_preferences = await self._fetch_user_preferences(user_id)
            expiring_items = await self._check_expiring_items(user_id)

            context = {
                "suggestion": suggestion,
                "user_id": user_id,
                "reasoning": [],
                "safety_considerations": [],
                "personalization_applied": True,
            }

            # Analyze why this suggestion was made
            suggestion_lower = suggestion.lower()

            if "expir" in suggestion_lower and expiring_items:
                context["reasoning"].append(f"You have {len(expiring_items)} items expiring soon")
                context["expiring_items"] = expiring_items
                context["safety_considerations"].append(
                    "Prioritizing expiring items to prevent waste"
                )

            if user_preferences.get("allergens"):
                for allergen in user_preferences["allergens"]:
                    if allergen.lower() in suggestion_lower:
                        context["reasoning"].append(f"Personalized for your {allergen} allergy")
                        context["safety_considerations"].append(
                            f"Will exclude {allergen} from all recommendations"
                        )

            if user_preferences.get("dietary_preferences"):
                for diet in user_preferences["dietary_preferences"]:
                    if diet.lower() in suggestion_lower:
                        context["reasoning"].append(f"Matched your {diet} dietary preference")

            if user_preferences.get("cuisine_preferences"):
                for cuisine in user_preferences["cuisine_preferences"]:
                    if cuisine.lower() in suggestion_lower:
                        context["reasoning"].append(f"Based on your love for {cuisine} cuisine")

            return context

        except Exception as e:
            logger.error(f"Error getting suggestion context: {str(e)}")
            return {
                "suggestion": suggestion,
                "user_id": user_id,
                "reasoning": ["Generic suggestion"],
                "safety_considerations": [],
                "personalization_applied": False,
            }
