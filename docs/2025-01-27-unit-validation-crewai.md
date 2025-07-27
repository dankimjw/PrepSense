# Unit Validation Integration with CrewAI

## Overview
Enhanced the CrewAI recipe generation system to properly handle food units based on category-specific rules using the SmartUnitValidator.

## Key Updates

### 1. Agent Enhancements

#### Recipe Search Agent
- Added comprehensive unit guidelines in backstory
- Ensures recipes use appropriate units:
  - Produce: lb, oz, each, container (NOT ml/liters)
  - Dairy liquids: gallon, quart, pint
  - Eggs: dozen/each (NOT by weight)
  - Meat: lb, oz, piece (NOT ml)

#### Nutritional Agent
- Enhanced to convert units for accurate nutrition analysis
- Handles conversions like "500 ml strawberries" → "~1 lb or 3 cups"
- Uses standard serving sizes for calculations

#### Response Formatting Agent
- Formats all recipe outputs with proper units
- Rounds to practical amounts (0.5 lb not 0.4823 lb)
- Ensures consistency with retail units

### 2. Unit Rules by Category

The system now enforces these unit rules:

```
Produce (Fruits/Vegetables):
- Allowed: lb, oz, each, container, pint, quart
- Forbidden: ml, l, fl oz, gallon
- Examples: strawberries by lb, lettuce by head

Dairy Products:
- Liquids: gallon, quart, pint, fl oz
- Solids: oz, lb, slice, stick
- Eggs: dozen, each (never by weight)

Beverages:
- Allowed: ml, l, bottle, can
- Forbidden: each, lb, oz

Meat/Poultry:
- Allowed: lb, oz, piece
- Forbidden: ml, each

Spices:
- Allowed: tsp, tbsp, oz, jar
- Forbidden: lb, gallon
```

### 3. Integration Points

#### With Existing Systems
- Chat Router (`/api/v1/chat`) - Already uses recipe recommendation
- Unit Validation Router (`/api/v1/unit-validation`) - Provides validation API
- SmartUnitValidator service - Core validation logic

#### Database Fixes
The system can now:
1. Validate units in real-time during recipe generation
2. Apply batch fixes using `/scripts/fix_pantry_units.py`
3. Prevent future incorrect units through agent prompts

### 4. Usage Examples

**Before**: Recipe suggests "500 ml strawberries"
**After**: Recipe suggests "1 lb strawberries"

**Before**: "3 each milk"
**After**: "3 quarts milk"

**Before**: "2 lb oregano"
**After**: "2 oz oregano"

## Testing the Integration

1. **Generate recipe with pantry items having wrong units**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/ai-recipes/generate" \
     -H "Authorization: Bearer <token>" \
     -d '{"max_recipes": 3}'
   ```

2. **Check unit validation**:
   ```bash
   curl -X GET "http://localhost:8001/api/v1/unit-validation/validate?food_name=strawberries&unit=ml"
   ```

3. **Fix existing pantry units**:
   ```bash
   python scripts/fix_pantry_units.py --apply
   ```

## Benefits

1. **Consistency** - All recipes use retail-standard units
2. **Accuracy** - Nutritional calculations are more precise
3. **User Experience** - No confusing units like "ml of strawberries"
4. **Prevention** - Agents won't suggest incorrect units

## Next Steps

1. Add unit conversion tooltips in frontend
2. Create unit preference settings (metric vs imperial)
3. Add smart unit suggestions during OCR scanning
4. Implement automatic unit fixes on pantry item creation