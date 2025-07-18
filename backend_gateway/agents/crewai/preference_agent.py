"""Preference Agent for managing user preferences and filtering recipes."""

from typing import Dict, List, Any, Optional
import logging
from crewai import Agent
from langchain_openai import ChatOpenAI

from backend_gateway.tools.preference_tool import create_preference_tool
from backend_gateway.tools.database_tool import create_database_tool
from backend_gateway.core.config_utils import get_openai_api_key

logger = logging.getLogger(__name__)


class PreferenceAgent:
    """Agent specialized in managing user preferences and filtering recipes."""
    
    def __init__(self):
        """Initialize the Preference agent."""
        self.preference_tool = create_preference_tool()
        self.database_tool = create_database_tool()
        
        # Initialize OpenAI LLM
        api_key = get_openai_api_key()
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0.1)
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Preference Specialist",
            goal="Understand and apply user preferences, dietary restrictions, and allergens to filter and score recipes for personalized recommendations",
            backstory=(
                "You are a skilled preference analyst with expertise in dietary requirements, "
                "cultural food preferences, and allergen management. You excel at understanding "
                "complex dietary needs and translating them into actionable recipe filters and "
                "scoring systems. Your knowledge spans various dietary approaches, cuisine types, "
                "and allergen considerations, helping users find recipes that perfectly match "
                "their personal preferences and safety requirements."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def apply_preferences(self, user_id: int, filter_type: str = "comprehensive", **kwargs) -> Dict[str, Any]:
        """
        Apply user preferences to filter and score recipes.
        
        Args:
            user_id: The user's ID
            filter_type: Type of filtering (dietary, allergen, cuisine, comprehensive)
            **kwargs: Additional parameters for filtering
            
        Returns:
            Dict containing filtered and scored recipes
        """
        try:
            logger.info(f"PreferenceAgent applying preferences for user {user_id}, filter: {filter_type}")
            
            if filter_type == "dietary":
                return self._apply_dietary_preferences(user_id, **kwargs)
            elif filter_type == "allergen":
                return self._apply_allergen_preferences(user_id, **kwargs)
            elif filter_type == "cuisine":
                return self._apply_cuisine_preferences(user_id, **kwargs)
            elif filter_type == "comprehensive":
                return self._apply_comprehensive_preferences(user_id, **kwargs)
            elif filter_type == "score":
                return self._score_recipes_by_preferences(user_id, **kwargs)
            elif filter_type == "analyze":
                return self._analyze_user_preferences(user_id, **kwargs)
            else:
                return self._apply_comprehensive_preferences(user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"PreferenceAgent error: {str(e)}")
            return {"error": f"Preference application failed: {str(e)}"}
    
    def _apply_dietary_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply dietary restriction preferences."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided for dietary filtering"}
        
        # Apply dietary filters
        filter_result = self.preference_tool._run(
            "apply_dietary_filters",
            user_id=user_id,
            recipes=recipes
        )
        
        if "error" in filter_result:
            return filter_result
        
        # Generate dietary insights
        dietary_insights = self._generate_dietary_insights(filter_result)
        
        # Provide recommendations for filtered out recipes
        filtered_out_advice = self._generate_filtered_out_advice(filter_result.get('filtered_out', []))
        
        return {
            "filter_type": "dietary",
            "user_id": user_id,
            "original_count": filter_result.get('original_count', 0),
            "filtered_count": filter_result.get('filtered_count', 0),
            "dietary_restrictions": filter_result.get('dietary_restrictions', []),
            "filtered_recipes": filter_result.get('filtered_recipes', []),
            "filtered_out": filter_result.get('filtered_out', []),
            "dietary_insights": dietary_insights,
            "filtered_out_advice": filtered_out_advice
        }
    
    def _apply_allergen_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply allergen preferences."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided for allergen filtering"}
        
        # Apply allergen filters
        filter_result = self.preference_tool._run(
            "apply_allergen_filters",
            user_id=user_id,
            recipes=recipes
        )
        
        if "error" in filter_result:
            return filter_result
        
        # Generate allergen safety insights
        allergen_insights = self._generate_allergen_insights(filter_result)
        
        # Provide substitution suggestions for filtered recipes
        substitution_suggestions = self._generate_substitution_suggestions(filter_result.get('filtered_out', []))
        
        return {
            "filter_type": "allergen",
            "user_id": user_id,
            "original_count": filter_result.get('original_count', 0),
            "filtered_count": filter_result.get('filtered_count', 0),
            "allergens": filter_result.get('allergens', []),
            "safe_recipes": filter_result.get('filtered_recipes', []),
            "unsafe_recipes": filter_result.get('filtered_out', []),
            "allergen_insights": allergen_insights,
            "substitution_suggestions": substitution_suggestions
        }
    
    def _apply_cuisine_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply cuisine preferences."""
        recipes = kwargs.get('recipes', [])
        preference_weight = kwargs.get('preference_weight', 1.0)
        
        if not recipes:
            return {"error": "No recipes provided for cuisine filtering"}
        
        # Apply cuisine filters (scoring)
        filter_result = self.preference_tool._run(
            "apply_cuisine_filters",
            user_id=user_id,
            recipes=recipes,
            preference_weight=preference_weight
        )
        
        if "error" in filter_result:
            return filter_result
        
        # Generate cuisine insights
        cuisine_insights = self._generate_cuisine_insights(filter_result)
        
        # Categorize recipes by cuisine match
        cuisine_categories = self._categorize_by_cuisine_match(filter_result.get('scored_recipes', []))
        
        return {
            "filter_type": "cuisine",
            "user_id": user_id,
            "cuisine_preferences": filter_result.get('cuisine_preferences', []),
            "scored_recipes": filter_result.get('scored_recipes', []),
            "cuisine_insights": cuisine_insights,
            "cuisine_categories": cuisine_categories,
            "preference_weight": preference_weight
        }
    
    def _apply_comprehensive_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply all user preferences comprehensively."""
        recipes = kwargs.get('recipes', [])
        strict_mode = kwargs.get('strict_mode', True)
        
        if not recipes:
            return {"error": "No recipes provided for comprehensive filtering"}
        
        # Apply comprehensive filters
        filter_result = self.preference_tool._run(
            "filter_recipes_by_preferences",
            user_id=user_id,
            recipes=recipes,
            strict_mode=strict_mode
        )
        
        if "error" in filter_result:
            return filter_result
        
        # Generate comprehensive insights
        comprehensive_insights = self._generate_comprehensive_insights(filter_result, user_id)
        
        # Score final recipes
        scored_recipes = self._score_filtered_recipes(filter_result.get('filtered_recipes', []), user_id)
        
        # Generate personalized recommendations
        personal_recommendations = self._generate_personalized_recommendations(scored_recipes, user_id)
        
        return {
            "filter_type": "comprehensive",
            "user_id": user_id,
            "original_count": filter_result.get('original_count', 0),
            "final_count": filter_result.get('final_count', 0),
            "filters_applied": filter_result.get('filters_applied', {}),
            "filtered_recipes": scored_recipes,
            "comprehensive_insights": comprehensive_insights,
            "personal_recommendations": personal_recommendations,
            "strict_mode": strict_mode
        }
    
    def _score_recipes_by_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Score recipes based on user preferences."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided for preference scoring"}
        
        scored_recipes = []
        
        for recipe in recipes:
            # Score individual recipe
            score_result = self.preference_tool._run(
                "score_preferences",
                user_id=user_id,
                recipe=recipe
            )
            
            if "error" not in score_result:
                recipe_copy = recipe.copy()
                recipe_copy['preference_score'] = score_result.get('preference_scores', {})
                recipe_copy['recommendation_level'] = score_result.get('recommendation_level', 'Suitable')
                scored_recipes.append(recipe_copy)
        
        # Sort by total preference score
        scored_recipes.sort(
            key=lambda x: x.get('preference_score', {}).get('total_score', 0), 
            reverse=True
        )
        
        # Generate scoring insights
        scoring_insights = self._generate_scoring_insights(scored_recipes)
        
        return {
            "filter_type": "score",
            "user_id": user_id,
            "scored_recipes": scored_recipes,
            "scoring_insights": scoring_insights,
            "recommendation_tiers": self._categorize_by_recommendation_level(scored_recipes)
        }
    
    def _analyze_user_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Analyze and provide insights about user preferences."""
        # Get user preferences
        prefs_result = self.preference_tool._run("get_preferences", user_id=user_id)
        
        if "error" in prefs_result:
            return prefs_result
        
        # Analyze preference patterns
        preference_analysis = self._analyze_preference_patterns(prefs_result)
        
        # Generate preference insights
        preference_insights = self._generate_preference_insights(prefs_result)
        
        # Suggest preference improvements
        improvement_suggestions = self._suggest_preference_improvements(prefs_result)
        
        return {
            "filter_type": "analyze",
            "user_id": user_id,
            "user_preferences": prefs_result,
            "preference_analysis": preference_analysis,
            "preference_insights": preference_insights,
            "improvement_suggestions": improvement_suggestions
        }
    
    def _generate_dietary_insights(self, filter_result: Dict[str, Any]) -> List[str]:
        """Generate insights about dietary filtering."""
        insights = []
        
        dietary_restrictions = filter_result.get('dietary_restrictions', [])
        original_count = filter_result.get('original_count', 0)
        filtered_count = filter_result.get('filtered_count', 0)
        
        if dietary_restrictions:
            insights.append(f"Applied dietary restrictions: {', '.join(dietary_restrictions)}")
        
        if original_count > 0:
            filter_rate = (original_count - filtered_count) / original_count * 100
            insights.append(f"Filtered out {filter_rate:.1f}% of recipes due to dietary restrictions")
        
        if filtered_count == 0:
            insights.append("No recipes match your dietary restrictions - consider broadening your search")
        elif filtered_count < 3:
            insights.append("Limited recipe options - you might want to explore recipe modifications")
        
        return insights
    
    def _generate_filtered_out_advice(self, filtered_out: List[Dict[str, Any]]) -> List[str]:
        """Generate advice for recipes that were filtered out."""
        advice = []
        
        if not filtered_out:
            return ["All recipes met your dietary requirements!"]
        
        # Analyze common reasons for filtering
        common_reasons = {}
        for item in filtered_out:
            reasons = item.get('reasons', [])
            for reason in reasons:
                common_reasons[reason] = common_reasons.get(reason, 0) + 1
        
        # Generate specific advice
        for reason, count in common_reasons.items():
            if reason == 'Contains meat':
                advice.append(f"{count} recipes contain meat - consider vegetarian substitutes")
            elif reason == 'Contains dairy':
                advice.append(f"{count} recipes contain dairy - try plant-based alternatives")
            elif reason == 'Contains gluten':
                advice.append(f"{count} recipes contain gluten - look for gluten-free flour substitutes")
        
        return advice
    
    def _generate_allergen_insights(self, filter_result: Dict[str, Any]) -> List[str]:
        """Generate insights about allergen filtering."""
        insights = []
        
        allergens = filter_result.get('allergens', [])
        original_count = filter_result.get('original_count', 0)
        filtered_count = filter_result.get('filtered_count', 0)
        
        if allergens:
            insights.append(f"Filtered for allergens: {', '.join(allergens)}")
        
        if original_count > 0:
            safety_rate = filtered_count / original_count * 100
            insights.append(f"{safety_rate:.1f}% of recipes are safe for your allergen restrictions")
        
        if filtered_count == original_count:
            insights.append("All recipes are safe for your allergen restrictions")
        
        return insights
    
    def _generate_substitution_suggestions(self, filtered_out: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate substitution suggestions for filtered recipes."""
        suggestions = {}
        
        for item in filtered_out:
            recipe_name = item.get('recipe', {}).get('name', 'Unknown Recipe')
            allergens_found = item.get('allergens_found', [])
            
            recipe_suggestions = []
            for allergen in allergens_found:
                allergen_lower = allergen.lower()
                if 'nuts' in allergen_lower:
                    recipe_suggestions.append("Replace nuts with seeds (sunflower, pumpkin)")
                elif 'dairy' in allergen_lower:
                    recipe_suggestions.append("Use plant-based milk, cheese, or yogurt alternatives")
                elif 'eggs' in allergen_lower:
                    recipe_suggestions.append("Try egg replacers like flax eggs or aquafaba")
                elif 'gluten' in allergen_lower:
                    recipe_suggestions.append("Use gluten-free flour blends or almond flour")
            
            if recipe_suggestions:
                suggestions[recipe_name] = recipe_suggestions
        
        return suggestions
    
    def _generate_cuisine_insights(self, filter_result: Dict[str, Any]) -> List[str]:
        """Generate insights about cuisine preferences."""
        insights = []
        
        cuisine_preferences = filter_result.get('cuisine_preferences', [])
        scored_recipes = filter_result.get('scored_recipes', [])
        
        if cuisine_preferences:
            insights.append(f"Your preferred cuisines: {', '.join(cuisine_preferences)}")
        
        # Analyze scoring results
        high_score_count = sum(1 for recipe in scored_recipes if recipe.get('cuisine_preference_score', 0) > 0)
        
        if high_score_count > 0:
            insights.append(f"{high_score_count} recipes match your cuisine preferences")
        else:
            insights.append("No recipes match your specific cuisine preferences - showing general results")
        
        return insights
    
    def _categorize_by_cuisine_match(self, scored_recipes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize recipes by cuisine preference match."""
        categories = {
            "perfect_match": [],
            "good_match": [],
            "general": []
        }
        
        for recipe in scored_recipes:
            score = recipe.get('cuisine_preference_score', 0)
            
            if score >= 2:
                categories["perfect_match"].append(recipe)
            elif score >= 1:
                categories["good_match"].append(recipe)
            else:
                categories["general"].append(recipe)
        
        return categories
    
    def _generate_comprehensive_insights(self, filter_result: Dict[str, Any], user_id: int) -> List[str]:
        """Generate comprehensive insights about all preference filtering."""
        insights = []
        
        original_count = filter_result.get('original_count', 0)
        final_count = filter_result.get('final_count', 0)
        filters_applied = filter_result.get('filters_applied', {})
        
        # Overall filtering insights
        if original_count > 0:
            retention_rate = final_count / original_count * 100
            insights.append(f"Found {final_count} recipes ({retention_rate:.1f}% of original) matching all your preferences")
        
        # Specific filter insights
        applied_filters = [filter_name for filter_name, applied in filters_applied.items() if applied]
        if applied_filters:
            insights.append(f"Applied filters: {', '.join(applied_filters)}")
        
        # Recommendation based on results
        if final_count == 0:
            insights.append("No recipes match all preferences - consider adjusting some restrictions")
        elif final_count < 3:
            insights.append("Limited options found - you might want to explore similar recipes")
        elif final_count > 20:
            insights.append("Many great options available - recipes are sorted by preference match")
        
        return insights
    
    def _score_filtered_recipes(self, filtered_recipes: List[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
        """Score filtered recipes by preference match."""
        scored_recipes = []
        
        for recipe in filtered_recipes:
            score_result = self.preference_tool._run(
                "score_preferences",
                user_id=user_id,
                recipe=recipe
            )
            
            recipe_copy = recipe.copy()
            if "error" not in score_result:
                recipe_copy['preference_score'] = score_result.get('preference_scores', {})
                recipe_copy['recommendation_level'] = score_result.get('recommendation_level', 'Suitable')
            
            scored_recipes.append(recipe_copy)
        
        # Sort by total preference score
        scored_recipes.sort(
            key=lambda x: x.get('preference_score', {}).get('total_score', 0), 
            reverse=True
        )
        
        return scored_recipes
    
    def _generate_personalized_recommendations(self, scored_recipes: List[Dict[str, Any]], user_id: int) -> List[str]:
        """Generate personalized recommendations based on scored recipes."""
        recommendations = []
        
        if not scored_recipes:
            return ["No recipes available for personalized recommendations"]
        
        # Top-rated recipes
        top_recipes = scored_recipes[:3]
        if top_recipes:
            top_names = [recipe.get('name', 'Unknown') for recipe in top_recipes]
            recommendations.append(f"Highly recommended: {', '.join(top_names)}")
        
        # Analyze recommendation levels
        highly_recommended = [r for r in scored_recipes if r.get('recommendation_level') == 'Highly Recommended']
        if highly_recommended:
            recommendations.append(f"You have {len(highly_recommended)} highly recommended recipes")
        
        # General advice
        if len(scored_recipes) > 10:
            recommendations.append("Great variety available - try different recipes throughout the week")
        
        return recommendations
    
    def _generate_scoring_insights(self, scored_recipes: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about recipe scoring."""
        insights = []
        
        if not scored_recipes:
            return ["No recipes available for scoring insights"]
        
        # Analyze score distribution
        scores = [recipe.get('preference_score', {}).get('total_score', 0) for recipe in scored_recipes]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            
            insights.append(f"Average preference score: {avg_score:.1f}")
            insights.append(f"Best match score: {max_score:.1f}")
        
        # Recommendation level distribution
        levels = {}
        for recipe in scored_recipes:
            level = recipe.get('recommendation_level', 'Suitable')
            levels[level] = levels.get(level, 0) + 1
        
        for level, count in levels.items():
            insights.append(f"{count} recipes are {level}")
        
        return insights
    
    def _categorize_by_recommendation_level(self, scored_recipes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize recipes by recommendation level."""
        categories = {
            "Highly Recommended": [],
            "Recommended": [],
            "Suitable": [],
            "Acceptable": [],
            "Not Recommended": []
        }
        
        for recipe in scored_recipes:
            level = recipe.get('recommendation_level', 'Suitable')
            if level in categories:
                categories[level].append(recipe)
        
        return categories
    
    def _analyze_preference_patterns(self, prefs_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in user preferences."""
        analysis = {
            "preference_complexity": "Simple",
            "dietary_approach": "Flexible",
            "cuisine_diversity": "Moderate",
            "allergen_considerations": "None"
        }
        
        dietary_restrictions = prefs_result.get('dietary_restrictions', [])
        allergens = prefs_result.get('allergens', [])
        cuisine_preferences = prefs_result.get('cuisine_preferences', [])
        
        # Analyze complexity
        total_restrictions = len(dietary_restrictions) + len(allergens)
        if total_restrictions > 5:
            analysis["preference_complexity"] = "Complex"
        elif total_restrictions > 2:
            analysis["preference_complexity"] = "Moderate"
        
        # Analyze dietary approach
        if dietary_restrictions:
            if len(dietary_restrictions) > 2:
                analysis["dietary_approach"] = "Restrictive"
            else:
                analysis["dietary_approach"] = "Selective"
        
        # Analyze cuisine diversity
        if len(cuisine_preferences) > 5:
            analysis["cuisine_diversity"] = "High"
        elif len(cuisine_preferences) == 0:
            analysis["cuisine_diversity"] = "Open"
        
        # Analyze allergen considerations
        if allergens:
            analysis["allergen_considerations"] = "Active"
        
        return analysis
    
    def _generate_preference_insights(self, prefs_result: Dict[str, Any]) -> List[str]:
        """Generate insights about user preferences."""
        insights = []
        
        has_preferences = prefs_result.get('has_preferences', False)
        
        if not has_preferences:
            insights.append("No specific preferences set - you'll see all recipe options")
            return insights
        
        dietary_restrictions = prefs_result.get('dietary_restrictions', [])
        allergens = prefs_result.get('allergens', [])
        cuisine_preferences = prefs_result.get('cuisine_preferences', [])
        
        if dietary_restrictions:
            insights.append(f"Following dietary approach: {', '.join(dietary_restrictions)}")
        
        if allergens:
            insights.append(f"Avoiding allergens: {', '.join(allergens)}")
        
        if cuisine_preferences:
            insights.append(f"Preferred cuisines: {', '.join(cuisine_preferences)}")
        
        return insights
    
    def _suggest_preference_improvements(self, prefs_result: Dict[str, Any]) -> List[str]:
        """Suggest improvements to user preferences."""
        suggestions = []
        
        has_preferences = prefs_result.get('has_preferences', False)
        
        if not has_preferences:
            suggestions.append("Consider setting dietary preferences for more personalized recommendations")
            suggestions.append("Add cuisine preferences to discover new recipe styles")
            return suggestions
        
        dietary_restrictions = prefs_result.get('dietary_restrictions', [])
        allergens = prefs_result.get('allergens', [])
        cuisine_preferences = prefs_result.get('cuisine_preferences', [])
        
        if not cuisine_preferences:
            suggestions.append("Add cuisine preferences to get more targeted recipe suggestions")
        
        if len(dietary_restrictions) > 3:
            suggestions.append("Consider if all dietary restrictions are necessary for more recipe options")
        
        if not allergens and not dietary_restrictions:
            suggestions.append("Your preferences are very open - great for discovering new recipes!")
        
        return suggestions


def create_preference_agent() -> PreferenceAgent:
    """Create and return a PreferenceAgent instance."""
    return PreferenceAgent()