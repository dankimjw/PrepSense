"""NutritionExpert Agent for analyzing nutritional content and providing dietary insights."""

from typing import Dict, List, Any, Optional
import logging
from crewai import Agent
from langchain_openai import ChatOpenAI

from backend_gateway.tools.nutrition_tool import create_nutrition_tool
from backend_gateway.tools.database_tool import create_database_tool
from backend_gateway.core.config_utils import get_openai_api_key

logger = logging.getLogger(__name__)


class NutritionExpertAgent:
    """Agent specialized in nutritional analysis and dietary guidance."""
    
    def __init__(self):
        """Initialize the NutritionExpert agent."""
        self.nutrition_tool = create_nutrition_tool()
        self.database_tool = create_database_tool()
        
        # Initialize OpenAI LLM
        api_key = get_openai_api_key()
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0.2)
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Nutrition Expert",
            goal="Analyze nutritional content of recipes, evaluate dietary balance, and provide expert nutritional guidance based on health goals and dietary needs",
            backstory=(
                "You are a certified nutritionist and dietitian with deep expertise in nutritional "
                "science, meal planning, and dietary optimization. You excel at analyzing the "
                "nutritional content of recipes, identifying nutritional gaps, and providing "
                "actionable dietary recommendations. Your knowledge spans macronutrients, "
                "micronutrients, dietary guidelines, and special dietary requirements. You help "
                "users make informed food choices that support their health and wellness goals."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_nutrition(self, user_id: int, analysis_type: str = "recipe", **kwargs) -> Dict[str, Any]:
        """
        Analyze nutritional content based on analysis type.
        
        Args:
            user_id: The user's ID
            analysis_type: Type of analysis (recipe, meal_plan, gaps, balance)
            **kwargs: Additional parameters for analysis
            
        Returns:
            Dict containing nutritional analysis results
        """
        try:
            logger.info(f"NutritionExpert analyzing nutrition for user {user_id}, type: {analysis_type}")
            
            if analysis_type == "recipe":
                return self._analyze_recipe_nutrition(user_id, **kwargs)
            elif analysis_type == "recipes_batch":
                return self._analyze_recipes_batch(user_id, **kwargs)
            elif analysis_type == "meal_plan":
                return self._analyze_meal_plan(user_id, **kwargs)
            elif analysis_type == "gaps":
                return self._identify_nutritional_gaps(user_id, **kwargs)
            elif analysis_type == "balance":
                return self._evaluate_dietary_balance(user_id, **kwargs)
            elif analysis_type == "recommendations":
                return self._generate_nutrition_recommendations(user_id, **kwargs)
            else:
                return self._analyze_recipe_nutrition(user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"NutritionExpert error: {str(e)}")
            return {"error": f"Nutrition analysis failed: {str(e)}"}
    
    def _analyze_recipe_nutrition(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Analyze nutrition of a single recipe."""
        recipe = kwargs.get('recipe', {})
        
        if not recipe:
            return {"error": "No recipe provided for analysis"}
        
        # Analyze recipe nutrition
        nutrition_result = self.nutrition_tool._run("analyze_recipe", recipe=recipe)
        
        if "error" in nutrition_result:
            return nutrition_result
        
        # Compare to RDA
        per_serving_nutrition = nutrition_result.get('per_serving', {})
        rda_comparison = self.nutrition_tool._run("compare_rda", nutrition=per_serving_nutrition)
        
        # Evaluate nutritional balance
        balance_result = self.nutrition_tool._run("evaluate_balance", nutrition=per_serving_nutrition)
        
        # Score the recipe
        score_result = self.nutrition_tool._run("score_recipe", recipe=recipe)
        
        # Get macro breakdown
        macro_breakdown = self.nutrition_tool._run("macro_breakdown", nutrition=per_serving_nutrition)
        
        # Generate expert insights
        expert_insights = self._generate_recipe_insights(recipe, nutrition_result, rda_comparison, balance_result)
        
        return {
            "analysis_type": "recipe",
            "user_id": user_id,
            "recipe_name": recipe.get('name', 'Unknown Recipe'),
            "nutrition_analysis": nutrition_result,
            "rda_comparison": rda_comparison,
            "balance_evaluation": balance_result,
            "nutrition_score": score_result,
            "macro_breakdown": macro_breakdown,
            "expert_insights": expert_insights,
            "recommendations": self._generate_recipe_recommendations(recipe, nutrition_result, rda_comparison)
        }
    
    def _analyze_recipes_batch(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Analyze nutrition of multiple recipes."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided for analysis"}
        
        analyzed_recipes = []
        nutrition_summary = {
            'total_recipes': len(recipes),
            'highly_nutritious': 0,
            'well_balanced': 0,
            'needs_improvement': 0,
            'average_scores': {
                'nutrition_score': 0,
                'protein_score': 0,
                'fiber_score': 0,
                'balance_score': 0
            }
        }
        
        total_scores = {
            'nutrition': 0,
            'protein': 0,
            'fiber': 0,
            'balance': 0
        }
        
        # Analyze each recipe
        for recipe in recipes:
            recipe_analysis = self._analyze_recipe_nutrition(user_id, recipe=recipe)
            
            if "error" not in recipe_analysis:
                analyzed_recipes.append(recipe_analysis)
                
                # Update summary statistics
                nutrition_score = recipe_analysis.get('nutrition_score', {})
                overall_score = nutrition_score.get('overall_score', 0)
                nutrition_scores = nutrition_score.get('nutrition_scores', {})
                
                if overall_score >= 8:
                    nutrition_summary['highly_nutritious'] += 1
                elif overall_score >= 6:
                    nutrition_summary['well_balanced'] += 1
                else:
                    nutrition_summary['needs_improvement'] += 1
                
                # Accumulate scores for averaging
                total_scores['nutrition'] += overall_score
                total_scores['protein'] += nutrition_scores.get('protein_score', 0)
                total_scores['fiber'] += nutrition_scores.get('fiber_score', 0)
                total_scores['balance'] += nutrition_scores.get('balance_score', 0)
        
        # Calculate average scores
        recipe_count = len(analyzed_recipes)
        if recipe_count > 0:
            nutrition_summary['average_scores'] = {
                'nutrition_score': round(total_scores['nutrition'] / recipe_count, 1),
                'protein_score': round(total_scores['protein'] / recipe_count, 1),
                'fiber_score': round(total_scores['fiber'] / recipe_count, 1),
                'balance_score': round(total_scores['balance'] / recipe_count, 1)
            }
        
        # Generate batch insights
        batch_insights = self._generate_batch_insights(nutrition_summary)
        
        return {
            "analysis_type": "recipes_batch",
            "user_id": user_id,
            "analyzed_recipes": analyzed_recipes,
            "nutrition_summary": nutrition_summary,
            "batch_insights": batch_insights,
            "recommendations": self._generate_batch_recommendations(nutrition_summary)
        }
    
    def _analyze_meal_plan(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Analyze nutrition of a meal plan."""
        meal_plan = kwargs.get('meal_plan', {})
        days = kwargs.get('days', 7)
        
        if not meal_plan:
            return {"error": "No meal plan provided for analysis"}
        
        # Analyze each day's nutrition
        daily_analyses = []
        cumulative_nutrition = {}
        
        for day, meals in meal_plan.items():
            day_nutrition = {}
            
            for meal_type, recipe in meals.items():
                if recipe:
                    recipe_analysis = self._analyze_recipe_nutrition(user_id, recipe=recipe)
                    if "error" not in recipe_analysis:
                        day_nutrition[meal_type] = recipe_analysis
            
            # Calculate daily totals
            daily_totals = self._calculate_daily_totals(day_nutrition)
            daily_analyses.append({
                "day": day,
                "meals": day_nutrition,
                "daily_totals": daily_totals
            })
            
            # Add to cumulative nutrition
            self._add_to_cumulative(cumulative_nutrition, daily_totals)
        
        # Calculate averages
        avg_daily_nutrition = self._calculate_averages(cumulative_nutrition, len(daily_analyses))
        
        # Compare to RDA
        rda_comparison = self.nutrition_tool._run("compare_rda", nutrition=avg_daily_nutrition)
        
        # Identify gaps
        gaps_result = self.nutrition_tool._run("identify_gaps", nutrition=avg_daily_nutrition)
        
        # Generate meal plan insights
        meal_plan_insights = self._generate_meal_plan_insights(daily_analyses, rda_comparison, gaps_result)
        
        return {
            "analysis_type": "meal_plan",
            "user_id": user_id,
            "days_analyzed": len(daily_analyses),
            "daily_analyses": daily_analyses,
            "average_daily_nutrition": avg_daily_nutrition,
            "rda_comparison": rda_comparison,
            "nutritional_gaps": gaps_result,
            "meal_plan_insights": meal_plan_insights,
            "recommendations": self._generate_meal_plan_recommendations(rda_comparison, gaps_result)
        }
    
    def _identify_nutritional_gaps(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Identify nutritional gaps in user's diet."""
        current_nutrition = kwargs.get('current_nutrition', {})
        user_profile = kwargs.get('user_profile', {})
        
        if not current_nutrition:
            return {"error": "No current nutrition data provided"}
        
        # Identify gaps
        gaps_result = self.nutrition_tool._run(
            "identify_gaps", 
            nutrition=current_nutrition, 
            user_profile=user_profile
        )
        
        if "error" in gaps_result:
            return gaps_result
        
        # Generate targeted recommendations
        gap_recommendations = self._generate_gap_recommendations(gaps_result)
        
        # Suggest specific foods to address gaps
        food_suggestions = self._suggest_foods_for_gaps(gaps_result)
        
        return {
            "analysis_type": "gaps",
            "user_id": user_id,
            "nutritional_gaps": gaps_result,
            "gap_recommendations": gap_recommendations,
            "food_suggestions": food_suggestions,
            "priority_actions": self._prioritize_gap_actions(gaps_result)
        }
    
    def _evaluate_dietary_balance(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Evaluate overall dietary balance."""
        nutrition_data = kwargs.get('nutrition_data', {})
        
        if not nutrition_data:
            return {"error": "No nutrition data provided"}
        
        # Evaluate balance
        balance_result = self.nutrition_tool._run("evaluate_balance", nutrition=nutrition_data)
        
        if "error" in balance_result:
            return balance_result
        
        # Generate balance insights
        balance_insights = self._generate_balance_insights(balance_result)
        
        # Provide improvement suggestions
        improvement_suggestions = self._generate_balance_improvements(balance_result)
        
        return {
            "analysis_type": "balance",
            "user_id": user_id,
            "balance_evaluation": balance_result,
            "balance_insights": balance_insights,
            "improvement_suggestions": improvement_suggestions,
            "overall_rating": self._get_overall_balance_rating(balance_result)
        }
    
    def _generate_nutrition_recommendations(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Generate personalized nutrition recommendations."""
        current_nutrition = kwargs.get('current_nutrition', {})
        health_goals = kwargs.get('health_goals', [])
        dietary_preferences = kwargs.get('dietary_preferences', [])
        
        recommendations = {
            "general_recommendations": [
                "Maintain a balanced diet with variety in food sources",
                "Stay hydrated by drinking plenty of water throughout the day",
                "Include both macronutrients and micronutrients in your meals"
            ],
            "specific_recommendations": [],
            "food_suggestions": [],
            "meal_timing_advice": [],
            "supplement_considerations": []
        }
        
        # Analyze current nutrition if provided
        if current_nutrition:
            rda_comparison = self.nutrition_tool._run("compare_rda", nutrition=current_nutrition)
            
            if "error" not in rda_comparison:
                # Add specific recommendations based on deficiencies
                deficiencies = rda_comparison.get('deficiencies', [])
                for deficiency in deficiencies:
                    nutrient = deficiency['nutrient']
                    recommendations['specific_recommendations'].append(
                        f"Increase {nutrient} intake to meet daily requirements"
                    )
        
        # Add recommendations based on health goals
        for goal in health_goals:
            goal_lower = goal.lower()
            if 'weight loss' in goal_lower:
                recommendations['specific_recommendations'].extend([
                    "Focus on high-protein, high-fiber foods for satiety",
                    "Monitor portion sizes and caloric intake",
                    "Include lean proteins and non-starchy vegetables"
                ])
            elif 'muscle gain' in goal_lower:
                recommendations['specific_recommendations'].extend([
                    "Increase protein intake to support muscle growth",
                    "Include post-workout nutrition within 30 minutes",
                    "Consume adequate calories to support training"
                ])
            elif 'heart health' in goal_lower:
                recommendations['specific_recommendations'].extend([
                    "Limit sodium intake and choose low-sodium options",
                    "Include omega-3 fatty acids from fish or supplements",
                    "Focus on whole grains and fiber-rich foods"
                ])
        
        # Add recommendations based on dietary preferences
        for preference in dietary_preferences:
            pref_lower = preference.lower()
            if 'vegetarian' in pref_lower:
                recommendations['food_suggestions'].extend([
                    "Include a variety of plant-based proteins",
                    "Ensure adequate B12 and iron intake",
                    "Combine complementary proteins for complete amino acids"
                ])
            elif 'low-carb' in pref_lower:
                recommendations['food_suggestions'].extend([
                    "Focus on healthy fats and high-quality proteins",
                    "Include low-carb vegetables for micronutrients",
                    "Monitor ketone levels if following ketogenic approach"
                ])
        
        return {
            "analysis_type": "recommendations",
            "user_id": user_id,
            "recommendations": recommendations,
            "personalization_factors": {
                "health_goals": health_goals,
                "dietary_preferences": dietary_preferences,
                "current_nutrition_considered": bool(current_nutrition)
            }
        }
    
    def _generate_recipe_insights(self, recipe: Dict[str, Any], nutrition_analysis: Dict[str, Any], 
                                 rda_comparison: Dict[str, Any], balance_result: Dict[str, Any]) -> List[str]:
        """Generate expert insights for a recipe."""
        insights = []
        
        # Nutrition density insights
        per_serving = nutrition_analysis.get('per_serving', {})
        calories = per_serving.get('calories', 0)
        protein = per_serving.get('protein', 0)
        fiber = per_serving.get('fiber', 0)
        
        if calories > 0:
            if protein / calories > 0.15:  # High protein density
                insights.append("This recipe is an excellent source of protein")
            
            if fiber > 5:
                insights.append("This recipe provides good fiber content for digestive health")
        
        # RDA insights
        if "comparison" in rda_comparison:
            excellent_nutrients = []
            for nutrient, data in rda_comparison['comparison'].items():
                if data.get('status') == 'excellent':
                    excellent_nutrients.append(nutrient)
            
            if excellent_nutrients:
                insights.append(f"Rich in: {', '.join(excellent_nutrients)}")
        
        # Balance insights
        if "balance_rating" in balance_result:
            rating = balance_result['balance_rating']
            if rating in ['Good', 'Excellent']:
                insights.append(f"Well-balanced macronutrient profile ({rating})")
        
        return insights
    
    def _generate_recipe_recommendations(self, recipe: Dict[str, Any], nutrition_analysis: Dict[str, Any], 
                                       rda_comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a recipe."""
        recommendations = []
        
        # Check for deficiencies
        if "deficiencies" in rda_comparison:
            for deficiency in rda_comparison['deficiencies']:
                nutrient = deficiency['nutrient']
                if nutrient == 'fiber':
                    recommendations.append("Add more vegetables or whole grains to increase fiber")
                elif nutrient == 'protein':
                    recommendations.append("Consider adding lean protein sources")
                elif nutrient == 'calcium':
                    recommendations.append("Include dairy or leafy greens for calcium")
        
        # Check for excesses
        if "excesses" in rda_comparison:
            for excess in rda_comparison['excesses']:
                nutrient = excess['nutrient']
                if nutrient == 'sodium':
                    recommendations.append("Reduce salt or use herbs and spices for flavor")
                elif nutrient == 'sugar':
                    recommendations.append("Consider reducing added sugars")
        
        return recommendations
    
    def _generate_batch_insights(self, nutrition_summary: Dict[str, Any]) -> List[str]:
        """Generate insights for a batch of recipes."""
        insights = []
        
        total_recipes = nutrition_summary['total_recipes']
        highly_nutritious = nutrition_summary['highly_nutritious']
        well_balanced = nutrition_summary['well_balanced']
        needs_improvement = nutrition_summary['needs_improvement']
        
        # Overall assessment
        if highly_nutritious / total_recipes > 0.5:
            insights.append("Most recipes in this collection are highly nutritious")
        elif well_balanced / total_recipes > 0.5:
            insights.append("This collection has a good balance of nutritious recipes")
        else:
            insights.append("Consider adding more nutritionally dense recipes to this collection")
        
        # Average scores insights
        avg_scores = nutrition_summary['average_scores']
        if avg_scores['protein_score'] < 5:
            insights.append("The collection could benefit from more protein-rich recipes")
        
        if avg_scores['fiber_score'] < 5:
            insights.append("Consider including more fiber-rich recipes")
        
        return insights
    
    def _generate_batch_recommendations(self, nutrition_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a batch of recipes."""
        recommendations = []
        
        needs_improvement = nutrition_summary['needs_improvement']
        total_recipes = nutrition_summary['total_recipes']
        
        if needs_improvement / total_recipes > 0.3:
            recommendations.append("Consider replacing some recipes with more nutritious alternatives")
        
        recommendations.append("Aim for variety in nutrients across different recipes")
        recommendations.append("Balance indulgent recipes with healthier options")
        
        return recommendations
    
    def _calculate_daily_totals(self, day_nutrition: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate daily nutrition totals."""
        totals = {}
        
        for meal_type, meal_analysis in day_nutrition.items():
            if "nutrition_analysis" in meal_analysis:
                per_serving = meal_analysis['nutrition_analysis'].get('per_serving', {})
                
                for nutrient, value in per_serving.items():
                    if isinstance(value, (int, float)):
                        totals[nutrient] = totals.get(nutrient, 0) + value
        
        return totals
    
    def _add_to_cumulative(self, cumulative: Dict[str, Any], daily_totals: Dict[str, Any]):
        """Add daily totals to cumulative nutrition."""
        for nutrient, value in daily_totals.items():
            if isinstance(value, (int, float)):
                cumulative[nutrient] = cumulative.get(nutrient, 0) + value
    
    def _calculate_averages(self, cumulative: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Calculate average daily nutrition."""
        averages = {}
        
        for nutrient, total in cumulative.items():
            if isinstance(total, (int, float)) and days > 0:
                averages[nutrient] = round(total / days, 2)
        
        return averages
    
    def _generate_meal_plan_insights(self, daily_analyses: List[Dict[str, Any]], 
                                   rda_comparison: Dict[str, Any], gaps_result: Dict[str, Any]) -> List[str]:
        """Generate insights for a meal plan."""
        insights = []
        
        # Consistency insights
        if len(daily_analyses) >= 7:
            insights.append("This meal plan provides a full week of nutrition data")
        
        # Gap insights
        if "high_priority_gaps" in gaps_result:
            high_priority_gaps = gaps_result['high_priority_gaps']
            if high_priority_gaps:
                gap_nutrients = [gap['nutrient'] for gap in high_priority_gaps]
                insights.append(f"Priority nutrients to address: {', '.join(gap_nutrients)}")
        
        return insights
    
    def _generate_meal_plan_recommendations(self, rda_comparison: Dict[str, Any], 
                                          gaps_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a meal plan."""
        recommendations = []
        
        # Address gaps
        if "recommendations" in gaps_result:
            recommendations.extend(gaps_result['recommendations'])
        
        # General meal plan advice
        recommendations.extend([
            "Include a variety of food groups across all meals",
            "Plan snacks to help meet nutritional needs",
            "Consider meal prep to ensure consistent nutrition"
        ])
        
        return recommendations
    
    def _generate_gap_recommendations(self, gaps_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on nutritional gaps."""
        recommendations = []
        
        if "recommendations" in gaps_result:
            recommendations.extend(gaps_result['recommendations'])
        
        return recommendations
    
    def _suggest_foods_for_gaps(self, gaps_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Suggest specific foods to address nutritional gaps."""
        food_suggestions = {}
        
        if "nutritional_gaps" in gaps_result:
            for gap in gaps_result['nutritional_gaps']:
                nutrient = gap['nutrient']
                
                if nutrient == 'protein':
                    food_suggestions[nutrient] = ['lean meats', 'fish', 'eggs', 'legumes', 'tofu']
                elif nutrient == 'fiber':
                    food_suggestions[nutrient] = ['whole grains', 'vegetables', 'fruits', 'legumes']
                elif nutrient == 'vitamin_c':
                    food_suggestions[nutrient] = ['citrus fruits', 'berries', 'bell peppers', 'broccoli']
                elif nutrient == 'calcium':
                    food_suggestions[nutrient] = ['dairy products', 'leafy greens', 'fortified foods']
                elif nutrient == 'iron':
                    food_suggestions[nutrient] = ['red meat', 'spinach', 'legumes', 'fortified cereals']
        
        return food_suggestions
    
    def _prioritize_gap_actions(self, gaps_result: Dict[str, Any]) -> List[str]:
        """Prioritize actions based on nutritional gaps."""
        priority_actions = []
        
        if "high_priority_gaps" in gaps_result:
            for gap in gaps_result['high_priority_gaps']:
                nutrient = gap['nutrient']
                priority_actions.append(f"Address {nutrient} deficiency immediately")
        
        return priority_actions
    
    def _generate_balance_insights(self, balance_result: Dict[str, Any]) -> List[str]:
        """Generate insights about dietary balance."""
        insights = []
        
        if "balance_rating" in balance_result:
            rating = balance_result['balance_rating']
            insights.append(f"Overall macronutrient balance: {rating}")
        
        if "recommendations" in balance_result:
            insights.extend(balance_result['recommendations'])
        
        return insights
    
    def _generate_balance_improvements(self, balance_result: Dict[str, Any]) -> List[str]:
        """Generate suggestions for improving dietary balance."""
        improvements = []
        
        if "recommendations" in balance_result:
            improvements.extend(balance_result['recommendations'])
        
        return improvements
    
    def _get_overall_balance_rating(self, balance_result: Dict[str, Any]) -> str:
        """Get overall balance rating."""
        return balance_result.get('balance_rating', 'Unknown')


def create_nutrition_expert_agent() -> NutritionExpertAgent:
    """Create and return a NutritionExpertAgent instance."""
    return NutritionExpertAgent()