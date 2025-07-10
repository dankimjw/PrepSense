# Recipe Ingredient Subtraction Test Cases
**Test Date**: 2025-01-10  
**Feature**: Recipe Completion with Ingredient Quantity Subtraction  
**API Endpoint**: `POST /pantry/recipe/complete`

## Test Environment Setup

### Prerequisites
1. User ID: 111 (test user)
2. Demo data loaded via `setup_demo_data.py` into PostgreSQL
3. API running on configured base URL
4. PostgreSQL database running locally or via Cloud SQL

### Test Data Reset Instructions
To ensure repeatable tests, run the following before each test suite:

```bash
# Reset pantry to initial state
cd backend_gateway/scripts
python3 setup_demo_data.py

# This will:
# 1. Clear existing pantry items for user 111
# 2. Add fresh demo pantry items with known quantities
# 3. Reset all used_quantity fields to 0
```

## Test Cases

### Test Case 1: Basic Ingredient Subtraction with Exact Match
**Description**: Test simple subtraction when units match exactly

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Simple Pasta Test",
  "ingredients": [
    {
      "ingredient_name": "pasta",
      "quantity": 200,
      "unit": "g"
    }
  ]
}
```

**Initial State**:
- Pasta (Spaghetti): 453.592g (1 lb converted)

**Expected Output**:
```json
{
  "message": "Recipe completed successfully",
  "recipe_name": "Simple Pasta Test",
  "updated_items": [
    {
      "item_name": "Pasta (Spaghetti)",
      "previous_quantity": 453.592,
      "new_quantity": 253.592,
      "used_quantity": 200,
      "unit": "g",
      "conversion_details": "200 g = 200.00 g"
    }
  ],
  "missing_items": [],
  "insufficient_items": []
}
```

**Test Result**: ⏳ Pending

---

### Test Case 2: Unit Conversion - Imperial to Metric
**Description**: Test conversion from cups to milliliters

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Baking Test",
  "ingredients": [
    {
      "ingredient_name": "milk",
      "quantity": 1,
      "unit": "cup"
    }
  ]
}
```

**Initial State**:
- Milk (Whole): 946.353ml (1 quart)

**Expected Output**:
```json
{
  "message": "Recipe completed successfully",
  "updated_items": [
    {
      "item_name": "Milk (Whole)",
      "previous_quantity": 946.353,
      "new_quantity": 709.765,
      "used_quantity": 236.588,
      "unit": "ml",
      "conversion_details": "1 cup = 236.59 ml"
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 3: Multiple Item Depletion (FIFO)
**Description**: Test using multiple items when one isn't sufficient

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Large Pasta Dish",
  "ingredients": [
    {
      "ingredient_name": "pasta",
      "quantity": 600,
      "unit": "g"
    }
  ]
}
```

**Initial State**:
- Pasta (Spaghetti): 453.592g
- Pasta (Penne): 453.592g

**Expected Output**:
```json
{
  "message": "Recipe completed successfully",
  "updated_items": [
    {
      "item_name": "Pasta (Spaghetti)",
      "previous_quantity": 453.592,
      "new_quantity": 0,
      "used_quantity": 453.592,
      "unit": "g"
    },
    {
      "item_name": "Pasta (Penne)",
      "previous_quantity": 453.592,
      "new_quantity": 307.184,
      "used_quantity": 146.408,
      "unit": "g"
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 4: Insufficient Quantity Handling
**Description**: Test behavior when pantry doesn't have enough

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Big Batch Cookies",
  "ingredients": [
    {
      "ingredient_name": "flour",
      "quantity": 1000,
      "unit": "g"
    }
  ]
}
```

**Initial State**:
- All Purpose Flour: 907.185g (2 lbs)

**Expected Output**:
```json
{
  "message": "Recipe completed successfully",
  "updated_items": [
    {
      "item_name": "All Purpose Flour",
      "previous_quantity": 907.185,
      "new_quantity": 0,
      "used_quantity": 907.185,
      "unit": "g"
    }
  ],
  "insufficient_items": [
    {
      "ingredient_name": "flour",
      "requested_quantity": 1000,
      "available_quantity": 907.185,
      "shortage": 92.815,
      "unit": "g"
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 5: Missing Ingredient
**Description**: Test when recipe needs ingredient not in pantry

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Exotic Recipe",
  "ingredients": [
    {
      "ingredient_name": "saffron",
      "quantity": 1,
      "unit": "g"
    }
  ]
}
```

**Expected Output**:
```json
{
  "message": "Recipe completed successfully",
  "updated_items": [],
  "missing_items": ["saffron"]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 6: Count to Count Conversion
**Description**: Test egg counting

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Scrambled Eggs",
  "ingredients": [
    {
      "ingredient_name": "eggs",
      "quantity": 3,
      "unit": "each"
    }
  ]
}
```

**Initial State**:
- Eggs: 12 each

**Expected Output**:
```json
{
  "updated_items": [
    {
      "item_name": "Eggs",
      "previous_quantity": 12,
      "new_quantity": 9,
      "used_quantity": 3,
      "unit": "each"
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 7: Smart Matching with Variations
**Description**: Test ingredient name matching flexibility

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Tomato Sauce",
  "ingredients": [
    {
      "ingredient_name": "tomatoes",
      "quantity": 2,
      "unit": "each"
    }
  ]
}
```

**Initial State**:
- Tomato: 4 each

**Expected Output**:
```json
{
  "updated_items": [
    {
      "item_name": "Tomato",
      "previous_quantity": 4,
      "new_quantity": 2,
      "used_quantity": 2,
      "unit": "each",
      "match_score": 90
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 8: No Quantity Specified
**Description**: Test behavior when recipe doesn't specify amount

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Seasoned Dish",
  "ingredients": [
    {
      "ingredient_name": "salt"
    }
  ]
}
```

**Expected Output**:
```json
{
  "updated_items": [
    {
      "item_name": "Salt",
      "previous_quantity": 737.09,
      "new_quantity": 0,
      "used_quantity": 737.09,
      "unit": "g",
      "note": "No quantity specified - used all available"
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

### Test Case 9: Complex Recipe with Multiple Conversions
**Description**: Test full recipe with various unit conversions

**Input**:
```json
{
  "user_id": 111,
  "recipe_name": "Chocolate Chip Cookies",
  "ingredients": [
    {
      "ingredient_name": "flour",
      "quantity": 2.25,
      "unit": "cups"
    },
    {
      "ingredient_name": "butter",
      "quantity": 1,
      "unit": "cup"
    },
    {
      "ingredient_name": "sugar",
      "quantity": 0.75,
      "unit": "cup"
    },
    {
      "ingredient_name": "eggs",
      "quantity": 2,
      "unit": "each"
    },
    {
      "ingredient_name": "chocolate chips",
      "quantity": 2,
      "unit": "cups"
    }
  ]
}
```

**Expected Output**: Should show conversions for each ingredient and update quantities accordingly.

**Test Result**: ⏳ Pending

---

### Test Case 10: Revert Functionality
**Description**: Test reverting a recipe completion

**Setup**: First complete Test Case 1, then revert

**Revert Input**:
```json
{
  "user_id": 111,
  "minutes_ago": 5,
  "revert_recipe": "Simple Pasta Test"
}
```

**Expected Output**:
```json
{
  "message": "Successfully reverted 1 item(s)",
  "reverted_items": [
    {
      "item_name": "Pasta (Spaghetti)",
      "quantity_restored": 200,
      "new_quantity": 453.592
    }
  ]
}
```

**Test Result**: ⏳ Pending

---

## Test Execution Script

Create `run_tests.py` in this directory:

```python
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"  # Update as needed

def run_test(test_name, endpoint, payload, expected_fields):
    """Run a single test case"""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    # Make request
    response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload)
    
    # Print results
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Basic validation
    if response.status_code == 200:
        data = response.json()
        for field in expected_fields:
            if field in data:
                print(f"✓ Found expected field: {field}")
            else:
                print(f"✗ Missing expected field: {field}")
    
    return response.json()

# Run all tests
if __name__ == "__main__":
    # Test Case 1
    run_test(
        "Test Case 1: Basic Subtraction",
        "/pantry/recipe/complete",
        {
            "user_id": 111,
            "recipe_name": "Simple Pasta Test",
            "ingredients": [
                {
                    "ingredient_name": "pasta",
                    "quantity": 200,
                    "unit": "g"
                }
            ]
        },
        ["message", "updated_items", "missing_items"]
    )
```

## Summary

- **Total Test Cases**: 10
- **Categories Covered**:
  - Basic subtraction
  - Unit conversions (metric/imperial)
  - Multiple item depletion
  - Insufficient quantities
  - Missing ingredients
  - Smart matching
  - Edge cases
  - Revert functionality

## Notes

1. All test cases assume fresh demo data state
2. Run reset script between test suites for consistency
3. API responses may include additional fields not shown in expected outputs
4. Conversion factors are based on standard culinary measurements
5. FIFO (First In, First Out) behavior ensures oldest items are used first