# Enhanced AI Recipe Generation Prompt

## Updated Prompt Structure

```python
prompt = f"""
You are a creative chef. Generate 5-8 recipes based on ONLY these available ingredients:
{', '.join(available_ingredients)}

User request: {message}
{expiring_instruction}

IMPORTANT User Preferences:
- Dietary restrictions: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
- Allergens to avoid: {', '.join(allergens) if allergens else 'None'}
- Favorite cuisines: {', '.join(cuisine_prefs) if cuisine_prefs else 'Any'}

Return a JSON array of recipes. Each recipe MUST have ALL these fields:

{
  "id": "ai-recipe-1",  // unique identifier
  "title": "Recipe Name",
  "readyInMinutes": 30,
  "servings": 4,
  "summary": "Brief description",
  
  "extendedIngredients": [
    {
      "id": 1,
      "name": "chicken breast",
      "original": "2 pounds chicken breast, boneless and skinless",
      "amount": 2,
      "unit": "pound"
    }
  ],
  
  "instructions": [
    {
      "number": 1,
      "step": "Detailed cooking instruction"
    }
  ],
  
  "nutrition": {
    "calories": 420,
    "protein": 35,      // grams
    "carbs": 25,        // grams
    "fat": 18,          // grams
    "fiber": 3,         // grams
    "sugar": 5,         // grams
    "sodium": 650       // milligrams
  },
  
  "taste": {
    "sweetness": 15,    // 0-100 scale
    "saltiness": 45,    // 0-100 scale
    "sourness": 10,     // 0-100 scale
    "bitterness": 5,    // 0-100 scale
    "savoriness": 65,   // 0-100 scale (umami)
    "fattiness": 35,    // 0-100 scale
    "spiciness": 20     // 0-100 scale
  },
  
  "difficulty": {
    "level": "easy",           // easy, intermediate, or advanced
    "prep_time": 10,           // minutes
    "cook_time": 20,           // minutes
    "total_time": 30,          // minutes
    "skill_requirements": []   // e.g., ["knife skills", "grilling", "baking"]
  },
  
  "equipment": ["skillet", "knife", "cutting board"],
  
  "cost_estimate": {
    "per_serving": 3.50,      // USD estimate
    "total": 14.00            // USD estimate
  },
  
  "meal_type": "dinner",      // breakfast, lunch, dinner, snack
  "cuisine_type": "italian",  // specific cuisine
  "dietary_tags": ["gluten-free", "high-protein"],
  
  "tags": ["quick", "healthy", "family-friendly", "one-pot"]
}

TASTE PROFILE GUIDELINES:
- Sweetness: desserts (70-90), breakfast items (30-60), savory dishes (0-20)
- Saltiness: soups/broths (60-80), main dishes (40-60), desserts (5-15)
- Sourness: citrus dishes (50-70), vinegar-based (40-60), most dishes (5-20)
- Bitterness: dark leafy greens (40-60), coffee-based (50-70), most dishes (0-10)
- Savoriness: meat dishes (60-80), mushroom dishes (70-90), vegetable dishes (30-50)
- Fattiness: fried foods (70-90), creamy dishes (50-70), lean dishes (10-30)
- Spiciness: mild (10-30), medium (40-60), hot (70-90), no spice (0)

DIFFICULTY GUIDELINES:
- Easy: < 5 ingredients, < 30 min total, basic techniques
- Intermediate: 5-10 ingredients, 30-60 min, some skill needed
- Advanced: > 10 ingredients, > 60 min, special techniques

NUTRITION ESTIMATION:
- Base estimates on standard portion sizes
- Consider cooking methods (frying adds fat, grilling reduces it)
- Account for all ingredients including oils and seasonings

Return ONLY the JSON array, no other text.
"""
```

## Benefits of Enhanced Data

### 1. **Taste Profile Learning**
- Track user preferences across taste dimensions
- Recommend recipes matching preferred taste profiles
- Avoid recipes with disliked taste characteristics

### 2. **Skill Level Matching**
- Suggest recipes appropriate to user's cooking experience
- Gradually increase complexity as users improve
- Filter out recipes requiring unavailable equipment

### 3. **Budget Awareness**
- Help users plan meals within budget
- Show cost comparisons between recipes
- Track spending over time

### 4. **Nutritional Goals**
- Support specific diets (keto, high-protein, low-sodium)
- Track macro and micronutrients
- Suggest balanced meal combinations

### 5. **Better Filtering**
- Quick weeknight meals (< 30 minutes)
- One-pot dishes (minimal cleanup)
- Family-friendly options
- Special occasion recipes

## Implementation Priority

1. **Phase 1** (Required Now):
   - Taste profiles
   - Complete nutrition data
   - Difficulty level

2. **Phase 2** (Nice to Have):
   - Equipment requirements
   - Cost estimates
   - Skill requirements

3. **Phase 3** (Future):
   - Wine pairings
   - Seasonal appropriateness
   - Cultural authenticity scores

## Testing the Enhanced Prompt

```python
def validate_ai_recipe(recipe):
    """Validate that AI recipe has all required fields"""
    required_fields = [
        'id', 'title', 'readyInMinutes', 'servings', 'summary',
        'extendedIngredients', 'instructions', 'nutrition', 'taste',
        'difficulty', 'meal_type', 'cuisine_type', 'dietary_tags'
    ]
    
    nutrition_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
    taste_fields = ['sweetness', 'saltiness', 'sourness', 'bitterness', 'savoriness', 'fattiness', 'spiciness']
    difficulty_fields = ['level', 'prep_time', 'cook_time', 'total_time']
    
    # Check all required fields exist
    for field in required_fields:
        assert field in recipe, f"Missing required field: {field}"
    
    # Validate nutrition
    for field in nutrition_fields:
        assert field in recipe['nutrition'], f"Missing nutrition field: {field}"
    
    # Validate taste (0-100 range)
    for field in taste_fields:
        assert field in recipe['taste'], f"Missing taste field: {field}"
        assert 0 <= recipe['taste'][field] <= 100, f"Taste {field} out of range"
    
    # Validate difficulty
    for field in difficulty_fields:
        assert field in recipe['difficulty'], f"Missing difficulty field: {field}"
    
    return True
```

## Cost Considerations

The enhanced prompt will increase token usage by approximately:
- Input: +500 tokens (detailed guidelines)
- Output: +200 tokens per recipe (additional fields)

For 5 recipes:
- Current: ~2000 tokens
- Enhanced: ~3000 tokens

This is still well within reasonable limits for GPT-3.5-turbo.