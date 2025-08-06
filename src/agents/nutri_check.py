
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NutriCheck:
    name = "nutri_check"

    async def run(self, recipes: list[dict], user_health_goals: dict = None):
        """
        Input: [{'recipe_id': 123, 'title': 'Chicken Stir Fry', 'nutrition': {...}}...]
        Output: Same recipes enriched with nutrition scores and health assessments
        """
        if not recipes:
            return []

        # Default health goals if none provided
        default_goals = {
            "max_calories_per_meal": 800,
            "max_sodium_mg": 2300,  # Daily value, will scale per meal
            "min_protein_g": 20,
            "max_saturated_fat_g": 20,  # Daily value, will scale per meal
            "min_fiber_g": 8,  # Per meal target
            "preferred_macros": {  # Percentage of calories
                "carbs": 45,  # 45-65% of calories
                "protein": 25,  # 10-35% of calories
                "fat": 30   # 20-35% of calories
            }
        }

        health_goals = {**default_goals, **(user_health_goals or {})}
        
        enriched_recipes = []
        for recipe in recipes:
            try:
                nutrition_score = self._calculate_nutrition_score(recipe, health_goals)
                health_assessment = self._assess_health_impact(recipe, health_goals)
                
                enriched_recipe = {
                    **recipe,
                    "nutrition_score": nutrition_score["overall_score"],
                    "nutrition_breakdown": nutrition_score,
                    "health_assessment": health_assessment,
                    "health_warnings": self._get_health_warnings(recipe, health_goals),
                    "nutrition_highlights": self._get_nutrition_highlights(recipe)
                }
                
                enriched_recipes.append(enriched_recipe)

            except Exception as e:
                logger.error(f"Error analyzing nutrition for recipe {recipe.get('recipe_id')}: {e}")
                # Include recipe without nutrition analysis
                enriched_recipes.append({
                    **recipe,
                    "nutrition_error": str(e)
                })

        # Sort by nutrition score (highest first)
        enriched_recipes.sort(key=lambda x: x.get("nutrition_score", 0), reverse=True)
        
        logger.info(f"Analyzed nutrition for {len(enriched_recipes)} recipes")
        return enriched_recipes

    def _calculate_nutrition_score(self, recipe: dict, health_goals: dict) -> dict:
        """Calculate comprehensive nutrition score (0-1)"""
        nutrition = recipe.get("nutrition", {})
        
        scores = {}
        
        # Calorie score (closer to target is better)
        calories = nutrition.get("calories", 0)
        target_calories = health_goals["max_calories_per_meal"]
        if calories == 0:
            scores["calorie_score"] = 0.5  # Unknown
        elif calories <= target_calories:
            scores["calorie_score"] = 1.0 - (abs(calories - target_calories * 0.8) / target_calories)
        else:
            scores["calorie_score"] = max(0, 1.0 - (calories - target_calories) / target_calories)
        
        # Protein score (higher is better, up to a point)
        protein = nutrition.get("protein_g", 0)
        min_protein = health_goals["min_protein_g"]
        if protein >= min_protein:
            scores["protein_score"] = min(1.0, protein / (min_protein * 1.5))
        else:
            scores["protein_score"] = protein / min_protein
        
        # Sodium score (lower is better)
        sodium = nutrition.get("sodium_mg", 0)
        max_sodium_per_meal = health_goals["max_sodium_mg"] / 3  # Assume 3 meals per day
        if sodium == 0:
            scores["sodium_score"] = 0.5
        else:
            scores["sodium_score"] = max(0, 1.0 - sodium / max_sodium_per_meal)
        
        # Saturated fat score (lower is better)
        sat_fat = nutrition.get("saturated_fat_g", 0)
        max_sat_fat_per_meal = health_goals["max_saturated_fat_g"] / 3
        if sat_fat == 0:
            scores["saturated_fat_score"] = 0.5
        else:
            scores["saturated_fat_score"] = max(0, 1.0 - sat_fat / max_sat_fat_per_meal)
        
        # Fiber score (higher is better)
        fiber = nutrition.get("fiber_g", 0)
        min_fiber = health_goals["min_fiber_g"]
        if fiber >= min_fiber:
            scores["fiber_score"] = 1.0
        else:
            scores["fiber_score"] = fiber / min_fiber
        
        # Macro balance score
        scores["macro_balance_score"] = self._calculate_macro_balance_score(nutrition, health_goals)
        
        # Overall score (weighted average)
        weights = {
            "calorie_score": 0.25,
            "protein_score": 0.20,
            "sodium_score": 0.15,
            "saturated_fat_score": 0.15,
            "fiber_score": 0.15,
            "macro_balance_score": 0.10
        }
        
        overall_score = sum(scores[key] * weight for key, weight in weights.items())
        scores["overall_score"] = round(overall_score, 3)
        
        return scores

    def _calculate_macro_balance_score(self, nutrition: dict, health_goals: dict) -> float:
        """Score how well macronutrients match preferred ratios"""
        calories = nutrition.get("calories", 0)
        if calories == 0:
            return 0.5
            
        carbs_g = nutrition.get("carbs_g", 0)
        protein_g = nutrition.get("protein_g", 0)
        fat_g = nutrition.get("fat_g", 0)
        
        # Calculate actual percentages
        carb_calories = carbs_g * 4
        protein_calories = protein_g * 4
        fat_calories = fat_g * 9
        
        total_macro_calories = carb_calories + protein_calories + fat_calories
        if total_macro_calories == 0:
            return 0.5
            
        actual_carb_pct = (carb_calories / total_macro_calories) * 100
        actual_protein_pct = (protein_calories / total_macro_calories) * 100
        actual_fat_pct = (fat_calories / total_macro_calories) * 100
        
        # Compare to preferred ratios
        preferred = health_goals["preferred_macros"]
        carb_diff = abs(actual_carb_pct - preferred["carbs"])
        protein_diff = abs(actual_protein_pct - preferred["protein"])
        fat_diff = abs(actual_fat_pct - preferred["fat"])
        
        # Average deviation (lower is better)
        avg_deviation = (carb_diff + protein_diff + fat_diff) / 3
        
        # Convert to score (0-1, where 0 deviation = 1.0 score)
        return max(0, 1.0 - avg_deviation / 50)  # 50% deviation = 0 score

    def _assess_health_impact(self, recipe: dict, health_goals: dict) -> dict:
        """Provide health impact assessment"""
        nutrition = recipe.get("nutrition", {})
        
        assessment = {
            "health_rating": "unknown",
            "positive_aspects": [],
            "concerns": [],
            "recommendations": []
        }
        
        # Analyze positive aspects
        protein = nutrition.get("protein_g", 0)
        fiber = nutrition.get("fiber_g", 0)
        calories = nutrition.get("calories", 0)
        
        if protein >= health_goals["min_protein_g"]:
            assessment["positive_aspects"].append(f"Good protein content ({protein}g)")
        
        if fiber >= health_goals["min_fiber_g"]:
            assessment["positive_aspects"].append(f"High fiber content ({fiber}g)")
            
        if calories > 0 and calories <= health_goals["max_calories_per_meal"]:
            assessment["positive_aspects"].append(f"Appropriate calorie level ({calories} cal)")
        
        # Analyze concerns
        sodium = nutrition.get("sodium_mg", 0)
        sat_fat = nutrition.get("saturated_fat_g", 0)
        
        if sodium > health_goals["max_sodium_mg"] / 3:
            assessment["concerns"].append(f"High sodium content ({sodium}mg)")
            
        if sat_fat > health_goals["max_saturated_fat_g"] / 3:
            assessment["concerns"].append(f"High saturated fat ({sat_fat}g)")
            
        if calories > health_goals["max_calories_per_meal"]:
            assessment["concerns"].append(f"High calorie content ({calories} cal)")
        
        # Determine overall health rating
        nutrition_score = self._calculate_nutrition_score(recipe, health_goals)["overall_score"]
        
        if nutrition_score >= 0.8:
            assessment["health_rating"] = "excellent"
        elif nutrition_score >= 0.6:
            assessment["health_rating"] = "good"
        elif nutrition_score >= 0.4:
            assessment["health_rating"] = "fair"
        else:
            assessment["health_rating"] = "poor"
        
        return assessment

    def _get_health_warnings(self, recipe: dict, health_goals: dict) -> list[str]:
        """Get specific health warnings for the recipe"""
        warnings = []
        nutrition = recipe.get("nutrition", {})
        
        calories = nutrition.get("calories", 0)
        if calories > health_goals["max_calories_per_meal"] * 1.2:
            warnings.append("Very high calorie content - consider smaller portions")
            
        sodium = nutrition.get("sodium_mg", 0)
        if sodium > health_goals["max_sodium_mg"] / 2:  # More than half daily limit
            warnings.append("Extremely high sodium - not suitable for low-sodium diets")
            
        sat_fat = nutrition.get("saturated_fat_g", 0)
        if sat_fat > health_goals["max_saturated_fat_g"] / 2:
            warnings.append("High saturated fat - limit frequency")
        
        return warnings

    def _get_nutrition_highlights(self, recipe: dict) -> list[str]:
        """Get positive nutrition highlights"""
        highlights = []
        nutrition = recipe.get("nutrition", {})
        
        protein = nutrition.get("protein_g", 0)
        if protein >= 30:
            highlights.append("High protein")
            
        fiber = nutrition.get("fiber_g", 0)
        if fiber >= 10:
            highlights.append("High fiber")
            
        calories = nutrition.get("calories", 0)
        if calories > 0 and calories <= 400:
            highlights.append("Low calorie")
            
        sodium = nutrition.get("sodium_mg", 0)
        if sodium <= 300:
            highlights.append("Low sodium")
            
        sat_fat = nutrition.get("saturated_fat_g", 0)
        if sat_fat <= 3:
            highlights.append("Low saturated fat")
        
        return highlights