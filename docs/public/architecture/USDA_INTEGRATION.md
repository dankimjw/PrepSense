# USDA Food Database Integration

## Overview

PrepSense now integrates with the USDA FoodData Central database, providing access to nutritional information for over 200,000 food products. This integration enhances OCR accuracy, enables barcode scanning, and provides comprehensive nutritional tracking.

## Features

### 1. Enhanced OCR Recognition
- **Automatic Text Correction**: Common OCR mistakes are corrected (e.g., "MLKWHL" → "Milk, Whole")
- **Product Matching**: Extracted items are matched against USDA database for standardized names
- **Brand Recognition**: Identifies brand information from product names
- **Confidence Scoring**: Each match includes a confidence score (0.0-1.0)

### 2. Barcode Scanning
- **Instant Product Lookup**: Scan UPC/EAN barcodes for immediate product information
- **Nutritional Data**: Get complete nutritional facts per serving
- **Brand Information**: Retrieve manufacturer and brand details
- **Ingredient Lists**: Access full ingredient information for packaged foods

### 3. Nutritional Analysis
- **Pantry Overview**: Calculate total nutritional content of entire pantry
- **Daily Values**: Track percentage of recommended daily intake
- **Recipe Nutrition**: Calculate nutritional information for recipes
- **Item-Level Data**: Get detailed nutrition for individual pantry items

### 4. Smart Categorization
- **25 Food Categories**: Items automatically categorized (Dairy, Meat, Produce, etc.)
- **120+ Units**: Standardized units of measure (cup, oz, lb, etc.)
- **Serving Sizes**: Standard serving information for accurate calculations

## API Endpoints

### Enhanced OCR
```
POST /api/v1/ocr-enhanced/scan-receipt
POST /api/v1/ocr-enhanced/scan-items
GET  /api/v1/ocr-enhanced/nutrition/{fdc_id}
```

### Barcode Lookup
```
GET  /api/v1/barcode/lookup/{barcode}
GET  /api/v1/barcode/nutrition/{barcode}
GET  /api/v1/barcode/search?pattern={partial_barcode}
```

### Pantry Nutrition
```
GET  /api/v1/pantry-nutrition/summary/{user_id}
POST /api/v1/pantry-nutrition/match-items/{user_id}
GET  /api/v1/pantry-nutrition/item/{pantry_item_id}
GET  /api/v1/pantry-nutrition/daily-intake/{user_id}
GET  /api/v1/pantry-nutrition/recipe-nutrition?recipe_id={id}
```

## Database Schema

### New Tables
1. **usda_foods** - Main food database (200K+ items)
2. **usda_food_categories** - Food categorization
3. **usda_measure_units** - Standardized units
4. **usda_nutrients** - Nutrient definitions
5. **usda_food_nutrients** - Nutritional values
6. **usda_food_portions** - Serving size information
7. **pantry_item_usda_mapping** - Links PrepSense items to USDA foods

## Usage Examples

### 1. Enhanced Receipt Scanning
```python
# Scan receipt with USDA enhancement
response = await client.post("/api/v1/ocr-enhanced/scan-receipt", json={
    "image_base64": base64_image,
    "mime_type": "image/jpeg"
})

# Response includes:
# - Original OCR text
# - Matched USDA product name
# - Brand information
# - Nutritional availability
# - Confidence scores
```

### 2. Barcode Lookup
```python
# Look up product by barcode
response = await client.get("/api/v1/barcode/lookup/041498117559")

# Returns:
{
    "found": true,
    "product": {
        "barcode": "041498117559",
        "name": "Organic 2% Reduced Fat Milk",
        "brand": "Trader Joe's",
        "category": "Dairy and Egg Products",
        "serving_size": 240,
        "serving_size_unit": "ml",
        "fdc_id": 123456
    }
}
```

### 3. Pantry Nutrition Summary
```python
# Get nutritional overview of pantry
response = await client.get("/api/v1/pantry-nutrition/summary/111")

# Returns:
{
    "total_items": 45,
    "items_with_nutrition": 38,
    "total_nutrition": {
        "calories": 15420,
        "protein_g": 823.5,
        "fat_g": 512.3,
        "carbs_g": 1845.7
    },
    "daily_values": {
        "calories_percent": 771.0,
        "protein_percent": 1647.0
    }
}
```

## Implementation Details

### OCR Enhancement Process
1. Extract text using existing OCR
2. Clean and expand abbreviated text
3. Search USDA database for matches
4. Calculate confidence scores
5. Return enhanced results with standardized names

### Barcode Processing
1. Clean barcode (remove spaces, leading zeros)
2. Query USDA database by GTIN/UPC
3. Retrieve full product details
4. Return nutritional information

### Nutrition Calculation
1. Map pantry items to USDA foods
2. Extract key nutrients (calories, protein, fat, etc.)
3. Calculate totals based on quantities
4. Convert to daily value percentages

## Setup Instructions

### 1. Create Database Tables
```bash
# Run the migration to create USDA tables
psql $DATABASE_URL < backend_gateway/migrations/create_usda_food_tables.sql
```

### 2. Import USDA Data
```bash
# Download USDA FoodData Central CSV files
# Run the import script
python backend_gateway/scripts/import_usda_data.py
```

### 3. Enable Enhanced Endpoints
The enhanced routers are automatically included when the backend starts.

## Benefits

1. **Improved Accuracy**: OCR text is validated against known products
2. **Instant Recognition**: Barcode scanning provides immediate product info
3. **Health Insights**: Track nutritional intake and dietary patterns
4. **Recipe Planning**: Calculate nutrition for meal planning
5. **Inventory Management**: Standardized product names and units

## Future Enhancements

1. **Allergen Tracking**: Flag items containing specific allergens
2. **Dietary Preferences**: Filter foods by dietary restrictions
3. **Nutritional Goals**: Set and track daily nutritional targets
4. **Shopping Suggestions**: Recommend healthier alternatives
5. **Waste Reduction**: Prioritize items by nutritional density

## Notes

- The USDA database is updated quarterly
- Nutritional values are per 100g unless otherwise specified
- Branded products may have more accurate data than generic items
- Confidence scores above 0.7 are considered reliable matches