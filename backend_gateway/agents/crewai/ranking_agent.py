"""Ranking Agent for final recipe recommendations and scoring."""

from typing import Dict, List, Any, Optional
import logging
from crewai import Agent
from langchain_openai import ChatOpenAI

from backend_gateway.tools.database_tool import create_database_tool
from backend_gateway.core.config_utils import get_openai_api_key

logger = logging.getLogger(__name__)


class RankingAgent:
    """Agent specialized in ranking and providing final recipe recommendations."""
    
    def __init__(self):
        """Initialize the Ranking agent."""
        self.database_tool = create_database_tool()
        
        # Initialize OpenAI LLM
        api_key = get_openai_api_key()
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0.1)
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Recipe Recommendation Specialist",
            goal="Synthesize analyses from all agents to provide final, personalized recipe recommendations with comprehensive scoring and ranking",
            backstory=(
                "You are a master recipe curator with expertise in combining multiple factors "
                "to create the perfect recipe recommendations. You excel at synthesizing "
                "pantry analysis, nutritional data, user preferences, and recipe search results "
                "into compelling, personalized recommendations. Your holistic approach considers "
                "ingredient availability, nutritional value, dietary preferences, cooking complexity, "
                "and user satisfaction to deliver recommendations that users will love and benefit from."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def rank_recipes(self, user_id: int, ranking_strategy: str = "balanced", **kwargs) -> Dict[str, Any]:
        """
        Rank recipes based on comprehensive analysis.
        
        Args:
            user_id: The user's ID
            ranking_strategy: Strategy for ranking (balanced, health_focused, convenience, etc.)
            **kwargs: Additional parameters including analysis results
            
        Returns:
            Dict containing ranked recipes and comprehensive recommendations
        """
        try:
            logger.info(f"RankingAgent ranking recipes for user {user_id}, strategy: {ranking_strategy}")
            
            if ranking_strategy == "balanced":
                return self._rank_balanced(user_id, **kwargs)
            elif ranking_strategy == "health_focused":
                return self._rank_health_focused(user_id, **kwargs)
            elif ranking_strategy == "convenience":
                return self._rank_convenience(user_id, **kwargs)
            elif ranking_strategy == "ingredient_match":
                return self._rank_ingredient_match(user_id, **kwargs)
            elif ranking_strategy == "comprehensive":
                return self._rank_comprehensive(user_id, **kwargs)
            else:
                return self._rank_balanced(user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"RankingAgent error: {str(e)}")
            return {"error": f"Recipe ranking failed: {str(e)}"}
    
    def _rank_balanced(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Rank recipes using a balanced approach considering all factors."""
        # Extract analysis results from kwargs
        pantry_analysis = kwargs.get('pantry_analysis', {})
        recipe_search_results = kwargs.get('recipe_search_results', {})
        nutrition_analysis = kwargs.get('nutrition_analysis', {})
        preference_analysis = kwargs.get('preference_analysis', {})
        
        recipes = recipe_search_results.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided for ranking"}
        
        # Score each recipe across multiple dimensions
        scored_recipes = []
        
        for recipe in recipes:
            comprehensive_score = self._calculate_comprehensive_score(
                recipe, pantry_analysis, nutrition_analysis, preference_analysis
            )
            
            recipe_copy = recipe.copy()
            recipe_copy['comprehensive_score'] = comprehensive_score
            recipe_copy['ranking_explanation'] = self._generate_ranking_explanation(
                recipe, comprehensive_score, pantry_analysis, nutrition_analysis, preference_analysis
            )
            
            scored_recipes.append(recipe_copy)
        
        # Sort by comprehensive score
        scored_recipes.sort(key=lambda x: x.get('comprehensive_score', {}).get('total_score', 0), reverse=True)
        
        # Generate final recommendations
        final_recommendations = self._generate_final_recommendations(scored_recipes, user_id)
        
        # Create recommendation tiers
        recommendation_tiers = self._create_recommendation_tiers(scored_recipes)
        
        return {
            "ranking_strategy": "balanced",
            "user_id": user_id,
            "total_recipes": len(scored_recipes),
            "ranked_recipes": scored_recipes,
            "final_recommendations": final_recommendations,
            "recommendation_tiers": recommendation_tiers,
            "ranking_metadata": {
                "factors_considered": ["pantry_match", "nutrition", "preferences", "complexity"],
                "weighting_strategy": "balanced"
            }
        }
    
    def _rank_health_focused(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Rank recipes with emphasis on nutritional value."""
        recipes = kwargs.get('recipe_search_results', {}).get('recipes', [])
        nutrition_analysis = kwargs.get('nutrition_analysis', {})
        
        if not recipes:
            return {"error": "No recipes provided for health-focused ranking"}
        
        scored_recipes = []
        
        for recipe in recipes:
            health_score = self._calculate_health_score(recipe, nutrition_analysis)
            
            recipe_copy = recipe.copy()
            recipe_copy['health_score'] = health_score
            recipe_copy['health_explanation'] = self._generate_health_explanation(recipe, health_score)
            
            scored_recipes.append(recipe_copy)
        
        # Sort by health score
        scored_recipes.sort(key=lambda x: x.get('health_score', {}).get('total_score', 0), reverse=True)
        
        # Generate health-focused recommendations
        health_recommendations = self._generate_health_recommendations(scored_recipes)
        
        return {
            "ranking_strategy": "health_focused",
            "user_id": user_id,
            "total_recipes": len(scored_recipes),
            "ranked_recipes": scored_recipes,
            "health_recommendations": health_recommendations,
            "ranking_metadata": {
                "primary_factor": "nutritional_value",
                "secondary_factors": ["ingredient_quality", "balance"]
            }
        }
    
    def _rank_convenience(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Rank recipes based on convenience and ease of preparation."""
        recipes = kwargs.get('recipe_search_results', {}).get('recipes', [])
        pantry_analysis = kwargs.get('pantry_analysis', {})
        
        if not recipes:
            return {"error": "No recipes provided for convenience ranking"}
        
        scored_recipes = []
        
        for recipe in recipes:
            convenience_score = self._calculate_convenience_score(recipe, pantry_analysis)
            
            recipe_copy = recipe.copy()
            recipe_copy['convenience_score'] = convenience_score
            recipe_copy['convenience_explanation'] = self._generate_convenience_explanation(recipe, convenience_score)
            
            scored_recipes.append(recipe_copy)
        
        # Sort by convenience score
        scored_recipes.sort(key=lambda x: x.get('convenience_score', {}).get('total_score', 0), reverse=True)
        
        # Generate convenience recommendations
        convenience_recommendations = self._generate_convenience_recommendations(scored_recipes)
        
        return {
            "ranking_strategy": "convenience",
            "user_id": user_id,
            "total_recipes": len(scored_recipes),
            "ranked_recipes": scored_recipes,
            "convenience_recommendations": convenience_recommendations,
            "ranking_metadata": {
                "primary_factor": "ease_of_preparation",
                "secondary_factors": ["ingredient_availability", "cooking_time"]
            }
        }
    
    def _rank_ingredient_match(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Rank recipes based on ingredient availability and match."""
        recipes = kwargs.get('recipe_search_results', {}).get('recipes', [])
        pantry_analysis = kwargs.get('pantry_analysis', {})
        
        if not recipes:
            return {"error": "No recipes provided for ingredient matching"}
        
        scored_recipes = []
        
        for recipe in recipes:
            ingredient_score = self._calculate_ingredient_match_score(recipe, pantry_analysis)
            
            recipe_copy = recipe.copy()
            recipe_copy['ingredient_match_score'] = ingredient_score
            recipe_copy['ingredient_explanation'] = self._generate_ingredient_explanation(recipe, ingredient_score, pantry_analysis)
            
            scored_recipes.append(recipe_copy)
        
        # Sort by ingredient match score
        scored_recipes.sort(key=lambda x: x.get('ingredient_match_score', {}).get('total_score', 0), reverse=True)
        
        # Generate ingredient-focused recommendations
        ingredient_recommendations = self._generate_ingredient_recommendations(scored_recipes, pantry_analysis)
        
        return {
            "ranking_strategy": "ingredient_match",
            "user_id": user_id,
            "total_recipes": len(scored_recipes),
            "ranked_recipes": scored_recipes,
            "ingredient_recommendations": ingredient_recommendations,
            "ranking_metadata": {
                "primary_factor": "ingredient_availability",
                "secondary_factors": ["expiring_items", "pantry_utilization"]
            }
        }
    
    def _rank_comprehensive(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Comprehensive ranking using all available analyses."""
        # This combines all strategies with weighted scoring
        balanced_result = self._rank_balanced(user_id, **kwargs)
        health_result = self._rank_health_focused(user_id, **kwargs)
        convenience_result = self._rank_convenience(user_id, **kwargs)
        ingredient_result = self._rank_ingredient_match(user_id, **kwargs)
        
        # Combine all scoring approaches
        comprehensive_rankings = self._combine_ranking_strategies(
            balanced_result, health_result, convenience_result, ingredient_result
        )
        
        return {
            "ranking_strategy": "comprehensive",
            "user_id": user_id,
            "comprehensive_rankings": comprehensive_rankings,
            "individual_rankings": {
                "balanced": balanced_result,
                "health_focused": health_result,
                "convenience": convenience_result,
                "ingredient_match": ingredient_result
            },
            "ranking_metadata": {
                "strategies_combined": ["balanced", "health_focused", "convenience", "ingredient_match"],
                "weighting_strategy": "comprehensive"
            }
        }
    
    def _calculate_comprehensive_score(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any], 
                                     nutrition_analysis: Dict[str, Any], preference_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive score for a recipe."""
        scores = {
            "pantry_match_score": 0,
            "nutrition_score": 0,
            "preference_score": 0,
            "complexity_score": 0,
            "total_score": 0
        }
        
        # Pantry match score (30% weight)
        pantry_score = self._score_pantry_match(recipe, pantry_analysis)
        scores["pantry_match_score"] = pantry_score
        
        # Nutrition score (25% weight)
        nutrition_score = self._score_nutrition(recipe, nutrition_analysis)
        scores["nutrition_score"] = nutrition_score
        
        # Preference score (25% weight)
        preference_score = self._score_preferences(recipe, preference_analysis)
        scores["preference_score"] = preference_score
        
        # Complexity score (20% weight) - inverted (lower complexity = higher score)
        complexity_score = self._score_complexity(recipe)
        scores["complexity_score"] = complexity_score
        
        # Calculate weighted total
        total_score = (
            pantry_score * 0.30 +
            nutrition_score * 0.25 +
            preference_score * 0.25 +
            complexity_score * 0.20
        )
        
        scores["total_score"] = round(total_score, 2)
        
        return scores
    
    def _calculate_health_score(self, recipe: Dict[str, Any], nutrition_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health-focused score for a recipe."""
        scores = {
            "nutritional_density": 0,
            "balance_score": 0,
            "vitamin_mineral_score": 0,
            "total_score": 0
        }
        
        # Get nutrition data
        nutrition = recipe.get('nutrition', {})
        
        if nutrition:
            # Nutritional density (40% weight)
            scores["nutritional_density"] = self._score_nutritional_density(nutrition)
            
            # Balance score (35% weight)
            scores["balance_score"] = self._score_nutritional_balance(nutrition)
            
            # Vitamin/mineral score (25% weight)
            scores["vitamin_mineral_score"] = self._score_micronutrients(nutrition)
            
            # Calculate weighted total
            total_score = (
                scores["nutritional_density"] * 0.40 +
                scores["balance_score"] * 0.35 +
                scores["vitamin_mineral_score"] * 0.25
            )
            
            scores["total_score"] = round(total_score, 2)
        
        return scores
    
    def _calculate_convenience_score(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate convenience score for a recipe."""
        scores = {
            "time_score": 0,
            "ingredient_availability": 0,
            "complexity_score": 0,
            "total_score": 0
        }
        
        # Time score (40% weight)
        ready_time = recipe.get('ready_in_minutes', 60)
        if ready_time <= 15:
            scores["time_score"] = 10
        elif ready_time <= 30:
            scores["time_score"] = 8
        elif ready_time <= 45:
            scores["time_score"] = 6
        else:
            scores["time_score"] = 4
        
        # Ingredient availability (35% weight)
        scores["ingredient_availability"] = self._score_ingredient_availability(recipe, pantry_analysis)
        
        # Complexity score (25% weight)
        scores["complexity_score"] = 10 - self._score_complexity(recipe)  # Inverted
        
        # Calculate weighted total
        total_score = (
            scores["time_score"] * 0.40 +
            scores["ingredient_availability"] * 0.35 +
            scores["complexity_score"] * 0.25
        )
        
        scores["total_score"] = round(total_score, 2)
        
        return scores
    
    def _calculate_ingredient_match_score(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ingredient match score for a recipe."""
        scores = {
            "available_ingredients": 0,
            "expiring_utilization": 0,
            "shopping_efficiency": 0,
            "total_score": 0
        }
        
        # Available ingredients (50% weight)
        scores["available_ingredients"] = self._score_ingredient_availability(recipe, pantry_analysis)
        
        # Expiring item utilization (30% weight)
        scores["expiring_utilization"] = self._score_expiring_utilization(recipe, pantry_analysis)
        
        # Shopping efficiency (20% weight)
        scores["shopping_efficiency"] = self._score_shopping_efficiency(recipe)
        
        # Calculate weighted total
        total_score = (
            scores["available_ingredients"] * 0.50 +
            scores["expiring_utilization"] * 0.30 +
            scores["shopping_efficiency"] * 0.20
        )
        
        scores["total_score"] = round(total_score, 2)
        
        return scores
    
    def _score_pantry_match(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> float:
        """Score how well recipe matches pantry items."""
        if not pantry_analysis:
            return 5.0
        
        # Use existing ingredient match score if available
        if 'ingredient_match_score' in recipe:
            return recipe['ingredient_match_score']
        
        # Calculate based on used vs missed ingredients
        used_ingredients = len(recipe.get('used_ingredients', []))
        missed_ingredients = len(recipe.get('missed_ingredients', []))
        
        if used_ingredients + missed_ingredients == 0:
            return 5.0
        
        match_ratio = used_ingredients / (used_ingredients + missed_ingredients)
        return round(match_ratio * 10, 1)
    
    def _score_nutrition(self, recipe: Dict[str, Any], nutrition_analysis: Dict[str, Any]) -> float:
        """Score nutritional value of recipe."""
        if 'nutrition_score' in recipe:
            return recipe['nutrition_score'].get('overall_score', 5.0)
        
        # Basic nutrition scoring
        nutrition = recipe.get('nutrition', {})
        if not nutrition:
            return 5.0
        
        # Simple scoring based on protein and fiber content
        protein = nutrition.get('protein', 0)
        fiber = nutrition.get('fiber', 0)
        calories = nutrition.get('calories', 0)
        
        if calories == 0:
            return 5.0
        
        protein_score = min(10, (protein / calories) * 100 * 2)  # Protein percentage * 2
        fiber_score = min(10, fiber * 2)  # Fiber grams * 2
        
        return round((protein_score + fiber_score) / 2, 1)
    
    def _score_preferences(self, recipe: Dict[str, Any], preference_analysis: Dict[str, Any]) -> float:
        """Score how well recipe matches user preferences."""
        if 'preference_score' in recipe:
            return recipe['preference_score'].get('total_score', 5.0)
        
        # Basic preference scoring
        return 5.0  # Neutral if no preference data
    
    def _score_complexity(self, recipe: Dict[str, Any]) -> float:
        """Score recipe complexity (higher = more complex)."""
        complexity = 1.0
        
        # Factor in cooking time
        ready_time = recipe.get('ready_in_minutes', 0)
        if ready_time > 60:
            complexity += 3.0
        elif ready_time > 30:
            complexity += 1.5
        
        # Factor in ingredient count
        total_ingredients = len(recipe.get('used_ingredients', [])) + len(recipe.get('missed_ingredients', []))
        if total_ingredients > 15:
            complexity += 2.0
        elif total_ingredients > 10:
            complexity += 1.0
        
        return min(complexity, 10.0)
    
    def _score_nutritional_density(self, nutrition: Dict[str, Any]) -> float:
        """Score nutritional density."""
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        fiber = nutrition.get('fiber', 0)
        
        if calories == 0:
            return 5.0
        
        # Higher protein and fiber relative to calories = better density
        density_score = ((protein * 4 + fiber * 2) / calories) * 100
        return min(10, density_score)
    
    def _score_nutritional_balance(self, nutrition: Dict[str, Any]) -> float:
        """Score nutritional balance."""
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        carbs = nutrition.get('carbohydrates', 0)
        fat = nutrition.get('fat', 0)
        
        if calories == 0:
            return 5.0
        
        # Calculate macro percentages
        protein_pct = (protein * 4 / calories) * 100
        carb_pct = (carbs * 4 / calories) * 100
        fat_pct = (fat * 9 / calories) * 100
        
        # Score based on ideal ranges
        balance_score = 0
        
        if 10 <= protein_pct <= 35:
            balance_score += 3.33
        if 45 <= carb_pct <= 65:
            balance_score += 3.33
        if 20 <= fat_pct <= 35:
            balance_score += 3.33
        
        return round(balance_score, 1)
    
    def _score_micronutrients(self, nutrition: Dict[str, Any]) -> float:
        """Score micronutrient content."""
        # Simple scoring based on available micronutrients
        micronutrients = ['vitamin_c', 'vitamin_d', 'calcium', 'iron', 'potassium']
        score = 0
        
        for nutrient in micronutrients:
            if nutrition.get(nutrient, 0) > 0:
                score += 2
        
        return min(10, score)
    
    def _score_ingredient_availability(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> float:
        """Score ingredient availability."""
        if not pantry_analysis:
            return 5.0
        
        available_ingredients = pantry_analysis.get('available_ingredients', [])
        available_names = [item.get('name', '').lower() for item in available_ingredients]
        
        used_ingredients = recipe.get('used_ingredients', [])
        missed_ingredients = recipe.get('missed_ingredients', [])
        
        if not used_ingredients and not missed_ingredients:
            return 5.0
        
        total_ingredients = len(used_ingredients) + len(missed_ingredients)
        available_count = len(used_ingredients)
        
        if total_ingredients == 0:
            return 5.0
        
        availability_ratio = available_count / total_ingredients
        return round(availability_ratio * 10, 1)
    
    def _score_expiring_utilization(self, recipe: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> float:
        """Score how well recipe uses expiring items."""
        if not pantry_analysis:
            return 5.0
        
        expiring_items = pantry_analysis.get('expiring_soon', [])
        expiring_names = [item.get('name', '').lower() for item in expiring_items]
        
        used_ingredients = recipe.get('used_ingredients', [])
        used_names = [ing.get('name', '').lower() for ing in used_ingredients]
        
        if not expiring_items:
            return 5.0  # No expiring items to utilize
        
        # Count how many expiring items are used
        expiring_used = sum(1 for name in used_names if any(exp in name for exp in expiring_names))
        
        utilization_ratio = expiring_used / len(expiring_items)
        return round(utilization_ratio * 10, 1)
    
    def _score_shopping_efficiency(self, recipe: Dict[str, Any]) -> float:
        """Score shopping efficiency (fewer missing ingredients = better)."""
        missed_ingredients = len(recipe.get('missed_ingredients', []))
        
        if missed_ingredients == 0:
            return 10.0
        elif missed_ingredients <= 2:
            return 8.0
        elif missed_ingredients <= 5:
            return 6.0
        else:
            return 4.0
    
    def _generate_ranking_explanation(self, recipe: Dict[str, Any], comprehensive_score: Dict[str, Any], 
                                    pantry_analysis: Dict[str, Any], nutrition_analysis: Dict[str, Any], 
                                    preference_analysis: Dict[str, Any]) -> str:
        """Generate explanation for recipe ranking."""
        explanations = []
        
        pantry_score = comprehensive_score.get('pantry_match_score', 0)
        nutrition_score = comprehensive_score.get('nutrition_score', 0)
        preference_score = comprehensive_score.get('preference_score', 0)
        complexity_score = comprehensive_score.get('complexity_score', 0)
        
        if pantry_score >= 8:
            explanations.append("Excellent pantry match")
        elif pantry_score >= 6:
            explanations.append("Good pantry match")
        
        if nutrition_score >= 8:
            explanations.append("Highly nutritious")
        elif nutrition_score >= 6:
            explanations.append("Nutritionally balanced")
        
        if preference_score >= 8:
            explanations.append("Perfect preference match")
        elif preference_score >= 6:
            explanations.append("Good preference match")
        
        if complexity_score >= 8:
            explanations.append("Easy to prepare")
        elif complexity_score >= 6:
            explanations.append("Moderately easy")
        
        return "; ".join(explanations) if explanations else "Suitable recipe option"
    
    def _generate_health_explanation(self, recipe: Dict[str, Any], health_score: Dict[str, Any]) -> str:
        """Generate health-focused explanation."""
        explanations = []
        
        if health_score.get('nutritional_density', 0) >= 8:
            explanations.append("Nutrient-dense")
        if health_score.get('balance_score', 0) >= 8:
            explanations.append("Well-balanced")
        if health_score.get('vitamin_mineral_score', 0) >= 8:
            explanations.append("Rich in vitamins and minerals")
        
        return "; ".join(explanations) if explanations else "Healthy option"
    
    def _generate_convenience_explanation(self, recipe: Dict[str, Any], convenience_score: Dict[str, Any]) -> str:
        """Generate convenience-focused explanation."""
        explanations = []
        
        if convenience_score.get('time_score', 0) >= 8:
            explanations.append("Quick to prepare")
        if convenience_score.get('ingredient_availability', 0) >= 8:
            explanations.append("Most ingredients available")
        if convenience_score.get('complexity_score', 0) >= 8:
            explanations.append("Simple preparation")
        
        return "; ".join(explanations) if explanations else "Convenient option"
    
    def _generate_ingredient_explanation(self, recipe: Dict[str, Any], ingredient_score: Dict[str, Any], 
                                       pantry_analysis: Dict[str, Any]) -> str:
        """Generate ingredient-focused explanation."""
        explanations = []
        
        if ingredient_score.get('available_ingredients', 0) >= 8:
            explanations.append("Most ingredients available")
        if ingredient_score.get('expiring_utilization', 0) >= 8:
            explanations.append("Uses expiring items")
        if ingredient_score.get('shopping_efficiency', 0) >= 8:
            explanations.append("Minimal shopping needed")
        
        return "; ".join(explanations) if explanations else "Good ingredient match"
    
    def _generate_final_recommendations(self, scored_recipes: List[Dict[str, Any]], user_id: int) -> List[str]:
        """Generate final recommendations based on ranked recipes."""
        recommendations = []
        
        if not scored_recipes:
            return ["No recipes available for recommendations"]
        
        # Top recommendations
        top_recipes = scored_recipes[:3]
        if top_recipes:
            top_names = [recipe.get('name', 'Unknown') for recipe in top_recipes]
            recommendations.append(f"Top recommendations: {', '.join(top_names)}")
        
        # Score-based insights
        top_score = scored_recipes[0].get('comprehensive_score', {}).get('total_score', 0)
        if top_score >= 8:
            recommendations.append("Excellent matches found - all factors align well")
        elif top_score >= 6:
            recommendations.append("Good matches found - most factors align")
        else:
            recommendations.append("Suitable options available - consider ingredient adjustments")
        
        # Variety recommendations
        if len(scored_recipes) > 10:
            recommendations.append("Great variety available - try different recipes throughout the week")
        
        return recommendations
    
    def _generate_health_recommendations(self, scored_recipes: List[Dict[str, Any]]) -> List[str]:
        """Generate health-focused recommendations."""
        recommendations = []
        
        if not scored_recipes:
            return ["No recipes available for health recommendations"]
        
        # Analyze health scores
        high_health_recipes = [r for r in scored_recipes if r.get('health_score', {}).get('total_score', 0) >= 8]
        
        if high_health_recipes:
            recommendations.append(f"Found {len(high_health_recipes)} highly nutritious recipes")
        
        # Nutritional balance recommendations
        balanced_recipes = [r for r in scored_recipes if r.get('health_score', {}).get('balance_score', 0) >= 8]
        if balanced_recipes:
            recommendations.append(f"{len(balanced_recipes)} recipes are well-balanced nutritionally")
        
        return recommendations
    
    def _generate_convenience_recommendations(self, scored_recipes: List[Dict[str, Any]]) -> List[str]:
        """Generate convenience-focused recommendations."""
        recommendations = []
        
        if not scored_recipes:
            return ["No recipes available for convenience recommendations"]
        
        # Quick recipes
        quick_recipes = [r for r in scored_recipes if r.get('convenience_score', {}).get('time_score', 0) >= 8]
        if quick_recipes:
            recommendations.append(f"Found {len(quick_recipes)} quick recipes (≤30 minutes)")
        
        # Easy recipes
        easy_recipes = [r for r in scored_recipes if r.get('convenience_score', {}).get('complexity_score', 0) >= 8]
        if easy_recipes:
            recommendations.append(f"{len(easy_recipes)} recipes are easy to prepare")
        
        return recommendations
    
    def _generate_ingredient_recommendations(self, scored_recipes: List[Dict[str, Any]], 
                                          pantry_analysis: Dict[str, Any]) -> List[str]:
        """Generate ingredient-focused recommendations."""
        recommendations = []
        
        if not scored_recipes:
            return ["No recipes available for ingredient recommendations"]
        
        # High availability recipes
        high_availability = [r for r in scored_recipes if r.get('ingredient_match_score', {}).get('available_ingredients', 0) >= 8]
        if high_availability:
            recommendations.append(f"Found {len(high_availability)} recipes with most ingredients available")
        
        # Expiring item utilization
        expiring_recipes = [r for r in scored_recipes if r.get('ingredient_match_score', {}).get('expiring_utilization', 0) >= 8]
        if expiring_recipes:
            recommendations.append(f"{len(expiring_recipes)} recipes help use expiring items")
        
        return recommendations
    
    def _create_recommendation_tiers(self, scored_recipes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create recommendation tiers based on scores."""
        tiers = {
            "highly_recommended": [],
            "recommended": [],
            "suitable": [],
            "consider": []
        }
        
        for recipe in scored_recipes:
            score = recipe.get('comprehensive_score', {}).get('total_score', 0)
            
            if score >= 8:
                tiers["highly_recommended"].append(recipe)
            elif score >= 6:
                tiers["recommended"].append(recipe)
            elif score >= 4:
                tiers["suitable"].append(recipe)
            else:
                tiers["consider"].append(recipe)
        
        return tiers
    
    def _combine_ranking_strategies(self, balanced_result: Dict[str, Any], health_result: Dict[str, Any], 
                                  convenience_result: Dict[str, Any], ingredient_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple ranking strategies."""
        # This is a simplified combination - in practice, you'd want more sophisticated merging
        combined_rankings = {
            "overall_best": balanced_result.get('ranked_recipes', [])[:5],
            "healthiest": health_result.get('ranked_recipes', [])[:5],
            "most_convenient": convenience_result.get('ranked_recipes', [])[:5],
            "best_ingredient_match": ingredient_result.get('ranked_recipes', [])[:5]
        }
        
        return combined_rankings


def create_ranking_agent() -> RankingAgent:
    """Create and return a RankingAgent instance."""
    return RankingAgent()