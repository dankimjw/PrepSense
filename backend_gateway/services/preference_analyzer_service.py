"""Service for analyzing user preferences from saved recipes and cooking history"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class PreferenceAnalyzerService:
    """Analyzes user preferences from their recipe history and ratings"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    def analyze_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze user's preferences based on their saved recipes and cooking history
        
        Returns:
            Dict containing preference insights
        """
        try:
            # Get user's saved recipes with ratings
            liked_recipes = self._get_liked_recipes(user_id)
            all_saved_recipes = self._get_all_saved_recipes(user_id)
            cooking_history = self._get_cooking_history(user_id)
            
            # Analyze patterns
            patterns = self._analyze_recipe_patterns(liked_recipes)
            cooking_frequency = self._analyze_cooking_frequency(cooking_history)
            
            # Extract insights
            insights = self._extract_preference_insights(patterns, cooking_frequency)
            
            return {
                'patterns': patterns,
                'insights': insights,
                'stats': {
                    'total_saved': len(all_saved_recipes),
                    'total_liked': len(liked_recipes),
                    'recipes_cooked': len(cooking_history)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing preferences for user {user_id}: {str(e)}")
            return {}
    
    def _get_liked_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all recipes the user has rated positively"""
        query = """
        SELECT 
            recipe_title,
            recipe_data,
            source,
            created_at
        FROM user_recipes
        WHERE user_id = %(user_id)s 
        AND (rating = 'thumbs_up' OR is_favorite = true)
        """
        
        return self.db_service.execute_query(query, {"user_id": user_id})
    
    def _get_all_saved_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all saved recipes for the user"""
        query = """
        SELECT 
            recipe_title,
            recipe_data,
            rating,
            is_favorite,
            source
        FROM user_recipes
        WHERE user_id = %(user_id)s
        """
        
        return self.db_service.execute_query(query, {"user_id": user_id})
    
    def _get_cooking_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get cooking history from pantry_history"""
        query = """
        SELECT 
            recipe_name,
            recipe_id,
            changed_at,
            COUNT(*) as times_cooked
        FROM pantry_history
        WHERE user_id = %(user_id)s 
        AND recipe_name IS NOT NULL
        GROUP BY recipe_name, recipe_id, changed_at
        ORDER BY changed_at DESC
        """
        
        return self.db_service.execute_query(query, {"user_id": user_id})
    
    def _analyze_recipe_patterns(self, liked_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in liked recipes"""
        patterns = {
            'common_ingredients': defaultdict(int),
            'cuisine_distribution': defaultdict(int),
            'cooking_time_preference': {
                'quick': 0,      # < 20 min
                'medium': 0,     # 20-45 min
                'long': 0        # > 45 min
            },
            'meal_type_distribution': defaultdict(int),
            'dietary_tags_frequency': defaultdict(int),
            'ingredient_categories': defaultdict(int)
        }
        
        for recipe in liked_recipes:
            recipe_data = recipe.get('recipe_data', {})
            
            # Analyze ingredients
            ingredients = self._extract_ingredients(recipe_data)
            for ingredient in ingredients:
                clean_name = self._clean_ingredient_name(ingredient)
                if clean_name:
                    patterns['common_ingredients'][clean_name] += 1
                    category = self._categorize_ingredient(clean_name)
                    patterns['ingredient_categories'][category] += 1
            
            # Analyze cuisine
            cuisine = recipe_data.get('cuisine_type', 'unknown')
            if cuisine and cuisine != 'unknown':
                patterns['cuisine_distribution'][cuisine] += 1
            
            # Analyze cooking time
            time = recipe_data.get('time', recipe_data.get('readyInMinutes', 30))
            if time < 20:
                patterns['cooking_time_preference']['quick'] += 1
            elif time <= 45:
                patterns['cooking_time_preference']['medium'] += 1
            else:
                patterns['cooking_time_preference']['long'] += 1
            
            # Analyze meal type
            meal_type = recipe_data.get('meal_type', 'dinner')
            patterns['meal_type_distribution'][meal_type] += 1
            
            # Analyze dietary tags
            dietary_tags = recipe_data.get('dietary_tags', recipe_data.get('diets', []))
            for tag in dietary_tags:
                patterns['dietary_tags_frequency'][tag] += 1
        
        return patterns
    
    def _analyze_cooking_frequency(self, cooking_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cooking frequency patterns"""
        frequency = {
            'most_cooked_recipes': [],
            'recent_recipes': [],
            'cooking_days': set()
        }
        
        recipe_counts = defaultdict(int)
        for entry in cooking_history:
            recipe_name = entry['recipe_name']
            recipe_counts[recipe_name] += entry.get('times_cooked', 1)
            
            # Track cooking days
            if entry.get('changed_at'):
                cooking_date = entry['changed_at'].date()
                frequency['cooking_days'].add(cooking_date)
        
        # Get most cooked recipes
        sorted_recipes = sorted(recipe_counts.items(), key=lambda x: x[1], reverse=True)
        frequency['most_cooked_recipes'] = [
            {'name': name, 'count': count} 
            for name, count in sorted_recipes[:5]
        ]
        
        # Get recent recipes (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        frequency['recent_recipes'] = [
            entry['recipe_name'] 
            for entry in cooking_history 
            if entry.get('changed_at') and entry['changed_at'] > recent_date
        ][:10]
        
        return frequency
    
    def _extract_preference_insights(self, patterns: Dict[str, Any], 
                                   cooking_frequency: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actionable insights from patterns"""
        insights = {
            'favorite_ingredients': [],
            'preferred_cuisines': [],
            'cooking_time_preference': '',
            'detected_dietary_pattern': [],
            'ingredient_categories_preference': [],
            'frequently_cooked': []
        }
        
        # Get top favorite ingredients (appearing in >25% of liked recipes)
        total_liked = sum(patterns['cuisine_distribution'].values()) or 1
        sorted_ingredients = sorted(patterns['common_ingredients'].items(), 
                                   key=lambda x: x[1], reverse=True)
        
        # Take ingredients that appear frequently
        insights['favorite_ingredients'] = [
            ing for ing, count in sorted_ingredients[:10] 
            if count >= max(3, total_liked * 0.25)
        ]
        
        # Get preferred cuisines
        for cuisine, count in patterns['cuisine_distribution'].items():
            if count >= max(2, total_liked * 0.2):  # At least 20% of liked recipes
                insights['preferred_cuisines'].append(cuisine)
        
        # Determine cooking time preference
        time_prefs = patterns['cooking_time_preference']
        if sum(time_prefs.values()) > 0:
            insights['cooking_time_preference'] = max(time_prefs, key=time_prefs.get)
        
        # Detect dietary patterns
        total_recipes = sum(patterns['dietary_tags_frequency'].values()) or 1
        for diet, count in patterns['dietary_tags_frequency'].items():
            if count >= max(3, total_recipes * 0.3):  # At least 30% of recipes
                insights['detected_dietary_pattern'].append(diet)
        
        # Preferred ingredient categories
        sorted_categories = sorted(patterns['ingredient_categories'].items(), 
                                  key=lambda x: x[1], reverse=True)
        insights['ingredient_categories_preference'] = [
            cat for cat, _ in sorted_categories[:5]
        ]
        
        # Add frequently cooked recipes
        insights['frequently_cooked'] = cooking_frequency['most_cooked_recipes']
        
        return insights
    
    def _extract_ingredients(self, recipe_data: Dict[str, Any]) -> List[str]:
        """Extract ingredient names from recipe data"""
        ingredients = []
        
        # Try different possible formats
        if 'ingredients' in recipe_data:
            ing_list = recipe_data['ingredients']
            if isinstance(ing_list, list):
                for ing in ing_list:
                    if isinstance(ing, str):
                        ingredients.append(ing)
                    elif isinstance(ing, dict) and 'name' in ing:
                        ingredients.append(ing['name'])
        
        # Also check extendedIngredients (Spoonacular format)
        if 'extendedIngredients' in recipe_data:
            for ing in recipe_data['extendedIngredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(ing['name'])
        
        return ingredients
    
    def _clean_ingredient_name(self, ingredient: str) -> str:
        """Clean and normalize ingredient name"""
        if not ingredient:
            return ""
        
        # Remove quantities and units
        cleaned = re.sub(r'^\d+[\d\s\/.]*', '', ingredient)
        cleaned = re.sub(r'\b(cup|cups|tsp|tbsp|tablespoon|teaspoon|oz|lb|g|kg|ml|l)\b', '', cleaned)
        
        # Remove common modifiers
        modifiers = ['fresh', 'frozen', 'dried', 'canned', 'chopped', 'diced', 'minced', 'sliced']
        for mod in modifiers:
            cleaned = cleaned.replace(mod, '')
        
        # Clean up and return
        cleaned = cleaned.strip().lower()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single
        
        return cleaned
    
    def _categorize_ingredient(self, ingredient: str) -> str:
        """Categorize ingredient into broad categories"""
        ingredient_lower = ingredient.lower()
        
        # Define category mappings
        categories = {
            'protein': ['chicken', 'beef', 'pork', 'fish', 'tofu', 'egg', 'bean', 'lentil'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'grain': ['rice', 'pasta', 'bread', 'flour', 'oat', 'quinoa'],
            'vegetable': ['carrot', 'broccoli', 'tomato', 'onion', 'pepper', 'lettuce', 'spinach'],
            'fruit': ['apple', 'banana', 'orange', 'berry', 'lemon', 'lime'],
            'spice': ['salt', 'pepper', 'cumin', 'paprika', 'garlic', 'ginger'],
            'oil': ['oil', 'butter', 'fat']
        }
        
        for category, keywords in categories.items():
            if any(keyword in ingredient_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def calculate_recipe_preference_score(self, recipe: Dict[str, Any], 
                                        user_insights: Dict[str, Any]) -> float:
        """
        Calculate how well a recipe matches user preferences
        
        Returns:
            Score between 0-1
        """
        score = 0.0
        max_score = 100.0
        
        recipe_data = recipe if 'ingredients' in recipe else recipe.get('recipe_data', {})
        
        # Check ingredient preferences (40 points)
        recipe_ingredients = self._extract_ingredients(recipe_data)
        recipe_ingredients_clean = [self._clean_ingredient_name(ing) for ing in recipe_ingredients]
        favorite_ingredients = user_insights.get('favorite_ingredients', [])
        
        if favorite_ingredients and recipe_ingredients_clean:
            matching_favorites = len(set(recipe_ingredients_clean) & set(favorite_ingredients))
            score += (matching_favorites / max(len(favorite_ingredients), 1)) * 40
        
        # Check cuisine preference (20 points)
        recipe_cuisine = recipe_data.get('cuisine_type', 'unknown')
        if recipe_cuisine in user_insights.get('preferred_cuisines', []):
            score += 20
        
        # Check cooking time preference (20 points)
        recipe_time = recipe_data.get('time', recipe_data.get('readyInMinutes', 30))
        time_pref = user_insights.get('cooking_time_preference', 'medium')
        
        if time_pref == 'quick' and recipe_time < 20:
            score += 20
        elif time_pref == 'medium' and 20 <= recipe_time <= 45:
            score += 20
        elif time_pref == 'long' and recipe_time > 45:
            score += 20
        else:
            score += 10  # Partial credit
        
        # Check dietary pattern match (20 points)
        recipe_diets = recipe_data.get('dietary_tags', recipe_data.get('diets', []))
        detected_patterns = user_insights.get('detected_dietary_pattern', [])
        
        if detected_patterns and recipe_diets:
            if any(diet in recipe_diets for diet in detected_patterns):
                score += 20
        
        return score / max_score