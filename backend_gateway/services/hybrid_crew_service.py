"""
Hybrid CrewAI Service - Combines fast OpenAI generation with CrewAI quality evaluation
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from crewai import Agent, Crew, Task, Process
except ImportError:
    # Mock for testing without CrewAI
    Agent = Crew = Task = Process = None

from backend_gateway.services.base_tool import BaseTool
from pydantic import BaseModel, Field

from backend_gateway.services.crew_ai_service import CrewAIService
from backend_gateway.services.recipe_evaluator_service import RecipeEvaluator
from backend_gateway.services.spoonacular_enhanced_agents import (
    EnhancedCrewAgents, 
    evaluate_ai_recipe_with_spoonacular,
    validate_recipe_authenticity,
    optimize_recipe_cost,
    check_leftover_compatibility
)
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)


class RecipeEvaluationTool(BaseTool):
    """Tool for evaluating recipe quality using Claude"""
    name: str = "recipe_quality_evaluator"
    description: str = "Evaluates a recipe for quality, clarity, and feasibility"
    
    def __init__(self):
        super().__init__()
        self.evaluator = RecipeEvaluator()
    
    def _run(self, recipe_text: str) -> str:
        """Evaluate a recipe and return quality assessment"""
        try:
            # Parse recipe if it's a string
            import json
            if isinstance(recipe_text, str):
                recipe = json.loads(recipe_text)
            else:
                recipe = recipe_text
                
            result = self.evaluator.evaluate_recipe(recipe)
            
            return f"""
Quality Score: {result['score']}/5
Critique: {result['critique']}
Suggestion: {result['suggestion']}
"""
        except Exception as e:
            logger.error(f"Error evaluating recipe: {e}")
            return f"Error evaluating recipe: {str(e)}"


class NutritionAnalysisTool(BaseTool):
    """Tool for analyzing nutritional content"""
    name: str = "nutrition_analyzer"
    description: str = "Analyzes the nutritional value and balance of a recipe"
    
    def _run(self, recipe_data: str) -> str:
        """Analyze nutrition and return assessment"""
        try:
            import json
            if isinstance(recipe_data, str):
                recipe = json.loads(recipe_data)
            else:
                recipe = recipe_data
            
            nutrition = recipe.get('nutrition', {})
            
            # Basic nutritional analysis
            calories = nutrition.get('calories', 0)
            protein = nutrition.get('protein', 0)
            carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
            fat = nutrition.get('fat', 0)
            
            # Calculate macro ratios
            total_macros = protein * 4 + carbs * 4 + fat * 9
            protein_ratio = (protein * 4 / total_macros * 100) if total_macros > 0 else 0
            carb_ratio = (carbs * 4 / total_macros * 100) if total_macros > 0 else 0
            fat_ratio = (fat * 9 / total_macros * 100) if total_macros > 0 else 0
            
            # Assess balance
            balance_score = 100
            feedback = []
            
            # Check protein (should be 20-35%)
            if protein_ratio < 15:
                balance_score -= 20
                feedback.append("Low protein content")
            elif protein_ratio > 40:
                balance_score -= 10
                feedback.append("Very high protein")
                
            # Check carbs (should be 45-65%)
            if carb_ratio < 30:
                balance_score -= 15
                feedback.append("Low carbohydrate content")
            elif carb_ratio > 70:
                balance_score -= 15
                feedback.append("High carbohydrate content")
                
            # Check fat (should be 20-35%)
            if fat_ratio < 15:
                balance_score -= 15
                feedback.append("Low fat content")
            elif fat_ratio > 40:
                balance_score -= 20
                feedback.append("High fat content")
            
            # Check calories (reasonable meal = 400-800)
            if calories < 300:
                feedback.append("Very low calorie")
            elif calories > 1000:
                feedback.append("Very high calorie")
            
            return f"""
Nutritional Analysis:
- Calories: {calories}
- Protein: {protein}g ({protein_ratio:.1f}%)
- Carbs: {carbs}g ({carb_ratio:.1f}%)
- Fat: {fat}g ({fat_ratio:.1f}%)

Balance Score: {balance_score}/100
Feedback: {', '.join(feedback) if feedback else 'Well balanced'}
"""
        except Exception as e:
            logger.error(f"Error analyzing nutrition: {e}")
            return f"Error analyzing nutrition: {str(e)}"


class PreferenceMatchingTool(BaseTool):
    """Tool for checking if recipe matches user preferences"""
    name: str = "preference_matcher"
    description: str = "Checks if a recipe matches user dietary preferences and restrictions"
    
    def __init__(self, db_service):
        super().__init__()
        self.db_service = db_service
    
    def _run(self, recipe_and_user: str) -> str:
        """Check preference matching"""
        try:
            import json
            data = json.loads(recipe_and_user)
            recipe = data['recipe']
            user_id = data['user_id']
            
            # Get user preferences
            prefs_query = """
            SELECT preferences 
            FROM user_preferences 
            WHERE user_id = %(user_id)s
            """
            result = self.db_service.execute_query(prefs_query, {"user_id": user_id})
            
            if not result:
                return "No preferences found for user"
            
            preferences = result[0]['preferences']
            dietary = set(preferences.get('dietary_restrictions', []))
            allergens = set(preferences.get('allergens', []))
            
            # Check recipe compliance
            issues = []
            
            # Check dietary tags
            recipe_tags = set(recipe.get('dietary_tags', []))
            if dietary and not dietary.intersection(recipe_tags):
                issues.append(f"Does not match dietary preferences: {dietary}")
            
            # Check allergens in ingredients
            ingredients_text = ' '.join([
                ing.get('name', '').lower() 
                for ing in recipe.get('extendedIngredients', [])
            ])
            
            for allergen in allergens:
                if allergen.lower() in ingredients_text:
                    issues.append(f"Contains allergen: {allergen}")
            
            if issues:
                return f"Preference Issues: {'; '.join(issues)}"
            else:
                return "Perfectly matches user preferences!"
                
        except Exception as e:
            logger.error(f"Error matching preferences: {e}")
            return f"Error matching preferences: {str(e)}"


class HybridCrewService:
    """
    Hybrid approach: Fast OpenAI generation + CrewAI quality evaluation
    """
    
    def __init__(self):
        self.crew_ai_service = CrewAIService()  # Existing fast generator
        self.db_service = get_database_service()
        self.enhanced_agents = EnhancedCrewAgents()  # Spoonacular-enhanced agents
        self._setup_agents()
        
        # Check if CrewAI is available
        self.crewai_available = self._check_crewai_availability()
    
    def _check_crewai_availability(self):
        """Check if CrewAI is properly installed"""
        try:
            from crewai import Agent, Crew, Task
            return True
        except ImportError:
            logger.warning("CrewAI not available. Will use Spoonacular-enhanced evaluation.")
            return False
    
    def _setup_agents(self):
        """Setup CrewAI agents for quality evaluation"""
        
        # Initialize tools
        self.recipe_eval_tool = RecipeEvaluationTool()
        self.nutrition_tool = NutritionAnalysisTool()
        self.preference_tool = PreferenceMatchingTool(self.db_service)
        
        # Create specialized agents
        self.quality_agent = Agent(
            role="Recipe Quality Evaluator",
            goal="Evaluate recipes for quality, clarity, and feasibility",
            backstory="You are a professional chef who evaluates recipe quality",
            tools=[self.recipe_eval_tool],
            verbose=True,
            allow_delegation=False
        )
        
        self.nutrition_agent = Agent(
            role="Nutritional Analyst",
            goal="Analyze nutritional balance and healthiness of recipes",
            backstory="You are a nutritionist who ensures meals are balanced",
            tools=[self.nutrition_tool],
            verbose=True,
            allow_delegation=False
        )
        
        self.preference_agent = Agent(
            role="Preference Compliance Checker",
            goal="Ensure recipes match user dietary preferences",
            backstory="You ensure recipes are safe and appropriate for users",
            tools=[self.preference_tool],
            verbose=True,
            allow_delegation=False
        )
        
        self.ranking_agent = Agent(
            role="Recipe Ranking Specialist",
            goal="Rank recipes based on quality, nutrition, and preferences",
            backstory="You combine all factors to rank recipes optimally",
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    async def generate_and_evaluate_recipes(
        self,
        user_id: int,
        message: str,
        use_preferences: bool = True,
        evaluate_top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Generate recipes with OpenAI, then evaluate with CrewAI
        
        Args:
            user_id: User ID
            message: User's request
            use_preferences: Whether to use dietary preferences
            evaluate_top_n: How many top recipes to evaluate
            
        Returns:
            Enhanced recipe recommendations with quality scores
        """
        
        # Step 1: Generate recipes using existing fast service
        logger.info("Generating recipes with OpenAI...")
        start_time = datetime.now()
        
        generation_result = await self.crew_ai_service.process_message(
            user_id=user_id,
            message=message,
            use_preferences=use_preferences
        )
        
        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Generated {len(generation_result['recipes'])} recipes in {generation_time:.2f}s")
        
        # Step 2: Choose evaluation method based on availability
        recipes = generation_result['recipes'][:evaluate_top_n]
        
        if not recipes:
            return generation_result
        
        eval_start = datetime.now()
        
        # Option 1: Use Spoonacular-enhanced evaluation (always available)
        if not self.crewai_available or evaluate_top_n > 0:
            logger.info(f"Evaluating top {len(recipes)} recipes with Spoonacular-enhanced agents...")
            return await self._evaluate_with_spoonacular(generation_result, user_id, message, evaluate_top_n, generation_time, eval_start)
        
        # Option 2: Use original CrewAI evaluation (if available)
        logger.info(f"Evaluating top {len(recipes)} recipes with CrewAI...")
        
        # Create evaluation tasks
        tasks = []
        for i, recipe in enumerate(recipes):
            # Quality evaluation task
            quality_task = Task(
                description=f"Evaluate the quality of recipe: {recipe.get('title', 'Unknown')}",
                agent=self.quality_agent,
                expected_output="Quality score and feedback"
            )
            
            # Nutrition analysis task
            nutrition_task = Task(
                description=f"Analyze the nutritional content of recipe: {recipe.get('title', 'Unknown')}",
                agent=self.nutrition_agent,
                expected_output="Nutritional assessment"
            )
            
            # Preference matching task
            pref_task = Task(
                description=f"Check if recipe matches user {user_id} preferences",
                agent=self.preference_agent,
                expected_output="Preference compliance report"
            )
            
            tasks.extend([quality_task, nutrition_task, pref_task])
        
        # Final ranking task
        ranking_task = Task(
            description="Rank all evaluated recipes based on quality, nutrition, and preferences",
            agent=self.ranking_agent,
            expected_output="Final ranked list with scores",
            context=tasks  # Depends on all evaluation tasks
        )
        tasks.append(ranking_task)
        
        # Create and run crew
        evaluation_crew = Crew(
            agents=[
                self.quality_agent,
                self.nutrition_agent,
                self.preference_agent,
                self.ranking_agent
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Prepare inputs for crew
        crew_inputs = {
            "recipes": recipes,
            "user_id": user_id
        }
        
        try:
            crew_result = evaluation_crew.kickoff(inputs=crew_inputs)
            eval_time = (datetime.now() - eval_start).total_seconds()
            logger.info(f"Evaluation completed in {eval_time:.2f}s")
            
            # Enhance original results with evaluation data
            generation_result['evaluation'] = {
                'evaluated_count': len(recipes),
                'evaluation_time': eval_time,
                'crew_output': str(crew_result)
            }
            
            # Add evaluation scores to recipes
            # (In production, parse crew_result to extract individual scores)
            for recipe in generation_result['recipes'][:evaluate_top_n]:
                recipe['quality_evaluated'] = True
                recipe['evaluation_score'] = 4  # Placeholder
            
        except Exception as e:
            logger.error(f"Crew evaluation failed: {e}")
            generation_result['evaluation'] = {
                'error': str(e),
                'evaluation_time': 0
            }
        
        # Total time
        total_time = (datetime.now() - start_time).total_seconds()
        generation_result['performance'] = {
            'generation_time': generation_time,
            'evaluation_time': eval_time if 'eval_time' in locals() else 0,
            'total_time': total_time
        }
        
        return generation_result
    
    async def _evaluate_with_spoonacular(
        self, 
        generation_result: Dict[str, Any],
        user_id: int,
        message: str,
        evaluate_top_n: int,
        generation_time: float,
        eval_start: datetime
    ) -> Dict[str, Any]:
        """Evaluate recipes using Spoonacular-enhanced agents"""
        
        recipes = generation_result.get('recipes', [])
        
        # Get user preferences for evaluation
        preferences = await self._get_user_preferences(user_id)
        user_prefs = {
            'budget_conscious': 'budget' in message.lower() or 'cheap' in message.lower(),
            'dietary_restrictions': preferences.get('dietary_preference', []),
            'wine_pairing': 'wine' in message.lower(),
            'measurement_system': 'metric' if preferences.get('prefers_metric', False) else 'imperial'
        }
        
        # Evaluate top recipes with Spoonacular agents
        evaluated_recipes = []
        for i, recipe in enumerate(recipes[:evaluate_top_n]):
            try:
                evaluated = await evaluate_ai_recipe_with_spoonacular(recipe, user_prefs)
                evaluated['quality_evaluated'] = True
                evaluated_recipes.append(evaluated)
            except Exception as e:
                logger.error(f"Failed to evaluate recipe {i}: {e}")
                recipe['quality_evaluated'] = False
                evaluated_recipes.append(recipe)
        
        # Replace top recipes with evaluated versions
        recipes[:evaluate_top_n] = evaluated_recipes
        
        # Check for specific use cases
        extra_analysis = {}
        
        # Check authenticity if cuisine is mentioned
        cuisines = ['italian', 'mexican', 'chinese', 'indian', 'thai', 'french', 'japanese']
        for cuisine in cuisines:
            if cuisine in message.lower() and evaluated_recipes:
                auth_check = await validate_recipe_authenticity(evaluated_recipes[0], cuisine)
                extra_analysis['authenticity'] = auth_check
                break
        
        # Check budget optimization if mentioned
        if 'budget' in message.lower() or 'cheap' in message.lower() or '$' in message:
            if evaluated_recipes:
                # Extract budget if mentioned (e.g., "under $10")
                import re
                budget_match = re.search(r'\$([0-9]+)', message)
                target_budget = float(budget_match.group(1)) if budget_match else 10.0
                
                budget_analysis = await optimize_recipe_cost(evaluated_recipes[0], target_budget=target_budget)
                extra_analysis['budget_optimization'] = budget_analysis
        
        # Check leftover usage if mentioned
        if 'leftover' in message.lower() or 'use up' in message.lower():
            # Extract potential leftovers from message
            # Simple extraction - in production would use NLP
            words = message.lower().split()
            common_leftovers = ['chicken', 'rice', 'pasta', 'vegetables', 'beef', 'salmon', 'tofu']
            leftovers = [w for w in words if w in common_leftovers]
            
            if evaluated_recipes and leftovers:
                leftover_check = await check_leftover_compatibility(leftovers, evaluated_recipes[0])
                extra_analysis['leftover_usage'] = leftover_check
        
        eval_time = (datetime.now() - eval_start).total_seconds()
        
        return {
            **generation_result,
            'recipes': recipes,
            'quality_evaluated': True,
            'evaluation_method': 'spoonacular_enhanced',
            'evaluated_count': len(evaluated_recipes),
            'extra_analysis': extra_analysis,
            'performance': {
                'generation_time': generation_time,
                'evaluation_time': eval_time,
                'total_time': generation_time + eval_time,
                'agents_used': len(self.enhanced_agents.create_agents())
            }
        }
    
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
                'cuisine_preference': prefs.get('cuisine_preferences', []),
                'prefers_metric': prefs.get('measurement_system', 'imperial') == 'metric'
            }
        
        return {}


# Example usage
async def test_hybrid_system():
    """Test the hybrid CrewAI system"""
    service = HybridCrewService()
    
    result = await service.generate_and_evaluate_recipes(
        user_id=111,
        message="What can I make for a healthy dinner?",
        use_preferences=True,
        evaluate_top_n=3
    )
    
    print(f"\nGenerated {len(result['recipes'])} recipes")
    print(f"Generation time: {result['performance']['generation_time']:.2f}s")
    print(f"Evaluation time: {result['performance']['evaluation_time']:.2f}s")
    print(f"Total time: {result['performance']['total_time']:.2f}s")
    
    for i, recipe in enumerate(result['recipes'][:3], 1):
        print(f"\n{i}. {recipe.get('title', 'Unknown')}")
        if recipe.get('quality_evaluated'):
            print(f"   Quality Score: {recipe.get('evaluation_score', 'N/A')}/5")