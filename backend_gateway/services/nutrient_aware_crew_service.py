"""Enhanced CrewAI service with nutrient gap awareness."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from .crew_ai_service import CrewAIService
from .nutrient_auditor_service import NutrientAuditorService
from ..models.nutrition import (
    NutrientGapAnalysis, NutrientProfile, RecipeNutrientScore,
    DailyIntakeLog, MealEntry, FoodItem
)
from ..agents.nutrient_auditor_agent import NutrientAuditorAgent, create_nutrient_auditor_flow

logger = logging.getLogger(__name__)

class NutrientAwareCrewService(CrewAIService):
    """Extended CrewAI service with nutrient gap awareness and enhanced recipe scoring."""
    
    def __init__(self):
        """Initialize the nutrient-aware crew service."""
        super().__init__()
        self.nutrient_auditor = NutrientAuditorAgent()
        self.nutrient_service = NutrientAuditorService()
        
    async def process_message_with_nutrition(self, user_id: int, message: str, 
                                           use_preferences: bool = True,
                                           include_nutrient_gaps: bool = True) -> Dict[str, Any]:
        """
        Process a chat message with nutrient gap awareness.
        
        Args:
            user_id: The user's ID
            message: The user's message
            use_preferences: Whether to use user preferences
            include_nutrient_gaps: Whether to include nutrient gap analysis
            
        Returns:
            Dict containing response, recipes, pantry items, and nutrient analysis
        """
        logger.info("="*60)
        logger.info(f"🧬 STARTING NUTRIENT-AWARE CHAT PROCESS for user {user_id}")
        logger.info(f"📝 Message: '{message}'")
        logger.info(f"🔬 Include nutrient gaps: {include_nutrient_gaps}")
        logger.info("="*60)
        
        try:
            # Step 1: Get standard recipe recommendations
            standard_result = await self.process_message(user_id, message, use_preferences)
            
            # Step 2: Get or create nutrient gap analysis
            gap_analysis = None
            if include_nutrient_gaps:
                logger.info("\n🔬 STEP 2: Performing nutrient gap analysis...")
                gap_analysis = await self._get_nutrient_gap_analysis(user_id)
                
                if gap_analysis:
                    logger.info(f"✅ Gap analysis found:")
                    logger.info(f"   - Overall score: {gap_analysis.overall_score:.1f}%")
                    logger.info(f"   - Deficiencies: {len(gap_analysis.priority_deficiencies)}")
                    logger.info(f"   - Excesses: {len(gap_analysis.priority_excesses)}")
                
            # Step 3: Score recipes based on nutrient gaps
            if gap_analysis and standard_result.get('recipes'):
                logger.info("\n🏆 STEP 3: Scoring recipes for nutrient gaps...")
                nutrient_scored_recipes = await self._score_recipes_for_nutrition(
                    standard_result['recipes'], gap_analysis
                )
                
                # Re-rank recipes with nutrient scoring
                logger.info("\n🔄 STEP 4: Re-ranking with nutrient scores...")
                enhanced_recipes = self._rerank_with_nutrition(
                    nutrient_scored_recipes, gap_analysis
                )
                
                # Update the result with enhanced recipes
                standard_result['recipes'] = enhanced_recipes
            
            # Step 4: Generate enhanced response with nutrient rationale
            if gap_analysis:
                logger.info("\n💬 STEP 5: Generating nutrient-aware response...")
                enhanced_response = self._generate_nutrient_aware_response(
                    standard_result['response'], 
                    standard_result['recipes'], 
                    gap_analysis, 
                    message
                )
                standard_result['response'] = enhanced_response
            
            # Add nutrient analysis to result
            result = standard_result.copy()
            if gap_analysis:
                result['nutrient_analysis'] = {
                    'overall_score': gap_analysis.overall_score,
                    'priority_deficiencies': gap_analysis.priority_deficiencies,
                    'priority_excesses': gap_analysis.priority_excesses,
                    'recommendations': self.nutrient_service.get_nutrient_recommendations(gap_analysis),
                    'priority_message': self.nutrient_auditor.generate_priority_message(gap_analysis)
                }
            
            logger.info(f"\n🎯 FINAL: Enhanced result with nutrition awareness")
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in nutrient-aware chat process: {str(e)}")
            # Fall back to standard processing
            return await self.process_message(user_id, message, use_preferences)
    
    async def _get_nutrient_gap_analysis(self, user_id: int) -> Optional[NutrientGapAnalysis]:
        """Get or create nutrient gap analysis for a user."""
        try:
            # Try to get today's analysis first
            today = date.today()
            analysis = self.nutrient_service.get_gap_analysis(str(user_id), today)
            
            if analysis:
                logger.info(f"📊 Found existing nutrient analysis for {today}")
                return analysis
            
            # If no analysis exists, try to create one from recent dietary data
            logger.info(f"🔍 No existing analysis found, attempting to create from recent data...")
            
            # In a real implementation, this would fetch from a dietary intake database
            # For now, we'll create a sample analysis with common deficiencies
            analysis = await self._create_sample_nutrient_analysis(user_id)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting nutrient gap analysis: {e}")
            return None
    
    async def _create_sample_nutrient_analysis(self, user_id: int) -> NutrientGapAnalysis:
        """Create a sample nutrient analysis for demonstration."""
        # This would normally come from actual dietary intake data
        # For demonstration, we'll create a typical analysis showing common deficiencies
        
        # Create sample daily intake log (representing typical American diet gaps)
        sample_nutrients = NutrientProfile(
            protein=35.0,      # Below RDA of 50g
            fiber=12.0,        # Below RDA of 25g
            vitamin_c=45.0,    # Below RDA of 90mg
            vitamin_d=0.008,   # Below RDA of 0.02mg
            calcium=600.0,     # Below RDA of 1000mg
            iron=10.0,         # Below RDA of 18mg
            potassium=2000.0,  # Below RDA of 3500mg
            sodium=2800.0,     # Above RDA of 2300mg (excess)
            saturated_fat=25.0, # Above RDA of 20g (excess)
            sugar=65.0,        # Above RDA of 50g (excess)
            calories=2000.0,
            carbohydrates=250.0,
            total_fat=60.0,
            vitamin_a=0.7,
            magnesium=300.0,
            phosphorus=800.0,
            zinc=9.0
        )
        
        # Create a mock daily log
        sample_food = FoodItem(
            name="Mixed Daily Intake",
            serving_size=1.0,
            serving_unit="day",
            nutrients=sample_nutrients
        )
        
        sample_meal = MealEntry(
            meal_type="dinner",
            food_item=sample_food,
            quantity=1.0
        )
        
        daily_log = DailyIntakeLog(
            user_id=str(user_id),
            date=date.today(),
            meals=[sample_meal]
        )
        
        # Run the analysis
        analysis = self.nutrient_service.analyze_daily_gaps(str(user_id), daily_log)
        
        logger.info(f"📊 Created sample nutrient analysis:")
        logger.info(f"   - Overall score: {analysis.overall_score:.1f}%")
        logger.info(f"   - Priority deficiencies: {analysis.priority_deficiencies}")
        logger.info(f"   - Priority excesses: {analysis.priority_excesses}")
        
        return analysis
    
    async def _score_recipes_for_nutrition(self, recipes: List[Dict[str, Any]], 
                                         gap_analysis: NutrientGapAnalysis) -> List[Dict[str, Any]]:
        """Score recipes based on how well they address nutrient gaps."""
        scored_recipes = []
        
        for recipe in recipes:
            try:
                # Extract or estimate nutrition from recipe
                recipe_nutrients = self._extract_recipe_nutrition(recipe)
                
                # Score the recipe against nutrient gaps
                nutrient_score = self.nutrient_service.score_recipe_for_gaps(
                    recipe_nutrients, gap_analysis, recipe.get('name', 'unknown')
                )
                
                # Add nutrient scoring to recipe
                recipe['nutrient_score'] = nutrient_score.total_score
                recipe['nutrient_analysis'] = {
                    'gap_closure_score': nutrient_score.gap_closure_score,
                    'balance_score': nutrient_score.balance_score,
                    'health_score': nutrient_score.health_score,
                    'addressed_deficiencies': nutrient_score.addressed_deficiencies,
                    'created_excesses': nutrient_score.created_excesses
                }
                
                scored_recipes.append(recipe)
                
            except Exception as e:
                logger.warning(f"Could not score recipe {recipe.get('name', 'unknown')} for nutrition: {e}")
                recipe['nutrient_score'] = 0.0
                recipe['nutrient_analysis'] = {}
                scored_recipes.append(recipe)
        
        return scored_recipes
    
    def _extract_recipe_nutrition(self, recipe: Dict[str, Any]) -> NutrientProfile:
        """Extract or estimate nutrition profile from a recipe."""
        # First, check if we have detailed nutrition data
        nutrition = recipe.get('nutrition', {})
        
        if isinstance(nutrition, dict) and nutrition.get('calories'):
            # We have some nutrition data, use what we have
            return NutrientProfile(
                calories=nutrition.get('calories', 0),
                protein=nutrition.get('protein', 0),
                carbohydrates=nutrition.get('carbohydrates', 0),
                fiber=nutrition.get('fiber', 0),
                total_fat=nutrition.get('fat', 0),
                saturated_fat=nutrition.get('saturated_fat', 0),
                sugar=nutrition.get('sugar', 0),
                sodium=nutrition.get('sodium', 0),
                # Add other nutrients if available
                vitamin_c=nutrition.get('vitamin_c', 0),
                calcium=nutrition.get('calcium', 0),
                iron=nutrition.get('iron', 0),
                potassium=nutrition.get('potassium', 0)
            )
        
        # If no detailed nutrition, estimate based on ingredients
        return self._estimate_nutrition_from_ingredients(recipe)
    
    def _estimate_nutrition_from_ingredients(self, recipe: Dict[str, Any]) -> NutrientProfile:
        """Estimate nutrition profile from recipe ingredients."""
        # This is a simple estimation - in a real system, you'd use a food database
        ingredients = recipe.get('ingredients', [])
        
        # Basic estimation based on common ingredient patterns
        nutrients = NutrientProfile()
        
        # Estimate based on ingredient keywords
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Protein sources
            if any(protein in ingredient_lower for protein in ['chicken', 'beef', 'pork', 'fish', 'tofu', 'beans', 'lentils']):
                nutrients.protein += 20.0
            if 'eggs' in ingredient_lower:
                nutrients.protein += 6.0
            
            # High fiber ingredients
            if any(fiber in ingredient_lower for fiber in ['beans', 'lentils', 'quinoa', 'oats', 'berries']):
                nutrients.fiber += 8.0
            elif any(fiber in ingredient_lower for fiber in ['vegetables', 'broccoli', 'spinach', 'carrots']):
                nutrients.fiber += 3.0
            
            # Vitamin C sources
            if any(vit_c in ingredient_lower for vit_c in ['citrus', 'orange', 'lemon', 'berries', 'bell pepper']):
                nutrients.vitamin_c += 30.0
            
            # Calcium sources
            if any(calcium in ingredient_lower for calcium in ['dairy', 'cheese', 'milk', 'yogurt', 'leafy greens']):
                nutrients.calcium += 150.0
            
            # Iron sources
            if any(iron in ingredient_lower for iron in ['spinach', 'beef', 'beans', 'lentils']):
                nutrients.iron += 3.0
            
            # High sodium ingredients
            if any(sodium in ingredient_lower for sodium in ['salt', 'soy sauce', 'cheese', 'processed']):
                nutrients.sodium += 400.0
        
        # Estimate calories based on meal type and ingredients
        base_calories = 300  # Base meal calories
        if len(ingredients) > 5:
            base_calories += 100
        if any(high_cal in ' '.join(ingredients).lower() for high_cal in ['oil', 'butter', 'cheese', 'nuts']):
            base_calories += 150
        
        nutrients.calories = base_calories
        
        return nutrients
    
    def _rerank_with_nutrition(self, recipes: List[Dict[str, Any]], 
                              gap_analysis: NutrientGapAnalysis) -> List[Dict[str, Any]]:
        """Re-rank recipes incorporating nutrient scores."""
        # Enhanced ranking that balances preference score with nutrient score
        ranked = sorted(recipes, key=lambda r: (
            # Primary: Combined preference and nutrient score
            (r.get('preference_score', 50) * 0.7 + r.get('nutrient_score', 0) * 0.3),
            # Secondary: Addresses priority deficiencies
            len(set(r.get('nutrient_analysis', {}).get('addressed_deficiencies', [])) & 
                set(gap_analysis.priority_deficiencies)),
            # Tertiary: Original ranking factors
            r.get('source') == 'saved' and r.get('user_rating') == 'thumbs_up',
            r.get('evaluation', {}).get('uses_expiring', False),
            r.get('missing_count', 999) == 0,
            r.get('match_score', 0),
            -r.get('missing_count', 999)
        ), reverse=True)
        
        # Log top 3 recipes with combined scores
        logger.info("🏆 Top nutrient-aware recipes:")
        for i, recipe in enumerate(ranked[:3]):
            pref_score = recipe.get('preference_score', 50)
            nutrient_score = recipe.get('nutrient_score', 0)
            combined_score = pref_score * 0.7 + nutrient_score * 0.3
            
            logger.info(f"  #{i+1}: {recipe['name']}")
            logger.info(f"      - Combined score: {combined_score:.1f} (Pref: {pref_score:.1f}, Nutrition: {nutrient_score:.1f})")
            logger.info(f"      - Addresses deficiencies: {recipe.get('nutrient_analysis', {}).get('addressed_deficiencies', [])}")
        
        return ranked
    
    def _generate_nutrient_aware_response(self, base_response: str, 
                                        recipes: List[Dict[str, Any]], 
                                        gap_analysis: NutrientGapAnalysis, 
                                        message: str) -> str:
        """Generate an enhanced response that explains nutrient rationale."""
        # Get priority message about current nutrient status
        priority_message = self.nutrient_auditor.generate_priority_message(gap_analysis)
        
        # Build nutrition-aware response
        nutrition_intro = f"🔬 **Nutrition Focus**: {priority_message}"
        
        # Add explanations for top recipes
        recipe_explanations = []
        for i, recipe in enumerate(recipes[:3]):
            nutrient_analysis = recipe.get('nutrient_analysis', {})
            addressed_deficiencies = nutrient_analysis.get('addressed_deficiencies', [])
            
            if addressed_deficiencies:
                deficiency_names = [d.replace('_', ' ').title() for d in addressed_deficiencies[:2]]
                explanation = f"**{recipe['name']}** helps with {', '.join(deficiency_names)}"
                recipe_explanations.append(explanation)
        
        # Combine everything
        enhanced_response = f"{nutrition_intro}\n\n{base_response}"
        
        if recipe_explanations:
            enhanced_response += "\n\n💡 **Nutrition Benefits:**\n"
            for explanation in recipe_explanations:
                enhanced_response += f"• {explanation}\n"
        
        return enhanced_response
    
    async def log_meal_and_update_gaps(self, user_id: int, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a meal and update nutrient gap analysis."""
        try:
            # This would normally save to a dietary intake database
            # For now, we'll create a placeholder response
            
            logger.info(f"📝 Logging meal for user {user_id}: {meal_data}")
            
            # In a real implementation, this would:
            # 1. Save the meal to dietary_intake table
            # 2. Update or regenerate nutrient gap analysis
            # 3. Trigger background flow to update gaps
            
            return {
                "success": True,
                "message": "Meal logged successfully",
                "meal_id": f"meal_{user_id}_{datetime.now().timestamp()}"
            }
            
        except Exception as e:
            logger.error(f"Error logging meal: {e}")
            return {
                "success": False,
                "message": "Failed to log meal",
                "error": str(e)
            }