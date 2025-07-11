"""Recipe quality and recommendation pipeline adapted for PostgreSQL"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.crew_ai_service import CrewAIService
from backend_gateway.services.recipe_evaluator_service import RecipeEvaluator
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)


class RecipeQualityPipeline:
    """
    Multi-stage recipe pipeline adapted from CrewAI notebook
    Uses PostgreSQL instead of BigQuery
    """
    
    def __init__(self):
        self.db_service = get_database_service()
        self.pantry_service = PantryService(self.db_service)
        self.crew_ai_service = CrewAIService()
        self.recipe_evaluator = RecipeEvaluator()
    
    async def get_quality_recipes(
        self, 
        user_id: int,
        message: str = "What can I make for dinner?",
        evaluate_quality: bool = True,
        min_quality_score: int = 3
    ) -> Dict[str, Any]:
        """
        Get high-quality recipe recommendations
        
        Pipeline:
        1. Fetch pantry items (PostgreSQL)
        2. Filter expired items
        3. Get user preferences
        4. Generate recipes with AI
        5. Evaluate quality with Claude
        6. Rank and return best recipes
        """
        
        try:
            # Stage 1: Get pantry items (PostgreSQL version)
            pantry_items = await self._get_filtered_pantry_items(user_id)
            logger.info(f"Found {len(pantry_items)} usable pantry items")
            
            # Stage 2: Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            # Stage 3: Generate recipes using CrewAI
            crew_response = await self.crew_ai_service.process_message(
                user_id=user_id,
                message=message,
                use_preferences=True
            )
            
            recipes = crew_response.get('recipes', [])
            logger.info(f"Generated {len(recipes)} recipes")
            
            # Stage 4: Evaluate quality if requested
            if evaluate_quality and recipes:
                evaluated_recipes = await self._evaluate_recipes(recipes[:5])  # Top 5
                # Filter by quality score
                quality_recipes = [
                    r for r in evaluated_recipes 
                    if r.get('quality_evaluation', {}).get('score', 0) >= min_quality_score
                ]
                logger.info(f"{len(quality_recipes)} recipes passed quality threshold")
            else:
                quality_recipes = recipes
            
            # Stage 5: Final ranking
            ranked_recipes = self._final_ranking(
                quality_recipes,
                pantry_items,
                preferences
            )
            
            return {
                'recipes': ranked_recipes[:3],  # Top 3
                'pantry_items': pantry_items,
                'user_preferences': preferences,
                'response': crew_response.get('response', ''),
                'quality_evaluated': evaluate_quality
            }
            
        except Exception as e:
            logger.error(f"Error in quality pipeline: {str(e)}")
            raise
    
    async def _get_filtered_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get non-expired pantry items with available quantity
        PostgreSQL version of the BigQuery query from notebook
        """
        
        query = """
        SELECT 
            pi.pantry_item_id,
            pi.product_name,
            pi.quantity,
            pi.used_quantity,
            pi.unit_of_measurement,
            pi.expiration_date,
            pi.category,
            COALESCE(pi.quantity - pi.used_quantity, pi.quantity) as available_quantity,
            CASE 
                WHEN pi.expiration_date <= CURRENT_DATE + INTERVAL '3 days' 
                THEN true 
                ELSE false 
            END as expiring_soon
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = %(user_id)s
            AND COALESCE(pi.quantity - pi.used_quantity, pi.quantity) > 0
            AND (pi.expiration_date IS NULL OR pi.expiration_date >= CURRENT_DATE)
        ORDER BY 
            expiring_soon DESC,  -- Prioritize expiring items
            pi.product_name
        LIMIT 50
        """
        
        result = self.db_service.execute_query(query, {"user_id": user_id})
        return result if result else []
    
    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user dietary preferences and restrictions
        PostgreSQL version
        """
        
        query = """
        SELECT 
            user_id,
            preferences
        FROM user_preferences
        WHERE user_id = %(user_id)s
        """
        
        result = self.db_service.execute_query(query, {"user_id": user_id})
        
        if result and result[0].get('preferences'):
            prefs = result[0]['preferences']
            return {
                'dietary_preference': prefs.get('dietary_restrictions', []),
                'allergens': prefs.get('allergens', []),
                'cuisine_preference': prefs.get('cuisine_preferences', []),
                'disliked_ingredients': prefs.get('disliked_ingredients', [])
            }
        
        return {
            'dietary_preference': [],
            'allergens': [],
            'cuisine_preference': [],
            'disliked_ingredients': []
        }
    
    async def _evaluate_recipes(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate recipes using Claude (from notebook pattern)"""
        
        # Evaluate recipes concurrently
        evaluation_tasks = [
            self.recipe_evaluator.evaluate_recipe(recipe)
            for recipe in recipes
        ]
        
        evaluations = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        
        # Add evaluations to recipes
        for recipe, evaluation in zip(recipes, evaluations):
            if isinstance(evaluation, dict):
                recipe['quality_evaluation'] = evaluation
            else:
                logger.error(f"Evaluation failed for recipe {recipe.get('id')}: {evaluation}")
                recipe['quality_evaluation'] = {
                    'score': 3,
                    'critique': 'Evaluation unavailable',
                    'suggestion': ''
                }
        
        return recipes
    
    def _final_ranking(
        self,
        recipes: List[Dict[str, Any]],
        pantry_items: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Final ranking combining all factors
        Inspired by the notebook's multi-agent scoring
        """
        
        # Get expiring items for bonus scoring
        expiring_items = {
            item['product_name'].lower()
            for item in pantry_items
            if item.get('expiring_soon', False)
        }
        
        for recipe in recipes:
            scores = {
                'ingredient_match': recipe.get('match_score', 0.5) * 30,
                'quality': recipe.get('quality_evaluation', {}).get('score', 3) * 20,
                'expected_joy': recipe.get('expected_joy', 50) * 0.5,
                'expiring_bonus': 0
            }
            
            # Bonus for using expiring ingredients
            if expiring_items:
                recipe_ingredients = set()
                
                # Handle both ingredient formats
                if 'extendedIngredients' in recipe:
                    for ing in recipe['extendedIngredients']:
                        recipe_ingredients.add(ing['name'].lower())
                elif 'ingredients' in recipe:
                    for ing in recipe['ingredients']:
                        # Simple string ingredients
                        recipe_ingredients.add(ing.lower().split()[0])
                
                used_expiring = expiring_items & recipe_ingredients
                if used_expiring:
                    scores['expiring_bonus'] = len(used_expiring) * 15
                    recipe['uses_expiring_ingredients'] = list(used_expiring)
            
            # Calculate composite score
            recipe['composite_score'] = sum(scores.values())
            recipe['score_breakdown'] = scores
        
        # Sort by composite score
        recipes.sort(key=lambda r: r['composite_score'], reverse=True)
        
        return recipes


# Example usage function
async def get_quality_dinner_suggestions(user_id: int = 111):
    """
    Example function showing how to use the pipeline
    Similar to the notebook's crew kickoff
    """
    pipeline = RecipeQualityPipeline()
    
    result = await pipeline.get_quality_recipes(
        user_id=user_id,
        message="What can I make for dinner tonight?",
        evaluate_quality=True,  # Use Claude for quality evaluation
        min_quality_score=3     # Only recipes scoring 3+ out of 5
    )
    
    # Format output similar to notebook
    print("\n=== DINNER RECOMMENDATIONS ===\n")
    
    for i, recipe in enumerate(result['recipes'], 1):
        print(f"{i}. {recipe.get('title', recipe.get('name', 'Unknown Recipe'))}")
        print(f"   Score: {recipe.get('composite_score', 0):.1f}")
        
        if 'quality_evaluation' in recipe:
            eval = recipe['quality_evaluation']
            print(f"   Quality: {eval['score']}/5 - {eval['critique']}")
            if eval.get('suggestion'):
                print(f"   Suggestion: {eval['suggestion']}")
        
        if recipe.get('uses_expiring_ingredients'):
            print(f"   ⚡ Uses expiring: {', '.join(recipe['uses_expiring_ingredients'])}")
        
        print(f"   Time: {recipe.get('readyInMinutes', 30)} minutes")
        print()