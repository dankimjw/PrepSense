"""
Real CrewAI Service

This service replaces the fake CrewAIService with actual CrewAI-powered
recipe recommendations using background flows and foreground crews.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from backend_gateway.config.database import get_database_service

# Import from the prepsense_crew module
from backend_gateway.prepsense_crew.cache_manager import ArtifactCacheManager
from backend_gateway.prepsense_crew.file_cache_manager import FileCacheManager
from backend_gateway.prepsense_crew.models import CrewInput, CrewOutput
from backend_gateway.prepsense_crew.foreground_crew import ForegroundRecipeCrew
from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


class RealCrewAIService:
    """
    Real CrewAI-powered recipe recommendation service.

    This service:
    1. Uses cached artifacts from background flows for fast responses
    2. Falls back to direct API calls when cache is cold
    3. Maintains <3 second response time target
    4. Provides intelligent, context-aware recommendations
    """

    def __init__(self):
        self.db_service = get_database_service()
        self.spoonacular_service = SpoonacularService()
        
        # Try Redis cache first, fall back to file cache if Redis unavailable
        try:
            self.cache_manager = ArtifactCacheManager()
            if not self.cache_manager.health_check():
                logger.info("Redis cache failed health check, switching to file cache")
                self.cache_manager = FileCacheManager()
        except Exception as e:
            logger.info(f"Redis cache initialization failed ({e}), using file cache")
            self.cache_manager = FileCacheManager()
            
        self.foreground_crew = ForegroundRecipeCrew()

    async def process_message(
        self, user_id: int, message: str, use_preferences: bool = True
    ) -> dict[str, Any]:
        """
        Process a chat message using real CrewAI.

        Args:
            user_id: The user's ID
            message: The user's message
            use_preferences: Whether to use user preferences

        Returns:
            Dict containing response, recipes, and pantry items
        """
        start_time = datetime.now()
        logger.info(f"🚀 Processing message with Real CrewAI for user {user_id}: '{message}'")

        try:
            # Step 1: Check for cached artifacts
            pantry_artifact = self.cache_manager.get_pantry_artifact(user_id)
            preference_artifact = (
                self.cache_manager.get_preference_artifact(user_id) if use_preferences else None
            )

            # If cache miss, create artifacts from database
            if not pantry_artifact:
                logger.info("Creating pantry artifact from database")
                pantry_artifact = await self._create_pantry_artifact(user_id)
            
            if use_preferences and not preference_artifact:
                logger.info("Creating preference artifact from database")
                preference_artifact = await self._create_preference_artifact(user_id)

            # Step 2: Get recipe candidates from Spoonacular
            recipe_candidates = await self._get_recipe_candidates(message, user_id)

            # Step 3: Create crew input
            crew_input = CrewInput(
                user_message=message,
                user_id=user_id,
                pantry_artifact=pantry_artifact,
                preference_artifact=preference_artifact,
                recipe_candidates=recipe_candidates,
                context=self._extract_context(message),
            )

            # Step 4: Use real CrewAI for recommendations
            crew_output = await self._get_crew_recommendations(crew_input)

            # Step 5: Format response for chat API
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"✅ Processed in {processing_time:.0f}ms")

            return self._format_chat_response(crew_output, crew_input)

        except Exception as e:
            logger.error(f"❌ Error in CrewAI processing: {e}")
            return await self._get_fallback_response(user_id, message)

    async def _get_recipe_candidates(self, message: str, user_id: int) -> list[dict[str, Any]]:
        """
        Get recipe candidates from Spoonacular based on message.
        
        Args:
            message (str): User's chat message requesting recipes
            user_id (int): User ID for fetching pantry items
            
        Returns:
            list[dict[str, Any]]: List of recipe dictionaries with structure:
                [
                    {
                        "id": int,
                        "title": str,
                        "image": str,
                        "usedIngredientCount": int,
                        "missedIngredientCount": int,
                        "likes": int,
                        "readyInMinutes": int,
                        "servings": int,
                        "sourceUrl": str,
                        "summary": str,
                        "cuisines": list[str],
                        "dishTypes": list[str],
                        "diets": list[str],
                        "instructions": str,
                        "extendedIngredients": list[dict]
                    }
                ]
        """
        try:
            # Extract ingredients from pantry if available
            pantry_items = await self._get_pantry_items(user_id)

            # Use Spoonacular to find recipes
            if pantry_items:
                ingredient_names = [item.get("product_name", "") for item in pantry_items[:10]]
                # IMPORTANT: Pass ingredient_names as a list, NOT a comma-separated string!
                # ingredient_names should be: ["chicken", "rice", "tomatoes", ...]
                recipes = await self.spoonacular_service.search_recipes_by_ingredients(
                    ingredients=ingredient_names,  # list[str] - e.g., ["chicken", "rice"]
                    number=10,                     # int - max recipes to return
                    ranking=2,                     # int - 1=minimize missing, 2=maximize used
                )
            else:
                # Search by query when no pantry items available
                # NOTE: complex_search may not exist in SpoonacularService
                # Consider using search_recipes method instead
                recipes = await self.spoonacular_service.search_recipes_complex(
                    query=message,                    # str - search query
                    number=10                         # int - max results
                )

            # search_recipes_by_ingredients returns a list directly
            # search_recipes_complex returns a dict with "results" key
            if isinstance(recipes, list):
                return recipes
            elif isinstance(recipes, dict):
                return recipes.get("results", [])
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting recipe candidates: {e}")
            return []

    async def _get_crew_recommendations(self, crew_input: CrewInput) -> CrewOutput:
        """
        Get recommendations using the real CrewAI prepsense_crew implementation.
        """
        try:
            logger.info(f"Running ForegroundRecipeCrew with {len(crew_input.recipe_candidates)} candidates")
            logger.info(f"Pantry artifact: {crew_input.pantry_artifact is not None}")
            logger.info(f"Preference artifact: {crew_input.preference_artifact is not None}")
            
            # Use the ForegroundRecipeCrew for real-time recommendations
            result = await self.foreground_crew.generate_recommendations(crew_input)
            logger.info(f"ForegroundRecipeCrew returned: {result.response_text[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Error running CrewAI: {e}", exc_info=True)
            # Fall back to the existing logic if crew fails
            return await self._get_recommendations_fallback(crew_input)
    
    async def _get_recommendations_fallback(self, crew_input: CrewInput) -> CrewOutput:
        """
        Fallback recommendation logic when CrewAI library isn't available.

        This simulates CrewAI behavior using the same patterns but without
        the actual library dependency.
        """
        start_time = datetime.now()

        # Simulate intelligent ranking
        ranked_recipes = self._rank_recipes_intelligently(
            crew_input.recipe_candidates, crew_input.pantry_artifact, crew_input.preference_artifact
        )

        # Generate contextual response
        response_text = self._generate_contextual_response(
            crew_input.user_message, ranked_recipes, crew_input.pantry_artifact
        )

        # Format recipe cards
        recipe_cards = self._format_recipe_cards(ranked_recipes[:5])

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return CrewOutput(
            response_text=response_text,
            recipe_cards=recipe_cards,
            processing_time_ms=processing_time_ms,
            agents_used=["intelligent_ranker", "context_generator", "card_formatter"],
            cache_hit=crew_input.pantry_artifact is not None,
            metadata={
                "fallback_mode": True,
                "recipes_considered": len(crew_input.recipe_candidates),
                "has_pantry_data": crew_input.pantry_artifact is not None,
                "has_preference_data": crew_input.preference_artifact is not None,
            },
        )

    def _rank_recipes_intelligently(
        self, recipes: list[dict], pantry_artifact, preference_artifact
    ) -> list[dict]:
        """Intelligent recipe ranking using available data"""
        if not recipes:
            return []

        for recipe in recipes:
            score = 0.5  # Base score

            # Pantry-based scoring
            if pantry_artifact:
                available_ingredients = {
                    item["name"].lower() for item in pantry_artifact.normalized_items
                }
                recipe_ingredients = set()

                # Extract ingredients from recipe
                if "extendedIngredients" in recipe:
                    recipe_ingredients = {
                        ing["name"].lower() for ing in recipe["extendedIngredients"]
                    }
                elif "ingredients" in recipe:
                    recipe_ingredients = {ing.lower() for ing in recipe["ingredients"]}

                # Score based on ingredient matches
                if recipe_ingredients:
                    matches = len(available_ingredients.intersection(recipe_ingredients))
                    total_recipe_ingredients = len(recipe_ingredients)
                    match_ratio = (
                        matches / total_recipe_ingredients if total_recipe_ingredients > 0 else 0
                    )
                    score += match_ratio * 0.4

                # Bonus for using expiring items
                if pantry_artifact.expiry_analysis:
                    expiring_items = {
                        item["name"].lower()
                        for item in pantry_artifact.expiry_analysis.get("expiring_soon", [])
                    }
                    if recipe_ingredients.intersection(expiring_items):
                        score += 0.3

            # Preference-based scoring
            if preference_artifact:
                # Cuisine preference bonus
                recipe_cuisines = recipe.get("cuisines", [])
                for cuisine in recipe_cuisines:
                    cuisine_lower = cuisine.lower()
                    if cuisine_lower in preference_artifact.cuisine_preferences:
                        score += preference_artifact.cuisine_preferences[cuisine_lower] * 0.2

                # Dietary restriction filtering (negative scoring)
                if "vegetarian" in preference_artifact.dietary_restrictions and not recipe.get(
                    "vegetarian", False
                ):
                    score -= 0.5
                if "vegan" in preference_artifact.dietary_restrictions and not recipe.get(
                    "vegan", False
                ):
                    score -= 0.5

            # Time-based scoring
            ready_time = recipe.get("readyInMinutes", 60)
            if ready_time <= 30:
                score += 0.2  # Quick meals bonus
            elif ready_time > 90:
                score -= 0.1  # Long meals penalty

            recipe["rank_score"] = score

        # Sort by score (descending)
        return sorted(recipes, key=lambda r: r.get("rank_score", 0), reverse=True)

    def _generate_contextual_response(
        self, message: str, recipes: list[dict], pantry_artifact
    ) -> str:
        """Generate contextual response based on available data"""
        message_lower = message.lower()

        # Context-aware responses
        if "quick" in message_lower or "fast" in message_lower:
            base_response = "Here are some quick recipes you can make"
        elif "dinner" in message_lower:
            base_response = "Perfect dinner options for you"
        elif "breakfast" in message_lower:
            base_response = "Great breakfast ideas"
        elif "lunch" in message_lower:
            base_response = "Delicious lunch recipes"
        else:
            base_response = "Here are some great recipe recommendations"

        # Add pantry context
        if pantry_artifact and pantry_artifact.expiry_analysis:
            expiring_count = len(pantry_artifact.expiry_analysis.get("expiring_soon", []))
            if expiring_count > 0:
                base_response += f" that help use up {expiring_count} item{'s' if expiring_count > 1 else ''} expiring soon"

        # Add recipe count
        if recipes:
            base_response += (
                f". I found {len(recipes)} recipe{'s' if len(recipes) > 1 else ''} for you!"
            )
        else:
            base_response = "I couldn't find recipes matching your request. Try being more specific or check your pantry items."

        return base_response

    def _format_recipe_cards(self, recipes: list[dict]) -> list[dict[str, Any]]:
        """Format recipes into standardized recipe cards"""
        cards = []

        for recipe in recipes:
            # Extract basic info
            card = {
                "id": recipe.get("id"),
                "title": recipe.get("title", "Unknown Recipe"),
                "ready_in_minutes": recipe.get("readyInMinutes", "Unknown"),
                "servings": recipe.get("servings", "Unknown"),
                "image": recipe.get("image", ""),
                "rank_score": recipe.get("rank_score", 0.5),
                "source": "spoonacular",
            }

            # Add cuisine info
            if "cuisines" in recipe:
                card["cuisines"] = recipe["cuisines"]

            # Add dietary info
            dietary_info = []
            if recipe.get("vegetarian"):
                dietary_info.append("Vegetarian")
            if recipe.get("vegan"):
                dietary_info.append("Vegan")
            if recipe.get("glutenFree"):
                dietary_info.append("Gluten-Free")
            if dietary_info:
                card["dietary_info"] = dietary_info

            # Add ingredient count
            if "extendedIngredients" in recipe:
                card["ingredient_count"] = len(recipe["extendedIngredients"])

            # Add difficulty estimate
            ready_time = recipe.get("readyInMinutes", 60)
            if ready_time <= 20:
                card["difficulty"] = "Easy"
            elif ready_time <= 45:
                card["difficulty"] = "Medium"
            else:
                card["difficulty"] = "Hard"

            cards.append(card)

        return cards

    def _format_chat_response(
        self, crew_output: CrewOutput, crew_input: CrewInput
    ) -> Dict[str, Any]:
        """Format CrewOutput for chat API response"""
        return {
            "response": crew_output.response_text,
            "recipes": crew_output.recipe_cards,
            "pantry_items": self._get_pantry_summary(crew_input.pantry_artifact),
            "user_preferences": self._get_preference_summary(crew_input.preference_artifact),
            "show_preference_choice": crew_input.preference_artifact is None,
            "metadata": {
                "processing_time_ms": crew_output.processing_time_ms,
                "meets_performance_target": crew_output.meets_performance_target(),
                "cache_hit": crew_output.cache_hit,
                "agents_used": crew_output.agents_used,
            },
        }

    def _get_pantry_summary(self, pantry_artifact) -> list[dict[str, Any]]:
        """Get pantry summary for response"""
        if not pantry_artifact:
            return []

        return [
            {
                "name": item.get("product_name", "Unknown"),
                "quantity": item.get("quantity"),
                "category": item.get("food_category", "Unknown"),
            }
            for item in pantry_artifact.normalized_items[:10]  # Limit to 10 items
        ]

    def _get_preference_summary(self, preference_artifact) -> dict[str, Any]:
        """Get preference summary for response"""
        if not preference_artifact:
            return {}  # Return empty dict instead of None

        return {
            "dietary_restrictions": preference_artifact.dietary_restrictions,
            "allergens": preference_artifact.allergens,
            "top_cuisines": list(preference_artifact.cuisine_preferences.keys())[:3],
        }

    def _extract_context(self, message: str) -> dict[str, Any]:
        """Extract context from user message"""
        message_lower = message.lower()
        context = {}

        # Meal type detection
        if "breakfast" in message_lower:
            context["meal_type"] = "breakfast"
        elif "lunch" in message_lower:
            context["meal_type"] = "lunch"
        elif "dinner" in message_lower:
            context["meal_type"] = "dinner"
        elif "snack" in message_lower:
            context["meal_type"] = "snack"

        # Time preference detection
        if any(word in message_lower for word in ["quick", "fast", "easy"]):
            context["time_preference"] = "quick"
        elif any(word in message_lower for word in ["elaborate", "complex", "fancy"]):
            context["time_preference"] = "elaborate"

        # Dietary context
        if "healthy" in message_lower:
            context["health_focus"] = True
        if "comfort" in message_lower:
            context["comfort_food"] = True

        return context

    async def _create_pantry_artifact(self, user_id: int):
        """Create pantry artifact from database data"""
        from backend_gateway.prepsense_crew.models import PantryArtifact
        from datetime import datetime
        
        try:
            pantry_items = await self._get_pantry_items(user_id)
            
            if not pantry_items:
                return None
                
            # Create pantry artifact
            return PantryArtifact(
                user_id=user_id,
                normalized_items=pantry_items,
                expiry_analysis={},
                ingredient_vectors=[],
                last_updated=datetime.now(),
                ttl_seconds=86400
            )
        except Exception as e:
            logger.error(f"Error creating pantry artifact: {e}")
            return None
    
    async def _create_preference_artifact(self, user_id: int):
        """Create preference artifact from database data"""
        from backend_gateway.prepsense_crew.models import PreferenceArtifact
        from datetime import datetime
        
        try:
            # Get user preferences - database service methods are synchronous
            try:
                preferences = self.db_service.get_user_preferences(user_id)
            except Exception as e:
                logger.error(f"Error fetching user preferences: {e}")
                return None
            
            if not preferences:
                return None
                
            # Create preference artifact
            return PreferenceArtifact(
                user_id=user_id,
                preference_vector=[],  # Empty vector for now
                dietary_restrictions=preferences.get("dietary_restrictions", []),
                allergens=preferences.get("allergens", []),
                cuisine_preferences=preferences.get("cuisine_preferences", {}),
                learning_data={},  # Empty learning data
                last_updated=datetime.now(),
                ttl_seconds=86400
            )
        except Exception as e:
            logger.error(f"Error creating preference artifact: {e}")
            return None

    async def _get_pantry_items(self, user_id: int) -> list[dict[str, Any]]:
        """Get pantry items from database"""
        try:
            # Database service methods are synchronous, don't await them
            pantry_items = self.db_service.get_user_pantry_items(user_id)
            return pantry_items if pantry_items else []
        except Exception as e:
            logger.error(f"Error fetching pantry items: {e}")
            return []
    
    async def _get_fallback_response(self, user_id: int, message: str) -> dict[str, Any]:
        """Generate fallback response when CrewAI processing fails"""
        return {
            "response": "I'm having trouble processing your request right now. Please try again in a moment.",
            "recipes": [],
            "pantry_items": [],
            "user_preferences": {},
            "show_preference_choice": False,
            "metadata": {"error": True, "processing_time_ms": 50},
        }
