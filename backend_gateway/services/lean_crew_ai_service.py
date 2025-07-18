"""
Lean CrewAI Service for PrepSense
Optimized for fast response times with parallel agents and smart caching
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import time
from functools import lru_cache
from dataclasses import dataclass

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None

import openai

from .background_flows import BackgroundFlowManager, CacheManager
from .spoonacular_service import SpoonacularService
from .recipe_preference_scorer import RecipePreferenceScorer
from ..utils.smart_cache import cache_recipe_search, cache_recipe_scoring, get_cache

logger = logging.getLogger(__name__)

@dataclass
class RecipeRecommendation:
    """Structured recipe recommendation"""
    recipe_id: str
    title: str
    match_score: float
    confidence: float
    explanation: str
    uses_expiring: bool
    cooking_time: int
    difficulty: str
    ingredients_available: int
    ingredients_missing: int
    nutrition_score: float
    recipe_data: Dict[str, Any]


class FastRecipeVectorSearch:
    """Fast recipe search using cached vectors and filters"""
    
    def __init__(self, spoonacular_service: SpoonacularService):
        self.spoonacular_service = spoonacular_service
        self.cache_ttl = 3600  # 1 hour
    
    @cache_recipe_search(ttl=1800)  # 30 minutes
    async def search_recipes_cached(self, query: str, num_results: int = 20, user_id: int = None) -> List[Dict]:
        """Cached recipe search with smart caching"""
        try:
            # For now, use Spoonacular search
            # In production, this would use vector similarity search
            search_params = {
                'query': query,
                'number': num_results,
                'addRecipeInformation': True,
                'fillIngredients': True,
                'includeNutrition': True
            }
            
            # This would be replaced with vector search
            results = await self.spoonacular_service.search_recipes_by_ingredients(
                ingredients=query.split(','),
                number=num_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in recipe search: {str(e)}")
            return []
    
    async def search_recipes_fast(self, pantry_items: List[str], preferences: Dict, 
                                 num_results: int = 20, user_id: int = None) -> List[Dict]:
        """Fast recipe search with caching"""
        # Search for recipes
        query = ','.join(pantry_items[:10])  # Limit ingredients for API
        
        # Use cached search
        results = await self.search_recipes_cached(query, num_results, user_id)
        
        return results


class NutritionistAgent:
    """Agent focused on nutritional analysis and dietary constraints"""
    
    def __init__(self):
        self.role = "Nutritionist"
        self.goal = "Evaluate recipes for nutritional balance and dietary compliance"
        self.backstory = """You are a registered nutritionist with expertise in meal planning 
        and dietary requirements. You quickly assess recipes for nutritional balance, 
        allergen content, and dietary restriction compliance."""
    
    async def evaluate_recipe(self, recipe: Dict[str, Any], preferences: Dict) -> Dict[str, Any]:
        """Quick nutritional evaluation of a recipe"""
        try:
            start_time = time.time()
            
            # Quick nutritional checks
            nutrition_score = self._calculate_nutrition_score(recipe)
            allergen_check = self._check_allergens(recipe, preferences.get('allergens', []))
            dietary_compliance = self._check_dietary_restrictions(recipe, preferences.get('dietary_restrictions', []))
            
            evaluation = {
                'nutrition_score': nutrition_score,
                'allergen_safe': allergen_check,
                'dietary_compliant': dietary_compliance,
                'calories_per_serving': recipe.get('nutrition', {}).get('calories', 0),
                'protein_score': self._get_protein_score(recipe),
                'evaluation_time': time.time() - start_time
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in nutritionist evaluation: {str(e)}")
            return {
                'nutrition_score': 0.5,
                'allergen_safe': True,
                'dietary_compliant': True,
                'calories_per_serving': 0,
                'protein_score': 0.5,
                'evaluation_time': 0.1
            }
    
    def _calculate_nutrition_score(self, recipe: Dict[str, Any]) -> float:
        """Calculate nutritional balance score (0-1)"""
        nutrition = recipe.get('nutrition', {})
        
        # Basic nutritional balance check
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        carbs = nutrition.get('carbs', 0)
        fat = nutrition.get('fat', 0)
        
        if calories == 0:
            return 0.5  # Unknown nutrition
        
        # Simple scoring based on macronutrient balance
        protein_pct = (protein * 4) / calories if calories > 0 else 0
        carbs_pct = (carbs * 4) / calories if calories > 0 else 0
        fat_pct = (fat * 9) / calories if calories > 0 else 0
        
        # Score based on balanced macros
        balance_score = 1.0
        if protein_pct < 0.1:  # Less than 10% protein
            balance_score -= 0.3
        if carbs_pct > 0.7:  # More than 70% carbs
            balance_score -= 0.2
        if fat_pct > 0.5:  # More than 50% fat
            balance_score -= 0.2
        
        return max(0, min(1, balance_score))
    
    def _check_allergens(self, recipe: Dict[str, Any], allergens: List[str]) -> bool:
        """Check if recipe contains user's allergens"""
        if not allergens:
            return True
        
        recipe_text = json.dumps(recipe).lower()
        for allergen in allergens:
            if allergen.lower() in recipe_text:
                return False
        
        return True
    
    def _check_dietary_restrictions(self, recipe: Dict[str, Any], restrictions: List[str]) -> bool:
        """Check if recipe complies with dietary restrictions"""
        if not restrictions:
            return True
        
        recipe_text = json.dumps(recipe).lower()
        
        # Simple keyword-based checking
        restriction_keywords = {
            'vegetarian': ['meat', 'chicken', 'beef', 'pork', 'fish'],
            'vegan': ['meat', 'chicken', 'beef', 'pork', 'fish', 'dairy', 'milk', 'cheese', 'egg'],
            'gluten-free': ['wheat', 'flour', 'bread', 'pasta'],
            'dairy-free': ['milk', 'cheese', 'butter', 'cream', 'yogurt'],
            'keto': []  # More complex logic needed
        }
        
        for restriction in restrictions:
            if restriction.lower() in restriction_keywords:
                forbidden_items = restriction_keywords[restriction.lower()]
                for item in forbidden_items:
                    if item in recipe_text:
                        return False
        
        return True
    
    def _get_protein_score(self, recipe: Dict[str, Any]) -> float:
        """Get protein adequacy score"""
        nutrition = recipe.get('nutrition', {})
        protein = nutrition.get('protein', 0)
        
        # Score based on protein content
        if protein >= 25:
            return 1.0
        elif protein >= 15:
            return 0.8
        elif protein >= 10:
            return 0.6
        elif protein >= 5:
            return 0.4
        else:
            return 0.2


class CopywriterAgent:
    """Agent focused on crafting engaging recipe descriptions and explanations"""
    
    def __init__(self):
        self.role = "Recipe Copywriter"
        self.goal = "Create compelling recipe descriptions and explanations"
        self.backstory = """You are a food writer who specializes in making recipes 
        sound delicious and explaining why they're perfect for the user's situation."""
    
    async def craft_recommendation(self, recipe: Dict[str, Any], match_details: Dict[str, Any],
                                  nutrition_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Craft engaging recommendation copy"""
        try:
            start_time = time.time()
            
            # Generate explanation
            explanation = self._generate_explanation(recipe, match_details, nutrition_eval)
            
            # Create structured recommendation
            recommendation = {
                'title': recipe.get('title', 'Unknown Recipe'),
                'explanation': explanation,
                'match_score': match_details.get('match_score', 0.5),
                'confidence': match_details.get('confidence', 0.5),
                'highlights': self._generate_highlights(recipe, match_details),
                'cooking_tips': self._generate_cooking_tips(recipe),
                'crafting_time': time.time() - start_time
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error in copywriter crafting: {str(e)}")
            return {
                'title': recipe.get('title', 'Recipe'),
                'explanation': "This recipe looks like a good match for your pantry!",
                'match_score': 0.5,
                'confidence': 0.5,
                'highlights': [],
                'cooking_tips': [],
                'crafting_time': 0.1
            }
    
    def _generate_explanation(self, recipe: Dict[str, Any], match_details: Dict[str, Any], 
                             nutrition_eval: Dict[str, Any]) -> str:
        """Generate explanation for why this recipe is recommended"""
        explanations = []
        
        # Expiring ingredients
        if match_details.get('uses_expiring', False):
            explanations.append("Perfect for using up ingredients that are expiring soon!")
        
        # Pantry match
        available = match_details.get('ingredients_available', 0)
        total = available + match_details.get('ingredients_missing', 0)
        if total > 0:
            match_pct = (available / total) * 100
            if match_pct >= 80:
                explanations.append(f"You have {int(match_pct)}% of the ingredients already!")
            elif match_pct >= 60:
                explanations.append(f"You have most ingredients - only need {match_details.get('ingredients_missing', 0)} more items.")
        
        # Nutrition
        if nutrition_eval.get('nutrition_score', 0) >= 0.7:
            explanations.append("Nutritionally well-balanced for a complete meal.")
        
        # Cooking time
        cook_time = recipe.get('readyInMinutes', 0)
        if cook_time <= 20:
            explanations.append("Quick and easy - ready in under 20 minutes!")
        elif cook_time <= 45:
            explanations.append("Moderate cooking time - perfect for a relaxed meal.")
        
        return " ".join(explanations) if explanations else "A delicious recipe that matches your pantry!"
    
    def _generate_highlights(self, recipe: Dict[str, Any], match_details: Dict[str, Any]) -> List[str]:
        """Generate key highlights for the recipe"""
        highlights = []
        
        # Time highlight
        cook_time = recipe.get('readyInMinutes', 0)
        if cook_time > 0:
            highlights.append(f"⏱️ {cook_time} minutes")
        
        # Servings
        servings = recipe.get('servings', 0)
        if servings > 0:
            highlights.append(f"🍽️ Serves {servings}")
        
        # Difficulty
        instructions = recipe.get('analyzedInstructions', [])
        if instructions:
            step_count = len(instructions[0].get('steps', []))
            if step_count <= 4:
                highlights.append("👌 Easy")
            elif step_count <= 8:
                highlights.append("🔧 Moderate")
            else:
                highlights.append("👨‍🍳 Advanced")
        
        return highlights
    
    def _generate_cooking_tips(self, recipe: Dict[str, Any]) -> List[str]:
        """Generate helpful cooking tips"""
        tips = []
        
        # Generic tips based on recipe type
        title = recipe.get('title', '').lower()
        
        if 'pasta' in title:
            tips.append("Cook pasta al dente for best texture")
        elif 'chicken' in title:
            tips.append("Use meat thermometer to ensure chicken reaches 165°F")
        elif 'salad' in title:
            tips.append("Dress salad just before serving to keep greens crisp")
        
        return tips


class LeanCrewAIService:
    """Optimized CrewAI service for fast recipe recommendations"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.background_flows = BackgroundFlowManager()
        self.cache_manager = CacheManager(self.background_flows)
        from .spoonacular_service import SpoonacularService
        self.vector_search = FastRecipeVectorSearch(SpoonacularService())
        self.preference_scorer = RecipePreferenceScorer()
        
        # Initialize agents
        self.nutritionist = NutritionistAgent()
        self.copywriter = CopywriterAgent()
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'avg_response_time': 0,
            'cache_hit_rate': 0
        }
    
    async def get_recipe_recommendations(self, user_id: int, query: str, 
                                       num_recommendations: int = 3) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get recipe recommendations with streaming response
        Optimized for <2s first response, <5s complete response
        """
        start_time = time.time()
        
        try:
            # Step 1: Ensure cache is fresh (fast if already cached)
            cache_start = time.time()
            await self.cache_manager.ensure_fresh_cache(user_id, self.db_service)
            cache_time = time.time() - cache_start
            
            # Step 2: Load cached data (very fast)
            inventory = self.background_flows.load_cached_inventory()
            expiry_data = self.background_flows.load_cached_expiry()
            preferences = self.background_flows.load_cached_preferences()
            
            if not inventory:
                raise ValueError("No inventory data available")
            
            # Step 3: Fast recipe search (≤300ms)
            search_start = time.time()
            pantry_items = [item['name'] for item in inventory['items']]
            pref_dict = preferences.__dict__ if preferences else {}
            
            candidate_recipes = await self.vector_search.search_recipes_fast(
                pantry_items, pref_dict, num_recommendations * 3, user_id
            )
            search_time = time.time() - search_start
            
            # Step 4: Parallel agent evaluation
            eval_start = time.time()
            
            # Process recipes in parallel
            recommendation_tasks = []
            for recipe in candidate_recipes[:num_recommendations * 2]:  # Process more than needed
                task = self._evaluate_recipe_parallel(recipe, inventory, expiry_data, preferences, user_id)
                recommendation_tasks.append(task)
            
            # Wait for all evaluations
            evaluations = await asyncio.gather(*recommendation_tasks, return_exceptions=True)
            
            # Filter out exceptions and sort by score
            valid_recommendations = [
                eval_result for eval_result in evaluations 
                if not isinstance(eval_result, Exception) and eval_result.get('match_score', 0) > 0.3
            ]
            
            valid_recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            eval_time = time.time() - eval_start
            
            # Step 5: Stream results
            total_time = time.time() - start_time
            
            # Update performance stats
            self.performance_stats['total_requests'] += 1
            self.performance_stats['avg_response_time'] = (
                (self.performance_stats['avg_response_time'] * (self.performance_stats['total_requests'] - 1) + total_time) 
                / self.performance_stats['total_requests']
            )
            
            # Yield results with timing info
            for i, recommendation in enumerate(valid_recommendations[:num_recommendations]):
                yield {
                    'recommendation': recommendation,
                    'index': i,
                    'total_found': len(valid_recommendations),
                    'timing': {
                        'cache_time': cache_time,
                        'search_time': search_time,
                        'eval_time': eval_time,
                        'total_time': total_time
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in recipe recommendations: {str(e)}")
            yield {
                'error': str(e),
                'timing': {
                    'total_time': time.time() - start_time
                }
            }
    
    async def _evaluate_recipe_parallel(self, recipe: Dict[str, Any], inventory: Dict[str, Any], 
                                       expiry_data: Dict[str, Any], preferences, user_id: int) -> Dict[str, Any]:
        """Evaluate a single recipe using parallel agents"""
        try:
            # Calculate match score
            match_details = await self._calculate_match_score(recipe, inventory, expiry_data, preferences, user_id)
            
            # Run agents in parallel
            nutrition_task = self.nutritionist.evaluate_recipe(
                recipe, preferences.__dict__ if preferences else {}
            )
            
            copywriter_task = self.copywriter.craft_recommendation(
                recipe, match_details, {}  # nutrition_eval will be filled after
            )
            
            # Wait for both agents
            nutrition_eval, copy_result = await asyncio.gather(nutrition_task, copywriter_task)
            
            # Combine results
            recommendation = {
                'recipe_id': str(recipe.get('id', 'unknown')),
                'title': recipe.get('title', 'Unknown Recipe'),
                'match_score': match_details['match_score'],
                'confidence': match_details['confidence'],
                'explanation': copy_result['explanation'],
                'uses_expiring': match_details['uses_expiring'],
                'cooking_time': recipe.get('readyInMinutes', 0),
                'difficulty': self._get_difficulty(recipe),
                'ingredients_available': match_details['ingredients_available'],
                'ingredients_missing': match_details['ingredients_missing'],
                'nutrition_score': nutrition_eval['nutrition_score'],
                'recipe_data': recipe,
                'highlights': copy_result['highlights'],
                'cooking_tips': copy_result['cooking_tips'],
                'allergen_safe': nutrition_eval['allergen_safe'],
                'dietary_compliant': nutrition_eval['dietary_compliant']
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error evaluating recipe {recipe.get('id', 'unknown')}: {str(e)}")
            return {
                'recipe_id': str(recipe.get('id', 'unknown')),
                'title': recipe.get('title', 'Unknown Recipe'),
                'match_score': 0.1,
                'confidence': 0.1,
                'explanation': "Unable to evaluate this recipe",
                'error': str(e)
            }
    
    @cache_recipe_scoring(ttl=1800)  # 30 minutes
    async def _calculate_match_score(self, recipe: Dict[str, Any], inventory: Dict[str, Any], 
                              expiry_data: Dict[str, Any], preferences, user_id: int) -> Dict[str, Any]:
        """Calculate how well recipe matches user's pantry and preferences"""
        
        # Use existing preference scorer
        if preferences:
            base_score = self.preference_scorer.calculate_preference_score(
                recipe, preferences.__dict__
            )
        else:
            base_score = 0.5
        
        # Check ingredient availability
        recipe_ingredients = recipe.get('extendedIngredients', [])
        pantry_items = [item['name'].lower() for item in inventory['items']]
        
        available_count = 0
        missing_count = 0
        uses_expiring = False
        
        for ingredient in recipe_ingredients:
            ingredient_name = ingredient.get('name', '').lower()
            
            # Check if we have this ingredient
            if any(ingredient_name in pantry_item for pantry_item in pantry_items):
                available_count += 1
            else:
                missing_count += 1
            
            # Check if it uses expiring ingredients
            if expiry_data:
                expiring_names = [item['name'].lower() for item in expiry_data['expiring_items']]
                if any(ingredient_name in expiring_name for expiring_name in expiring_names):
                    uses_expiring = True
        
        # Calculate match score
        total_ingredients = available_count + missing_count
        pantry_match = available_count / total_ingredients if total_ingredients > 0 else 0
        
        # Boost score for using expiring ingredients
        if uses_expiring:
            base_score += 0.2
        
        # Combine scores
        final_score = (base_score * 0.6) + (pantry_match * 0.4)
        
        return {
            'match_score': min(1.0, final_score),
            'confidence': pantry_match,
            'uses_expiring': uses_expiring,
            'ingredients_available': available_count,
            'ingredients_missing': missing_count,
            'pantry_match': pantry_match
        }
    
    def _get_difficulty(self, recipe: Dict[str, Any]) -> str:
        """Determine recipe difficulty"""
        instructions = recipe.get('analyzedInstructions', [])
        if not instructions:
            return 'unknown'
        
        step_count = len(instructions[0].get('steps', []))
        cook_time = recipe.get('readyInMinutes', 0)
        
        if step_count <= 4 and cook_time <= 30:
            return 'easy'
        elif step_count <= 8 and cook_time <= 60:
            return 'medium'
        else:
            return 'hard'
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()


# Singleton instance
_lean_crew_service = None

def get_lean_crew_service(db_service) -> LeanCrewAIService:
    """Get singleton instance of LeanCrewAIService"""
    global _lean_crew_service
    if _lean_crew_service is None:
        _lean_crew_service = LeanCrewAIService(db_service)
    return _lean_crew_service