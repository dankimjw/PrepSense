# Manual Test Results - Ingredient Subtraction
**Test Date**: 2025-01-10  
**Tester**: System  
**Status**: Manual execution required - Backend server not running

## Prerequisites Not Met

1. ❌ Backend server is not running on http://localhost:8000
2. ❌ Python requests module not available in system environment

## How to Run Tests

### Option 1: Use run_app.py (Recommended)

```bash
# From project root, run tests with automatic server management
python run_app.py --test-sub
```

### Option 2: Manual Setup

```bash
# Terminal 1 - Start the backend from project root
python run_app.py

# Terminal 2 - Run tests
cd tests/ingredient-subtraction
python3 simple_test.py  # or run_tests.py for full suite
```

### Option 2: Manual API Testing

You can manually test each case using curl. Here are the commands:

#### Test Case 1: Basic Subtraction
```bash
curl -X POST http://localhost:8000/pantry/recipe/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "recipe_name": "Simple Pasta Test",
    "ingredients": [{
      "ingredient_name": "pasta",
      "quantity": 200,
      "unit": "g"
    }]
  }'
```

Expected: Pasta quantity reduced from 453.592g to 253.592g

#### Test Case 2: Unit Conversion
```bash
curl -X POST http://localhost:8000/pantry/recipe/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "recipe_name": "Baking Test",
    "ingredients": [{
      "ingredient_name": "milk",
      "quantity": 1,
      "unit": "cup"
    }]
  }'
```

Expected: Milk reduced by 236.588ml (1 cup conversion)

#### Test Case 3: Multiple Items (FIFO)
```bash
# Reset data first
python3 ../../backend_gateway/scripts/setup_demo_data.py

curl -X POST http://localhost:8000/pantry/recipe/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "recipe_name": "Large Pasta Dish",
    "ingredients": [{
      "ingredient_name": "pasta",
      "quantity": 600,
      "unit": "g"
    }]
  }'
```

Expected: First pasta item depleted, second partially used

#### Test Case 4: Insufficient Quantity
```bash
curl -X POST http://localhost:8000/pantry/recipe/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "recipe_name": "Big Batch Cookies",
    "ingredients": [{
      "ingredient_name": "flour",
      "quantity": 1000,
      "unit": "g"
    }]
  }'
```

Expected: All flour used (907.185g), shortage reported

#### Test Case 5: Missing Ingredient
```bash
curl -X POST http://localhost:8000/pantry/recipe/complete \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "recipe_name": "Exotic Recipe",
    "ingredients": [{
      "ingredient_name": "saffron",
      "quantity": 1,
      "unit": "g"
    }]
  }'
```

Expected: "saffron" in missing_items list

## Current Test Status

Since the backend server is not running, here's what we expect based on the implementation:

### ✅ What Should Work:
1. **Basic subtraction** - Direct quantity reduction
2. **Unit conversions** - Within same category (weight-to-weight, volume-to-volume)
3. **Smart matching** - Singular/plural, partial name matches
4. **FIFO depletion** - Oldest items used first
5. **Insufficient handling** - Partial fulfillment with shortage report
6. **Missing items** - Graceful handling with report

### ⚠️ Edge Cases to Watch:
1. **Cross-category conversions** - Won't work (e.g., "2 eggs" to "dozen")
2. **No quantity specified** - Uses entire available amount
3. **Multiple matches** - Picks highest scoring match
4. **Concurrent updates** - No transaction isolation

## Next Steps

1. Start the backend server
2. Run `python3 run_tests.py` for automated testing
3. Review results in console output
4. Update this file with actual results

## Mock Recipe Testing

The mock recipes added to My Recipes should display:
- Classic Spaghetti Carbonara (liked, favorited)
- Thai Green Curry Chicken (liked)
- Homemade Margherita Pizza (neutral, favorited)
- Vegan Buddha Bowl (liked, AI-generated)
- Chocolate Lava Cake (disliked)

These will appear when the iOS app fetches recipes for user 111.