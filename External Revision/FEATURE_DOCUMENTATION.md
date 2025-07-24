# PrepSense Feature Documentation

## Version 2.0 - Major Update (January 2025)

This document provides comprehensive documentation for all features implemented in the latest PrepSense update.

## Table of Contents

1. [Recipe Management Features](#recipe-management-features)
2. [Pantry Management Features](#pantry-management-features)
3. [User Experience Enhancements](#user-experience-enhancements)
4. [AI and Recommendation Features](#ai-and-recommendation-features)
5. [Analytics and Statistics](#analytics-and-statistics)
6. [Technical Improvements](#technical-improvements)

---

## Recipe Management Features

### 1. Recipe Completion Modal with Quantity Adjustment

**Location**: `ios-app/components/modals/RecipeCompletionModal.tsx`

**Description**: When completing a recipe, users can now adjust how much of each ingredient they actually used.

**Features**:
- Slider controls for each ingredient (0-100% usage)
- Real-time calculation of amounts to be deducted
- Visual indicators for sufficient/insufficient quantities
- Smart unit conversion display

**How to use**:
1. Navigate to any recipe detail screen
2. Tap "Quick Complete" button
3. Adjust sliders for each ingredient based on actual usage
4. Tap "Complete Recipe" to update pantry

**Code Example**:
```typescript
// Usage in recipe-details.tsx
<RecipeCompletionModal
  visible={showCompletionModal}
  onClose={() => setShowCompletionModal(false)}
  onConfirm={handleRecipeCompletionConfirm}
  recipe={recipe}
  pantryItems={pantryItems}
  loading={isCompletingRecipe}
/>
```

### 2. Bookmark and Rating System

**Location**: 
- Backend: `backend_gateway/routers/user_recipes_router.py`
- Frontend: `ios-app/app/recipe-details.tsx`, `recipe-spoonacular-detail.tsx`

**Description**: Users can now bookmark favorite recipes and rate them with thumbs up/down.

**Features**:
- Bookmark toggle for saving favorites
- Thumbs up/down rating system
- Ratings persist across sessions
- Ratings influence future recommendations

**API Endpoints**:
- `POST /api/v1/user-recipes` - Save a recipe
- `PUT /api/v1/user-recipes/{recipe_id}/rating` - Update rating
- `PUT /api/v1/user-recipes/{recipe_id}/favorite` - Toggle favorite

**How to use**:
1. Open any recipe detail screen
2. Tap bookmark icon to save/unsave
3. Tap thumbs up/down to rate
4. Ratings automatically improve recommendations

---

## Pantry Management Features

### 3. OCR Receipt Scanner

**Location**: 
- Backend: `backend_gateway/routers/ocr_router.py`
- Frontend: `ios-app/app/receipt-scanner.tsx`

**Description**: Automatically add items to pantry by scanning grocery receipts.

**Features**:
- Camera and photo library support
- AI-powered text extraction using OpenAI Vision
- Automatic item categorization
- Edit items before adding
- Smart expiration date calculation

**API Endpoints**:
- `POST /api/v1/ocr/scan-receipt` - Process receipt image
- `POST /api/v1/ocr/add-scanned-items` - Add items to pantry

**How to use**:
1. Tap the "+" button on any screen
2. Select "Scan Receipt"
3. Take photo or select from gallery
4. Review extracted items
5. Edit quantities/units if needed
6. Tap "Add Items" to save to pantry

### 4. Enhanced Unit Validation

**Location**: `ios-app/app/edit-pantry-item.tsx`

**Description**: Comprehensive validation for pantry item quantities and units.

**Features**:
- Whole number enforcement for count units (each, package, etc.)
- Range validation for weights/volumes
- Real-time input validation
- Automatic rounding when switching units
- User-friendly error messages

**Validation Rules**:
```javascript
// Count units require whole numbers
['each', 'package', 'bag', 'case', 'carton', 'gross']

// Weight/volume ranges
- mg: max 1,000,000 (suggests kg for larger)
- ml: max 10,000 (suggests liters for larger)
- tsp: max 48 (suggests cups for larger)
- tbsp: max 16 (suggests cups for larger)
```

---

## User Experience Enhancements

### 5. User Preferences System

**Location**: `ios-app/app/components/UserPreferencesModal.tsx`

**Description**: Centralized preferences management accessible from header.

**Features**:
- Dietary restrictions selection
- Allergen management
- Cuisine preferences
- Quick access from any screen
- Preferences affect recipe recommendations

**How to use**:
1. Tap user icon in header
2. Select preferences
3. Changes save automatically
4. Affects all recipe suggestions

### 6. Enhanced Recipe Image System

**Location**: `backend_gateway/routers/chat_router.py`

**Description**: Improved variety and relevance of recipe images.

**Features**:
- Category-based image mapping
- Hash-based selection for consistency
- Expanded image pools (3-5 per category)
- Fallback to AI generation if needed

**Image Categories**:
- Bowl dishes, Stir fry, Pasta, Salads
- Burgers, Sandwiches, Pizza, Soups
- Smoothies, Chicken, Fish, Rice dishes
- Breakfast items, Desserts

### 7. Fixed Shopping List Navigation

**Location**: `ios-app/app/recipe-details.tsx`

**Description**: Missing ingredients now properly route through selection screen.

**Changes**:
- "Add to Shopping List" in alerts → select-ingredients screen
- Allows selective addition
- Consistent with main shopping list flow

---

## AI and Recommendation Features

### 8. Meal Type Detection

**Location**: `backend_gateway/services/crew_ai_service.py`

**Description**: AI recipes now match requested meal types.

**Features**:
- Detects meal type from user query
- Categories: breakfast, lunch, dinner, snack, dessert
- Generates appropriate recipes
- No more default desserts

**Detection Keywords**:
```python
meal_type_keywords = {
    'breakfast': ['breakfast', 'morning', 'brunch'],
    'lunch': ['lunch', 'midday', 'noon'],
    'dinner': ['dinner', 'supper', 'evening'],
    'snack': ['snack', 'appetizer', 'treat'],
    'dessert': ['dessert', 'sweet', 'cake', 'cookie']
}
```

### 9. Rating-Based Recommendations

**Location**: `backend_gateway/services/crew_ai_service.py`

**Description**: User ratings now influence recipe recommendations.

**Ranking Priority**:
1. Saved recipes with thumbs_up
2. Favorite recipes
3. Recipes using expiring ingredients
4. Recipes you can make now
5. Well-balanced meals
6. High ingredient match

---

## Analytics and Statistics

### 10. Comprehensive Stats Dashboard

**Location**: 
- Backend: `backend_gateway/routers/stats_router.py`
- Frontend: `ios-app/app/(tabs)/stats.tsx`

**Description**: Detailed analytics about pantry and cooking habits.

**API Endpoints**:
- `GET /api/v1/stats/comprehensive` - All statistics
- `GET /api/v1/stats/milestones` - User achievements

**Features**:
- Pantry analytics (expired, expiring, categories)
- Cooking history and streaks
- Environmental impact (CO2 saved)
- Shopping patterns
- Milestones and achievements
- Time-based filtering (week/month/year)

**Statistics Included**:
```json
{
  "pantry": {
    "total_items": 45,
    "expired_items": 2,
    "expiring_soon": 5,
    "top_categories": [...],
    "top_products": [...]
  },
  "recipes": {
    "total_recipes": 23,
    "cooked_this_week": 5,
    "current_streak": 3,
    "favorite_recipes": [...]
  },
  "sustainability": {
    "food_saved_kg": 13.5,
    "co2_saved_kg": 33.75
  }
}
```

---

## Technical Improvements

### 11. Food Categorization System

**Location**: `backend_gateway/services/practical_food_categorization.py`

**Description**: Intelligent food categorization using rule-based system with AI fallback.

**Features**:
- 15 main categories
- Pattern matching for common items
- AI fallback for unknown items
- Database caching for performance

**Categories**:
- Produce, Dairy, Meat, Seafood
- Bakery, Frozen, Pantry, Beverages
- Snacks, Condiments, Canned Goods
- Grains, Spices, Baking, Other

### 12. Unit Conversion Service

**Location**: `backend_gateway/services/unit_conversion_service.py`

**Description**: Comprehensive unit conversion for recipe calculations.

**Features**:
- Weight conversions (mg ↔ g ↔ kg ↔ oz ↔ lb)
- Volume conversions (ml ↔ l ↔ cup ↔ tsp ↔ tbsp)
- Smart unit suggestions
- Ingredient-specific conversions

---

## Testing Guide

### Backend Testing

1. **Start the backend**:
```bash
source venv/bin/activate
python run_app.py
```

2. **Test OCR endpoint**:
```bash
# Visit http://localhost:8001/docs
# Try POST /api/v1/ocr/scan-receipt with base64 image
```

3. **Test stats endpoint**:
```bash
curl http://localhost:8001/api/v1/stats/comprehensive?user_id=111
```

### Frontend Testing

1. **Start the iOS app**:
```bash
cd ios-app
npx expo start --ios
```

2. **Test Receipt Scanner**:
- Tap + button → Scan Receipt
- Use camera or select receipt image
- Verify items are extracted
- Edit and add to pantry

3. **Test Recipe Completion**:
- Open any recipe
- Tap "Quick Complete"
- Adjust sliders
- Verify pantry updates

4. **Test Ratings**:
- Open recipe details
- Tap thumbs up/down
- Verify state persists
- Check if recommendations improve

5. **Test Stats Page**:
- Navigate to Stats tab
- Switch between week/month/year
- Verify all metrics load
- Check charts render correctly

---

## Troubleshooting

### Common Issues

1. **OCR not working**:
   - Check OPENAI_API_KEY is set
   - Ensure image is clear and well-lit
   - Try portrait orientation

2. **Stats not loading**:
   - Check database connection
   - Verify user has pantry items
   - Check console for SQL errors

3. **Ratings not saving**:
   - Ensure backend is running
   - Check network connectivity
   - Verify user_id is correct

### Debug Commands

```bash
# Check backend logs
tail -f backend.log

# Test database connection
python -c "from backend_gateway.config.database import get_database_service; print(get_database_service())"

# Verify OpenAI key
python -c "import os; print('API Key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

---

## Future Enhancements

1. **Barcode Scanning**: Add barcode support to receipt scanner
2. **Meal Planning**: Weekly meal planning with calendar
3. **Social Features**: Share recipes and shopping lists
4. **Voice Commands**: Add items via voice
5. **Nutrition Tracking**: Detailed nutritional analysis

---

## API Reference

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/ocr/scan-receipt | Process receipt image |
| POST | /api/v1/ocr/add-scanned-items | Add scanned items |
| GET | /api/v1/stats/comprehensive | Get all statistics |
| GET | /api/v1/stats/milestones | Get achievements |
| POST | /api/v1/user-recipes | Save recipe |
| PUT | /api/v1/user-recipes/{id}/rating | Update rating |
| PUT | /api/v1/user-recipes/{id}/favorite | Toggle favorite |

---

## Version History

- **v2.0.0** (January 2025): Major update with OCR, ratings, stats, and UX improvements
- **v1.0.0** (December 2024): Initial release

---

## Contributing

Please follow the guidelines in CLAUDE.md when contributing to this project.