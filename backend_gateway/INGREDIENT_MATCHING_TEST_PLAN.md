# Comprehensive Test Plan: Recipe Ingredient Matching Bug

## **Root Cause Analysis**

The issue is that there are **TWO DIFFERENT ingredient matching systems**:

1. **Saved Recipes**: Uses `user_recipes_service.match_recipes_with_pantry()` 
   - Pre-calculated counts from database
   - Lines 350-351: `missing_count = len(recipe['missing_ingredients'])`

2. **Spoonacular Recipes**: Uses real-time matching in `_get_spoonacular_recipes()`
   - Live calculation using `_is_similar_ingredient()` logic
   - Lines 507-508: `available_count = len(available_ingredients)`

## **Step-by-Step Testing Strategy**

### **Phase 1: Data Collection & Validation**

#### Test 1: **Identify the 3 Recipe Tabs**
```python
# Determine what the 3 tabs are:
# Tab 1: Saved Recipes?
# Tab 2: Spoonacular Recipes?
# Tab 3: Combined/Recommended?

test_data = {
    "user_id": 111,
    "pantry_items": [
        {"product_name": "Chicken Breast", "quantity": 2, "unit": "lbs"},
        {"product_name": "Rice", "quantity": 3, "unit": "cups"},
        {"product_name": "Milk", "quantity": 1, "unit": "gallon"}
    ]
}

# Call each tab's endpoint and document data sources
```

#### Test 2: **Extract Sample Recipe Data**
```python
# For each tab, capture:
sample_recipe = {
    "name": "Chicken Rice Bowl",
    "ingredients": [
        "2 lbs chicken breast",
        "2 cups rice", 
        "1 cup milk",
        "soy sauce",
        "garlic"
    ],
    "card_display": {
        "have_count": 3,  # What card shows
        "missing_count": 2  # What card shows
    },
    "details_display": {
        "available_ingredients": ["chicken breast", "rice", "milk"],
        "missing_ingredients": ["soy sauce", "garlic"]
    }
}
```

### **Phase 2: Ingredient Matching Logic Testing**

#### Test 3: **Test Ingredient Normalization**
```python
# Test the _clean_ingredient_name function
test_cases = [
    {
        "input": "2 lbs Organic Chicken Breast – Fresh",
        "expected": "chicken breast",
        "pantry_item": "Chicken Breast"
    },
    {
        "input": "1 cup whole milk",
        "expected": "milk", 
        "pantry_item": "Milk"
    },
    {
        "input": "2 cups basmati rice",
        "expected": "rice",
        "pantry_item": "Rice"
    }
]

for test in test_cases:
    cleaned = _clean_ingredient_name(test["input"])
    assert cleaned == test["expected"], f"Failed: {test}"
```

#### Test 4: **Test Similarity Matching**
```python
# Test the _is_similar_ingredient function
similarity_tests = [
    {
        "ingredient": "chicken breast",
        "pantry_item": "Chicken Breast",
        "should_match": True
    },
    {
        "ingredient": "soy sauce",
        "pantry_item": "Chicken Breast", 
        "should_match": False
    },
    {
        "ingredient": "rice",
        "pantry_item": "Basmati Rice",
        "should_match": True
    }
]

for test in similarity_tests:
    result = _is_similar_ingredient(test["ingredient"], test["pantry_item"])
    assert result == test["should_match"], f"Failed: {test}"
```

### **Phase 3: End-to-End Recipe Testing**

#### Test 5: **Compare Card vs Details for Same Recipe**
```python
# Create test function
def test_recipe_consistency(recipe_id, user_id):
    # Get recipe from card display
    card_data = get_recipe_card_data(recipe_id, user_id)
    
    # Get recipe from details display  
    details_data = get_recipe_details_data(recipe_id, user_id)
    
    # Compare counts
    assert card_data["have_count"] == len(details_data["available_ingredients"])
    assert card_data["missing_count"] == len(details_data["missing_ingredients"])
    
    # Compare ingredients
    assert set(card_data["available"]) == set(details_data["available_ingredients"])
    assert set(card_data["missing"]) == set(details_data["missing_ingredients"])

# Test across all tabs
for tab in ["saved", "spoonacular", "recommended"]:
    for recipe in get_recipes_from_tab(tab, user_id=111):
        test_recipe_consistency(recipe["id"], 111)
```

#### Test 6: **Test Different Recipe Sources**
```python
# Test saved recipes
saved_recipes = await crew_ai_service._get_matching_saved_recipes(
    user_id=111, 
    pantry_items=test_pantry
)

# Test spoonacular recipes  
spoonacular_recipes = await crew_ai_service._get_spoonacular_recipes(
    pantry_items=test_pantry,
    message="dinner",
    user_preferences={},
    num_recipes=5
)

# Compare counting logic
for recipe in saved_recipes:
    verify_ingredient_counts(recipe, test_pantry, source="saved")
    
for recipe in spoonacular_recipes:
    verify_ingredient_counts(recipe, test_pantry, source="spoonacular")
```

### **Phase 4: Edge Case Testing**

#### Test 7: **Edge Cases**
```python
edge_cases = [
    {
        "name": "Empty ingredients list",
        "recipe": {"ingredients": []},
        "expected": {"have_count": 0, "missing_count": 0}
    },
    {
        "name": "All ingredients available",
        "recipe": {"ingredients": ["chicken breast", "rice"]},
        "expected": {"have_count": 2, "missing_count": 0}
    },
    {
        "name": "No ingredients available", 
        "recipe": {"ingredients": ["caviar", "truffle oil"]},
        "expected": {"have_count": 0, "missing_count": 2}
    },
    {
        "name": "Duplicate ingredients",
        "recipe": {"ingredients": ["chicken breast", "chicken breast", "rice"]},
        "expected": {"have_count": 2, "missing_count": 0}  # Should dedupe
    },
    {
        "name": "Case sensitivity",
        "recipe": {"ingredients": ["CHICKEN BREAST", "chicken breast", "Rice"]},
        "expected": {"have_count": 2, "missing_count": 0}
    }
]

for case in edge_cases:
    result = calculate_ingredient_counts(case["recipe"], test_pantry)
    assert result == case["expected"], f"Failed: {case['name']}"
```

### **Phase 5: User Interface Testing**

#### Test 8: **UI Consistency Check**
```python
# Test the actual UI components
def test_ui_consistency():
    # Navigate to recipe tabs
    for tab_name in ["Tab 1", "Tab 2", "Tab 3"]:
        recipes = get_recipes_from_ui_tab(tab_name)
        
        for recipe in recipes:
            # Extract badge numbers from UI
            ui_have = extract_have_count_from_badge(recipe)
            ui_missing = extract_missing_count_from_badge(recipe)
            
            # Click on recipe to see details
            details = click_recipe_and_get_details(recipe)
            
            # Count ingredients in details
            details_have = count_available_ingredients(details)
            details_missing = count_missing_ingredients(details)
            
            # Assert consistency
            assert ui_have == details_have, f"Have count mismatch in {recipe['name']}"
            assert ui_missing == details_missing, f"Missing count mismatch in {recipe['name']}"
```

### **Phase 6: Data Debugging**

#### Test 9: **Debug Data Pipeline**
```python
# Create debug function to trace data flow
def debug_ingredient_matching(recipe_name, user_id):
    print(f"\n=== DEBUG: {recipe_name} ===")
    
    # 1. Get pantry items
    pantry = get_user_pantry(user_id)
    print(f"Pantry items: {[item['product_name'] for item in pantry]}")
    
    # 2. Get recipe ingredients
    recipe = get_recipe_by_name(recipe_name)
    print(f"Recipe ingredients: {recipe['ingredients']}")
    
    # 3. Step through matching logic
    for ingredient in recipe['ingredients']:
        cleaned = _clean_ingredient_name(ingredient)
        print(f"  '{ingredient}' -> cleaned: '{cleaned}'")
        
        matches = []
        for pantry_item in pantry:
            if _is_similar_ingredient(cleaned, pantry_item['product_name']):
                matches.append(pantry_item['product_name'])
        
        print(f"    Matches: {matches}")
        
    # 4. Final counts
    print(f"Final counts: have={recipe['available_count']}, missing={recipe['missing_count']}")
    print(f"UI shows: have={get_ui_have_count(recipe)}, missing={get_ui_missing_count(recipe)}")
```

### **Phase 7: Fix Validation**

#### Test 10: **Automated Regression Testing**
```python
# Create test suite that runs after any fixes
def regression_test_suite():
    test_users = [111, 222, 333]  # Different pantry scenarios
    
    for user_id in test_users:
        print(f"\n=== Testing User {user_id} ===")
        
        # Test all recipe sources
        for tab in get_recipe_tabs():
            recipes = get_recipes_from_tab(tab, user_id)
            
            for recipe in recipes:
                # Verify consistency
                card_counts = get_card_counts(recipe)
                detail_counts = get_detail_counts(recipe, user_id)
                
                assert card_counts == detail_counts, f"FAIL: {recipe['name']} in {tab}"
                
        print(f"✅ User {user_id} passed all tests")
```

## **Common Issues to Look For**

### **1. Inconsistent Ingredient Normalization**
- Card uses one cleaning method, details use another
- Case sensitivity differences
- Unit parsing differences ("2 cups rice" vs "rice")

### **2. Different Matching Logic**
- Saved recipes: Pre-calculated from database
- Spoonacular: Real-time calculation  
- Different similarity thresholds

### **3. Data Source Confusion**
- Card pulls from cached data
- Details pulls from live API
- Stale data issues

### **4. UI State Management**
- Recipe data updated but UI not refreshed
- Wrong recipe ID passed to details view
- State pollution between tabs

## **Test Execution Order**

1. **Start with Test 1** - Identify what the 3 tabs are
2. **Run Test 2** - Capture sample data showing the bug
3. **Execute Tests 3-4** - Verify the core matching logic
4. **Run Test 5** - Compare card vs details for same recipes
5. **Execute Tests 6-7** - Test different scenarios and edge cases
6. **Run Test 8** - UI consistency check
7. **Use Test 9** - Debug specific failing cases
8. **Run Test 10** - Validate fixes

## **Expected Outcomes**

After running this test suite, you should be able to:
- Identify exactly where the count mismatch occurs
- Determine if it's a data issue, logic issue, or UI issue
- Fix the root cause systematically
- Prevent regression with automated tests

The key is to test both the **data calculation logic** and the **UI display logic** separately, then verify they work together correctly.