"""
Simplified evaluation pipeline without full CrewAI dependency
Uses direct API calls to Claude for recipe evaluation
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from backend_gateway.services.crew_ai_service import CrewAIService
from backend_gateway.services.recipe_evaluator_service import RecipeEvaluator
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)


class SimpleEvaluationPipeline:
    """
    Simplified version of hybrid approach without CrewAI agents
    Uses direct service calls for evaluation
    """
    
    def __init__(self):
        self.crew_ai_service = CrewAIService()  # Existing recipe generator
        self.recipe_evaluator = RecipeEvaluator()  # Claude evaluator
        self.db_service = get_database_service()
    
    async def generate_and_evaluate(
        self,
        user_id: int,
        message: str,
        use_preferences: bool = True,
        evaluate_quality: bool = True,
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Generate recipes and optionally evaluate their quality
        
        This is a simplified version that:
        1. Generates recipes with OpenAI (fast)
        2. Evaluates top N with Claude (quality check)
        3. Adds nutrition and preference scoring
        """
        
        # Step 1: Generate recipes (2-3 seconds)
        logger.info("Generating recipes...")
        start_time = datetime.now()
        
        generation_result = await self.crew_ai_service.process_message(
            user_id=user_id,
            message=message,
            use_preferences=use_preferences
        )
        
        generation_time = (datetime.now() - start_time).total_seconds()
        recipes = generation_result.get('recipes', [])
        
        if not recipes or not evaluate_quality:
            return {
                **generation_result,
                'performance': {
                    'generation_time': generation_time,
                    'evaluation_time': 0,
                    'total_time': generation_time
                }
            }
        
        # Step 2: Evaluate top recipes
        logger.info(f"Evaluating top {top_n} recipes...")
        eval_start = datetime.now()
        
        # Get user preferences for scoring
        preferences = await self._get_user_preferences(user_id)
        
        # Evaluate recipes in parallel
        recipes_to_eval = recipes[:top_n]
        evaluation_tasks = []
        
        for recipe in recipes_to_eval:
            task = self._evaluate_single_recipe(recipe, preferences)
            evaluation_tasks.append(task)
        
        evaluations = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        
        # Add evaluations to recipes
        for recipe, evaluation in zip(recipes_to_eval, evaluations):
            if isinstance(evaluation, dict):
                recipe['evaluation'] = evaluation
                recipe['quality_evaluated'] = True
            else:
                logger.error(f"Evaluation failed: {evaluation}")
                recipe['quality_evaluated'] = False
        
        # Step 3: Final scoring and ranking
        self._calculate_final_scores(recipes)
        
        # Sort by final score
        recipes.sort(key=lambda r: r.get('final_score', 0), reverse=True)
        
        eval_time = (datetime.now() - eval_start).total_seconds()
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            **generation_result,
            'recipes': recipes,
            'quality_evaluated': True,
            'evaluated_count': len([r for r in recipes if r.get('quality_evaluated')]),
            'performance': {
                'generation_time': generation_time,
                'evaluation_time': eval_time,
                'total_time': total_time
            }
        }
    
    async def _evaluate_single_recipe(
        self, 
        recipe: Dict[str, Any], 
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a single recipe for quality, nutrition, and preferences"""
        
        evaluation = {}
        
        # 1. Quality evaluation with Claude
        try:
            quality_result = await self.recipe_evaluator.evaluate_recipe(recipe)
            evaluation['quality'] = quality_result
        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}")
            evaluation['quality'] = {'score': 3, 'critique': 'Evaluation unavailable'}
        
        # 2. Nutritional scoring
        nutrition_score = self._score_nutrition(recipe.get('nutrition', {}), preferences)
        evaluation['nutrition_score'] = nutrition_score
        
        # 3. Preference matching
        preference_score = self._score_preferences(recipe, preferences)
        evaluation['preference_score'] = preference_score
        
        # 4. Complexity assessment
        complexity = self._assess_complexity(recipe)
        evaluation['complexity'] = complexity
        
        return evaluation
    
    def _score_nutrition(self, nutrition: Dict[str, Any], preferences: Dict[str, Any]) -> int:
        """Score nutritional content (0-100)"""
        
        score = 100
        
        # Check calories (ideal meal: 400-700 calories)
        calories = nutrition.get('calories', 500)
        if calories < 300:
            score -= 20
        elif calories > 900:
            score -= 25
        
        # Check protein (ideal: 20-40g)
        protein = nutrition.get('protein', 25)
        if protein < 15:
            score -= 15
        elif protein > 50:
            score -= 10
        
        # Check balance
        carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 50))
        fat = nutrition.get('fat', 20)
        
        # Simple macro balance check
        total_cals_from_macros = (protein * 4) + (carbs * 4) + (fat * 9)
        if total_cals_from_macros > 0:
            protein_percent = (protein * 4) / total_cals_from_macros * 100
            if protein_percent < 15 or protein_percent > 40:
                score -= 10
        
        return max(0, score)
    
    def _score_preferences(self, recipe: Dict[str, Any], preferences: Dict[str, Any]) -> int:
        """Score recipe based on user preferences (0-100)"""
        
        score = 100
        
        # Check dietary restrictions
        dietary = set(preferences.get('dietary_preference', []))
        recipe_tags = set(recipe.get('dietary_tags', []))
        
        if dietary and not dietary.intersection(recipe_tags):
            score -= 30
        
        # Check allergens
        allergens = preferences.get('allergens', [])
        if allergens:
            ingredients_text = ' '.join([
                ing.get('name', '').lower() 
                for ing in recipe.get('extendedIngredients', [])
            ])
            
            for allergen in allergens:
                if allergen.lower() in ingredients_text:
                    score = 0  # Automatic fail
                    break
        
        # Bonus for matching cuisine preferences
        cuisine_prefs = set(preferences.get('cuisine_preference', []))
        recipe_cuisine = recipe.get('cuisine_type', '').lower()
        
        if cuisine_prefs and recipe_cuisine in cuisine_prefs:
            score = min(100, score + 10)
        
        return score
    
    def _assess_complexity(self, recipe: Dict[str, Any]) -> str:
        """Assess recipe complexity"""
        
        # Get number of ingredients and steps
        num_ingredients = len(recipe.get('extendedIngredients', []))
        num_steps = len(recipe.get('instructions', []))
        cook_time = recipe.get('readyInMinutes', 30)
        
        # Simple complexity scoring
        if num_ingredients <= 5 and num_steps <= 4 and cook_time <= 20:
            return "easy"
        elif num_ingredients <= 10 and num_steps <= 8 and cook_time <= 45:
            return "moderate"
        else:
            return "complex"
    
    def _calculate_final_scores(self, recipes: List[Dict[str, Any]]):
        """Calculate final composite scores for all recipes"""
        
        for recipe in recipes:
            if recipe.get('quality_evaluated'):
                eval = recipe.get('evaluation', {})
                
                # Weighted scoring
                scores = {
                    'quality': eval.get('quality', {}).get('score', 3) * 20,  # 0-100
                    'nutrition': eval.get('nutrition_score', 50),  # 0-100
                    'preferences': eval.get('preference_score', 50),  # 0-100
                    'match_score': recipe.get('match_score', 0.5) * 100,  # 0-100
                    'expected_joy': recipe.get('expected_joy', 50)  # 0-100
                }
                
                # Bonus for simple recipes
                if eval.get('complexity') == 'easy':
                    scores['complexity_bonus'] = 10
                else:
                    scores['complexity_bonus'] = 0
                
                # Calculate weighted average
                weights = {
                    'quality': 0.25,
                    'nutrition': 0.15,
                    'preferences': 0.20,
                    'match_score': 0.20,
                    'expected_joy': 0.15,
                    'complexity_bonus': 0.05
                }
                
                final_score = sum(scores[k] * weights[k] for k in scores)
                recipe['final_score'] = final_score
                recipe['score_breakdown'] = scores
            else:
                # Non-evaluated recipes get base score
                recipe['final_score'] = recipe.get('expected_joy', 50)
    
    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences from database"""
        
        query = """
        SELECT preferences 
        FROM user_preferences 
        WHERE user_id = %(user_id)s
        """
        
        result = self.db_service.execute_query(query, {"user_id": user_id})
        
        if result and result[0].get('preferences'):
            prefs = result[0]['preferences']
            return {
                'dietary_preference': prefs.get('dietary_restrictions', []),
                'allergens': prefs.get('allergens', []),
                'cuisine_preference': prefs.get('cuisine_preferences', [])
            }
        
        return {}


# Comparison function for testing
async def compare_approaches(user_id: int = 111):
    """Compare generation with and without evaluation"""
    
    pipeline = SimpleEvaluationPipeline()
    
    print("\n=== COMPARISON TEST ===\n")
    
    # Test 1: Without evaluation
    print("1. Fast generation only...")
    result1 = await pipeline.generate_and_evaluate(
        user_id=user_id,
        message="What can I make for dinner?",
        evaluate_quality=False
    )
    print(f"   Time: {result1['performance']['total_time']:.2f}s")
    print(f"   Recipes: {len(result1['recipes'])}")
    
    # Test 2: With evaluation
    print("\n2. Generation + quality evaluation...")
    result2 = await pipeline.generate_and_evaluate(
        user_id=user_id,
        message="What can I make for dinner?",
        evaluate_quality=True,
        top_n=3
    )
    print(f"   Time: {result2['performance']['total_time']:.2f}s")
    print(f"   Recipes: {len(result2['recipes'])}")
    print(f"   Evaluated: {result2['evaluated_count']}")
    
    # Show evaluated recipes
    print("\n=== TOP EVALUATED RECIPES ===")
    for i, recipe in enumerate(result2['recipes'][:3], 1):
        print(f"\n{i}. {recipe.get('title', 'Unknown')}")
        print(f"   Final Score: {recipe.get('final_score', 0):.1f}/100")
        
        if recipe.get('quality_evaluated'):
            eval = recipe.get('evaluation', {})
            print(f"   Quality: {eval.get('quality', {}).get('score', 'N/A')}/5")
            print(f"   Nutrition: {eval.get('nutrition_score', 'N/A')}/100")
            print(f"   Preferences: {eval.get('preference_score', 'N/A')}/100")
            print(f"   Complexity: {eval.get('complexity', 'N/A')}")