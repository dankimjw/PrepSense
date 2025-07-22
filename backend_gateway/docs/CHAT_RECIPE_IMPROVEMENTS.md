# Chat/Recipe Recommendation System Improvements

## Executive Summary

The current system has basic preference matching but lacks sophisticated context understanding and personalization. Here's a comprehensive plan to enhance the system to better match user preferences, ingredients, and queries.

## Immediate Improvements (1-2 days)

### 1. Enhanced Message Context Extraction

Create a new service for better understanding user intent:

```python
# services/message_context_service.py
import re
from typing import Dict, List, Optional
from datetime import datetime

class MessageContextService:
    """Extract rich context from user messages for better recipe matching"""
    
    def __init__(self):
        self.meal_patterns = {
            'breakfast': ['breakfast', 'morning', 'brunch', 'wake up', 'start my day'],
            'lunch': ['lunch', 'midday', 'noon', 'work meal', 'quick bite'],
            'dinner': ['dinner', 'supper', 'evening', 'tonight', 'family meal'],
            'snack': ['snack', 'appetizer', 'munchies', 'bite', 'treat'],
            'dessert': ['dessert', 'sweet', 'cake', 'cookie', 'after dinner']
        }
        
        self.time_patterns = {
            'quick': ['quick', 'fast', 'hurry', 'minutes', 'instant', 'speedy'],
            'medium': ['normal', 'regular', 'standard'],
            'leisurely': ['slow', 'weekend', 'elaborate', 'fancy', 'special']
        }
        
        self.health_patterns = {
            'healthy': ['healthy', 'nutritious', 'light', 'fresh', 'clean'],
            'comfort': ['comfort', 'hearty', 'filling', 'cozy', 'satisfying'],
            'diet': ['diet', 'low calorie', 'weight loss', 'lean', 'fit']
        }
    
    def extract_context(self, message: str, time_of_day: Optional[datetime] = None) -> Dict:
        """Extract comprehensive context from user message"""
        message_lower = message.lower()
        
        context = {
            'meal_type': self._detect_meal_type(message_lower, time_of_day),
            'time_constraint': self._extract_time_constraint(message_lower),
            'health_focus': self._detect_health_intent(message_lower),
            'cuisine_hints': self._extract_cuisine_hints(message_lower),
            'ingredient_focus': self._extract_ingredient_focus(message_lower),
            'serving_info': self._extract_serving_info(message_lower),
            'special_requirements': self._extract_special_requirements(message_lower)
        }
        
        return context
    
    def _detect_meal_type(self, message: str, time_of_day: Optional[datetime]) -> str:
        """Detect meal type with time-based defaults"""
        # Check explicit mentions
        for meal_type, patterns in self.meal_patterns.items():
            if any(pattern in message for pattern in patterns):
                return meal_type
        
        # Use time of day as hint
        if time_of_day:
            hour = time_of_day.hour
            if 5 <= hour < 11:
                return 'breakfast'
            elif 11 <= hour < 15:
                return 'lunch'
            elif 15 <= hour < 17:
                return 'snack'
            elif 17 <= hour < 21:
                return 'dinner'
            else:
                return 'snack'
        
        return 'dinner'  # default
    
    def _extract_time_constraint(self, message: str) -> Dict:
        """Extract cooking time preferences"""
        # Check for specific time mentions
        time_match = re.search(r'(\d+)\s*(?:min|minute)', message)
        if time_match:
            return {
                'max_minutes': int(time_match.group(1)),
                'preference': 'quick' if int(time_match.group(1)) <= 30 else 'medium'
            }
        
        # Check for qualitative time
        for time_type, patterns in self.time_patterns.items():
            if any(pattern in message for pattern in patterns):
                max_times = {'quick': 20, 'medium': 45, 'leisurely': 120}
                return {
                    'max_minutes': max_times.get(time_type, 45),
                    'preference': time_type
                }
        
        return {'max_minutes': 60, 'preference': 'medium'}
    
    def _extract_ingredient_focus(self, message: str) -> List[str]:
        """Extract specific ingredients user wants to use"""
        # Common ingredient patterns
        patterns = [
            r'using (\w+)',
            r'with (\w+)',
            r'make.*with (\w+)',
            r'recipe.*for (\w+)'
        ]
        
        ingredients = []
        for pattern in patterns:
            matches = re.findall(pattern, message)
            ingredients.extend(matches)
        
        return list(set(ingredients))
```

### 2. Improved Recipe Matching

Enhance the recipe matching logic with better ingredient understanding:

```python
# services/ingredient_matcher_service.py
from typing import Dict, List, Tuple
import difflib

class IngredientMatcherService:
    """Advanced ingredient matching with substitution awareness"""
    
    def __init__(self):
        # Ingredient categories for better matching
        self.ingredient_categories = {
            'proteins': {
                'chicken': ['chicken breast', 'chicken thigh', 'chicken wings', 'whole chicken'],
                'beef': ['ground beef', 'beef steak', 'beef roast', 'beef strips'],
                'pork': ['pork chops', 'ground pork', 'pork tenderloin', 'bacon'],
                'seafood': ['salmon', 'tuna', 'shrimp', 'cod', 'tilapia'],
                'vegetarian': ['tofu', 'tempeh', 'beans', 'lentils', 'chickpeas']
            },
            'grains': {
                'rice': ['white rice', 'brown rice', 'jasmine rice', 'basmati rice'],
                'pasta': ['spaghetti', 'penne', 'fusilli', 'linguine', 'macaroni'],
                'bread': ['white bread', 'whole wheat bread', 'sourdough', 'baguette']
            },
            'dairy': {
                'milk': ['whole milk', '2% milk', 'skim milk', 'almond milk', 'soy milk'],
                'cheese': ['cheddar', 'mozzarella', 'parmesan', 'swiss', 'feta']
            }
        }
        
        # Substitution rules
        self.substitutions = {
            'butter': ['margarine', 'oil', 'coconut oil'],
            'sugar': ['honey', 'maple syrup', 'agave'],
            'milk': ['cream', 'yogurt', 'buttermilk'],
            'egg': ['flax egg', 'applesauce', 'banana']
        }
    
    def match_recipe_to_pantry(
        self, 
        recipe_ingredients: List[str], 
        pantry_items: List[Dict]
    ) -> Dict:
        """Match recipe ingredients to pantry with substitution suggestions"""
        
        results = {
            'perfect_matches': [],
            'category_matches': [],
            'possible_substitutions': [],
            'missing_ingredients': [],
            'match_score': 0.0,
            'can_make_with_substitutions': False
        }
        
        pantry_names = [item['product_name'].lower() for item in pantry_items]
        
        for ingredient in recipe_ingredients:
            ingredient_lower = ingredient.lower()
            
            # Check for perfect match
            perfect_match = self._find_perfect_match(ingredient_lower, pantry_names)
            if perfect_match:
                results['perfect_matches'].append({
                    'recipe_ingredient': ingredient,
                    'pantry_item': perfect_match
                })
                continue
            
            # Check for category match
            category_match = self._find_category_match(ingredient_lower, pantry_names)
            if category_match:
                results['category_matches'].append({
                    'recipe_ingredient': ingredient,
                    'pantry_item': category_match,
                    'match_type': 'category'
                })
                continue
            
            # Check for substitutions
            substitution = self._find_substitution(ingredient_lower, pantry_names)
            if substitution:
                results['possible_substitutions'].append({
                    'recipe_ingredient': ingredient,
                    'suggested_substitute': substitution,
                    'in_pantry': True
                })
            else:
                results['missing_ingredients'].append(ingredient)
        
        # Calculate match score
        total_ingredients = len(recipe_ingredients)
        matched = len(results['perfect_matches']) + len(results['category_matches'])
        substitutable = len(results['possible_substitutions'])
        
        results['match_score'] = matched / total_ingredients if total_ingredients > 0 else 0
        results['can_make_with_substitutions'] = (
            matched + substitutable == total_ingredients
        )
        
        return results
```

### 3. Enhanced Preference Learning

Track and learn from user interactions:

```python
# services/preference_learning_service.py
from typing import Dict, List
from datetime import datetime, timedelta

class PreferenceLearningService:
    """Learn and adapt to user preferences over time"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    async def track_recipe_interaction(
        self, 
        user_id: int, 
        recipe_id: str, 
        action: str,
        context: Dict
    ):
        """Track user interactions with recipes"""
        
        interaction_data = {
            'user_id': user_id,
            'recipe_id': recipe_id,
            'action': action,  # viewed, saved, cooked, rated
            'context': context,  # time of day, day of week, season
            'timestamp': datetime.now()
        }
        
        # Store in database
        await self._store_interaction(interaction_data)
        
        # Update user preferences based on action
        if action in ['saved', 'cooked', 'rated_positive']:
            await self._update_preferences_from_recipe(user_id, recipe_id)
    
    async def get_personalized_weights(self, user_id: int) -> Dict[str, float]:
        """Get personalized scoring weights based on user history"""
        
        # Get user's interaction history
        history = await self._get_user_history(user_id)
        
        # Analyze patterns
        weights = self._default_weights.copy()
        
        # Adjust weights based on patterns
        if self._user_prioritizes_health(history):
            weights['nutritional_goal_match'] *= 1.5
            weights['dietary_restriction_match'] *= 1.2
        
        if self._user_likes_quick_meals(history):
            weights['cooking_time_match'] *= 1.8
        
        if self._user_explores_cuisines(history):
            weights['preferred_cuisine_match'] *= 0.8  # Less weight on known cuisines
            weights['seasonal_match'] *= 1.3  # More variety
        
        return weights
    
    async def suggest_new_preferences(self, user_id: int) -> List[Dict]:
        """Suggest new preferences based on user behavior"""
        
        suggestions = []
        history = await self._get_user_history(user_id)
        
        # Analyze frequently used ingredients
        ingredient_counts = self._count_ingredients_in_history(history)
        top_ingredients = sorted(
            ingredient_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        current_favorites = await self._get_user_favorite_ingredients(user_id)
        
        for ingredient, count in top_ingredients:
            if ingredient not in current_favorites and count >= 5:
                suggestions.append({
                    'type': 'favorite_ingredient',
                    'value': ingredient,
                    'reason': f'You\'ve used {ingredient} in {count} recipes recently'
                })
        
        # Analyze cuisine patterns
        cuisine_counts = self._count_cuisines_in_history(history)
        for cuisine, count in cuisine_counts.items():
            if count >= 3:
                suggestions.append({
                    'type': 'cuisine_preference',
                    'value': cuisine,
                    'reason': f'You\'ve enjoyed {count} {cuisine} recipes'
                })
        
        return suggestions
```

### 4. Context-Aware Response Generation

Improve response formatting based on context:

```python
# services/response_formatter_service.py
class ResponseFormatterService:
    """Format responses based on context and user preferences"""
    
    def format_recipe_response(
        self, 
        recipes: List[Dict], 
        context: Dict, 
        user_preferences: Dict
    ) -> str:
        """Generate contextual responses"""
        
        # Determine response style based on context
        if context.get('health_focus') == 'diet':
            return self._format_diet_focused_response(recipes)
        
        if context.get('time_constraint', {}).get('preference') == 'quick':
            return self._format_time_focused_response(recipes)
        
        if context.get('special_requirements', {}).get('guests'):
            return self._format_entertaining_response(recipes)
        
        # Default formatting with personalization
        response_parts = []
        
        # Greeting based on meal type and time
        greeting = self._get_contextual_greeting(context)
        response_parts.append(greeting)
        
        # Highlight matching preferences
        if recipes and recipes[0].get('score_reasoning'):
            top_reasons = recipes[0]['score_reasoning'][:2]
            response_parts.append(
                f"I found recipes that {' and '.join(top_reasons).lower()}!"
            )
        
        # Special callouts
        perfect_matches = [r for r in recipes if r.get('missing_count', 0) == 0]
        if perfect_matches:
            response_parts.append(
                f"✨ {len(perfect_matches)} recipes need no additional ingredients!"
            )
        
        expiring_used = [
            r for r in recipes 
            if r.get('evaluation', {}).get('uses_expiring')
        ]
        if expiring_used:
            response_parts.append(
                f"🕐 {len(expiring_used)} recipes use your expiring items"
            )
        
        return "\n\n".join(response_parts)
```

## Medium-term Improvements (1-2 weeks)

### 1. Multi-source Recipe Aggregation

```python
# services/recipe_aggregator_service.py
class RecipeAggregatorService:
    """Aggregate recipes from multiple sources"""
    
    def __init__(self):
        self.sources = {
            'spoonacular': SpoonacularService(),
            'edamam': EdamamService(),  # New
            'yummly': YummlyService(),   # New
            'internal': InternalRecipeService(),  # User-created
            'community': CommunityRecipeService()  # Shared recipes
        }
    
    async def get_aggregated_recipes(
        self, 
        query: Dict, 
        user_preferences: Dict
    ) -> List[Dict]:
        """Get recipes from all sources"""
        
        # Parallel fetch from all sources
        tasks = []
        for source_name, service in self.sources.items():
            if self._should_use_source(source_name, user_preferences):
                tasks.append(
                    self._fetch_from_source(source_name, service, query)
                )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate
        all_recipes = []
        seen_signatures = set()
        
        for source_recipes in results:
            if isinstance(source_recipes, Exception):
                continue
                
            for recipe in source_recipes:
                signature = self._get_recipe_signature(recipe)
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    recipe['sources'] = [recipe.get('source', 'unknown')]
                    all_recipes.append(recipe)
        
        return all_recipes
```

### 2. Nutritional Intelligence

```python
# services/nutrition_intelligence_service.py
class NutritionIntelligenceService:
    """Provide intelligent nutritional analysis and recommendations"""
    
    def analyze_meal_balance(
        self, 
        recipes: List[Dict], 
        user_goals: Dict
    ) -> Dict:
        """Analyze nutritional balance of recipes"""
        
        analysis = {
            'balanced_meals': [],
            'protein_rich': [],
            'low_calorie': [],
            'high_fiber': [],
            'recommendations': []
        }
        
        for recipe in recipes:
            nutrition = recipe.get('nutrition', {})
            
            # Categorize by nutritional profile
            if self._is_balanced_meal(nutrition):
                analysis['balanced_meals'].append(recipe)
            
            if nutrition.get('protein', 0) >= 25:
                analysis['protein_rich'].append(recipe)
            
            if nutrition.get('calories', 999) <= 400:
                analysis['low_calorie'].append(recipe)
            
            if nutrition.get('fiber', 0) >= 5:
                analysis['high_fiber'].append(recipe)
        
        # Generate recommendations
        if user_goals.get('weight_loss'):
            analysis['recommendations'].append(
                "Focus on the low-calorie, high-fiber options for satiety"
            )
        
        if user_goals.get('muscle_gain'):
            analysis['recommendations'].append(
                "Prioritize protein-rich meals with adequate calories"
            )
        
        return analysis
```

### 3. Smart Meal Planning

```python
# services/meal_planning_service.py
class MealPlanningService:
    """Generate intelligent meal plans"""
    
    async def generate_weekly_plan(
        self, 
        user_id: int, 
        preferences: Dict
    ) -> Dict:
        """Generate a balanced weekly meal plan"""
        
        plan = {
            'monday': {},
            'tuesday': {},
            'wednesday': {},
            'thursday': {},
            'friday': {},
            'saturday': {},
            'sunday': {}
        }
        
        # Get pantry items
        pantry = await self._get_pantry_items(user_id)
        
        # Track nutritional balance across the week
        weekly_nutrition = {
            'total_calories': 0,
            'total_protein': 0,
            'cuisine_variety': set(),
            'used_ingredients': set()
        }
        
        for day in plan.keys():
            # Generate meals for the day
            daily_meals = await self._generate_daily_meals(
                user_id,
                pantry,
                preferences,
                weekly_nutrition,
                day
            )
            
            plan[day] = daily_meals
            
            # Update weekly tracking
            self._update_weekly_nutrition(weekly_nutrition, daily_meals)
        
        return {
            'meal_plan': plan,
            'shopping_list': self._generate_shopping_list(plan, pantry),
            'nutritional_summary': self._summarize_nutrition(weekly_nutrition),
            'variety_score': self._calculate_variety_score(plan)
        }
```

## Long-term Improvements (1+ months)

### 1. Machine Learning Integration

```python
# services/ml_recommendation_service.py
import tensorflow as tf
from sklearn.feature_extraction.text import TfidfVectorizer

class MLRecommendationService:
    """ML-powered recipe recommendations"""
    
    def __init__(self):
        self.user_embedding_model = self._load_user_model()
        self.recipe_embedding_model = self._load_recipe_model()
        self.interaction_predictor = self._load_interaction_model()
    
    async def get_ml_recommendations(
        self, 
        user_id: int, 
        context: Dict
    ) -> List[Dict]:
        """Get ML-based recommendations"""
        
        # Get user embedding
        user_features = await self._extract_user_features(user_id)
        user_embedding = self.user_embedding_model.predict(user_features)
        
        # Get candidate recipes
        candidates = await self._get_candidate_recipes(context)
        
        # Score each recipe
        scored_recipes = []
        for recipe in candidates:
            recipe_features = self._extract_recipe_features(recipe)
            recipe_embedding = self.recipe_embedding_model.predict(recipe_features)
            
            # Predict interaction probability
            interaction_prob = self.interaction_predictor.predict([
                user_embedding,
                recipe_embedding,
                self._extract_context_features(context)
            ])
            
            recipe['ml_score'] = float(interaction_prob)
            scored_recipes.append(recipe)
        
        # Sort by ML score
        return sorted(scored_recipes, key=lambda x: x['ml_score'], reverse=True)
```

### 2. Social Features

```python
# services/social_recipe_service.py
class SocialRecipeService:
    """Social features for recipe sharing and discovery"""
    
    async def get_trending_recipes(self, user_id: int) -> List[Dict]:
        """Get trending recipes in user's network"""
        
        # Get user's connections
        connections = await self._get_user_connections(user_id)
        
        # Get recipes trending among connections
        trending = await self._get_trending_among_users(
            connections, 
            time_window=timedelta(days=7)
        )
        
        return trending
    
    async def share_recipe_with_notes(
        self, 
        user_id: int, 
        recipe_id: str, 
        notes: Dict
    ):
        """Share a recipe with personal notes"""
        
        share_data = {
            'user_id': user_id,
            'recipe_id': recipe_id,
            'personal_notes': notes.get('notes'),
            'modifications': notes.get('modifications'),
            'rating': notes.get('rating'),
            'photos': notes.get('photos'),
            'shared_with': notes.get('share_with', 'public')
        }
        
        await self._create_recipe_share(share_data)
```

## Implementation Priority

### Week 1:
1. ✅ Implement MessageContextService
2. ✅ Enhance recipe matching with IngredientMatcherService
3. ✅ Add basic preference learning

### Week 2:
4. ⏳ Add nutrition intelligence
5. ⏳ Implement response formatting improvements
6. ⏳ Start collecting interaction data

### Week 3-4:
7. ⏳ Multi-source recipe aggregation
8. ⏳ Basic meal planning features
9. ⏳ A/B testing framework

### Month 2+:
10. ⏳ ML model development
11. ⏳ Social features
12. ⏳ Advanced personalization

## Success Metrics

1. **User Engagement**:
   - Recipe interaction rate (view → cook)
   - Preference update frequency
   - Return user rate

2. **Recommendation Quality**:
   - Click-through rate on recipes
   - Recipe completion rate
   - User satisfaction scores

3. **System Performance**:
   - Response time < 2 seconds
   - 99.9% uptime
   - Successful recipe matches > 90%

## Testing Strategy

1. **Unit Tests**: Each new service
2. **Integration Tests**: End-to-end flows
3. **A/B Testing**: Algorithm variations
4. **User Testing**: Beta group feedback
5. **Performance Testing**: Load and scale