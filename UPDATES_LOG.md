# PrepSense Updates Log

## 2025-01-14: Recipe Recommendation System Overhaul

### Major Changes

1. **Simplified CrewAI Architecture**
   - Removed complex multi-agent system (6 agents → 1 advisor)
   - Eliminated CrewAI dependency - now optional
   - Reduced codebase by ~45% (950 → 520 lines)
   - Removed abstract "joy score" calculations

2. **New RecipeAdvisor Agent**
   - Single intelligent agent combining useful logic from original agents
   - Pantry analysis: Tracks expiring items, categorizes ingredients
   - Recipe evaluation: Nutritional balance, cooking complexity
   - Contextual advice generation based on user queries

3. **Hybrid Recipe Recommendations**
   - Integrates user's saved recipes from "My Recipes" feature
   - Prioritizes user's liked and favorite recipes
   - Generates 2-5 AI recipes to complement saved ones
   - Smart duplicate detection between sources

4. **Enhanced Recipe Matching**
   - New `match_recipes_with_pantry()` method in UserRecipesService
   - Extracts ingredients from saved recipe JSONB data
   - Calculates match scores for saved recipes
   - Shows which ingredients are available vs missing

5. **Practical Ranking System**
   - User's liked saved recipes (highest priority)
   - Favorite recipes
   - Recipes using expiring ingredients
   - Recipes you can make without shopping
   - Good nutritional balance
   - High ingredient match percentage

### Technical Improvements

- Better separation of concerns
- More maintainable code structure
- Reduced API calls by using saved recipes
- Faster response times for personalized recommendations
- Allergen detection retained for safety

### User Experience Enhancements

- Clear indication when recipes are from saved collection
- Contextual advice about recipe choices
- Expiring items prioritization
- Nutritional balance awareness
- Cooking complexity estimates

### Files Modified

- `backend_gateway/services/crew_ai_service.py` - Complete overhaul
- `backend_gateway/services/user_recipes_service.py` - Added pantry matching
- `ios-app/app/(tabs)/chat.tsx` - Removed joy score display
- `ios-app/app/recipe-details.tsx` - Removed joy score display
- `ios-app/services/api.ts` - Updated TypeScript interfaces

### New Documentation

- Created `App Features Reference/Recipe_Recommendation_System.md`
- Comprehensive documentation of the new system architecture

---

## 2025-01-11: Security Fixes

### GitGuardian Security Resolution
- Removed hardcoded credentials from multiple files
- Implemented environment variable usage throughout
- Installed GitGuardian pre-commit hooks
- Cleaned git history to remove exposed secrets

### Files Updated
- `backend_gateway/scripts/setup_iam_auth.py`
- `backend_gateway/scripts/grant_iam_permissions.py`
- `backend_gateway/DATABASE_MIGRATION_GUIDE.md`

---

## 2025-01-10: Ingredient Subtraction Feature

### New Feature: Automatic Pantry Updates
- Tracks ingredient consumption when recipes are completed
- Automatically subtracts used ingredients from pantry
- Smart quantity parsing and unit conversion
- Handles edge cases like unmarked recipes

### Implementation Details
- New `recipe_completion_service.py` for handling consumption
- Enhanced ingredient parsing with fuzzy matching
- Comprehensive test suite in `tests/ingredient-subtraction/`

---

## Previous Updates

For earlier updates, see git commit history or previous documentation.