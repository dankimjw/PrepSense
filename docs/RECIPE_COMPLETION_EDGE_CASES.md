# Recipe Completion Edge Cases and Unit Conversion Issues

## Current Problems with Recipe Completion

### 1. Unit Mismatch Scenarios

**Problem**: Recipe calls for ingredients in different units than what's stored in pantry.

Examples:
- Recipe needs: "2 cups flour"
- Pantry has: "500 grams flour"
- Current system would try to subtract 2 from 500 (meaningless!)

Common mismatches:
- Volume vs Weight: cups/tbsp/tsp vs grams/oz/lbs
- Different volume units: cups vs ml/liters
- Different weight units: grams vs pounds/ounces
- Count vs weight: "3 tomatoes" vs "500g tomatoes"
- Count vs volume: "2 eggs" vs "100ml egg whites"

### 2. Ingredient Name Variations

**Problem**: Same ingredient, different names or forms.

Examples:
- Recipe: "tomatoes" vs Pantry: "cherry tomatoes" / "roma tomatoes" / "canned tomatoes"
- Recipe: "milk" vs Pantry: "whole milk" / "2% milk" / "oat milk"
- Recipe: "chicken" vs Pantry: "chicken breast" / "chicken thighs" / "whole chicken"

### 3. Quantity Ambiguity

**Problem**: Recipe quantities that are hard to quantify.

Examples:
- "Salt to taste"
- "A pinch of pepper"
- "Handful of spinach"
- "Drizzle of olive oil"
- "Few drops of vanilla"

### 4. Partial Unit Consumption

**Problem**: Using part of a whole item.

Examples:
- Recipe needs: "1/2 onion"
- Pantry has: "3 onions" (whole units)
- How to track the remaining half?

### 5. Combined Ingredients

**Problem**: Recipe combines what pantry tracks separately.

Examples:
- Recipe: "1 cup mixed vegetables"
- Pantry: Individual items (carrots, peas, corn)

### 6. Brand/Package Size Issues

**Problem**: Pantry items stored with brand info that affects matching.

Examples:
- Recipe: "pasta"
- Pantry: "Barilla Penne Pasta 16oz"

## Proposed Solutions

### 1. Unit Conversion Service

Create a comprehensive unit conversion system that:
- Maintains conversion tables for common ingredients
- Handles volume <-> weight conversions using ingredient densities
- Supports fractional amounts
- Has fallback strategies for unknown conversions

### 2. Smart Ingredient Matching

Implement fuzzy matching that:
- Uses ingredient hierarchies (milk -> dairy milk -> whole milk)
- Recognizes common variations and synonyms
- Handles brand name removal
- Supports ingredient substitutions

### 3. User Confirmation for Ambiguous Cases

When system can't automatically convert:
- Show user what we found vs what's needed
- Let them confirm or adjust the match
- Allow manual unit conversion input
- Remember user preferences for future

### 4. Partial Consumption Tracking

- Support fractional quantities in database
- Track "opened" vs "unopened" items
- Smart defaults for common scenarios

### 5. Graceful Degradation

When conversion isn't possible:
- Still allow recipe completion
- Mark items as "manually verify"
- Log for future improvement
- Don't block user workflow

## Implementation Priority

1. **High Priority**: Basic unit conversions (cups<->ml, g<->oz, etc.)
2. **Medium Priority**: Ingredient name fuzzy matching
3. **Low Priority**: Complex conversions and special cases

## Database Changes Needed

- Add `base_unit` field to track canonical units
- Add `conversion_factor` for items
- Add `partial_quantity` for opened items
- Add `ingredient_category` for better matching