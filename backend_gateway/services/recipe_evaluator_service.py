"""Service for evaluating recipe quality using Claude AI"""

import os
import logging
from typing import Dict, Any, Optional, List
import anthropic
from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)


class RecipeEvaluator:
    """Evaluates recipe quality using Claude AI"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        )
    
    async def evaluate_recipe(
        self, 
        recipe: Dict[str, Any],
        critique_goal: str = "taste, clarity, feasibility, and ingredient alignment"
    ) -> Dict[str, Any]:
        """
        Evaluate a recipe using Claude AI
        
        Args:
            recipe: Recipe data (either from Spoonacular or AI-generated)
            critique_goal: What aspects to evaluate
            
        Returns:
            Dictionary with score (1-5) and critique
        """
        # Format recipe for evaluation
        recipe_text = self._format_recipe_for_evaluation(recipe)
        
        prompt = f"""You are a professional food critic and chef. Evaluate the following recipe based on {critique_goal}.

Recipe:
{recipe_text}

Please provide:
1. A score from 1-5 (5 being excellent)
2. A brief critique (2-3 sentences)
3. One specific improvement suggestion

Format your response as:
Score: [1-5]
Critique: [Your critique]
Suggestion: [Your improvement suggestion]
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20241022",  # More cost-effective than Opus
                max_tokens=300,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            evaluation = self._parse_evaluation(response.content[0].text)
            evaluation['recipe_id'] = recipe.get('id')
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating recipe: {str(e)}")
            return {
                'score': 3,
                'critique': 'Unable to evaluate recipe',
                'suggestion': 'Please try again later',
                'error': str(e)
            }
    
    def _format_recipe_for_evaluation(self, recipe: Dict[str, Any]) -> str:
        """Format recipe data into readable text for evaluation"""
        
        # Handle both Spoonacular and AI format
        ingredients = []
        if 'extendedIngredients' in recipe:
            ingredients = [ing['original'] for ing in recipe['extendedIngredients']]
        elif 'ingredients' in recipe:
            ingredients = recipe['ingredients']
        
        instructions = []
        if 'analyzedInstructions' in recipe and recipe['analyzedInstructions']:
            instructions = [step['step'] for step in recipe['analyzedInstructions'][0]['steps']]
        elif 'instructions' in recipe:
            instructions = [inst['step'] if isinstance(inst, dict) else inst 
                          for inst in recipe['instructions']]
        
        recipe_text = f"""
Title: {recipe.get('title', 'Untitled Recipe')}
Servings: {recipe.get('servings', 4)}
Time: {recipe.get('readyInMinutes', 30)} minutes

Ingredients:
{chr(10).join(f"- {ing}" for ing in ingredients)}

Instructions:
{chr(10).join(f"{i+1}. {inst}" for i, inst in enumerate(instructions))}

Nutrition (per serving):
- Calories: {recipe.get('nutrition', {}).get('calories', 'N/A')}
- Protein: {recipe.get('nutrition', {}).get('protein', 'N/A')}g
- Carbs: {recipe.get('nutrition', {}).get('carbs', 'N/A')}g
- Fat: {recipe.get('nutrition', {}).get('fat', 'N/A')}g
"""
        return recipe_text.strip()
    
    def _parse_evaluation(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response into structured data"""
        
        lines = response_text.strip().split('\n')
        evaluation = {
            'score': 3,
            'critique': '',
            'suggestion': ''
        }
        
        for line in lines:
            if line.startswith('Score:'):
                try:
                    evaluation['score'] = int(line.split(':')[1].strip())
                except:
                    evaluation['score'] = 3
            elif line.startswith('Critique:'):
                evaluation['critique'] = line.split(':', 1)[1].strip()
            elif line.startswith('Suggestion:'):
                evaluation['suggestion'] = line.split(':', 1)[1].strip()
        
        return evaluation


class RecipeQualityFilter:
    """Filter recipes based on quality scores"""
    
    def __init__(self, evaluator: RecipeEvaluator):
        self.evaluator = evaluator
    
    async def filter_and_rank_recipes(
        self, 
        recipes: List[Dict[str, Any]], 
        min_score: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Evaluate and filter recipes by quality
        
        Args:
            recipes: List of recipes to evaluate
            min_score: Minimum score to include (1-5)
            
        Returns:
            List of recipes with evaluation data, filtered and sorted by score
        """
        evaluated_recipes = []
        
        for recipe in recipes:
            evaluation = await self.evaluator.evaluate_recipe(recipe)
            
            if evaluation['score'] >= min_score:
                recipe['quality_evaluation'] = evaluation
                evaluated_recipes.append(recipe)
        
        # Sort by score descending
        evaluated_recipes.sort(key=lambda r: r['quality_evaluation']['score'], reverse=True)
        
        return evaluated_recipes