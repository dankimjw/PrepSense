# Food Categorization and Unit Validation System

## Overview

This comprehensive solution enhances PrepSense's food item categorization and unit validation capabilities by integrating multiple external food databases with intelligent caching, fallback mechanisms, and a learning system that improves over time.

## Key Features

### 🎯 Multi-Database Integration
- **USDA FoodData Central**: High-quality nutrition and basic food data
- **OpenFoodFacts**: Comprehensive packaged food database
- **Spoonacular**: Recipe-focused food information with excellent parsing
- **Pattern Matching Fallback**: Regex-based categorization when APIs are unavailable

### 🧠 Intelligent Caching System
- Database-backed cache for fast lookups
- Confidence scoring for categorization quality
- Automatic cache warming with common items
- User correction integration for continuous improvement

### ✅ Advanced Unit Validation
- Context-aware unit suggestions (shopping, recipe, storage)
- Special validation rules for edge cases
- Quantity-based warnings and suggestions
- Intelligent unit conversion with food-specific factors

### 📚 Learning System
- User correction tracking and application
- Confidence score adjustments based on feedback
- Popular item identification for better caching
- Historical analytics for system improvement

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│  API Endpoints   │────│  Core Services  │
│   Components    │    │  /api/food/*     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Food Database Service                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │    USDA     │  │Spoonacular  │  │OpenFoodFacts│  │ Pattern │ │
│  │    API      │  │    API      │  │    API      │  │Matching │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Cache Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Food Items      │  │ Unit Mappings   │  │ User Corrections│  │
│  │ Cache           │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Core Services

#### 1. FoodDatabaseService
**File**: `backend_gateway/services/food_database_service.py`

Primary service that orchestrates food categorization across multiple APIs:

```python
# Example usage
food_service = FoodDatabaseService(db_service)
result = await food_service.categorize_food_item("Trader Joe's Cereal Bars")
# Returns: {
#   'category': 'snacks',
#   'confidence': 0.8,
#   'allowed_units': ['each', 'package', 'box'],
#   'data_source': 'pattern_matching'
# }
```

**Key Methods**:
- `categorize_food_item()`: Main categorization method with fallback chain
- `validate_unit_for_item()`: Check if a unit is appropriate for an item  
- `get_unit_conversions()`: Convert between units for specific foods
- `record_user_correction()`: Learn from user feedback

#### 2. UnitValidationService
**File**: `backend_gateway/services/unit_validation_service.py`

Advanced unit validation with context awareness:

```python
# Example usage
unit_service = UnitValidationService(db_service)
result = await unit_service.validate_unit("cereal bar", "liter")
# Returns: {
#   'is_valid': False,
#   'message': 'Solid items like cereal bar cannot be measured in liquid units',
#   'suggestions': ['each', 'package']
# }
```

**Special Validation Rules**:
- **Solid items → No liquid units**: Bars, cookies, chips cannot use liters/cups
- **Liquid items → No "each" units**: Unless it's a container (bottle, can)
- **Eggs → Special units**: Each, dozen, carton, size descriptors
- **Spices → Small quantities**: Teaspoons, grams, pinches

#### 3. PantryItemManagerEnhanced
**File**: `backend_gateway/services/pantry_item_manager_enhanced.py`

Enhanced pantry management with automatic categorization:

```python
# Smart natural language parsing
result = await manager.smart_add_item(user_id, "2 pounds of chicken breast")
# Automatically categorizes, validates units, converts if needed

# Batch processing with categorization
items = [
    {'item_name': 'cereal bar', 'quantity_amount': 1, 'quantity_unit': 'liter'},
    {'item_name': 'apple', 'quantity_amount': 5, 'quantity_unit': 'each'}
]
result = await manager.add_items_batch_enhanced(user_id, items)
# Corrects the cereal bar unit from 'liter' to 'each'
```

### Database Schema

#### New Tables

**food_items_cache**: Stores categorization results
```sql
CREATE TABLE food_items_cache (
    item_id SERIAL PRIMARY KEY,
    normalized_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3, 2),
    data_source VARCHAR(50),
    metadata JSONB
);
```

**food_unit_mappings**: Valid units for each food item
```sql
CREATE TABLE food_unit_mappings (
    mapping_id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES food_items_cache(item_id),
    unit VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    conversion_to_grams DECIMAL(10, 4)
);
```

**food_categorization_corrections**: User feedback tracking
```sql
CREATE TABLE food_categorization_corrections (
    correction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    normalized_name VARCHAR(255),
    corrected_category VARCHAR(100),
    corrected_unit VARCHAR(50),
    confidence_boost DECIMAL(3, 2)
);
```

### API Endpoints

**Base URL**: `/api/food`

#### Categorization
- `POST /categorize` - Categorize a single food item
- `POST /categorize/batch` - Categorize multiple items
- `GET /search` - Search across food databases

#### Unit Validation  
- `POST /validate-unit` - Validate unit for an item
- `POST /suggest-unit` - Get best unit suggestion
- `POST /convert-unit` - Convert between units

#### Learning System
- `POST /user-correction` - Record user correction
- `GET /stats/corrections` - View correction statistics (admin)
- `GET /stats/api-usage` - View API usage (admin)

#### Utility
- `GET /common-units/{category}` - Get common units for category

## Edge Cases Handled

### 1. Trader Joe's Cereal Bars Issue ✅
**Problem**: Cereal bars were being categorized incorrectly and allowed liquid units

**Solution**: 
- Special pattern matching for branded bars: `r"trader joe'?s.*bar"`
- Validation rule preventing solid items from using liquid units
- Automatic unit correction with conversion

### 2. Brand Recognition ✅  
**Problem**: Brand names affecting categorization

**Solution**:
- Separate brand field in categorization
- Brand-aware cache keys
- OpenFoodFacts integration for branded items

### 3. International Foods ✅
**Problem**: Unicode characters and non-English names

**Solution**:
- Unicode-safe string processing
- Character normalization
- Graceful fallback for unknown items

### 4. API Failures ✅
**Problem**: External APIs going down or hitting rate limits

**Solution**:
- Automatic fallback chain: Spoonacular → USDA → OpenFoodFacts → Pattern Matching
- Rate limit tracking and management
- Graceful degradation with pattern matching

### 5. Natural Language Parsing ✅
**Problem**: Users entering "2 pounds of chicken breast" instead of structured data

**Solution**:
- Smart parsing with regex patterns
- Quantity/unit/item extraction
- Brand detection for possessive forms

## Deployment Guide

### Prerequisites
1. PostgreSQL database with existing PrepSense schema
2. Optional: API keys for external services
3. Python 3.9+ with async support

### Quick Deployment

```bash
# 1. Run the deployment script
cd backend_gateway/scripts
python deploy_food_categorization.py --mode incremental

# 2. Add router to your FastAPI app
# In your main app file:
from backend_gateway.routers import food_categorization_router
app.include_router(food_categorization_router.router)

# 3. Set environment variables (optional)
export SPOONACULAR_API_KEY="your_key_here"
export USDA_API_KEY="your_key_here"
```

### Incremental Rollout (Recommended)

The system supports gradual rollout through feature flags:

**Phase 1**: New items only
```sql
UPDATE feature_flags SET is_enabled = TRUE 
WHERE flag_name = 'food_categorization_new_items';
```

**Phase 2**: Migrate existing items  
```sql
UPDATE feature_flags SET is_enabled = TRUE 
WHERE flag_name = 'food_categorization_existing';
```

**Phase 3**: Enable unit validation
```sql
UPDATE feature_flags SET is_enabled = TRUE, rollout_percentage = 50
WHERE flag_name = 'unit_validation';
```

**Phase 4**: Full learning system
```sql
UPDATE feature_flags SET is_enabled = TRUE 
WHERE flag_name = 'user_corrections';
```

## Integration Examples

### Frontend Integration

#### Pantry Item Addition
```javascript
// Enhanced item addition with validation
const addItem = async (itemData) => {
  // 1. Categorize item
  const categorization = await fetch('/api/food/categorize', {
    method: 'POST',
    body: JSON.stringify({
      item_name: itemData.name,
      brand: itemData.brand
    })
  });
  
  // 2. Validate unit
  const validation = await fetch('/api/food/validate-unit', {
    method: 'POST', 
    body: JSON.stringify({
      item_name: itemData.name,
      unit: itemData.unit,
      quantity: itemData.quantity
    })
  });
  
  // 3. Show warnings if needed
  if (!validation.is_valid) {
    showWarning(validation.message, validation.suggestions);
  }
  
  // 4. Add to pantry
  return addToPantry(itemData);
};
```

#### Smart Input Component
```javascript
// Natural language item input
const SmartItemInput = () => {
  const handleSmartAdd = async (description) => {
    const result = await fetch('/api/pantry/smart-add', {
      method: 'POST',
      body: JSON.stringify({ description })
    });
    
    if (result.success) {
      showSuccess(`Added ${result.item.name} to pantry`);
    }
  };
  
  return (
    <input
      placeholder="e.g., '2 pounds chicken breast' or 'dozen eggs'"
      onSubmit={handleSmartAdd}
    />
  );
};
```

### Backend Integration

#### Using the Enhanced Manager
```python
# In your pantry router
from backend_gateway.services.pantry_item_manager_enhanced import PantryItemManagerEnhanced

@router.post("/items/smart-add")
async def smart_add_item(
    description: str,
    current_user: dict = Depends(get_current_user),
    db_service: PostgresService = Depends(get_postgres_service)
):
    manager = PantryItemManagerEnhanced(db_service)
    result = await manager.smart_add_item(current_user['user_id'], description)
    return result

@router.post("/items/batch-enhanced")  
async def add_items_batch_enhanced(
    items: List[PantryItemCreate],
    current_user: dict = Depends(get_current_user),
    db_service: PostgresService = Depends(get_postgres_service)
):
    manager = PantryItemManagerEnhanced(db_service)
    result = await manager.add_items_batch_enhanced(
        current_user['user_id'], 
        [item.dict() for item in items]
    )
    return result
```

## Testing

### Running Tests
```bash
# Run all food categorization tests
pytest backend_gateway/tests/test_food_categorization.py -v

# Run specific edge case tests
pytest backend_gateway/tests/test_food_categorization.py::TestEdgeCases -v

# Run with coverage
pytest backend_gateway/tests/test_food_categorization.py --cov=backend_gateway/services
```

### Key Test Cases
- ✅ Trader Joe's Cereal Bars categorization
- ✅ Unit validation for bars vs liquid units  
- ✅ Brand recognition and processing
- ✅ Unicode and international food names
- ✅ API failure graceful handling
- ✅ Natural language parsing
- ✅ Concurrent categorization requests
- ✅ User correction learning
- ✅ Real-world grocery receipt items

## Monitoring and Analytics

### API Usage Monitoring
```sql
-- Check current API usage
SELECT * FROM api_usage_stats;

-- Top corrected items (indicates problems)
SELECT * FROM most_corrected_foods LIMIT 10;

-- Recent search patterns
SELECT search_term, COUNT(*) as frequency
FROM food_search_history 
WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY search_term
ORDER BY frequency DESC;
```

### Performance Metrics
- **Cache Hit Rate**: Monitor `found_in_cache` in search history
- **API Response Times**: Track `response_time_ms` 
- **Categorization Accuracy**: Monitor user corrections
- **System Load**: Track concurrent categorization requests

## Troubleshooting

### Common Issues

#### 1. API Rate Limits Exceeded
**Symptoms**: Categorization falling back to pattern matching frequently
**Solution**: 
- Check API usage: `GET /api/food/stats/api-usage`
- Increase cache warm-up for common items
- Consider upgrading API plans

#### 2. Poor Categorization Quality  
**Symptoms**: Many user corrections for same items
**Solution**:
- Check `most_corrected_foods` view
- Add specific patterns to pattern matching
- Improve cache warm-up data

#### 3. Slow Performance
**Symptoms**: Long response times for categorization
**Solution**:
- Check database indexes on cache tables
- Implement connection pooling
- Add Redis layer for frequently accessed items

#### 4. Unit Validation Too Strict
**Symptoms**: Users complaining about valid units being rejected
**Solution**:
- Review validation rules in `UnitValidationService`
- Add exceptions for specific cases
- Use warning mode instead of blocking

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('backend_gateway.services.food_database_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **ML-Based Categorization**: Train custom models on user data
2. **Nutrition Integration**: Full nutrition facts from categorization
3. **Recipe Matching**: Suggest recipes based on categorized items
4. **Expiry Prediction**: Smart expiry date suggestions by category
5. **Shopping List Generation**: Auto-categorized shopping lists
6. **Barcode Integration**: Use UPC codes for instant categorization

### API Extensibility
The system is designed for easy extension:
- New food databases can be added to `FoodDatabaseService`
- Custom validation rules can be added to `UnitValidationService`  
- Additional categorization methods can be plugged into the fallback chain

## License and Attribution

This system integrates with several external services:
- **USDA FoodData Central**: Public domain, no API key required for basic use
- **OpenFoodFacts**: Open Database License, free for non-commercial use
- **Spoonacular**: Commercial API, requires subscription for production use

Please ensure compliance with each service's terms of use.

---

For technical support or questions about this system, please refer to the PrepSense development team or create an issue in the project repository.