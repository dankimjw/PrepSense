"""Enhanced recipe preference scoring system with weighted factors"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecipePreferenceScorer:
    """Advanced recipe scoring based on user preferences, history, and behavior"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        
        # Weight configuration for different factors
        self.weights = {
            # Positive weights
            'favorite_ingredient_match': 3.0,      # High weight for favorite ingredients
            'preferred_cuisine_match': 2.5,        # Medium-high for cuisine preference
            'dietary_restriction_match': 5.0,      # Highest for dietary needs
            'cooking_time_match': 2.0,             # Medium for time preference
            'highly_rated_similar': 4.0,           # High for similar liked recipes
            'frequently_cooked_ingredient': 2.5,   # Medium-high for familiar ingredients
            'seasonal_match': 1.5,                 # Low-medium for seasonal items
            'expiring_ingredient_use': 3.5,        # High for using expiring items
            'nutritional_goal_match': 2.0,         # Medium for nutrition goals
            
            # Negative weights
            'disliked_cuisine': -4.0,              # Strong negative for disliked cuisines
            'disliked_ingredient': -3.0,           # Negative for specific ingredients
            'too_complex': -2.0,                   # Negative for overly complex recipes
            'poor_rating_similar': -3.5,           # Negative for similar disliked recipes
            'allergen_present': -10.0,             # Extreme negative (should never show)
            'missing_key_equipment': -2.5,         # Negative if requires special equipment
        }
        
        # Maximum possible score for normalization
        self.max_score = sum(v for v in self.weights.values() if v > 0)
    
    def calculate_comprehensive_score(
        self, 
        recipe: Dict[str, Any], 
        user_id: int,
        pantry_items: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive recipe score with detailed breakdown
        
        Args:
            recipe: Recipe data dictionary
            user_id: User ID for preference lookup
            pantry_items: Current pantry items (for expiring item bonus)
            context: Additional context (meal type, season, etc.)
            
        Returns:
            Dictionary with score, breakdown, and recommendations
        """
        
        # Get user preferences and history
        user_data = self._get_user_preference_data(user_id)
        
        # Initialize scoring components
        score_components = {}
        total_score = 0.0
        
        # 1. Ingredient matching
        ingredient_score = self._score_ingredients(recipe, user_data, pantry_items)
        score_components['ingredients'] = ingredient_score
        total_score += ingredient_score['weighted_score']
        
        # 2. Cuisine matching
        cuisine_score = self._score_cuisine(recipe, user_data)
        score_components['cuisine'] = cuisine_score
        total_score += cuisine_score['weighted_score']
        
        # 3. Dietary compatibility
        dietary_score = self._score_dietary_compatibility(recipe, user_data)
        score_components['dietary'] = dietary_score
        total_score += dietary_score['weighted_score']
        
        # 4. Cooking time preference
        time_score = self._score_cooking_time(recipe, user_data)
        score_components['cooking_time'] = time_score
        total_score += time_score['weighted_score']
        
        # 5. Recipe similarity to liked/disliked recipes
        similarity_score = self._score_recipe_similarity(recipe, user_data)
        score_components['similarity'] = similarity_score
        total_score += similarity_score['weighted_score']
        
        # 6. Nutritional goals
        nutrition_score = self._score_nutritional_match(recipe, user_data)
        score_components['nutrition'] = nutrition_score
        total_score += nutrition_score['weighted_score']
        
        # 7. Context-based scoring (seasonal, meal type, etc.)
        if context:
            context_score = self._score_context_match(recipe, context)
            score_components['context'] = context_score
            total_score += context_score['weighted_score']
        
        # Normalize score to 0-100 range
        normalized_score = max(0, min(100, (total_score / self.max_score) * 100))
        
        # Generate recommendation reasoning
        reasoning = self._generate_reasoning(score_components, recipe)
        
        return {
            'score': normalized_score,
            'raw_score': total_score,
            'max_possible_score': self.max_score,
            'components': score_components,
            'reasoning': reasoning,
            'recommendation_level': self._get_recommendation_level(normalized_score),
            'personalization_confidence': self._calculate_confidence(user_data)
        }
    
    def _get_user_preference_data(self, user_id: int) -> Dict[str, Any]:
        """Fetch comprehensive user preference data"""
        
        data = {
            'preferences': {},
            'history': {},
            'ratings': {},
            'allergens': [],
            'dietary_restrictions': [],
            'disliked_cuisines': [],
            'favorite_ingredients': [],
            'disliked_ingredients': [],
            'cooking_skill_level': 'intermediate',
            'nutritional_goals': []
        }
        
        # Get allergens
        allergen_query = """
        SELECT allergen FROM user_allergens WHERE user_id = %(user_id)s
        """
        allergens = self.db_service.execute_query(allergen_query, {'user_id': user_id})
        data['allergens'] = [row['allergen'] for row in allergens]
        
        # Get dietary preferences
        dietary_query = """
        SELECT preference FROM user_dietary_preferences WHERE user_id = %(user_id)s
        """
        dietary = self.db_service.execute_query(dietary_query, {'user_id': user_id})
        data['dietary_restrictions'] = [row['preference'] for row in dietary]
        
        # Get cuisine preferences (including negative preferences)
        cuisine_query = """
        SELECT cuisine, preference_level 
        FROM user_cuisine_preferences 
        WHERE user_id = %(user_id)s
        """
        cuisines = self.db_service.execute_query(cuisine_query, {'user_id': user_id})
        for row in cuisines:
            if row.get('preference_level', 1) < 0:
                data['disliked_cuisines'].append(row['cuisine'])
        
        # Get recipe history and ratings
        history_query = """
        SELECT 
            recipe_id,
            recipe_title,
            recipe_data,
            rating,
            is_favorite,
            created_at
        FROM user_recipes
        WHERE user_id = %(user_id)s
        ORDER BY created_at DESC
        LIMIT 100
        """
        history = self.db_service.execute_query(history_query, {'user_id': user_id})
        
        # Analyze history for patterns
        ingredient_frequency = defaultdict(int)
        for recipe in history:
            recipe_data = recipe.get('recipe_data', {})
            
            # Track liked recipes
            if recipe.get('rating') == 'thumbs_up' or recipe.get('is_favorite'):
                data['ratings'][recipe['recipe_id']] = 'positive'
                
                # Extract favorite ingredients from liked recipes
                ingredients = self._extract_recipe_ingredients(recipe_data)
                for ing in ingredients:
                    ingredient_frequency[ing] += 1
            
            elif recipe.get('rating') == 'thumbs_down':
                data['ratings'][recipe['recipe_id']] = 'negative'
        
        # Top ingredients become favorites
        data['favorite_ingredients'] = [
            ing for ing, count in sorted(
                ingredient_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        ]
        
        return data
    
    def _score_ingredients(
        self, 
        recipe: Dict[str, Any], 
        user_data: Dict[str, Any],
        pantry_items: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Score recipe based on ingredient preferences"""
        
        recipe_ingredients = self._extract_recipe_ingredients(recipe)
        score = 0.0
        details = []
        
        # Check favorite ingredients
        favorite_matches = set(recipe_ingredients) & set(user_data['favorite_ingredients'])
        if favorite_matches:
            score += len(favorite_matches) * self.weights['favorite_ingredient_match']
            details.append(f"Contains {len(favorite_matches)} favorite ingredients")
        
        # Check disliked ingredients
        disliked_matches = set(recipe_ingredients) & set(user_data['disliked_ingredients'])
        if disliked_matches:
            score += len(disliked_matches) * self.weights['disliked_ingredient']
            details.append(f"Contains {len(disliked_matches)} disliked ingredients")
        
        # Bonus for using expiring items
        if pantry_items:
            expiring_used = self._count_expiring_items_used(recipe_ingredients, pantry_items)
            if expiring_used > 0:
                score += self.weights['expiring_ingredient_use'] * min(expiring_used / 3, 1)
                details.append(f"Uses {expiring_used} expiring items")
        
        return {
            'weighted_score': score,
            'details': details,
            'favorite_matches': list(favorite_matches),
            'disliked_matches': list(disliked_matches)
        }
    
    def _score_cuisine(self, recipe: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score recipe based on cuisine preferences"""
        
        recipe_cuisine = recipe.get('cuisine_type', recipe.get('cuisines', ['unknown']))[0]
        score = 0.0
        details = []
        
        if recipe_cuisine in user_data['disliked_cuisines']:
            score += self.weights['disliked_cuisine']
            details.append(f"Disliked cuisine: {recipe_cuisine}")
        elif recipe_cuisine in user_data.get('preferred_cuisines', []):
            score += self.weights['preferred_cuisine_match']
            details.append(f"Preferred cuisine: {recipe_cuisine}")
        
        return {
            'weighted_score': score,
            'cuisine': recipe_cuisine,
            'details': details
        }
    
    def _score_dietary_compatibility(
        self, 
        recipe: Dict[str, Any], 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score recipe based on dietary restrictions and allergens"""
        
        score = 0.0
        details = []
        violations = []
        
        # Check allergens (should never recommend if present)
        recipe_allergens = self._extract_allergens(recipe)
        allergen_matches = set(recipe_allergens) & set(user_data['allergens'])
        if allergen_matches:
            score += self.weights['allergen_present']
            violations.extend(f"Contains allergen: {a}" for a in allergen_matches)
        
        # Check dietary restrictions
        recipe_diets = recipe.get('diets', [])
        for restriction in user_data['dietary_restrictions']:
            if restriction.lower() in [d.lower() for d in recipe_diets]:
                score += self.weights['dietary_restriction_match']
                details.append(f"Matches {restriction} diet")
        
        return {
            'weighted_score': score,
            'details': details,
            'violations': violations,
            'is_safe': len(violations) == 0
        }
    
    def _score_cooking_time(self, recipe: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score recipe based on cooking time preferences"""
        
        recipe_time = recipe.get('readyInMinutes', recipe.get('time', 30))
        time_pref = user_data.get('cooking_time_preference', 'medium')
        score = 0.0
        details = []
        
        if time_pref == 'quick' and recipe_time <= 20:
            score += self.weights['cooking_time_match']
            details.append("Quick recipe matches preference")
        elif time_pref == 'medium' and 20 < recipe_time <= 45:
            score += self.weights['cooking_time_match']
            details.append("Medium cook time matches preference")
        elif time_pref == 'long' and recipe_time > 45:
            score += self.weights['cooking_time_match']
            details.append("Long cook time matches preference")
        else:
            score += self.weights['cooking_time_match'] * 0.5  # Partial credit
            details.append(f"{recipe_time} min cook time")
        
        return {
            'weighted_score': score,
            'cook_time': recipe_time,
            'preference': time_pref,
            'details': details
        }
    
    def _score_recipe_similarity(
        self, 
        recipe: Dict[str, Any], 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score based on similarity to previously rated recipes"""
        
        score = 0.0
        details = []
        
        # This is a simplified version - could use more sophisticated similarity metrics
        recipe_ingredients = set(self._extract_recipe_ingredients(recipe))
        
        similar_positive = 0
        similar_negative = 0
        
        for rated_id, rating in user_data['ratings'].items():
            # In practice, would fetch recipe data for comparison
            # For now, using a simple heuristic
            if rating == 'positive':
                similar_positive += 1
            elif rating == 'negative':
                similar_negative += 1
        
        # Apply similarity scores
        if similar_positive > similar_negative:
            score += self.weights['highly_rated_similar'] * 0.5
            details.append("Similar to liked recipes")
        elif similar_negative > similar_positive:
            score += self.weights['poor_rating_similar'] * 0.5
            details.append("Similar to disliked recipes")
        
        return {
            'weighted_score': score,
            'details': details
        }
    
    def _score_nutritional_match(
        self, 
        recipe: Dict[str, Any], 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score based on nutritional goals"""
        
        score = 0.0
        details = []
        
        # Check if recipe has nutrition data
        nutrition = recipe.get('nutrition', {})
        if nutrition and user_data.get('nutritional_goals'):
            # Simplified scoring - would need more sophisticated nutrition matching
            score += self.weights['nutritional_goal_match'] * 0.5
            details.append("Matches some nutritional goals")
        
        return {
            'weighted_score': score,
            'details': details
        }
    
    def _score_context_match(
        self, 
        recipe: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score based on context (season, meal type, occasion)"""
        
        score = 0.0
        details = []
        
        # Seasonal matching
        if context.get('season'):
            # Simple seasonal ingredient matching
            score += self.weights['seasonal_match'] * 0.5
            details.append(f"Good for {context['season']}")
        
        return {
            'weighted_score': score,
            'details': details
        }
    
    def _extract_recipe_ingredients(self, recipe: Dict[str, Any]) -> List[str]:
        """Extract ingredient names from recipe"""
        ingredients = []
        
        if 'extendedIngredients' in recipe:
            for ing in recipe['extendedIngredients']:
                if 'name' in ing:
                    ingredients.append(ing['name'].lower())
        elif 'ingredients' in recipe:
            if isinstance(recipe['ingredients'], list):
                for ing in recipe['ingredients']:
                    if isinstance(ing, str):
                        ingredients.append(ing.lower())
                    elif isinstance(ing, dict) and 'name' in ing:
                        ingredients.append(ing['name'].lower())
        
        return ingredients
    
    def _extract_allergens(self, recipe: Dict[str, Any]) -> List[str]:
        """Extract potential allergens from recipe"""
        allergens = []
        
        # Check explicit allergen fields
        if 'allergens' in recipe:
            allergens.extend(recipe['allergens'])
        
        # Check dietary flags
        if not recipe.get('dairyFree', True):
            allergens.append('dairy')
        if not recipe.get('glutenFree', True):
            allergens.append('gluten')
        
        # Could add more sophisticated allergen detection from ingredients
        
        return allergens
    
    def _count_expiring_items_used(
        self, 
        recipe_ingredients: List[str], 
        pantry_items: List[Dict[str, Any]]
    ) -> int:
        """Count how many expiring pantry items the recipe uses"""
        
        expiring_count = 0
        today = datetime.now().date()
        
        for item in pantry_items:
            if item.get('expiration_date'):
                exp_date = item['expiration_date']
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
                
                days_until = (exp_date - today).days
                if 0 <= days_until <= 7:  # Expiring within a week
                    item_name = item.get('product_name', '').lower()
                    if any(item_name in ing or ing in item_name for ing in recipe_ingredients):
                        expiring_count += 1
        
        return expiring_count
    
    def _generate_reasoning(
        self, 
        components: Dict[str, Any], 
        recipe: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasoning for the score"""
        
        reasoning = []
        
        # Gather all positive reasons
        for component, data in components.items():
            if data.get('weighted_score', 0) > 0:
                reasoning.extend(data.get('details', []))
        
        # Add warnings for negative scores
        warnings = []
        for component, data in components.items():
            if data.get('weighted_score', 0) < 0:
                warnings.extend(data.get('details', []))
                warnings.extend(data.get('violations', []))
        
        if warnings:
            reasoning.append(f"⚠️ Concerns: {', '.join(warnings)}")
        
        return reasoning
    
    def _get_recommendation_level(self, score: float) -> str:
        """Get recommendation level based on score"""
        
        if score >= 80:
            return "Highly Recommended"
        elif score >= 60:
            return "Recommended"
        elif score >= 40:
            return "Suitable"
        elif score >= 20:
            return "Possible"
        else:
            return "Not Recommended"
    
    def _calculate_confidence(self, user_data: Dict[str, Any]) -> float:
        """Calculate confidence in personalization based on available data"""
        
        data_points = 0
        if user_data['allergens']:
            data_points += 2
        if user_data['dietary_restrictions']:
            data_points += 2
        if user_data['favorite_ingredients']:
            data_points += 1
        if user_data['ratings']:
            data_points += min(len(user_data['ratings']) / 10, 3)
        
        return min(data_points / 8.0, 1.0)  # Max confidence at 8 data points