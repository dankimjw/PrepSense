"""Nutrition analysis tool for CrewAI agents."""

import logging
from typing import Any, Dict, List, Optional

# from crewai_tools import BaseTool  # Not available in CrewAI 0.5.0

logger = logging.getLogger(__name__)


class NutritionTool:
    """Tool for nutritional analysis and evaluation."""

    name: str = "nutrition_tool"
    description: str = (
        "A tool for analyzing nutritional content of recipes and meals, "
        "evaluating nutritional balance, and identifying dietary gaps."
    )

    def __init__(self):
        # RDA values for adults (general reference)
        self.rda_values = {
            "calories": 2000,
            "protein": 50,  # grams
            "carbohydrates": 300,  # grams
            "fat": 65,  # grams
            "fiber": 25,  # grams
            "sugar": 50,  # grams (max recommended)
            "sodium": 2300,  # mg (max recommended)
            "vitamin_c": 90,  # mg
            "vitamin_d": 20,  # mcg
            "calcium": 1000,  # mg
            "iron": 18,  # mg
            "potassium": 3500,  # mg
            "saturated_fat": 20,  # grams (max recommended)
            "cholesterol": 300,  # mg (max recommended)
            "vitamin_a": 900,  # mcg
            "magnesium": 400,  # mg
            "phosphorus": 700,  # mg
            "zinc": 11,  # mg
        }

    def _run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a nutrition analysis action.

        Args:
            action: The action to perform (analyze_recipe, compare_rda, etc.)
            **kwargs: Additional parameters

        Returns:
            Dict containing the analysis results
        """
        try:
            if action == "analyze_recipe":
                return self._analyze_recipe(**kwargs)
            elif action == "compare_rda":
                return self._compare_to_rda(**kwargs)
            elif action == "evaluate_balance":
                return self._evaluate_nutritional_balance(**kwargs)
            elif action == "identify_gaps":
                return self._identify_nutritional_gaps(**kwargs)
            elif action == "score_recipe":
                return self._score_recipe_nutrition(**kwargs)
            elif action == "macro_breakdown":
                return self._get_macro_breakdown(**kwargs)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Nutrition tool error: {str(e)}")
            return {"error": f"Nutrition analysis failed: {str(e)}"}

    def _analyze_recipe(self, **kwargs) -> Dict[str, Any]:
        """Analyze nutritional content of a recipe."""
        recipe = kwargs.get("recipe", {})

        if not recipe:
            return {"error": "No recipe provided"}

        # Extract nutrition data
        nutrition = recipe.get("nutrition", {})

        if not nutrition:
            return {"error": "No nutrition data found in recipe"}

        # Standardize nutrition format
        standardized_nutrition = self._standardize_nutrition(nutrition)

        # Calculate per serving if needed
        servings = recipe.get("servings", 1)
        per_serving = {}

        for nutrient, value in standardized_nutrition.items():
            if isinstance(value, (int, float)):
                per_serving[nutrient] = round(value / servings, 2)
            else:
                per_serving[nutrient] = value

        return {
            "recipe_name": recipe.get("name", "Unknown Recipe"),
            "servings": servings,
            "total_nutrition": standardized_nutrition,
            "per_serving": per_serving,
            "analysis_complete": True,
        }

    def _compare_to_rda(self, **kwargs) -> Dict[str, Any]:
        """Compare nutrition values to RDA."""
        nutrition = kwargs.get("nutrition", {})

        if not nutrition:
            return {"error": "No nutrition data provided"}

        comparison = {}
        deficiencies = []
        excesses = []

        for nutrient, value in nutrition.items():
            if nutrient in self.rda_values and isinstance(value, (int, float)):
                rda = self.rda_values[nutrient]
                percentage = (value / rda) * 100

                comparison[nutrient] = {
                    "value": value,
                    "rda": rda,
                    "percentage": round(percentage, 1),
                    "status": self._get_nutrient_status(nutrient, percentage),
                }

                # Check for deficiencies (< 70% RDA)
                if percentage < 70:
                    deficiencies.append(
                        {
                            "nutrient": nutrient,
                            "percentage": percentage,
                            "deficit": round(rda - value, 2),
                        }
                    )

                # Check for excesses (> 120% RDA for limited nutrients)
                if (
                    nutrient in ["sodium", "sugar", "saturated_fat", "cholesterol"]
                    and percentage > 120
                ):
                    excesses.append(
                        {
                            "nutrient": nutrient,
                            "percentage": percentage,
                            "excess": round(value - rda, 2),
                        }
                    )

        return {
            "comparison": comparison,
            "deficiencies": deficiencies,
            "excesses": excesses,
            "overall_score": self._calculate_overall_score(comparison),
        }

    def _evaluate_nutritional_balance(self, **kwargs) -> Dict[str, Any]:
        """Evaluate overall nutritional balance."""
        nutrition = kwargs.get("nutrition", {})

        if not nutrition:
            return {"error": "No nutrition data provided"}

        # Calculate macronutrient balance
        calories = nutrition.get("calories", 0)
        protein = nutrition.get("protein", 0)
        carbs = nutrition.get("carbohydrates", 0)
        fat = nutrition.get("fat", 0)

        if calories == 0:
            return {"error": "No calorie data available"}

        # Calculate percentages (4 cal/g protein, 4 cal/g carbs, 9 cal/g fat)
        protein_cals = protein * 4
        carb_cals = carbs * 4
        fat_cals = fat * 9

        total_macro_cals = protein_cals + carb_cals + fat_cals

        if total_macro_cals == 0:
            return {"error": "No macronutrient data available"}

        macro_percentages = {
            "protein": round((protein_cals / total_macro_cals) * 100, 1),
            "carbohydrates": round((carb_cals / total_macro_cals) * 100, 1),
            "fat": round((fat_cals / total_macro_cals) * 100, 1),
        }

        # Evaluate balance (ideal ranges: protein 10-35%, carbs 45-65%, fat 20-35%)
        balance_score = 0
        recommendations = []

        if 10 <= macro_percentages["protein"] <= 35:
            balance_score += 1
        else:
            recommendations.append(
                f"Adjust protein intake (currently {macro_percentages['protein']}%, ideal 10-35%)"
            )

        if 45 <= macro_percentages["carbohydrates"] <= 65:
            balance_score += 1
        else:
            recommendations.append(
                f"Adjust carbohydrate intake (currently {macro_percentages['carbohydrates']}%, ideal 45-65%)"
            )

        if 20 <= macro_percentages["fat"] <= 35:
            balance_score += 1
        else:
            recommendations.append(
                f"Adjust fat intake (currently {macro_percentages['fat']}%, ideal 20-35%)"
            )

        balance_rating = ["Poor", "Fair", "Good", "Excellent"][balance_score]

        return {
            "macro_percentages": macro_percentages,
            "balance_score": balance_score,
            "balance_rating": balance_rating,
            "recommendations": recommendations,
            "total_calories": calories,
        }

    def _identify_nutritional_gaps(self, **kwargs) -> Dict[str, Any]:
        """Identify nutritional gaps and deficiencies."""
        nutrition = kwargs.get("nutrition", {})
        user_profile = kwargs.get("user_profile", {})

        if not nutrition:
            return {"error": "No nutrition data provided"}

        # Adjust RDA based on user profile if provided
        adjusted_rda = self._adjust_rda_for_user(user_profile)

        gaps = []
        priorities = []

        for nutrient, rda in adjusted_rda.items():
            current_value = nutrition.get(nutrient, 0)

            if isinstance(current_value, (int, float)) and current_value < rda * 0.7:
                gap_amount = rda - current_value
                gap_percentage = (gap_amount / rda) * 100

                gap_info = {
                    "nutrient": nutrient,
                    "current": current_value,
                    "recommended": rda,
                    "gap_amount": round(gap_amount, 2),
                    "gap_percentage": round(gap_percentage, 1),
                    "priority": self._get_nutrient_priority(nutrient),
                }

                gaps.append(gap_info)

                if gap_info["priority"] == "high":
                    priorities.append(gap_info)

        return {
            "nutritional_gaps": gaps,
            "high_priority_gaps": priorities,
            "gap_count": len(gaps),
            "recommendations": self._generate_gap_recommendations(gaps),
        }

    def _score_recipe_nutrition(self, **kwargs) -> Dict[str, Any]:
        """Score a recipe's nutritional value."""
        recipe = kwargs.get("recipe", {})

        if not recipe:
            return {"error": "No recipe provided"}

        nutrition = recipe.get("nutrition", {})

        if not nutrition:
            return {"error": "No nutrition data in recipe"}

        # Score different aspects
        scores = {
            "protein_score": self._score_protein_content(nutrition),
            "fiber_score": self._score_fiber_content(nutrition),
            "vitamin_score": self._score_vitamin_content(nutrition),
            "mineral_score": self._score_mineral_content(nutrition),
            "balance_score": self._score_macro_balance(nutrition),
            "calorie_score": self._score_calorie_density(nutrition),
        }

        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)

        # Determine rating
        if overall_score >= 8:
            rating = "Excellent"
        elif overall_score >= 6:
            rating = "Good"
        elif overall_score >= 4:
            rating = "Fair"
        else:
            rating = "Poor"

        return {
            "recipe_name": recipe.get("name", "Unknown Recipe"),
            "nutrition_scores": scores,
            "overall_score": round(overall_score, 1),
            "rating": rating,
            "max_score": 10,
        }

    def _get_macro_breakdown(self, **kwargs) -> Dict[str, Any]:
        """Get detailed macronutrient breakdown."""
        nutrition = kwargs.get("nutrition", {})

        if not nutrition:
            return {"error": "No nutrition data provided"}

        calories = nutrition.get("calories", 0)
        protein = nutrition.get("protein", 0)
        carbs = nutrition.get("carbohydrates", 0)
        fat = nutrition.get("fat", 0)

        # Calculate calories from macros
        protein_cals = protein * 4
        carb_cals = carbs * 4
        fat_cals = fat * 9

        breakdown = {
            "total_calories": calories,
            "macronutrients": {
                "protein": {
                    "grams": protein,
                    "calories": protein_cals,
                    "percentage": round((protein_cals / calories) * 100, 1) if calories > 0 else 0,
                },
                "carbohydrates": {
                    "grams": carbs,
                    "calories": carb_cals,
                    "percentage": round((carb_cals / calories) * 100, 1) if calories > 0 else 0,
                },
                "fat": {
                    "grams": fat,
                    "calories": fat_cals,
                    "percentage": round((fat_cals / calories) * 100, 1) if calories > 0 else 0,
                },
            },
        }

        return breakdown

    def _standardize_nutrition(self, nutrition: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize nutrition data format."""
        standardized = {}

        # Handle different nutrition data formats
        if "nutrients" in nutrition:
            # Spoonacular format
            for nutrient in nutrition["nutrients"]:
                name = nutrient.get("name", "").lower()
                amount = nutrient.get("amount", 0)

                # Map to standardized names
                if name == "calories":
                    standardized["calories"] = amount
                elif name == "protein":
                    standardized["protein"] = amount
                elif name == "carbohydrates":
                    standardized["carbohydrates"] = amount
                elif name == "fat":
                    standardized["fat"] = amount
                elif name == "fiber":
                    standardized["fiber"] = amount
                elif name == "sugar":
                    standardized["sugar"] = amount
                elif name == "sodium":
                    standardized["sodium"] = amount
        else:
            # Direct format
            for key, value in nutrition.items():
                if isinstance(value, (int, float)):
                    standardized[key.lower()] = value

        return standardized

    def _get_nutrient_status(self, nutrient: str, percentage: float) -> str:
        """Get status of nutrient based on percentage of RDA."""
        if nutrient in ["sodium", "sugar", "saturated_fat", "cholesterol"]:
            # These should be limited
            if percentage > 120:
                return "excessive"
            elif percentage > 100:
                return "high"
            elif percentage > 70:
                return "adequate"
            else:
                return "low"
        else:
            # These should be adequate
            if percentage < 70:
                return "deficient"
            elif percentage < 100:
                return "adequate"
            else:
                return "excellent"

    def _calculate_overall_score(self, comparison: Dict[str, Any]) -> float:
        """Calculate overall nutritional score."""
        scores = []

        for nutrient, data in comparison.items():
            percentage = data["percentage"]

            if nutrient in ["sodium", "sugar", "saturated_fat", "cholesterol"]:
                # Lower is better for these
                if percentage <= 100:
                    score = 10
                elif percentage <= 120:
                    score = 7
                else:
                    score = 3
            else:
                # Higher is better for these
                if percentage >= 100:
                    score = 10
                elif percentage >= 70:
                    score = 7
                else:
                    score = 3

            scores.append(score)

        return round(sum(scores) / len(scores), 1) if scores else 0

    def _adjust_rda_for_user(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust RDA values based on user profile."""
        # For now, return standard RDA values
        # In future, could adjust based on age, gender, activity level, etc.
        return self.rda_values.copy()

    def _get_nutrient_priority(self, nutrient: str) -> str:
        """Get priority level for a nutrient."""
        high_priority = ["protein", "fiber", "vitamin_c", "vitamin_d", "calcium", "iron"]
        medium_priority = ["potassium", "magnesium", "zinc", "vitamin_a"]

        if nutrient in high_priority:
            return "high"
        elif nutrient in medium_priority:
            return "medium"
        else:
            return "low"

    def _generate_gap_recommendations(self, gaps: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on nutritional gaps."""
        recommendations = []

        for gap in gaps:
            nutrient = gap["nutrient"]
            gap_amount = gap["gap_amount"]

            if nutrient == "protein":
                recommendations.append(
                    f"Add {gap_amount:.0f}g more protein (lean meats, beans, nuts)"
                )
            elif nutrient == "fiber":
                recommendations.append(
                    f"Add {gap_amount:.0f}g more fiber (whole grains, vegetables, fruits)"
                )
            elif nutrient == "vitamin_c":
                recommendations.append(
                    f"Add {gap_amount:.0f}mg more vitamin C (citrus fruits, berries)"
                )
            elif nutrient == "calcium":
                recommendations.append(f"Add {gap_amount:.0f}mg more calcium (dairy, leafy greens)")
            elif nutrient == "iron":
                recommendations.append(
                    f"Add {gap_amount:.0f}mg more iron (red meat, spinach, legumes)"
                )

        return recommendations

    def _score_protein_content(self, nutrition: Dict[str, Any]) -> float:
        """Score protein content (0-10)."""
        protein = nutrition.get("protein", 0)
        calories = nutrition.get("calories", 0)

        if calories == 0:
            return 0

        protein_percentage = (protein * 4 / calories) * 100

        if protein_percentage >= 25:
            return 10
        elif protein_percentage >= 15:
            return 8
        elif protein_percentage >= 10:
            return 6
        else:
            return 3

    def _score_fiber_content(self, nutrition: Dict[str, Any]) -> float:
        """Score fiber content (0-10)."""
        fiber = nutrition.get("fiber", 0)
        calories = nutrition.get("calories", 0)

        if calories == 0:
            return 0

        fiber_per_100_cal = (fiber / calories) * 100

        if fiber_per_100_cal >= 2:
            return 10
        elif fiber_per_100_cal >= 1.5:
            return 8
        elif fiber_per_100_cal >= 1:
            return 6
        else:
            return 3

    def _score_vitamin_content(self, nutrition: Dict[str, Any]) -> float:
        """Score vitamin content (0-10)."""
        vitamin_c = nutrition.get("vitamin_c", 0)
        vitamin_d = nutrition.get("vitamin_d", 0)
        vitamin_a = nutrition.get("vitamin_a", 0)

        score = 0
        count = 0

        if vitamin_c > 0:
            score += min(10, (vitamin_c / 90) * 10)
            count += 1

        if vitamin_d > 0:
            score += min(10, (vitamin_d / 20) * 10)
            count += 1

        if vitamin_a > 0:
            score += min(10, (vitamin_a / 900) * 10)
            count += 1

        return score / count if count > 0 else 5

    def _score_mineral_content(self, nutrition: Dict[str, Any]) -> float:
        """Score mineral content (0-10)."""
        calcium = nutrition.get("calcium", 0)
        iron = nutrition.get("iron", 0)
        potassium = nutrition.get("potassium", 0)

        score = 0
        count = 0

        if calcium > 0:
            score += min(10, (calcium / 1000) * 10)
            count += 1

        if iron > 0:
            score += min(10, (iron / 18) * 10)
            count += 1

        if potassium > 0:
            score += min(10, (potassium / 3500) * 10)
            count += 1

        return score / count if count > 0 else 5

    def _score_macro_balance(self, nutrition: Dict[str, Any]) -> float:
        """Score macronutrient balance (0-10)."""
        balance_result = self._evaluate_nutritional_balance(nutrition=nutrition)

        if "error" in balance_result:
            return 5

        balance_score = balance_result["balance_score"]
        return (balance_score / 3) * 10

    def _score_calorie_density(self, nutrition: Dict[str, Any]) -> float:
        """Score calorie density (0-10)."""
        calories = nutrition.get("calories", 0)

        # Assume per serving, ideal range 200-600 calories
        if 200 <= calories <= 600:
            return 10
        elif 150 <= calories <= 800:
            return 8
        elif 100 <= calories <= 1000:
            return 6
        else:
            return 3


# Helper function to create the tool
def create_nutrition_tool() -> NutritionTool:
    """Create and return a NutritionTool instance."""
    return NutritionTool()
