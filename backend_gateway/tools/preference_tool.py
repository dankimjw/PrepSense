"""User preference tool for CrewAI agents."""

from typing import Dict, List, Any, Optional
import logging
# from crewai_tools import BaseTool  # Not available in CrewAI 0.5.0

from backend_gateway.tools.database_tool import create_database_tool

logger = logging.getLogger(__name__)


class PreferenceTool:
    """Tool for managing and applying user preferences."""
    
    name: str = "preference_tool"
    description: str = (
        "A tool for managing user preferences including dietary restrictions, "
        "allergens, cuisine preferences, and applying them to recipe recommendations."
    )
    
    def __init__(self):
        self.db_tool = create_database_tool()
    
    def _run(self, action: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Execute a preference management action.
        
        Args:
            action: The action to perform (get_preferences, apply_filters, etc.)
            user_id: The user ID
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the results
        """
        try:
            if action == "get_preferences":
                return self._get_user_preferences(user_id)
            elif action == "apply_dietary_filters":
                return self._apply_dietary_filters(user_id, **kwargs)
            elif action == "apply_allergen_filters":
                return self._apply_allergen_filters(user_id, **kwargs)
            elif action == "apply_cuisine_filters":
                return self._apply_cuisine_filters(user_id, **kwargs)
            elif action == "score_preferences":
                return self._score_recipe_preferences(user_id, **kwargs)
            elif action == "filter_recipes":
                return self._filter_recipes_by_preferences(user_id, **kwargs)
            elif action == "get_preference_matches":
                return self._get_preference_matches(user_id, **kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Preference tool error: {str(e)}")
            return {"error": f"Preference processing failed: {str(e)}"}
    
    def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences from database."""
        prefs_data = self.db_tool._run("user_preferences", user_id)
        
        if "error" in prefs_data:
            return prefs_data
        
        preferences = prefs_data.get("preferences", {})
        
        return {
            "user_id": user_id,
            "dietary_restrictions": preferences.get('dietary_preference', []),
            "allergens": preferences.get('allergens', []),
            "cuisine_preferences": preferences.get('cuisine_preference', []),
            "has_preferences": bool(preferences.get('dietary_preference') or 
                                   preferences.get('allergens') or 
                                   preferences.get('cuisine_preference'))
        }
    
    def _apply_dietary_filters(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply dietary restriction filters."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided"}
        
        # Get user preferences
        prefs = self._get_user_preferences(user_id)
        
        if "error" in prefs:
            return prefs
        
        dietary_restrictions = prefs.get('dietary_restrictions', [])
        
        if not dietary_restrictions:
            return {
                "user_id": user_id,
                "filtered_recipes": recipes,
                "filter_applied": False,
                "message": "No dietary restrictions to apply"
            }
        
        filtered_recipes = []
        filtered_out = []
        
        for recipe in recipes:
            is_compatible = True
            incompatible_reasons = []
            
            # Check recipe dietary tags
            recipe_diets = recipe.get('dietary_tags', []) or recipe.get('diets', [])
            recipe_diets_lower = [diet.lower() for diet in recipe_diets]
            
            for restriction in dietary_restrictions:
                restriction_lower = restriction.lower()
                
                if restriction_lower == 'vegetarian':
                    if not self._is_vegetarian_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('Contains meat')
                elif restriction_lower == 'vegan':
                    if not self._is_vegan_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('Contains animal products')
                elif restriction_lower == 'gluten-free':
                    if not self._is_gluten_free_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('Contains gluten')
                elif restriction_lower == 'dairy-free':
                    if not self._is_dairy_free_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('Contains dairy')
                elif restriction_lower == 'keto':
                    if not self._is_keto_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('High carb content')
                elif restriction_lower == 'low-sodium':
                    if not self._is_low_sodium_compatible(recipe):
                        is_compatible = False
                        incompatible_reasons.append('High sodium content')
            
            if is_compatible:
                filtered_recipes.append(recipe)
            else:
                filtered_out.append({
                    'recipe': recipe,
                    'reasons': incompatible_reasons
                })
        
        return {
            "user_id": user_id,
            "dietary_restrictions": dietary_restrictions,
            "filtered_recipes": filtered_recipes,
            "filtered_out": filtered_out,
            "filter_applied": True,
            "original_count": len(recipes),
            "filtered_count": len(filtered_recipes)
        }
    
    def _apply_allergen_filters(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply allergen filters."""
        recipes = kwargs.get('recipes', [])
        
        if not recipes:
            return {"error": "No recipes provided"}
        
        # Get user preferences
        prefs = self._get_user_preferences(user_id)
        
        if "error" in prefs:
            return prefs
        
        allergens = prefs.get('allergens', [])
        
        if not allergens:
            return {
                "user_id": user_id,
                "filtered_recipes": recipes,
                "filter_applied": False,
                "message": "No allergens to filter"
            }
        
        filtered_recipes = []
        filtered_out = []
        
        for recipe in recipes:
            contains_allergens = []
            
            # Check ingredients for allergens
            ingredients = recipe.get('ingredients', [])
            ingredients_text = ' '.join(ingredients).lower()
            
            for allergen in allergens:
                if self._contains_allergen(ingredients_text, allergen):
                    contains_allergens.append(allergen)
            
            if not contains_allergens:
                filtered_recipes.append(recipe)
            else:
                filtered_out.append({
                    'recipe': recipe,
                    'allergens_found': contains_allergens
                })
        
        return {
            "user_id": user_id,
            "allergens": allergens,
            "filtered_recipes": filtered_recipes,
            "filtered_out": filtered_out,
            "filter_applied": True,
            "original_count": len(recipes),
            "filtered_count": len(filtered_recipes)
        }
    
    def _apply_cuisine_filters(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Apply cuisine preference filters."""
        recipes = kwargs.get('recipes', [])
        preference_weight = kwargs.get('preference_weight', 1.0)
        
        if not recipes:
            return {"error": "No recipes provided"}
        
        # Get user preferences
        prefs = self._get_user_preferences(user_id)
        
        if "error" in prefs:
            return prefs
        
        cuisine_preferences = prefs.get('cuisine_preferences', [])
        
        if not cuisine_preferences:
            return {
                "user_id": user_id,
                "filtered_recipes": recipes,
                "filter_applied": False,
                "message": "No cuisine preferences to apply"
            }
        
        # Score recipes based on cuisine preferences
        scored_recipes = []
        
        for recipe in recipes:
            recipe_cuisines = recipe.get('cuisines', []) or recipe.get('cuisine_type', [])
            if isinstance(recipe_cuisines, str):
                recipe_cuisines = [recipe_cuisines]
            
            # Calculate cuisine preference score
            cuisine_score = 0
            matched_cuisines = []
            
            for cuisine in recipe_cuisines:
                cuisine_lower = cuisine.lower()
                for pref_cuisine in cuisine_preferences:
                    if pref_cuisine.lower() in cuisine_lower or cuisine_lower in pref_cuisine.lower():
                        cuisine_score += preference_weight
                        matched_cuisines.append(cuisine)
            
            # Add preference score to recipe
            recipe_copy = recipe.copy()
            recipe_copy['cuisine_preference_score'] = cuisine_score
            recipe_copy['matched_cuisines'] = matched_cuisines
            
            scored_recipes.append(recipe_copy)
        
        # Sort by cuisine preference score
        scored_recipes.sort(key=lambda x: x.get('cuisine_preference_score', 0), reverse=True)
        
        return {
            "user_id": user_id,
            "cuisine_preferences": cuisine_preferences,
            "scored_recipes": scored_recipes,
            "filter_applied": True,
            "preference_weight": preference_weight
        }
    
    def _score_recipe_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Score a recipe based on user preferences."""
        recipe = kwargs.get('recipe', {})
        
        if not recipe:
            return {"error": "No recipe provided"}
        
        # Get user preferences
        prefs = self._get_user_preferences(user_id)
        
        if "error" in prefs:
            return prefs
        
        scores = {
            'dietary_score': 0,
            'cuisine_score': 0,
            'allergen_penalty': 0,
            'total_score': 0
        }
        
        # Score dietary compatibility
        dietary_restrictions = prefs.get('dietary_restrictions', [])
        if dietary_restrictions:
            dietary_result = self._apply_dietary_filters(user_id, recipes=[recipe])
            if not dietary_result.get('error') and dietary_result.get('filtered_recipes'):
                scores['dietary_score'] = 10  # Compatible
            else:
                scores['dietary_score'] = 0  # Not compatible
        else:
            scores['dietary_score'] = 5  # Neutral
        
        # Score cuisine preference
        cuisine_preferences = prefs.get('cuisine_preferences', [])
        if cuisine_preferences:
            cuisine_result = self._apply_cuisine_filters(user_id, recipes=[recipe])
            if not cuisine_result.get('error') and cuisine_result.get('scored_recipes'):
                scores['cuisine_score'] = cuisine_result['scored_recipes'][0].get('cuisine_preference_score', 0)
        
        # Check allergen penalties
        allergens = prefs.get('allergens', [])
        if allergens:
            allergen_result = self._apply_allergen_filters(user_id, recipes=[recipe])
            if not allergen_result.get('error') and not allergen_result.get('filtered_recipes'):
                scores['allergen_penalty'] = -20  # Contains allergens
        
        # Calculate total score
        scores['total_score'] = scores['dietary_score'] + scores['cuisine_score'] + scores['allergen_penalty']
        
        return {
            "user_id": user_id,
            "recipe_name": recipe.get('name', 'Unknown Recipe'),
            "preference_scores": scores,
            "recommendation_level": self._get_recommendation_level(scores['total_score'])
        }
    
    def _filter_recipes_by_preferences(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Filter recipes by all user preferences."""
        recipes = kwargs.get('recipes', [])
        strict_mode = kwargs.get('strict_mode', True)
        
        if not recipes:
            return {"error": "No recipes provided"}
        
        # Apply dietary filters
        dietary_result = self._apply_dietary_filters(user_id, recipes=recipes)
        if dietary_result.get('error'):
            return dietary_result
        
        filtered_recipes = dietary_result.get('filtered_recipes', recipes)
        
        # Apply allergen filters
        allergen_result = self._apply_allergen_filters(user_id, recipes=filtered_recipes)
        if allergen_result.get('error'):
            return allergen_result
        
        filtered_recipes = allergen_result.get('filtered_recipes', filtered_recipes)
        
        # Apply cuisine preferences (scoring, not filtering)
        cuisine_result = self._apply_cuisine_filters(user_id, recipes=filtered_recipes)
        if cuisine_result.get('error'):
            return cuisine_result
        
        final_recipes = cuisine_result.get('scored_recipes', filtered_recipes)
        
        return {
            "user_id": user_id,
            "filtered_recipes": final_recipes,
            "original_count": len(recipes),
            "final_count": len(final_recipes),
            "filters_applied": {
                "dietary": dietary_result.get('filter_applied', False),
                "allergen": allergen_result.get('filter_applied', False),
                "cuisine": cuisine_result.get('filter_applied', False)
            }
        }
    
    def _get_preference_matches(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Get preference matches for a recipe."""
        recipe = kwargs.get('recipe', {})
        
        if not recipe:
            return {"error": "No recipe provided"}
        
        # Get user preferences
        prefs = self._get_user_preferences(user_id)
        
        if "error" in prefs:
            return prefs
        
        matches = []
        
        # Check dietary matches
        dietary_restrictions = prefs.get('dietary_restrictions', [])
        recipe_diets = recipe.get('dietary_tags', []) or recipe.get('diets', [])
        
        for restriction in dietary_restrictions:
            if any(restriction.lower() in diet.lower() for diet in recipe_diets):
                matches.append(f"Diet: {restriction}")
        
        # Check cuisine matches
        cuisine_preferences = prefs.get('cuisine_preferences', [])
        recipe_cuisines = recipe.get('cuisines', []) or recipe.get('cuisine_type', [])
        
        if isinstance(recipe_cuisines, str):
            recipe_cuisines = [recipe_cuisines]
        
        for pref_cuisine in cuisine_preferences:
            for recipe_cuisine in recipe_cuisines:
                if pref_cuisine.lower() in recipe_cuisine.lower():
                    matches.append(f"Cuisine: {recipe_cuisine}")
        
        return {
            "user_id": user_id,
            "recipe_name": recipe.get('name', 'Unknown Recipe'),
            "preference_matches": matches,
            "match_count": len(matches)
        }
    
    def _is_vegetarian_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is vegetarian compatible."""
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join(ingredients).lower()
        
        meat_keywords = ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'fish', 'salmon', 'tuna', 'meat', 'bacon', 'ham']
        
        return not any(keyword in ingredients_text for keyword in meat_keywords)
    
    def _is_vegan_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is vegan compatible."""
        if not self._is_vegetarian_compatible(recipe):
            return False
        
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join(ingredients).lower()
        
        animal_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'egg', 'honey', 'gelatin']
        
        return not any(keyword in ingredients_text for keyword in animal_keywords)
    
    def _is_gluten_free_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is gluten-free compatible."""
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join(ingredients).lower()
        
        gluten_keywords = ['wheat', 'flour', 'bread', 'pasta', 'barley', 'rye', 'soy sauce', 'bulgur']
        
        return not any(keyword in ingredients_text for keyword in gluten_keywords)
    
    def _is_dairy_free_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is dairy-free compatible."""
        ingredients = recipe.get('ingredients', [])
        ingredients_text = ' '.join(ingredients).lower()
        
        dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose']
        
        return not any(keyword in ingredients_text for keyword in dairy_keywords)
    
    def _is_keto_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is keto compatible (low carb)."""
        nutrition = recipe.get('nutrition', {})
        carbs = nutrition.get('carbohydrates', 0)
        calories = nutrition.get('calories', 0)
        
        if calories == 0:
            return True  # Can't determine, assume compatible
        
        # Keto typically <10% carbs
        carb_percentage = (carbs * 4 / calories) * 100
        return carb_percentage < 15  # Slightly lenient
    
    def _is_low_sodium_compatible(self, recipe: Dict[str, Any]) -> bool:
        """Check if recipe is low sodium compatible."""
        nutrition = recipe.get('nutrition', {})
        sodium = nutrition.get('sodium', 0)
        
        # Low sodium typically <600mg per serving
        return sodium < 600
    
    def _contains_allergen(self, ingredients_text: str, allergen: str) -> bool:
        """Check if ingredients contain an allergen."""
        allergen_lower = allergen.lower()
        
        # Map allergens to keywords
        allergen_keywords = {
            'nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'macadamia'],
            'peanuts': ['peanut'],
            'eggs': ['egg'],
            'soy': ['soy', 'tofu', 'tempeh', 'edamame'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt'],
            'gluten': ['wheat', 'flour', 'bread', 'pasta', 'barley', 'rye'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'scallop', 'oyster'],
            'fish': ['salmon', 'tuna', 'cod', 'tilapia', 'bass']
        }
        
        # Check direct match
        if allergen_lower in ingredients_text:
            return True
        
        # Check mapped keywords
        keywords = allergen_keywords.get(allergen_lower, [])
        return any(keyword in ingredients_text for keyword in keywords)
    
    def _get_recommendation_level(self, score: float) -> str:
        """Get recommendation level based on score."""
        if score >= 15:
            return "Highly Recommended"
        elif score >= 10:
            return "Recommended"
        elif score >= 5:
            return "Suitable"
        elif score >= 0:
            return "Acceptable"
        else:
            return "Not Recommended"


# Helper function to create the tool
def create_preference_tool() -> PreferenceTool:
    """Create and return a PreferenceTool instance."""
    return PreferenceTool()