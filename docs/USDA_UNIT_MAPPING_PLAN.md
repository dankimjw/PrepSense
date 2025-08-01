# USDA Unit Mapping Implementation Plan

## Overview
This document outlines the plan for importing and utilizing USDA data to improve food-to-unit matching in PrepSense.

## Available USDA Data

### 1. **measure_unit.csv** (✓ Available)
- Contains 123 measure units including:
  - Volume: cup, tablespoon, teaspoon, liter, milliliter, gallon, pint, fl oz
  - Weight: lb, oz, gram weights
  - Count/portion: each, piece, slice, serving, package, container
  - Food-specific: breast, chop, patty, loaf, wedge

### 2. **food_portion.csv** (✓ Available)
- Links foods (by FDC ID) to measure units
- Provides gram weight conversions
- Example: 2 tablespoons = 35.8 grams

### 3. **branded_food.csv** (✓ Available)
- Contains serving_size and serving_size_unit
- household_serving_fulltext (e.g., "1 Tbsp (15 ml)")
- Brand-specific unit information

### 4. **food_category.csv** (✓ Available)
- 28 main food categories
- Used to group foods for unit rules

## What's Missing

### Category-to-Unit Rules (✗ Not in USDA)
USDA doesn't provide rules about which units are appropriate for each category. We need to:
1. Analyze portion data to derive patterns
2. Create category-to-unit mappings
3. Replace hardcoded rules with data-driven approach

## Implementation Steps

### Phase 1: Data Import (Completed)
- Created `import_usda_unit_mappings.py` script
- Analyzes food_portion.csv to find unit usage patterns
- Generates category-to-unit mapping rules
- Creates `usda_category_unit_mappings` table

### Phase 2: API Integration (Completed)
- Created `usda_unit_router.py` with endpoints:
  - `/api/v1/usda/units/validate` - Validate unit for food
  - `/api/v1/usda/units/category/{id}/units` - Get units for category
  - `/api/v1/usda/units/suggest-units` - Suggest units for food
  - `/api/v1/usda/units/unit-types` - Get all unit types

### Phase 3: Service Integration (Next Steps)
1. Update `smart_unit_validator.py` to use USDA data instead of hardcoded rules
2. Integrate with OCR service for better unit detection
3. Update pantry item creation to use USDA unit validation

### Phase 4: Frontend Integration
1. Update iOS app to call unit validation API
2. Show unit suggestions in add item modal
3. Validate units before saving

## Database Schema

### New Tables Created:
```sql
-- Category to unit mappings derived from USDA data
CREATE TABLE usda_category_unit_mappings (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    usage_percentage DECIMAL(5,2),
    is_preferred BOOLEAN DEFAULT FALSE,
    notes TEXT,
    FOREIGN KEY (category_id) REFERENCES usda_food_categories(id),
    FOREIGN KEY (unit_id) REFERENCES usda_measure_units(id)
);
```

### New Functions:
```sql
-- Validate unit for a food item
validate_unit_for_food(
    p_food_name TEXT,
    p_unit_name TEXT,
    p_category_id INTEGER DEFAULT NULL
) RETURNS TABLE (
    is_valid BOOLEAN,
    confidence DECIMAL,
    suggested_units TEXT[],
    reason TEXT
)
```

## Benefits

1. **Data-driven validation**: Replace hardcoded rules with USDA patterns
2. **Better accuracy**: Based on actual food data, not assumptions
3. **Category awareness**: Different rules for produce vs. dairy vs. meat
4. **Portion conversions**: Convert between units using gram weights
5. **Brand awareness**: Use brand-specific serving sizes when available

## Testing

Run the import script:
```bash
cd backend_gateway/scripts
python import_usda_unit_mappings.py
```

Test the API endpoints:
```bash
# Validate unit
curl "http://localhost:8001/api/v1/usda/units/validate?food_name=strawberries&unit=ml"

# Get units for dairy category (ID: 1)
curl "http://localhost:8001/api/v1/usda/units/category/1/units"

# Suggest units for a food
curl "http://localhost:8001/api/v1/usda/units/suggest-units?food_name=chicken%20breast"
```

## Next Steps

1. Run the import script to populate the database
2. Test the API endpoints
3. Update existing services to use USDA data
4. Monitor and refine based on user feedback