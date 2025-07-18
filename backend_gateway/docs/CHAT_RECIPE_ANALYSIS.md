# Chat/Recipe Recommendation System Analysis

## Current System Architecture

### 1. **Request Flow**
```
User Message → Chat Router → CrewAI Service → Recipe Sources → Preference Scorer → Ranked Results
```

### 2. **Key Components**

#### a) **Chat Router** (`chat_router.py`)
- Receives user messages with preferences flag
- Detects preference usage intent
- Routes to CrewAI service

#### b) **CrewAI Service** (`crew_ai_service.py`)
Main orchestrator that:
1. Fetches pantry items
2. Fetches user preferences (if enabled)
3. Analyzes pantry with RecipeAdvisor
4. Gets saved recipes matching pantry
5. Gets Spoonacular recipes
6. Combines and ranks all recipes
7. Formats response

#### c) **Recipe Sources**
- **Saved Recipes**: User's bookmarked/liked recipes from database
- **Spoonacular API**: External recipe database with filtering
- **OpenAI Service**: DEPRECATED - was used for AI-generated recipes

#### d) **Recipe Preference Scorer** (`recipe_preference_scorer.py`)
Comprehensive scoring system with weighted factors:
- Favorite ingredient match: 3.0
- Preferred cuisine match: 2.5
- Dietary restriction match: 5.0 (highest)
- Cooking time match: 2.0
- Highly rated similar: 4.0
- Frequently cooked ingredient: 2.5
- Seasonal match: 1.5
- Expiring ingredient use: 3.5
- Nutritional goal match: 2.0

Negative weights:
- Disliked cuisine: -4.0
- Disliked ingredient: -3.0
- Too complex: -2.0
- Poor rating similar: -3.5
- Allergen present: -10.0 (extreme negative)
- Missing key equipment: -2.5

### 3. **User Data Sources**

#### Database Tables:
- `user_preferences`: JSONB with dietary restrictions, allergens, cuisines
- `user_allergens`: Specific allergen list
- `user_dietary_preferences`: Dietary restrictions
- `user_cuisine_preferences`: Cuisine preferences with preference_level
- `user_recipes`: Saved recipes with ratings and favorites
- `pantry_items`: Current inventory with expiration dates

### 4. **Message Processing**

#### Meal Type Detection:
- Searches for keywords: breakfast, lunch, dinner, snack, dessert
- Defaults to dinner if not specified
- Checks both user message and recipe titles

#### Special Queries:
- **Expiring items**: "expiring", "expire", "going bad", "use soon"
- **Available only**: "only ingredients i have", "without shopping"
- **Quick meals**: "quick", "fast", "easy"

### 5. **Recipe Matching Process**

1. **Ingredient Matching**:
   - Cleans ingredient names (removes sizes, brands, modifiers)
   - Uses fuzzy matching for variations (chicken → chicken breast)
   - Maps recipe ingredients to pantry items

2. **Allergen Detection**:
   - Maps allergen categories to ingredient patterns
   - Checks each recipe ingredient against user allergens
   - Assigns -10.0 score for allergen presence

3. **Preference Matching**:
   - Cuisine type matching
   - Dietary tag matching (vegetarian, vegan, etc.)
   - Cooking time preferences

### 6. **Ranking Algorithm**

Primary sort by:
1. Preference score (0-100)
2. User's liked recipes (source='saved' + thumbs_up)
3. Uses expiring ingredients
4. Perfect match (missing_count=0)
5. Match score (available/total ingredients)
6. Fewer missing ingredients

## Current Limitations

### 1. **Preference Data**
- No user-specific ingredient likes/dislikes
- No cooking skill level tracking
- No equipment preferences
- Limited nutritional goal tracking

### 2. **Context Understanding**
- Basic keyword matching for meal types
- No seasonal awareness
- No time-of-day context
- No previous meal history

### 3. **Recipe Quality**
- Limited recipe sources (mainly Spoonacular)
- No user feedback loop for recommendations
- No collaborative filtering

### 4. **Personalization**
- Generic scoring weights for all users
- No learning from user behavior
- No A/B testing of recommendations

## Improvement Opportunities

### 1. **Enhanced User Profiling**
```python
user_profile = {
    'cooking_skill': 'intermediate',
    'available_time': {'weekday': 30, 'weekend': 60},
    'equipment': ['oven', 'stovetop', 'slow_cooker'],
    'favorite_ingredients': ['chicken', 'pasta', 'tomatoes'],
    'disliked_ingredients': ['mushrooms', 'olives'],
    'meal_history': [...],  # Last 30 days
    'nutritional_goals': {
        'daily_calories': 2000,
        'protein_target': 60,
        'low_carb': True
    }
}
```

### 2. **Advanced Context Detection**
```python
def extract_context(message: str, user_id: int) -> Dict:
    return {
        'meal_type': detect_meal_type(message),
        'time_constraint': extract_time_limit(message),
        'serving_size': extract_servings(message),
        'cuisine_preference': extract_cuisine(message),
        'cooking_method': extract_method(message),
        'dietary_override': extract_dietary(message),
        'occasion': detect_occasion(message),  # party, date, family
        'health_focus': detect_health_intent(message)  # healthy, comfort, diet
    }
```

### 3. **Machine Learning Integration**
- Collaborative filtering based on similar users
- Content-based filtering using recipe features
- Reinforcement learning from user feedback
- NLP for better message understanding

### 4. **Recipe Source Expansion**
- Multiple recipe APIs (Yummly, Edamam)
- User-generated recipes
- Restaurant-inspired recipes
- Cultural/authentic recipe sources

### 5. **Feedback Loop**
```python
# Track user interactions
user_feedback = {
    'recipe_id': 12345,
    'action': 'cooked',  # viewed, saved, cooked, rated
    'rating': 'thumbs_up',
    'cook_time_actual': 35,  # vs estimated 30
    'difficulty_feedback': 'easier_than_expected',
    'would_make_again': True,
    'modifications': ['used milk instead of cream']
}
```

### 6. **Smart Recommendations**
- Meal planning (weekly menus)
- Nutritional balance over time
- Budget optimization
- Seasonal ingredients
- Local availability

## Implementation Plan

### Phase 1: Data Collection
1. Add user interaction tracking
2. Implement feedback collection
3. Create user preference surveys

### Phase 2: Enhanced Profiling
1. Extend user preferences schema
2. Add ingredient preference tracking
3. Implement cooking history

### Phase 3: Algorithm Improvements
1. Implement context extraction
2. Add collaborative filtering
3. Improve allergen detection

### Phase 4: Testing & Optimization
1. A/B test recommendation algorithms
2. Optimize scoring weights per user
3. Add real-time learning

## Next Steps

1. **Immediate fixes**:
   - Better meal type detection
   - Improved expiring item prioritization
   - More granular preference tracking

2. **Short term**:
   - Add user feedback collection
   - Implement basic ML models
   - Expand recipe sources

3. **Long term**:
   - Full personalization system
   - Predictive meal planning
   - Social features (share recipes)