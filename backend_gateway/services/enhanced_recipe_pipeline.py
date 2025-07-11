"""Enhanced recipe generation pipeline using multi-agent approach"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnhancedRecipePipeline:
    """
    Multi-stage recipe generation pipeline inspired by CrewAI notebook
    
    Stages:
    1. Pantry Analysis - What ingredients are available/expiring
    2. Preference Analysis - User dietary restrictions and preferences
    3. Recipe Generation - Create recipes using AI
    4. Quality Evaluation - Score recipes for quality
    5. Nutritional Analysis - Ensure nutritional balance
    6. Final Ranking - Combine all scores for best recommendations
    """
    
    def __init__(
        self,
        pantry_service,
        preference_service,
        recipe_generator,
        recipe_evaluator,
        nutrition_analyzer
    ):
        self.pantry_service = pantry_service
        self.preference_service = preference_service
        self.recipe_generator = recipe_generator
        self.recipe_evaluator = recipe_evaluator
        self.nutrition_analyzer = nutrition_analyzer
    
    async def generate_recommendations(
        self, 
        user_id: int,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate recipe recommendations through multi-stage pipeline
        
        Args:
            user_id: User ID
            context: Additional context (meal_type, time_available, etc.)
            
        Returns:
            List of scored and ranked recipes
        """
        
        # Stage 1: Pantry Analysis
        pantry_analysis = await self._analyze_pantry(user_id)
        
        # Stage 2: Preference Analysis
        preferences = await self._get_user_preferences(user_id)
        
        # Stage 3: Recipe Generation
        recipes = await self._generate_recipes(
            pantry_analysis,
            preferences,
            context
        )
        
        # Stage 4: Quality Evaluation
        evaluated_recipes = await self._evaluate_recipe_quality(recipes)
        
        # Stage 5: Nutritional Analysis
        nutritionally_scored = await self._analyze_nutrition(
            evaluated_recipes,
            preferences
        )
        
        # Stage 6: Final Ranking
        ranked_recipes = self._rank_recipes(
            nutritionally_scored,
            pantry_analysis,
            preferences,
            context
        )
        
        return ranked_recipes[:5]  # Return top 5
    
    async def _analyze_pantry(self, user_id: int) -> Dict[str, Any]:
        """Analyze pantry for available and expiring ingredients"""
        
        # Get all pantry items
        items = await self.pantry_service.get_user_pantry_items(user_id)
        
        # Categorize by expiration
        today = datetime.now().date()
        expiring_soon = []
        fresh = []
        
        for item in items:
            if item.get('expiration_date'):
                exp_date = datetime.strptime(
                    str(item['expiration_date']), 
                    '%Y-%m-%d'
                ).date()
                days_until = (exp_date - today).days
                
                if 0 <= days_until <= 3:
                    expiring_soon.append(item)
                elif days_until > 3:
                    fresh.append(item)
        
        return {
            'all_items': items,
            'expiring_soon': expiring_soon,
            'fresh': fresh,
            'total_count': len(items),
            'expiring_count': len(expiring_soon)
        }
    
    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user preferences"""
        
        # This would fetch from your preference service
        # For now, return structure
        return {
            'dietary_restrictions': [],
            'allergens': [],
            'cuisine_preferences': [],
            'disliked_ingredients': [],
            'cooking_skill': 'intermediate',
            'nutritional_goals': {
                'daily_calories': 2000,
                'protein_target': 50,
                'low_sodium': False
            }
        }
    
    async def _generate_recipes(
        self,
        pantry_analysis: Dict[str, Any],
        preferences: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recipes prioritizing expiring ingredients"""
        
        # Prioritize expiring ingredients
        ingredient_list = []
        if pantry_analysis['expiring_soon']:
            # Add expiring items first
            ingredient_list.extend([
                item['product_name'] 
                for item in pantry_analysis['expiring_soon']
            ])
        
        # Add other available ingredients
        ingredient_list.extend([
            item['product_name'] 
            for item in pantry_analysis['fresh'][:20]  # Limit to 20
        ])
        
        # Generate recipes
        message = f"Create recipes for {context.get('meal_type', 'dinner')}"
        if pantry_analysis['expiring_soon']:
            message += f" using these expiring ingredients: {', '.join(ingredient_list[:5])}"
        
        recipes = await self.recipe_generator.generate_recipes(
            ingredients=ingredient_list,
            preferences=preferences,
            message=message
        )
        
        return recipes
    
    async def _evaluate_recipe_quality(
        self, 
        recipes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate each recipe for quality"""
        
        for recipe in recipes:
            evaluation = await self.recipe_evaluator.evaluate_recipe(recipe)
            recipe['quality_score'] = evaluation['score']
            recipe['quality_feedback'] = evaluation['critique']
            recipe['improvement_suggestion'] = evaluation['suggestion']
        
        return recipes
    
    async def _analyze_nutrition(
        self,
        recipes: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score recipes based on nutritional goals"""
        
        goals = preferences.get('nutritional_goals', {})
        
        for recipe in recipes:
            nutrition = recipe.get('nutrition', {})
            
            # Simple scoring based on goals
            score = 100
            
            # Calorie check (within 20% of target for a meal)
            meal_calories = goals.get('daily_calories', 2000) / 3
            recipe_calories = nutrition.get('calories', meal_calories)
            calorie_diff = abs(recipe_calories - meal_calories) / meal_calories
            if calorie_diff > 0.2:
                score -= min(20, calorie_diff * 50)
            
            # Protein check
            if goals.get('protein_target'):
                meal_protein = goals['protein_target'] / 3
                recipe_protein = nutrition.get('protein', 0)
                if recipe_protein < meal_protein * 0.8:
                    score -= 10
            
            # Sodium check
            if goals.get('low_sodium') and nutrition.get('sodium', 0) > 600:
                score -= 20
            
            recipe['nutrition_score'] = max(0, score)
        
        return recipes
    
    def _rank_recipes(
        self,
        recipes: List[Dict[str, Any]],
        pantry_analysis: Dict[str, Any],
        preferences: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Final ranking combining all factors"""
        
        for recipe in recipes:
            # Calculate composite score
            scores = {
                'quality': recipe.get('quality_score', 3) * 20,  # 0-100
                'nutrition': recipe.get('nutrition_score', 50),  # 0-100
                'ingredient_match': recipe.get('match_score', 0.5) * 100,  # 0-100
                'uses_expiring': 0  # Bonus for using expiring ingredients
            }
            
            # Bonus for using expiring ingredients
            if pantry_analysis['expiring_soon']:
                expiring_names = {
                    item['product_name'].lower() 
                    for item in pantry_analysis['expiring_soon']
                }
                recipe_ingredients = set()
                for ing in recipe.get('extendedIngredients', []):
                    recipe_ingredients.add(ing['name'].lower())
                
                overlap = expiring_names & recipe_ingredients
                if overlap:
                    scores['uses_expiring'] = len(overlap) * 10
            
            # Time appropriateness
            if context.get('time_available'):
                if recipe.get('readyInMinutes', 30) <= context['time_available']:
                    scores['time_appropriate'] = 20
                else:
                    scores['time_appropriate'] = 0
            
            # Calculate final score
            recipe['final_score'] = sum(scores.values()) / len(scores)
            recipe['score_breakdown'] = scores
        
        # Sort by final score
        recipes.sort(key=lambda r: r['final_score'], reverse=True)
        
        return recipes