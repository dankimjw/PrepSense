# Ingredient Subtraction Test Suite

This folder contains comprehensive test cases for the recipe ingredient subtraction feature in PrepSense.

## Overview

The ingredient subtraction feature automatically deducts ingredients from the user's pantry when they complete a recipe. This test suite validates:

- Basic quantity subtraction
- Unit conversions (metric ↔ imperial)
- Smart ingredient matching
- FIFO (First In, First Out) depletion
- Edge cases and error handling
- Revert functionality

## Files

- `test-cases-2025-01-10.md` - Detailed test case documentation with inputs/outputs
- `run_tests.py` - Automated test runner for all test cases
- `reset_test_data.py` - Quick utility to reset pantry to initial state
- `README.md` - This file

## Running Tests

### Prerequisites

1. Backend API running on `http://localhost:8000` (or set `API_BASE_URL` env var)
2. PostgreSQL database accessible with demo data
3. Python 3.8+

### Quick Start

```bash
# From the project root directory:

# Option 1: Run tests with automatic server management
python run_app.py --test-sub

# Option 2: Manual testing
# Terminal 1 - Start backend
python run_app.py

# Terminal 2 - Run tests
cd tests/ingredient-subtraction
python3 simple_test.py  # No external dependencies
# or
python3 run_tests.py    # Full test suite (requires requests module)

# Reset data to initial state
python run_app.py --reset-data
# or
python3 tests/ingredient-subtraction/reset_test_data.py
```

### Manual Testing

1. Reset the test data:
   ```bash
   python3 reset_test_data.py
   ```

2. Make individual API calls:
   ```bash
   curl -X POST http://localhost:8000/pantry/recipe/complete \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 111,
       "recipe_name": "Test Recipe",
       "ingredients": [
         {
           "ingredient_name": "pasta",
           "quantity": 200,
           "unit": "g"
         }
       ]
     }'
   ```

## Test Cases Summary

1. **Basic Subtraction** - Simple quantity reduction
2. **Unit Conversion** - Cup to ml, g to lb, etc.
3. **Multiple Items** - FIFO depletion across items
4. **Insufficient Quantity** - Partial fulfillment
5. **Missing Ingredients** - Graceful handling
6. **Count Units** - Eggs, tomatoes (each)
7. **Smart Matching** - Singular/plural, variations
8. **No Quantity** - Use all available
9. **Complex Recipe** - Multiple conversions
10. **Revert** - Undo recipe completion

## Expected Behavior

- ✅ Successful subtraction with detailed conversion info
- ✅ FIFO depletion when multiple items exist
- ✅ Graceful handling of missing/insufficient items
- ✅ Smart unit conversions within categories
- ✅ Flexible ingredient name matching
- ✅ Ability to revert recent changes

## Common Issues

1. **Authentication**: Ensure user_id 111 exists in database
2. **Units**: Some conversions may fail across categories (weight ↔ volume)
3. **Timing**: Revert only works within time window (default 60 min)
4. **Data State**: Always reset between test runs for consistency

## Future Improvements

- [ ] Add performance benchmarks
- [ ] Test concurrent recipe completions
- [ ] Add negative test cases
- [ ] Create visual test report
- [ ] Add integration with CI/CD