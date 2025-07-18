"""Custom tools for nutrient-aware CrewAI agents."""

from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging

from ..models.nutrition import NutrientGapAnalysis, NutrientProfile
from ..config.nutrient_config import ESSENTIAL_NUTRIENTS, UPPER_LIMIT_NUTRIENTS
from .food_lookup_tool import food_lookup_tool

logger = logging.getLogger(__name__)

class NutrientFilterInput(BaseModel):
    """Input for nutrient-based recipe filtering."""
    recipes: List[Dict[str, Any]] = Field(..., description="List of recipes to filter")
    nutrient_gaps: Dict[str, float] = Field(..., description="Dictionary of nutrient gaps (negative=deficit, positive=excess)")
    focus_nutrients: Optional[List[str]] = Field(None, description="Specific nutrients to focus on")
    min_score_threshold: float = Field(0.0, description="Minimum nutrient score threshold for filtering")

class NutrientFilterTool(BaseTool):
    """Tool for filtering recipes based on nutrient gaps and requirements."""
    name: str = "NutrientFilterTool"
    description: str = "Filters and ranks recipes based on how well they address nutrient gaps and deficiencies"
    args_schema: Type[BaseModel] = NutrientFilterInput
    
    def _run(self, recipes: List[Dict[str, Any]], nutrient_gaps: Dict[str, float], 
             focus_nutrients: Optional[List[str]] = None, min_score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Filter recipes based on nutrient criteria."""
        logger.info(f"Filtering {len(recipes)} recipes based on nutrient gaps")
        
        filtered_recipes = []
        
        for recipe in recipes:
            try:
                # Calculate nutrient score for the recipe
                score = self._calculate_nutrient_score(recipe, nutrient_gaps, focus_nutrients)
                
                # Only include recipes above threshold
                if score >= min_score_threshold:
                    recipe['nutrient_filter_score'] = score
                    filtered_recipes.append(recipe)
                    
            except Exception as e:
                logger.warning(f"Error scoring recipe {recipe.get('name', 'unknown')}: {e}")
                continue
        
        # Sort by nutrient score (descending)
        filtered_recipes.sort(key=lambda r: r.get('nutrient_filter_score', 0), reverse=True)
        
        logger.info(f"Filtered to {len(filtered_recipes)} recipes meeting nutrient criteria")
        return filtered_recipes
    
    def _calculate_nutrient_score(self, recipe: Dict[str, Any], nutrient_gaps: Dict[str, float], 
                                 focus_nutrients: Optional[List[str]] = None) -> float:
        """Calculate nutrient score for a recipe."""
        score = 0.0
        
        # Extract nutrition from recipe
        nutrition = recipe.get('nutrition', {})
        ingredients = recipe.get('ingredients', [])
        
        # If no nutrition data, estimate from ingredients
        if not nutrition.get('protein', 0) and ingredients:
            estimated_nutrition = self._estimate_nutrition_from_ingredients(ingredients)
            nutrition.update(estimated_nutrition)
        
        # Score based on nutrient gaps
        for nutrient, gap in nutrient_gaps.items():
            recipe_amount = nutrition.get(nutrient, 0)
            
            if recipe_amount <= 0:
                continue
                
            # Focus on specific nutrients if provided
            if focus_nutrients and nutrient not in focus_nutrients:
                continue
                
            # Score based on how well the recipe addresses gaps
            if gap < 0:  # Deficit - recipe should provide this nutrient
                # Positive score for providing deficient nutrients
                gap_fill_ratio = min(abs(recipe_amount / gap), 1.0)
                weight = 3.0 if nutrient in ESSENTIAL_NUTRIENTS else 1.0
                score += gap_fill_ratio * weight
                
            elif gap > 0 and nutrient in UPPER_LIMIT_NUTRIENTS:  # Excess - recipe should avoid this
                # Negative score for adding excess nutrients
                excess_penalty = min(recipe_amount / gap, 1.0)
                score -= excess_penalty * 2.0
        
        return max(0.0, score)
    
    def _estimate_nutrition_from_ingredients(self, ingredients: List[str]) -> Dict[str, float]:
        """Estimate nutrition from ingredients."""
        nutrition = {
            'protein': 0.0,
            'fiber': 0.0,
            'vitamin_c': 0.0,
            'calcium': 0.0,
            'iron': 0.0,
            'sodium': 0.0
        }
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Simple keyword-based estimation
            if any(protein in ingredient_lower for protein in ['chicken', 'beef', 'fish', 'tofu', 'beans']):
                nutrition['protein'] += 15.0
            
            if any(fiber in ingredient_lower for fiber in ['beans', 'lentils', 'vegetables', 'broccoli']):
                nutrition['fiber'] += 5.0
            
            if any(vit_c in ingredient_lower for vit_c in ['citrus', 'berries', 'pepper', 'tomato']):
                nutrition['vitamin_c'] += 20.0
            
            if any(calcium in ingredient_lower for calcium in ['cheese', 'milk', 'leafy greens']):
                nutrition['calcium'] += 100.0
            
            if any(iron in ingredient_lower for iron in ['spinach', 'beef', 'beans']):
                nutrition['iron'] += 2.0
            
            if any(sodium in ingredient_lower for sodium in ['salt', 'soy sauce', 'cheese']):
                nutrition['sodium'] += 300.0
        
        return nutrition

class FoodNutritionLookupInput(BaseModel):
    """Input for food nutrition lookup."""
    food_name: str = Field(..., description="Name of the food item to look up")
    quantity: float = Field(1.0, description="Quantity of the food item")
    serving_unit: str = Field("serving", description="Unit of measurement")

class FoodNutritionLookupTool(BaseTool):
    """Tool for looking up detailed nutrition information for foods."""
    name: str = "FoodNutritionLookupTool"
    description: str = "Looks up detailed nutrition information for food items using USDA database"
    args_schema: Type[BaseModel] = FoodNutritionLookupInput
    
    def _run(self, food_name: str, quantity: float = 1.0, serving_unit: str = "serving") -> Dict[str, Any]:
        """Look up nutrition information for a food item."""
        logger.info(f"Looking up nutrition for: {food_name} ({quantity} {serving_unit})")
        
        try:
            # Use the food lookup tool
            food_item = food_lookup_tool.lookup_food_nutrition(food_name, quantity)
            
            if food_item:
                nutrition_data = {
                    'food_name': food_item.name,
                    'usda_id': food_item.usda_id,
                    'brand': food_item.brand,
                    'serving_size': food_item.serving_size,
                    'serving_unit': food_item.serving_unit,
                    'nutrients': food_item.nutrients.to_dict(),
                    'data_source': 'usda'
                }
                
                logger.info(f"Found nutrition data for {food_name}")
                return nutrition_data
            else:
                logger.warning(f"No nutrition data found for {food_name}")
                return {
                    'food_name': food_name,
                    'error': 'Nutrition data not found',
                    'data_source': 'none'
                }
                
        except Exception as e:
            logger.error(f"Error looking up nutrition for {food_name}: {e}")
            return {
                'food_name': food_name,
                'error': str(e),
                'data_source': 'error'
            }

class NutrientGapAnalysisInput(BaseModel):
    """Input for nutrient gap analysis."""
    user_id: int = Field(..., description="User ID for the analysis")
    target_nutrients: Optional[List[str]] = Field(None, description="Specific nutrients to analyze")
    analysis_period: int = Field(1, description="Number of days to analyze (1=today, 7=weekly)")

class NutrientGapAnalysisTool(BaseTool):
    """Tool for analyzing nutrient gaps for a user."""
    name: str = "NutrientGapAnalysisTool"
    description: str = "Analyzes current nutrient gaps and deficiencies for a user"
    args_schema: Type[BaseModel] = NutrientGapAnalysisInput
    
    def __init__(self, nutrient_auditor_service):
        super().__init__()
        self.nutrient_service = nutrient_auditor_service
    
    def _run(self, user_id: int, target_nutrients: Optional[List[str]] = None, 
             analysis_period: int = 1) -> Dict[str, Any]:
        """Analyze nutrient gaps for a user."""
        logger.info(f"Analyzing nutrient gaps for user {user_id}")
        
        try:
            # Get or create gap analysis
            gap_analysis = self.nutrient_service.get_gap_analysis(str(user_id))
            
            if not gap_analysis:
                # Create sample analysis for demonstration
                from ..services.nutrient_aware_crew_service import NutrientAwareCrewService
                crew_service = NutrientAwareCrewService()
                gap_analysis = crew_service._create_sample_nutrient_analysis(user_id)
            
            # Filter to target nutrients if specified
            if target_nutrients:
                filtered_gaps = [gap for gap in gap_analysis.gaps if gap.nutrient in target_nutrients]
            else:
                filtered_gaps = gap_analysis.gaps
            
            # Format results
            analysis_result = {
                'user_id': user_id,
                'analysis_date': gap_analysis.analysis_date.isoformat(),
                'overall_score': gap_analysis.overall_score,
                'gaps': [
                    {
                        'nutrient': gap.nutrient,
                        'consumed': gap.consumed,
                        'recommended': gap.recommended,
                        'gap': gap.gap,
                        'percentage_met': gap.percentage_met,
                        'is_deficient': gap.is_deficient,
                        'is_excessive': gap.is_excessive,
                        'priority': gap.priority
                    }
                    for gap in filtered_gaps
                ],
                'priority_deficiencies': gap_analysis.priority_deficiencies,
                'priority_excesses': gap_analysis.priority_excesses,
                'recommendations': self.nutrient_service.get_nutrient_recommendations(gap_analysis)
            }
            
            logger.info(f"Nutrient gap analysis complete for user {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing nutrient gaps: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'analysis_date': None,
                'overall_score': 0.0,
                'gaps': [],
                'priority_deficiencies': [],
                'priority_excesses': [],
                'recommendations': []
            }

class RecipeNutritionEnhancerInput(BaseModel):
    """Input for recipe nutrition enhancement."""
    recipe: Dict[str, Any] = Field(..., description="Recipe to enhance with nutrition data")
    detailed_lookup: bool = Field(True, description="Whether to do detailed USDA lookup")

class RecipeNutritionEnhancerTool(BaseTool):
    """Tool for enhancing recipes with detailed nutrition information."""
    name: str = "RecipeNutritionEnhancerTool"
    description: str = "Enhances recipes with detailed nutrition information by analyzing ingredients"
    args_schema: Type[BaseModel] = RecipeNutritionEnhancerInput
    
    def _run(self, recipe: Dict[str, Any], detailed_lookup: bool = True) -> Dict[str, Any]:
        """Enhance a recipe with nutrition information."""
        logger.info(f"Enhancing recipe '{recipe.get('name', 'unknown')}' with nutrition data")
        
        try:
            enhanced_recipe = recipe.copy()
            
            # Get ingredients
            ingredients = recipe.get('ingredients', [])
            
            if not ingredients:
                logger.warning("No ingredients found in recipe")
                return enhanced_recipe
            
            # Calculate nutrition from ingredients
            if detailed_lookup:
                # Use USDA lookup for detailed nutrition
                total_nutrition = food_lookup_tool.estimate_nutrition_from_ingredients(ingredients)
            else:
                # Use simple estimation
                total_nutrition = self._simple_nutrition_estimate(ingredients)
            
            # Update recipe with nutrition data
            enhanced_recipe['nutrition'] = total_nutrition.to_dict() if hasattr(total_nutrition, 'to_dict') else total_nutrition
            enhanced_recipe['nutrition_source'] = 'usda_lookup' if detailed_lookup else 'estimated'
            enhanced_recipe['nutrition_confidence'] = 0.8 if detailed_lookup else 0.5
            
            logger.info(f"Enhanced recipe with nutrition data (source: {'usda' if detailed_lookup else 'estimated'})")
            return enhanced_recipe
            
        except Exception as e:
            logger.error(f"Error enhancing recipe with nutrition: {e}")
            recipe['nutrition_error'] = str(e)
            return recipe
    
    def _simple_nutrition_estimate(self, ingredients: List[str]) -> Dict[str, float]:
        """Simple nutrition estimation from ingredients."""
        nutrition = {
            'calories': 0.0,
            'protein': 0.0,
            'carbohydrates': 0.0,
            'fiber': 0.0,
            'total_fat': 0.0,
            'sodium': 0.0,
            'sugar': 0.0
        }
        
        base_calories = 300  # Base recipe calories
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Protein sources
            if any(protein in ingredient_lower for protein in ['chicken', 'beef', 'fish', 'tofu', 'beans']):
                nutrition['protein'] += 20.0
                base_calories += 100
            
            # Carb sources
            if any(carb in ingredient_lower for carb in ['rice', 'pasta', 'bread', 'potato']):
                nutrition['carbohydrates'] += 30.0
                base_calories += 150
            
            # Fiber sources
            if any(fiber in ingredient_lower for fiber in ['vegetables', 'beans', 'whole grain']):
                nutrition['fiber'] += 5.0
            
            # Fat sources
            if any(fat in ingredient_lower for fat in ['oil', 'butter', 'cheese', 'nuts']):
                nutrition['total_fat'] += 10.0
                base_calories += 90
            
            # Sodium sources
            if any(sodium in ingredient_lower for sodium in ['salt', 'soy sauce', 'cheese']):
                nutrition['sodium'] += 400.0
        
        nutrition['calories'] = base_calories
        return nutrition