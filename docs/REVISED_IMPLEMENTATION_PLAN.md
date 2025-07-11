# Revised Implementation Plan

## Overview
Focus on fixing core functionality (ingredient subtraction) first, then add preference learning without complex taste profiles.

## Phase 1: Enhanced AI Recipe Data (Week 1, Day 1)
**Goal**: Update AI recipes to match data quality needed for proper tracking

### Tasks:
1. **Update CrewAI Recipe Prompt**
   - Add complete nutrition fields (carbs, fat, fiber, sugar, sodium)
   - Add difficulty information (level, prep_time, cook_time)
   - Add tags array for filtering
   - Keep existing extendedIngredients format

### Implementation:
```python
# Update in crew_ai_service.py line ~290-360
# Add to the recipe format example:
"nutrition": {
    "calories": 420,
    "protein": 35,
    "carbs": 45,
    "fat": 18,
    "fiber": 5,
    "sugar": 8,
    "sodium": 650
},
"difficulty": {
    "level": "easy",
    "prep_time": 10,
    "cook_time": 20,
    "total_time": 30
},
"tags": ["quick", "one-pot", "weeknight"]
```

## Phase 2: Fix Ingredient Subtraction (Week 1, Days 2-4)
**Goal**: Accurately match and subtract ingredients with proper unit conversion

### Tasks:
1. **Create Unit Converter Service**
   ```python
   backend_gateway/services/unit_converter.py
   - Volume conversions (ml, l, cup, tbsp, tsp, oz, etc.)
   - Weight conversions (g, kg, lb, oz)
   - Count conversions (each, dozen)
   - Density mappings for common ingredients
   ```

2. **Create Ingredient Matching Service**
   ```python
   backend_gateway/services/ingredient_matcher.py
   - Fuzzy name matching (pasta = spaghetti, etc.)
   - Handle brand names and modifiers
   - Match by category when exact match fails
   ```

3. **Update Recipe Consumption Router**
   ```python
   backend_gateway/routers/recipe_consumption_router.py
   - Use new matching service
   - Handle unit conversions
   - Track partial usage
   - Suggest substitutions for missing items
   ```

4. **Fix Test/Reset Features**
   - Ensure demo data reset works properly
   - Add test recipes that use exact pantry items
   - Create admin panel UI for test/reset

### Testing:
- Unit tests for converters
- Integration tests with demo recipes
- End-to-end cooking flow tests

## Phase 3: Test & Debug (Week 1, Day 5)
**Goal**: Ensure ingredient subtraction works reliably

### Tasks:
1. Test all demo recipes (pasta, cookies, chicken)
2. Test edge cases:
   - Insufficient quantities
   - Missing ingredients
   - Unit mismatches
   - Multiple pantry items for same ingredient
3. Fix any bugs found
4. Deploy to staging

## Phase 4: Simple Preference System (Week 2, Days 1-3)
**Goal**: Track user preferences without complex taste profiles

### Database Schema:
```sql
CREATE TABLE recipe_ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    recipe_id VARCHAR(100),
    recipe_source VARCHAR(20), -- 'ai' or 'spoonacular'
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    would_cook_again BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cooking_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    recipe_id VARCHAR(100),
    cooked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingredients_used JSONB,
    modifications JSONB
);
```

### API Endpoints:
```python
POST /api/recipes/rate
GET /api/users/{user_id}/preferences
GET /api/users/{user_id}/cooking-history
```

### Preference Learning (Simple):
- Track 5-star ratings
- Monitor cooking frequency
- Note cuisine preferences
- Track nutritional patterns
- Learn time preferences (quick vs elaborate)

## Phase 5: Enhanced Recommendations (Week 2, Days 4-5)
**Goal**: Use learned preferences for better recommendations

### Implementation:
1. **Recipe Scoring Without Taste**:
   ```python
   score = (
       ingredient_match_score * 0.35 +
       dietary_compliance * 0.25 +
       cuisine_preference * 0.15 +
       time_appropriateness * 0.15 +
       nutrition_match * 0.10
   )
   ```

2. **Behavioral Learning**:
   - Recipes cooked multiple times = strong preference
   - High ratings = preferred style
   - Consistent cuisine choices = cuisine preference
   - Average cooking time = time preference

3. **Context Awareness**:
   - Time of day → breakfast/lunch/dinner
   - Weekday vs weekend → quick vs elaborate
   - Previous meals → variety

## Success Metrics

### Phase 1-3 (Ingredient Subtraction):
- ✓ 95% accuracy in ingredient matching
- ✓ Correct unit conversions
- ✓ Successful pantry updates after cooking
- ✓ Demo recipes work without errors

### Phase 4-5 (Preferences):
- ✓ 70% of users rate at least 3 recipes
- ✓ Recommendations match user patterns
- ✓ Increased cooking frequency
- ✓ Reduced "no ingredients" scenarios

## Timeline Summary

**Week 1**:
- Day 1: Update AI recipe format ⚡
- Days 2-4: Implement ingredient subtraction 🔧
- Day 5: Test and debug 🐛

**Week 2**:
- Days 1-3: Basic preference system 📊
- Days 4-5: Enhanced recommendations 🎯

## Risk Mitigation

### Technical Risks:
- **Unit conversion complexity**: Start with common units, add edge cases later
- **Name matching accuracy**: Use fuzzy matching with confidence thresholds
- **Performance**: Cache conversions and matches

### User Experience:
- **Adoption**: Make rating super easy (one tap)
- **Trust**: Show why recipes were recommended
- **Flexibility**: Allow manual preference adjustments

## Next Action Items

1. [ ] Update CrewAI prompt with enhanced recipe format
2. [ ] Create unit_converter.py with basic conversions
3. [ ] Create ingredient_matcher.py with fuzzy matching
4. [ ] Update recipe consumption endpoint
5. [ ] Write comprehensive tests
6. [ ] Deploy and test with real users

This revised plan focuses on:
- **Practical implementation** without complex taste analysis
- **Core functionality first** (ingredient subtraction)
- **Simple but effective** preference learning
- **Quick wins** that provide immediate value