
import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class JudgeThyme:
    name = "judge_thyme"

    async def run(self, preference_scored_recipes: list[dict], max_recipes: int = 5):
        """
        Input: [{'recipe_id': 123, 'title': 'Chicken Stir Fry', 'combined_score': 0.85, 'nutrition_score': 0.8, 'preference_score': 0.9}...]
        Output: Top N recipes with final judgments and recommendations
        """
        # Check if Judge Thyme is enabled
        enable_judge = os.getenv("ENABLE_JUDGE_THYME", "true").lower() == "true"
        if not enable_judge:
            logger.info("Judge Thyme disabled by environment variable - returning all recipes")
            return preference_scored_recipes

        if not preference_scored_recipes:
            return []

        try:
            # Apply final judgment logic
            judged_recipes = []
            for recipe in preference_scored_recipes:
                final_judgment = self._make_final_judgment(recipe)
                
                enriched_recipe = {
                    **recipe,
                    **final_judgment,
                    "judge_processed": True
                }
                
                judged_recipes.append(enriched_recipe)

            # Sort by final recommendation score
            judged_recipes.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            
            # Select top recipes and add ranking
            top_recipes = judged_recipes[:max_recipes]
            for i, recipe in enumerate(top_recipes):
                recipe["rank"] = i + 1
                recipe["recommendation_strength"] = self._get_recommendation_strength(recipe["final_score"])

            logger.info(f"Judge Thyme selected {len(top_recipes)} top recipes from {len(preference_scored_recipes)} candidates")
            return top_recipes

        except Exception as e:
            logger.error(f"Judge Thyme processing failed: {e}")
            # Fallback to top recipes by combined score
            fallback_recipes = sorted(preference_scored_recipes, 
                                    key=lambda x: x.get("combined_score", 0), 
                                    reverse=True)[:max_recipes]
            for i, recipe in enumerate(fallback_recipes):
                recipe["rank"] = i + 1
                recipe["judge_error"] = str(e)
            return fallback_recipes

    def _make_final_judgment(self, recipe: dict) -> dict:
        """Make final judgment on recipe suitability"""
        
        # Base scores
        nutrition_score = recipe.get("nutrition_score", 0.5)
        preference_score = recipe.get("preference_score", 0.5)
        combined_score = recipe.get("combined_score", 0.5)
        
        # Factor in additional considerations
        judgment_factors = self._evaluate_judgment_factors(recipe)
        
        # Calculate final score with judgment adjustments
        final_score = combined_score
        
        # Apply judgment factor adjustments
        for factor, adjustment in judgment_factors["adjustments"].items():
            final_score += adjustment
            
        # Clamp to 0-1 range
        final_score = max(0, min(1, final_score))
        
        # Generate recommendation
        recommendation = self._generate_recommendation(recipe, final_score, judgment_factors)
        
        return {
            "final_score": round(final_score, 3),
            "judgment_factors": judgment_factors,
            "recommendation": recommendation,
            "confidence": self._calculate_confidence(recipe, judgment_factors)
        }

    def _evaluate_judgment_factors(self, recipe: dict) -> dict:
        """Evaluate additional factors for final judgment"""
        factors = {
            "complexity": self._assess_complexity(recipe),
            "ingredient_availability": self._assess_ingredient_availability(recipe),
            "health_impact": self._assess_health_impact(recipe),
            "user_history": self._assess_user_history_fit(recipe),
            "seasonal_appropriateness": self._assess_seasonal_fit(recipe),
            "equipment_requirements": self._assess_equipment_needs(recipe)
        }
        
        # Calculate adjustments based on factors
        adjustments = {}
        
        # Complexity adjustment (-0.1 to +0.05)
        if factors["complexity"] == "too_complex":
            adjustments["complexity"] = -0.1
        elif factors["complexity"] == "optimal":
            adjustments["complexity"] = 0.05
        else:
            adjustments["complexity"] = 0

        # Ingredient availability adjustment (-0.15 to +0.1)
        if factors["ingredient_availability"] == "poor":
            adjustments["ingredient_availability"] = -0.15
        elif factors["ingredient_availability"] == "excellent":
            adjustments["ingredient_availability"] = 0.1
        else:
            adjustments["ingredient_availability"] = 0

        # Health impact adjustment (-0.2 to +0.1)
        if factors["health_impact"] == "concerning":
            adjustments["health_impact"] = -0.2
        elif factors["health_impact"] == "excellent":
            adjustments["health_impact"] = 0.1
        else:
            adjustments["health_impact"] = 0

        factors["adjustments"] = adjustments
        return factors

    def _assess_complexity(self, recipe: dict) -> str:
        """Assess recipe complexity"""
        instructions = recipe.get("instructions", [])
        ingredients = recipe.get("ingredients", [])
        prep_time = recipe.get("ready_in_minutes", 0)
        
        complexity_score = 0
        
        # Factor in number of instructions
        if len(instructions) > 15:
            complexity_score += 2
        elif len(instructions) > 10:
            complexity_score += 1
            
        # Factor in number of ingredients
        if len(ingredients) > 20:
            complexity_score += 2
        elif len(ingredients) > 15:
            complexity_score += 1
            
        # Factor in prep time
        if prep_time > 90:
            complexity_score += 2
        elif prep_time > 60:
            complexity_score += 1
            
        # Check for complex cooking techniques in instructions
        complex_techniques = ['sous vide', 'flambé', 'tempering', 'confit', 'braising']
        instruction_text = ' '.join(instructions).lower()
        for technique in complex_techniques:
            if technique in instruction_text:
                complexity_score += 1
                
        if complexity_score >= 4:
            return "too_complex"
        elif complexity_score <= 1:
            return "optimal"
        else:
            return "moderate"

    def _assess_ingredient_availability(self, recipe: dict) -> str:
        """Assess how available/common the ingredients are"""
        ingredients = recipe.get("ingredients", [])
        missed_ingredients = recipe.get("missed_ingredients", [])
        used_ingredients = recipe.get("used_ingredients", [])
        
        # Higher ratio of used to missed ingredients is better
        total_required = len(missed_ingredients) + len(used_ingredients)
        if total_required == 0:
            return "unknown"
            
        availability_ratio = len(used_ingredients) / total_required
        
        # Check for exotic/hard-to-find ingredients
        exotic_indicators = ['truffle', 'saffron', 'caviar', 'foie gras', 'duck fat', 'miso', 'tahini']
        has_exotic = False
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get("name", "").lower()
            if any(exotic in ingredient_name for exotic in exotic_indicators):
                has_exotic = True
                break
                
        if availability_ratio >= 0.8 and not has_exotic:
            return "excellent"
        elif availability_ratio >= 0.6:
            return "good"
        elif availability_ratio >= 0.4:
            return "fair"
        else:
            return "poor"

    def _assess_health_impact(self, recipe: dict) -> str:
        """Assess overall health impact"""
        health_assessment = recipe.get("health_assessment", {})
        health_warnings = recipe.get("health_warnings", [])
        nutrition_score = recipe.get("nutrition_score", 0.5)
        
        if health_warnings:
            return "concerning"
        elif health_assessment.get("health_rating") == "excellent":
            return "excellent"
        elif nutrition_score >= 0.7:
            return "good"
        elif nutrition_score >= 0.4:
            return "fair"
        else:
            return "concerning"

    def _assess_user_history_fit(self, recipe: dict) -> str:
        """Assess how well recipe fits user's historical preferences"""
        # This would typically involve checking user's recipe interaction history
        # For now, use preference score as proxy
        preference_score = recipe.get("preference_score", 0.5)
        
        if preference_score >= 0.8:
            return "excellent_fit"
        elif preference_score >= 0.6:
            return "good_fit"
        elif preference_score >= 0.4:
            return "fair_fit"
        else:
            return "poor_fit"

    def _assess_seasonal_fit(self, recipe: dict) -> str:
        """Assess seasonal appropriateness (simplified)"""
        # This could be enhanced with actual seasonal ingredient analysis
        dish_types = recipe.get("dish_types", [])
        
        # Simple heuristic based on dish type
        comfort_foods = ['soup', 'stew', 'casserole', 'roast']
        light_foods = ['salad', 'smoothie', 'cold soup', 'gazpacho']
        
        if any(comfort in ' '.join(dish_types).lower() for comfort in comfort_foods):
            return "comfort_food"
        elif any(light in ' '.join(dish_types).lower() for light in light_foods):
            return "light_food"
        else:
            return "neutral"

    def _assess_equipment_needs(self, recipe: dict) -> str:
        """Assess special equipment requirements"""
        instructions = recipe.get("instructions", [])
        instruction_text = ' '.join(instructions).lower()
        
        # Check for specialized equipment
        special_equipment = ['food processor', 'stand mixer', 'mandoline', 'thermometer', 
                           'pressure cooker', 'slow cooker', 'grill', 'deep fryer']
        
        equipment_count = sum(1 for equip in special_equipment if equip in instruction_text)
        
        if equipment_count >= 3:
            return "high_requirements"
        elif equipment_count >= 1:
            return "moderate_requirements"
        else:
            return "basic_requirements"

    def _generate_recommendation(self, recipe: dict, final_score: float, judgment_factors: dict) -> dict:
        """Generate final recommendation with reasoning"""
        
        title = recipe.get("title", "Unknown Recipe")
        
        # Determine recommendation level
        if final_score >= 0.8:
            recommendation_level = "highly_recommended"
            action = "This recipe is an excellent choice!"
        elif final_score >= 0.6:
            recommendation_level = "recommended"
            action = "This recipe is a good choice."
        elif final_score >= 0.4:
            recommendation_level = "consider"
            action = "This recipe might work for you."
        else:
            recommendation_level = "not_recommended"
            action = "Consider other options first."

        # Generate reasoning
        reasons = []
        
        # Positive factors
        if judgment_factors["complexity"] == "optimal":
            reasons.append("easy to prepare")
        if judgment_factors["ingredient_availability"] == "excellent":
            reasons.append("uses ingredients you have")
        if judgment_factors["health_impact"] == "excellent":
            reasons.append("very nutritious")
            
        # Concerns
        if judgment_factors["complexity"] == "too_complex":
            reasons.append("may be complex to prepare")
        if judgment_factors["ingredient_availability"] == "poor":
            reasons.append("requires many ingredients you don't have")
        if judgment_factors["health_impact"] == "concerning":
            reasons.append("has some nutritional concerns")

        return {
            "level": recommendation_level,
            "action": action,
            "reasons": reasons,
            "summary": f"{action} {', '.join(reasons[:3])}." if reasons else action
        }

    def _get_recommendation_strength(self, final_score: float) -> str:
        """Get recommendation strength label"""
        if final_score >= 0.85:
            return "very_strong"
        elif final_score >= 0.7:
            return "strong"
        elif final_score >= 0.5:
            return "moderate"
        elif final_score >= 0.3:
            return "weak"
        else:
            return "very_weak"

    def _calculate_confidence(self, recipe: dict, judgment_factors: dict) -> float:
        """Calculate confidence in the recommendation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if we have good nutrition data
        if recipe.get("nutrition", {}).get("calories", 0) > 0:
            confidence += 0.1
            
        # Higher confidence if we have user preference data
        if recipe.get("preference_score", 0) != 0.5:  # Not default/neutral
            confidence += 0.1
            
        # Higher confidence if ingredient availability is clear
        if judgment_factors["ingredient_availability"] in ["excellent", "poor"]:
            confidence += 0.1
            
        # Lower confidence if there were errors
        if "nutrition_error" in recipe or "preference_error" in recipe:
            confidence -= 0.2
            
        return max(0.1, min(1.0, confidence))