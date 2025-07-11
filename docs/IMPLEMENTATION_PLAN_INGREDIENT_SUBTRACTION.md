# Implementation Plan: Ingredient Subtraction & Preference System

## Priority 1: Fix Ingredient Subtraction Logic

### Current Issues
1. Unit conversion mismatches between pantry items and recipe requirements
2. Ingredient name matching (exact vs fuzzy matching)
3. Partial quantity usage tracking
4. Demo data alignment with recipe formats

### Implementation Steps

#### Step 1: Enhance Ingredient Matching Logic
```python
# backend_gateway/services/ingredient_matching_service.py

class IngredientMatcher:
    def __init__(self):
        self.unit_converter = UnitConverter()
        self.name_normalizer = IngredientNameNormalizer()
    
    def match_pantry_to_recipe(self, pantry_item, recipe_ingredient):
        """
        Match pantry items to recipe ingredients with:
        - Fuzzy name matching
        - Unit conversion
        - Quantity validation
        """
        # Normalize names
        pantry_name = self.name_normalizer.normalize(pantry_item['product_name'])
        recipe_name = self.name_normalizer.normalize(recipe_ingredient['name'])
        
        # Check name similarity
        if not self.is_similar(pantry_name, recipe_name):
            return None
            
        # Convert units to common base
        pantry_qty = self.unit_converter.to_base_unit(
            pantry_item['quantity'],
            pantry_item['unit_of_measurement']
        )
        
        recipe_qty = self.unit_converter.to_base_unit(
            recipe_ingredient['amount'],
            recipe_ingredient['unit']
        )
        
        return {
            'pantry_item_id': pantry_item['pantry_item_id'],
            'available': pantry_qty,
            'required': recipe_qty,
            'sufficient': pantry_qty >= recipe_qty
        }
```

#### Step 2: Implement Comprehensive Unit Converter
```python
# backend_gateway/services/unit_converter.py

class UnitConverter:
    # Volume conversions (to ml)
    VOLUME_TO_ML = {
        'ml': 1,
        'l': 1000,
        'cup': 236.588,
        'cups': 236.588,
        'tbsp': 14.787,
        'tablespoon': 14.787,
        'tsp': 4.929,
        'teaspoon': 4.929,
        'fl oz': 29.574,
        'pint': 473.176,
        'quart': 946.353,
        'gallon': 3785.41
    }
    
    # Weight conversions (to grams)
    WEIGHT_TO_GRAMS = {
        'g': 1,
        'gram': 1,
        'kg': 1000,
        'oz': 28.3495,
        'ounce': 28.3495,
        'lb': 453.592,
        'pound': 453.592
    }
    
    # Special handling for common ingredients
    INGREDIENT_DENSITY = {
        'flour': 0.593,  # g/ml
        'sugar': 0.845,
        'butter': 0.911,
        'milk': 1.03,
        'oil': 0.92
    }
```

#### Step 3: Update Recipe Consumption Endpoint
```python
# backend_gateway/routers/recipe_consumption_router.py

@router.post("/cook-with-subtraction")
async def cook_recipe_with_smart_subtraction(request: CookRecipeRequest):
    """
    Enhanced cooking endpoint with:
    - Smart ingredient matching
    - Unit conversion
    - Partial usage tracking
    - Substitution suggestions
    """
    matcher = IngredientMatcher()
    pantry_service = get_pantry_service()
    
    results = {
        'matched': [],
        'missing': [],
        'substitutable': [],
        'warnings': []
    }
    
    # Get user's pantry items
    pantry_items = await pantry_service.get_user_pantry_items(request.user_id)
    
    # Process each recipe ingredient
    for recipe_ing in request.recipe['extendedIngredients']:
        matches = []
        
        # Try to match with pantry items
        for pantry_item in pantry_items:
            match = matcher.match_pantry_to_recipe(pantry_item, recipe_ing)
            if match:
                matches.append(match)
        
        if matches:
            # Use best match (most available)
            best_match = max(matches, key=lambda x: x['available'])
            results['matched'].append(best_match)
        else:
            # Check for substitutes
            substitutes = await get_ingredient_substitutes(recipe_ing['id'])
            results['missing'].append({
                'ingredient': recipe_ing,
                'substitutes': substitutes
            })
    
    return results
```

### Testing Strategy

#### 1. Unit Tests
```python
def test_unit_conversion():
    converter = UnitConverter()
    
    # Volume tests
    assert converter.convert(2, 'cup', 'ml') == 473.176
    assert converter.convert(500, 'ml', 'cup') == 2.11
    
    # Weight tests
    assert converter.convert(1, 'lb', 'g') == 453.592
    assert converter.convert(100, 'g', 'oz') == 3.527
    
    # Cross-category with density
    assert converter.convert_with_density(1, 'cup', 'g', 'flour') == 140.0
```

#### 2. Integration Tests
- Test with demo recipes (pasta, cookies, chicken)
- Verify pantry updates after cooking
- Check edge cases (insufficient quantities, missing items)

#### 3. User Acceptance Tests
- Cook a recipe with exact ingredients
- Cook with partial ingredients
- Handle unit mismatches
- Suggest substitutions

## Priority 2: User Preference Learning System

### Phase 1: Basic Preference Tracking

#### Database Schema
```sql
-- Core preference tables
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    dietary_restrictions JSONB DEFAULT '[]',
    allergens JSONB DEFAULT '[]',
    cuisine_preferences JSONB DEFAULT '[]',
    disliked_ingredients JSONB DEFAULT '[]',
    cooking_skill_level VARCHAR(50),
    max_cooking_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipe_ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    recipe_id VARCHAR(100),
    recipe_source VARCHAR(50), -- 'spoonacular' or 'ai'
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    would_cook_again BOOLEAN,
    difficulty_rating INTEGER CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
    taste_notes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cooking_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    recipe_id VARCHAR(100),
    cooked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    servings_made INTEGER,
    leftovers BOOLEAN,
    modifications JSONB,
    context JSONB -- time_of_day, weather, occasion
);
```

#### API Endpoints
```python
# backend_gateway/routers/preferences_router.py

@router.post("/preferences/rate-recipe")
async def rate_recipe(
    user_id: int,
    recipe_id: str,
    rating: int,
    taste_feedback: Optional[Dict] = None
):
    """Rate a recipe and update taste preferences"""
    
@router.get("/preferences/profile/{user_id}")
async def get_preference_profile(user_id: int):
    """Get comprehensive preference profile"""
    
@router.post("/preferences/learn-from-history")
async def learn_from_cooking_history(user_id: int):
    """Analyze cooking history to infer preferences"""
```

### Phase 2: Taste Profile Integration

#### Fetch and Store Taste Profiles
```python
async def enrich_recipe_with_taste(recipe_id: str):
    """Fetch taste profile from Spoonacular"""
    if recipe_id.startswith('ai-'):
        # Estimate taste for AI recipes
        return estimate_taste_from_ingredients(recipe)
    else:
        # Fetch from Spoonacular
        taste_data = await spoonacular.get_taste_profile(recipe_id)
        return {
            'sweetness': taste_data['sweetness'],
            'saltiness': taste_data['saltiness'],
            'sourness': taste_data['sourness'],
            'bitterness': taste_data['bitterness'],
            'savoriness': taste_data['savoriness'],
            'fattiness': taste_data['fattiness'],
            'spiciness': taste_data['spiciness']
        }
```

#### Learn User Taste Preferences
```python
def update_taste_preferences(user_id: int, recipe_id: str, rating: int):
    """Update user's taste preferences based on recipe rating"""
    
    # Get recipe's taste profile
    taste_profile = await get_recipe_taste_profile(recipe_id)
    
    # Get user's current preferences
    user_prefs = await get_user_taste_preferences(user_id)
    
    # Update preferences with weighted average
    learning_rate = 0.1  # How much new data influences preferences
    
    for dimension in taste_profile:
        if rating >= 4:  # Liked recipe
            # Move preferences toward this taste
            user_prefs[dimension]['preferred'] += (
                learning_rate * (taste_profile[dimension] - user_prefs[dimension]['preferred'])
            )
        elif rating <= 2:  # Disliked recipe
            # Move preferences away from this taste
            user_prefs[dimension]['preferred'] -= (
                learning_rate * (taste_profile[dimension] - user_prefs[dimension]['preferred'])
            )
    
    # Save updated preferences
    await save_user_taste_preferences(user_id, user_prefs)
```

### Phase 3: Enhanced Recipe Recommendations

#### Recommendation Algorithm
```python
async def get_personalized_recommendations(
    user_id: int,
    available_ingredients: List[str],
    context: Dict
):
    """Generate personalized recipe recommendations"""
    
    # Get user preferences
    preferences = await get_user_preferences(user_id)
    taste_profile = await get_user_taste_preferences(user_id)
    cooking_history = await get_recent_cooking_history(user_id)
    
    # Search for base recipes
    if context.get('use_ai'):
        recipes = await crew_ai.generate_recipes(
            ingredients=available_ingredients,
            preferences=preferences,
            context=context
        )
    else:
        recipes = await spoonacular.search_by_ingredients(
            ingredients=available_ingredients,
            diet=preferences.get('dietary_restrictions'),
            intolerances=preferences.get('allergens')
        )
    
    # Score and rank recipes
    scored_recipes = []
    for recipe in recipes:
        score = calculate_recipe_score(
            recipe=recipe,
            taste_preferences=taste_profile,
            cooking_history=cooking_history,
            context=context
        )
        scored_recipes.append((score, recipe))
    
    # Sort by score and return top recommendations
    scored_recipes.sort(key=lambda x: x[0], reverse=True)
    return [recipe for score, recipe in scored_recipes[:10]]
```

## Testing Plan

### 1. Ingredient Subtraction Tests
- [ ] Test exact ingredient matches
- [ ] Test fuzzy name matching
- [ ] Test unit conversions (volume, weight, count)
- [ ] Test insufficient quantity handling
- [ ] Test substitute suggestions
- [ ] Test pantry updates after cooking

### 2. Preference System Tests
- [ ] Test preference storage and retrieval
- [ ] Test rating system
- [ ] Test taste profile learning
- [ ] Test recommendation scoring
- [ ] Test dietary restriction filtering
- [ ] Test context-aware recommendations

### 3. Integration Tests
- [ ] End-to-end cooking flow
- [ ] Preference learning from cooking history
- [ ] Recommendation accuracy over time
- [ ] Performance with large datasets

## Rollout Strategy

### Week 1-2: Ingredient Subtraction
1. Implement unit converter
2. Create ingredient matcher
3. Update consumption endpoint
4. Test with demo data
5. Deploy to staging

### Week 3-4: Basic Preferences
1. Create database schema
2. Implement preference API
3. Add rating system
4. Create preference UI
5. Deploy basic version

### Week 5-6: Taste Profiles
1. Integrate Spoonacular taste API
2. Implement taste learning
3. Add to recommendation scoring
4. Test preference evolution
5. Deploy enhanced version

### Week 7-8: Advanced Features
1. Context-aware recommendations
2. Meal planning integration
3. Social preferences
4. Performance optimization
5. Full production deployment

## Success Criteria

### Ingredient Subtraction
- 95% accuracy in ingredient matching
- Correct unit conversions for 90% of common cases
- Successful pantry updates after cooking
- User satisfaction with subtraction accuracy

### Preference System
- 80% of users rate at least 5 recipes
- 70% recommendation acceptance rate
- Improved cooking frequency by 25%
- Reduced food waste by 20%

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Implement caching and batch requests
- **Data Privacy**: Clear consent and data control options
- **Performance**: Optimize database queries and use indexes

### User Experience Risks
- **Complexity**: Progressive disclosure of features
- **Trust**: Explainable recommendations
- **Adoption**: Gamification and incentives