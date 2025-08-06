from crewai import Crew
import logging
import os
from src.crews.pantry_normalization import PantryNormalizationCrew
from src.agents.recipe_search import RecipeSearch
from src.agents.nutri_check import NutriCheck
from src.agents.user_preferences import UserPreferences
from src.agents.judge_thyme import JudgeThyme
from src.agents.pantry_ledger import PantryLedger

logger = logging.getLogger(__name__)

class PrepSenseMainCrew(Crew):
    """
    PrepSense Main Crew: End-to-end intelligent recipe recommendation and pantry management.
    
    Flow: PantryNormalization -> RecipeSearch -> NutriCheck -> UserPreferences -> JudgeThyme -> PantryLedger
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize sub-crew and agents
        self.pantry_normalization = PantryNormalizationCrew()
        self.recipe_search = RecipeSearch()
        self.nutri_check = NutriCheck()
        self.user_preferences = UserPreferences()
        self.judge_thyme = JudgeThyme()
        self.pantry_ledger = PantryLedger()
        
        # Environment flags
        self.enable_judge_thyme = os.getenv("ENABLE_JUDGE_THYME", "true").lower() == "true"
        
        logger.info(f"PrepSenseMainCrew initialized - JudgeThyme: {self.enable_judge_thyme}")

    async def run(self, input_data: dict):
        """
        Run the complete PrepSense workflow.
        
        Args:
            input_data: {
                # Pantry normalization inputs
                "image_b64": str (optional) - Base64 encoded image for BiteCam
                "raw_items": list[dict] (optional) - Pre-extracted raw items
                "user_id": str (required) - User ID for personalization
                "freshness_days": int (optional) - Days threshold for freshness filter
                
                # Recipe search inputs
                "max_recipes": int (optional) - Maximum recipes to search (default: 20)
                
                # User preference inputs
                "user_health_goals": dict (optional) - Health goals for nutrition analysis
                
                # Final selection inputs
                "selected_recipe_id": int (optional) - Recipe to deduct ingredients for
                "commit_deduction": bool (optional) - Whether to actually deduct ingredients
            }
            
        Returns:
            dict: Complete workflow results with recommendations and pantry updates
        """
        try:
            logger.info("Starting PrepSense main workflow")
            
            user_id = input_data.get("user_id")
            if not user_id:
                raise ValueError("user_id is required for PrepSense workflow")

            workflow_result = {
                "user_id": user_id,
                "workflow": "prepsense_main",
                "timestamp": self._get_timestamp(),
                "steps": {}
            }

            # Step 1: Pantry Normalization (sub-crew)
            logger.info("Step 1: Running Pantry Normalization Crew")
            try:
                fresh_items = await self.pantry_normalization.run(input_data)
                workflow_result["steps"]["pantry_normalization"] = {
                    "status": "success",
                    "items_processed": len(fresh_items),
                    "fresh_items": fresh_items
                }
                logger.info(f"Pantry normalization completed: {len(fresh_items)} fresh items")
            except Exception as e:
                logger.error(f"Pantry normalization failed: {e}")
                workflow_result["steps"]["pantry_normalization"] = {
                    "status": "error",
                    "error": str(e)
                }
                fresh_items = []

            if not fresh_items:
                logger.warning("No fresh items available, cannot proceed with recipe search")
                workflow_result["status"] = "no_ingredients"
                workflow_result["message"] = "No fresh ingredients available for recipe recommendations"
                return workflow_result

            # Step 2: Recipe Search
            logger.info("Step 2: Running Recipe Search")
            try:
                max_recipes = input_data.get("max_recipes", 20)
                recipes = await self.recipe_search.run(fresh_items, max_recipes)
                workflow_result["steps"]["recipe_search"] = {
                    "status": "success",
                    "recipes_found": len(recipes)
                }
                logger.info(f"Recipe search completed: {len(recipes)} recipes found")
            except Exception as e:
                logger.error(f"Recipe search failed: {e}")
                workflow_result["steps"]["recipe_search"] = {
                    "status": "error", 
                    "error": str(e)
                }
                recipes = []

            if not recipes:
                logger.warning("No recipes found")
                workflow_result["status"] = "no_recipes"
                workflow_result["message"] = "No recipes found for available ingredients"
                return workflow_result

            # Step 3: Nutrition Analysis
            logger.info("Step 3: Running Nutrition Analysis")
            try:
                user_health_goals = input_data.get("user_health_goals", {})
                nutrition_scored_recipes = await self.nutri_check.run(recipes, user_health_goals)
                workflow_result["steps"]["nutrition_analysis"] = {
                    "status": "success",
                    "recipes_analyzed": len(nutrition_scored_recipes)
                }
                logger.info(f"Nutrition analysis completed: {len(nutrition_scored_recipes)} recipes analyzed")
            except Exception as e:
                logger.error(f"Nutrition analysis failed: {e}")
                workflow_result["steps"]["nutrition_analysis"] = {
                    "status": "error",
                    "error": str(e)
                }
                nutrition_scored_recipes = recipes  # Fallback to original recipes

            # Step 4: User Preference Scoring
            logger.info("Step 4: Running User Preference Analysis")
            try:
                preference_scored_recipes = await self.user_preferences.run(nutrition_scored_recipes, user_id)
                workflow_result["steps"]["user_preferences"] = {
                    "status": "success",
                    "recipes_scored": len(preference_scored_recipes)
                }
                logger.info(f"User preference analysis completed: {len(preference_scored_recipes)} recipes scored")
            except Exception as e:
                logger.error(f"User preference analysis failed: {e}")
                workflow_result["steps"]["user_preferences"] = {
                    "status": "error",
                    "error": str(e)
                }
                preference_scored_recipes = nutrition_scored_recipes  # Fallback

            # Step 5: Final Judgment (Judge Thyme)
            logger.info("Step 5: Running Final Judgment")
            try:
                if self.enable_judge_thyme:
                    max_final_recipes = input_data.get("max_final_recipes", 5)
                    final_recipes = await self.judge_thyme.run(preference_scored_recipes, max_final_recipes)
                    workflow_result["steps"]["final_judgment"] = {
                        "status": "success",
                        "top_recipes_selected": len(final_recipes),
                        "judge_enabled": True
                    }
                else:
                    # Sort by combined score and take top 5
                    sorted_recipes = sorted(preference_scored_recipes, 
                                          key=lambda x: x.get("combined_score", 0), 
                                          reverse=True)
                    final_recipes = sorted_recipes[:5]
                    for i, recipe in enumerate(final_recipes):
                        recipe["rank"] = i + 1
                    workflow_result["steps"]["final_judgment"] = {
                        "status": "success",
                        "top_recipes_selected": len(final_recipes),
                        "judge_enabled": False
                    }
                
                logger.info(f"Final judgment completed: {len(final_recipes)} top recipes")
            except Exception as e:
                logger.error(f"Final judgment failed: {e}")
                workflow_result["steps"]["final_judgment"] = {
                    "status": "error",
                    "error": str(e)
                }
                # Fallback to top 5 by preference score
                sorted_recipes = sorted(preference_scored_recipes, 
                                      key=lambda x: x.get("combined_score", 0), 
                                      reverse=True)
                final_recipes = sorted_recipes[:5]

            # Step 6: Pantry Ledger (Ingredient Matching and Optional Deduction)
            logger.info("Step 6: Running Pantry Ledger")
            try:
                selected_recipe_id = input_data.get("selected_recipe_id")
                commit_deduction = input_data.get("commit_deduction", False)
                
                final_recipes_with_pantry = await self.pantry_ledger.run(
                    final_recipes, user_id, selected_recipe_id, commit_deduction
                )
                
                workflow_result["steps"]["pantry_ledger"] = {
                    "status": "success",
                    "recipes_processed": len(final_recipes_with_pantry),
                    "deduction_performed": commit_deduction and selected_recipe_id is not None
                }
                logger.info(f"Pantry ledger completed: {len(final_recipes_with_pantry)} recipes with pantry matching")
            except Exception as e:
                logger.error(f"Pantry ledger failed: {e}")
                workflow_result["steps"]["pantry_ledger"] = {
                    "status": "error",
                    "error": str(e)
                }
                final_recipes_with_pantry = final_recipes  # Fallback

            # Compile final results
            workflow_result.update({
                "status": "success",
                "message": f"PrepSense workflow completed successfully. {len(final_recipes_with_pantry)} recipes recommended.",
                "recommendations": final_recipes_with_pantry,
                "workflow_summary": {
                    "fresh_ingredients": len(fresh_items),
                    "recipes_found": len(recipes),
                    "final_recommendations": len(final_recipes_with_pantry),
                    "top_recipe": final_recipes_with_pantry[0] if final_recipes_with_pantry else None
                }
            })

            logger.info("PrepSense main workflow completed successfully")
            return workflow_result

        except Exception as e:
            logger.error(f"PrepSense main crew failed: {e}")
            return {
                "status": "error",
                "message": f"Workflow failed: {str(e)}",
                "timestamp": self._get_timestamp(),
                "user_id": input_data.get("user_id")
            }

    async def quick_recipe_recommendation(self, user_id: str, max_recipes: int = 3) -> dict:
        """
        Quick recipe recommendation based on current pantry without image processing.
        
        Args:
            user_id: User ID
            max_recipes: Maximum number of recipes to return
            
        Returns:
            dict: Quick recommendations
        """
        try:
            logger.info(f"Running quick recipe recommendation for user {user_id}")
            
            # Get current pantry summary
            pantry_summary = await self.pantry_ledger.get_pantry_summary(user_id)
            
            if pantry_summary.get("total_items", 0) == 0:
                return {
                    "status": "no_pantry_items",
                    "message": "No pantry items found. Please add items to your pantry first.",
                    "recommendations": []
                }

            # Create minimal workflow input
            input_data = {
                "user_id": user_id,
                "max_recipes": max_recipes,
                "max_final_recipes": max_recipes,
                "freshness_days": 14  # More lenient for quick recommendations
            }
            
            # Run simplified workflow (skip pantry normalization, use existing pantry)
            workflow_result = await self._run_recipe_only_workflow(input_data)
            
            return {
                "status": "success",
                "message": f"Quick recommendations based on your pantry ({pantry_summary['total_items']} items)",
                "recommendations": workflow_result.get("recommendations", []),
                "pantry_summary": pantry_summary,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Quick recipe recommendation failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate quick recommendations: {str(e)}",
                "recommendations": []
            }

    async def _run_recipe_only_workflow(self, input_data: dict) -> dict:
        """Run workflow starting from recipe search (skip pantry normalization)"""
        user_id = input_data["user_id"]
        
        # Get fresh items from existing pantry
        pantry_items = []  # This would need to be populated from database
        
        # Run recipe workflow steps
        recipes = await self.recipe_search.run(pantry_items, input_data.get("max_recipes", 10))
        
        if recipes:
            nutrition_scored = await self.nutri_check.run(recipes, {})
            preference_scored = await self.user_preferences.run(nutrition_scored, user_id)
            
            if self.enable_judge_thyme:
                final_recipes = await self.judge_thyme.run(preference_scored, input_data.get("max_final_recipes", 3))
            else:
                sorted_recipes = sorted(preference_scored, key=lambda x: x.get("combined_score", 0), reverse=True)
                final_recipes = sorted_recipes[:input_data.get("max_final_recipes", 3)]
            
            final_with_pantry = await self.pantry_ledger.run(final_recipes, user_id)
            
            return {"recommendations": final_with_pantry}
        
        return {"recommendations": []}

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def health_check(self) -> dict:
        """Check the health of the entire crew system"""
        health_status = {
            "crew": "prepsense_main",
            "status": "healthy",
            "sub_crews": {},
            "agents": {},
            "enabled_features": []
        }
        
        try:
            # Check sub-crew health
            pantry_health = await self.pantry_normalization.health_check()
            health_status["sub_crews"]["pantry_normalization"] = pantry_health
            
            if pantry_health["status"] != "healthy":
                health_status["status"] = "degraded"

            # Check main crew agents
            main_agents = [
                ("recipe_search", self.recipe_search, True),
                ("nutri_check", self.nutri_check, True),
                ("user_preferences", self.user_preferences, True),
                ("judge_thyme", self.judge_thyme, self.enable_judge_thyme),
                ("pantry_ledger", self.pantry_ledger, True)
            ]
            
            for agent_name, agent_instance, is_enabled in main_agents:
                if is_enabled:
                    health_status["enabled_features"].append(agent_name)
                    if hasattr(agent_instance, 'run'):
                        health_status["agents"][agent_name] = "healthy"
                    else:
                        health_status["agents"][agent_name] = "unhealthy - missing run method"
                        health_status["status"] = "degraded"
                else:
                    health_status["agents"][agent_name] = "disabled"

            return health_status

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            return health_status

    def get_workflow_description(self) -> dict:
        """Get complete workflow description"""
        return {
            "name": "PrepSense Main Crew",
            "description": "End-to-end intelligent recipe recommendation and pantry management system",
            "workflow": [
                {
                    "step": 1,
                    "component": "PantryNormalizationCrew",
                    "description": "Process raw ingredients into normalized inventory",
                    "sub_workflow": self.pantry_normalization.get_workflow_description()
                },
                {
                    "step": 2,
                    "agent": "RecipeSearch",
                    "description": "Search for recipes using available ingredients via Spoonacular API",
                    "input": "Fresh normalized ingredients",
                    "output": "Recipe candidates with detailed information"
                },
                {
                    "step": 3,
                    "agent": "NutriCheck",
                    "description": "Analyze nutritional content and health impact of recipes",
                    "input": "Recipe candidates",
                    "output": "Recipes with nutrition scores and health assessments"
                },
                {
                    "step": 4,
                    "agent": "UserPreferences",
                    "description": "Score recipes based on user preferences and dietary restrictions",
                    "input": "Nutrition-scored recipes",
                    "output": "Recipes with preference scores and combined ratings"
                },
                {
                    "step": 5,
                    "agent": "JudgeThyme",
                    "description": "Make final judgment and select top recipe recommendations",
                    "enabled": self.enable_judge_thyme,
                    "input": "Preference-scored recipes",
                    "output": "Top recipe recommendations with final judgments"
                },
                {
                    "step": 6,
                    "agent": "PantryLedger",
                    "description": "Match ingredients and optionally deduct from pantry",
                    "input": "Final recipe recommendations",
                    "output": "Recipes with pantry matching and optional ingredient deduction"
                }
            ],
            "features": {
                "image_processing": "Extract ingredients from photos",
                "intelligent_matching": "Match ingredients using USDA database",
                "nutritional_analysis": "Comprehensive health and nutrition scoring",
                "personalization": "User preference learning and application",
                "pantry_management": "Real-time inventory tracking and deduction"
            },
            "environment_flags": {
                "ENABLE_JUDGE_THYME": self.enable_judge_thyme,
                **self.pantry_normalization.get_workflow_description()["environment_flags"]
            }
        }