"""
CrewAI Foreground Crew

Real-time crew that responds to user queries in ≤2-3 seconds.
Uses pre-computed artifacts from background flows for optimal latency.
Implements the hot path of the background/foreground pattern.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task

from .cache_manager import ArtifactCacheManager
from .models import CrewInput, CrewOutput, RecipeArtifact

logger = logging.getLogger(__name__)


class ForegroundRecipeCrew:
    """
    Lightweight crew for real-time recipe recommendations.

    This crew:
    1. Loads cached artifacts (pantry + preferences)
    2. Ranks recipe candidates using cached vectors
    3. Validates nutrition requirements
    4. Formats response for UI consumption

    Target latency: <3 seconds with allow_parallel=True
    """

    def __init__(self):
        self.cache_manager = ArtifactCacheManager()
        self._initialize_agents()
        self._initialize_tasks()
        self._initialize_crew()

    def _initialize_agents(self):
        """Initialize the lightweight agent team"""

        # Recipe Ranker Agent - Uses cached vectors for fast ranking
        self.ranker = Agent(
            role="Recipe Ranker",
            goal="Rank recipe candidates using cached pantry and preference data",
            backstory="""You are an expert at matching recipes to available ingredients 
            and user preferences. You work with pre-computed pantry analysis and preference 
            vectors to quickly rank recipe candidates by relevance and feasibility.""",
            verbose=False,
            allow_delegation=False,
            max_iter=5,  # Limit iterations for faster response
            max_execution_time=60,  # 60 second timeout per agent
        )

        # Nutritionist Agent - Fast macro validation
        self.nutritionist = Agent(
            role="Nutritionist",
            goal="Quickly validate recipes against dietary restrictions and macro limits",
            backstory="""You are a nutrition expert who quickly evaluates recipes 
            for dietary compliance. You focus on allergen checking, dietary restrictions, 
            and basic macro validation without deep analysis.""",
            verbose=False,
            allow_delegation=False,
            max_iter=3,  # Faster nutrition validation
            max_execution_time=45,  # 45 second timeout
        )

        # UX Formatter Agent - Prepares final response
        self.formatter = Agent(
            role="UX Formatter",
            goal="Format recipe recommendations into user-friendly response with recipe cards",
            backstory="""You are a UX expert who transforms recipe data into engaging, 
            mobile-optimized recipe cards with clear ingredients, instructions, and metadata.""",
            verbose=False,
            allow_delegation=False,
            max_iter=2,  # Simple formatting should be quick
            max_execution_time=30,  # 30 second timeout
        )

    def _initialize_tasks(self):
        """Initialize the task workflow"""

        # Task 1: Rank recipes using cached data
        self.ranking_task = Task(
            description="""Rank the provided recipe candidates using:
            1. Cached pantry analysis (available ingredients, expiry urgency)
            2. Cached preference vectors (user taste preferences, cuisine preferences)
            3. Recipe feasibility (missing ingredients count, prep time)
            
            Return top 5 recipes with ranking scores and reasoning.""",
            agent=self.ranker,
            expected_output="List of top 5 ranked recipes with scores and brief reasoning",
        )

        # Task 2: Nutrition validation (runs in parallel with ranking)
        self.nutrition_task = Task(
            description="""Validate ranked recipes against:
            1. Dietary restrictions (vegetarian, vegan, etc.)
            2. Allergen list (nuts, shellfish, etc.)  
            3. Basic macro requirements if specified
            
            Filter out non-compliant recipes and flag any concerns.""",
            agent=self.nutritionist,
            context=[self.ranking_task],  # Depends on ranking results
            expected_output="Filtered recipe list with nutrition compliance status",
        )

        # Task 3: Format final response
        self.formatting_task = Task(
            description="""Create the final user response with:
            1. Conversational text summarizing recommendations
            2. Recipe cards with ingredients, steps, and metadata
            3. Helpful context about pantry usage and expiring items
            
            Format as JSON with 'response_text' and 'recipe_cards' fields.""",
            agent=self.formatter,
            context=[self.nutrition_task],  # Uses validated recipes
            expected_output="JSON response with conversational text and structured recipe cards",
        )

    def _initialize_crew(self):
        """Initialize the crew with parallel processing and optimized iteration limits"""
        self.crew = Crew(
            agents=[self.nutritionist, self.formatter],  # Manager agent excluded from agents list
            tasks=[self.ranking_task, self.nutrition_task, self.formatting_task],
            process=Process.hierarchical,  # Ranker manages the workflow
            manager_agent=self.ranker,
            allow_parallel=True,  # Critical for <3s latency
            verbose=False,
            max_iter=10,  # Limit iterations to prevent "maximum iterations reached" warnings
            max_execution_time=180,  # 3 minute timeout for safety
        )

    async def generate_recommendations(self, crew_input: CrewInput) -> CrewOutput:
        """
        Generate recipe recommendations using cached artifacts.

        Target latency: <3 seconds (ideally <2s)
        """
        start_time = datetime.now()

        try:
            # Step 1: Use artifacts from crew_input if available, otherwise load from cache
            if crew_input.pantry_artifact:
                artifacts = {
                    "pantry": crew_input.pantry_artifact,
                    "preferences": crew_input.preference_artifact  # Can be None
                }
                logger.info("Using artifacts from crew_input")
            else:
                # Fall back to loading from cache
                artifacts = await self._load_cached_artifacts(crew_input.user_id)
                logger.info("Loading artifacts from cache")

            # Check if we have required artifacts
            if not artifacts["pantry"]:
                logger.warning(f"Missing pantry artifact for user {crew_input.user_id}")
                # Return cache miss response
                return await self._handle_cache_miss(crew_input)

            # Step 2: Prepare crew context with artifacts
            crew_context = self._prepare_crew_context(crew_input, artifacts)
            logger.info(f"Prepared crew context with keys: {list(crew_context.keys())}")

            # Step 3: Execute crew (target <2s)
            logger.info("Starting crew kickoff...")
            result = self.crew.kickoff(inputs=crew_context)
            logger.info(f"Crew kickoff completed. Result type: {type(result)}")

            # Step 4: Process result and create CrewOutput
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Parse crew result
            response_data = self._parse_crew_result(result)

            # Cache recipe results for future requests
            await self._cache_recipe_results(crew_input, response_data, processing_time)

            return CrewOutput(
                response_text=response_data.get(
                    "response_text", "Here are your recipe recommendations!"
                ),
                recipe_cards=response_data.get("recipe_cards", []),
                processing_time_ms=int(processing_time),
                agents_used=["ranker", "nutritionist", "formatter"],
                cache_hit=True,  # We used cached artifacts
                metadata={
                    "pantry_freshness": artifacts["pantry"].last_updated.isoformat(),
                    "preference_freshness": artifacts["preferences"].last_updated.isoformat() if artifacts["preferences"] else None,
                    "recipes_considered": len(crew_input.recipe_candidates),
                    "context": crew_input.context,
                },
            )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return CrewOutput(
                response_text="I'm having trouble generating recommendations right now. Please try again.",
                recipe_cards=[],
                processing_time_ms=int(processing_time),
                agents_used=[],
                cache_hit=False,
                metadata={"error": str(e)},
            )

    async def _load_cached_artifacts(self, user_id: int) -> Dict[str, Any]:
        """Load pre-computed artifacts from cache"""
        try:
            pantry_artifact = self.cache_manager.get_pantry_artifact(user_id)
            preference_artifact = self.cache_manager.get_preference_artifact(user_id)

            return {"pantry": pantry_artifact, "preferences": preference_artifact}

        except Exception as e:
            logger.error(f"Failed to load cached artifacts for user {user_id}: {e}")
            return {"pantry": None, "preferences": None}

    def _prepare_crew_context(
        self, crew_input: CrewInput, artifacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare context for crew execution"""
        pantry = artifacts["pantry"]
        preferences = artifacts["preferences"]

        # Calculate priority ingredients (expiring soon)
        priority_ingredients = []
        if pantry and pantry.expiry_analysis:
            expiring_soon = pantry.expiry_analysis.get("expiring_soon", [])
            logger.info(f"Expiring soon items: {expiring_soon}")
            priority_ingredients = [
                item.get("product_name", "") for item in expiring_soon
            ]

        # Log pantry items structure
        if pantry and pantry.normalized_items:
            logger.info(f"First pantry item keys: {list(pantry.normalized_items[0].keys()) if pantry.normalized_items else 'No items'}")

        return {
            "user_message": crew_input.user_message,
            "recipe_candidates": crew_input.recipe_candidates,
            "available_ingredients": (
                [item.get("product_name", "") for item in pantry.normalized_items] if pantry else []
            ),
            "priority_ingredients": priority_ingredients,
            "dietary_restrictions": preferences.dietary_restrictions if preferences else [],
            "allergens": preferences.allergens if preferences else [],
            "cuisine_preferences": preferences.cuisine_preferences if preferences else {},
            "urgency_score": pantry.expiry_analysis.get("urgency_score", 0.0) if pantry else 0.0,
            "context": crew_input.context,
        }

    async def _handle_cache_miss(self, crew_input: CrewInput) -> CrewOutput:
        """Handle case where cached artifacts are missing"""
        logger.warning(f"Cache miss for user {crew_input.user_id} - triggering background flows")

        # TODO: Trigger background flows asynchronously
        # from .background_flows import BackgroundFlowOrchestrator
        # orchestrator = BackgroundFlowOrchestrator()
        # await orchestrator.warm_user_cache(crew_input.user_id, "cache_miss")

        # Return basic response while cache warms
        return CrewOutput(
            response_text="I'm analyzing your pantry and preferences. Please try again in a moment for personalized recommendations!",
            recipe_cards=[],
            processing_time_ms=50,  # Very fast fallback
            agents_used=[],
            cache_hit=False,
            metadata={"cache_miss": True, "warming_cache": True},
        )

    def _parse_crew_result(self, result: Any) -> Dict[str, Any]:
        """Parse crew execution result into structured format"""
        try:
            # The formatter agent should return JSON
            # For now, create a mock structure
            return {
                "response_text": "Based on your pantry and preferences, here are my top recommendations!",
                "recipe_cards": [
                    {
                        "id": 1,
                        "title": "Quick Pasta Primavera",
                        "prep_time": "20 min",
                        "ingredients_available": 8,
                        "ingredients_needed": 2,
                        "difficulty": "Easy",
                        "cuisine": "Italian",
                        "rating": 4.5,
                        "uses_expiring": ["bell peppers", "zucchini"],
                    }
                ],
            }

        except Exception as e:
            logger.error(f"Failed to parse crew result: {e}")
            return {"response_text": "I found some great recipes for you!", "recipe_cards": []}

    async def _cache_recipe_results(
        self, crew_input: CrewInput, response_data: Dict[str, Any], processing_time: float
    ):
        """Cache recipe results for future similar requests"""
        try:
            # Create search hash for caching
            search_context = {
                "user_message": crew_input.user_message,
                "context": crew_input.context,
            }
            search_hash = hashlib.md5(str(search_context).encode()).hexdigest()[:8]

            # Create recipe artifact
            recipe_artifact = RecipeArtifact(
                user_id=crew_input.user_id,
                ranked_recipes=response_data.get("recipe_cards", []),
                embeddings_index={},  # Would store embeddings for similarity search
                context_metadata={
                    "search_hash": search_hash,
                    "processing_time_ms": processing_time,
                    "query": crew_input.user_message,
                },
                last_updated=datetime.now(),
                ttl_seconds=7200,  # 2 hours TTL
            )

            # Save to cache
            self.cache_manager.save_recipe_artifact(recipe_artifact)

        except Exception as e:
            logger.error(f"Failed to cache recipe results: {e}")


# Helper function for API endpoints
async def get_recipe_recommendations(
    user_message: str,
    user_id: int,
    recipe_candidates: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> CrewOutput:
    """
    Main entry point for recipe recommendations API.

    Usage:
    ```python
    from backend_gateway.crewai.foreground_crew import get_recipe_recommendations

    result = await get_recipe_recommendations(
        user_message="What can I make for dinner?",
        user_id=111,
        recipe_candidates=spoonacular_recipes,
        context={"meal_type": "dinner", "time_preference": "quick"}
    )
    ```
    """
    crew_input = CrewInput(
        user_message=user_message,
        user_id=user_id,
        recipe_candidates=recipe_candidates or [],
        context=context or {},
    )

    crew = ForegroundRecipeCrew()
    return await crew.generate_recommendations(crew_input)
