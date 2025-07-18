# Food Database Import Pipeline

## Overview

The Food Database Import Pipeline is a comprehensive system for importing and maintaining food data from external sources including USDA FoodData Central and Open Food Facts. This ensures PrepSense has up-to-date food categorization and nutritional information.

## Features

- **Multi-source Integration**: Imports from USDA FoodData Central and Open Food Facts
- **Incremental Updates**: Only imports new or updated items to minimize API usage
- **Scheduled Imports**: Automated daily, weekly, and monthly import schedules
- **Rate Limiting**: Respects API rate limits and tracks usage
- **Data Quality**: Validates and scores data quality, preferring high-confidence sources
- **Duplicate Prevention**: Intelligently merges data from multiple sources
- **Nutritional Data**: Imports calories, protein, carbs, and fat per 100g
- **Unit Mapping**: Automatically assigns appropriate units based on food category

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐
│   USDA FoodData     │     │  Open Food Facts │
│      Central        │     │       API        │
└──────────┬──────────┘     └────────┬─────────┘
           │                         │
           └────────────┬────────────┘
                        │
                   ┌────▼─────┐
                   │  Import   │
                   │ Pipeline  │
                   └────┬─────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │  Food    │   │  Unit   │   │  Cache  │
    │  Items   │   │Mappings │   │ Tables  │
    └─────────┘   └─────────┘   └─────────┘
```

## Setup

### 1. Install Dependencies

```bash
cd backend_gateway/scripts
./setup_import_pipeline.sh
```

### 2. Configure API Keys

#### USDA FoodData Central
1. Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html
2. Add to your environment:
   ```bash
   export USDA_API_KEY="your-api-key-here"
   ```

#### Open Food Facts
No API key required - it's an open database!

### 3. Initialize Database

The pipeline will automatically create required tables on first run:
- `food_items_cache`: Stores normalized food information
- `food_unit_mappings`: Valid units for each food item
- `food_categorization_corrections`: User feedback tracking
- `api_rate_limits`: API usage tracking
- `food_import_statistics`: Import history and metrics

## Usage

### One-Time Import

```bash
# Import from all sources
python3 food_database_import_pipeline.py

# Import only from USDA
python3 food_database_import_pipeline.py --sources usda

# Import only from Open Food Facts  
python3 food_database_import_pipeline.py --sources openfoodfacts

# Test import with limited data (10 items per batch)
python3 food_database_import_pipeline.py --test
```

### Scheduled Imports

#### Option 1: Run as Service
```bash
python3 food_database_import_pipeline.py --schedule
```

This runs continuously and executes:
- Daily USDA import at 2 AM
- Weekly Open Food Facts import on Sunday at 3 AM
- Monthly full import on the 1st at 4 AM

#### Option 2: Use Cron Jobs
```bash
# Add to crontab
crontab -e

# Add these lines:
0 2 * * * cd /path/to/scripts && python3 food_database_import_pipeline.py --sources usda
0 3 * * 0 cd /path/to/scripts && python3 food_database_import_pipeline.py --sources openfoodfacts
0 4 1 * * cd /path/to/scripts && python3 food_database_import_pipeline.py
```

#### Option 3: Systemd Service (Linux)
```bash
# Copy service file
sudo cp /tmp/prepsense-food-import.service /etc/systemd/system/

# Enable and start
sudo systemctl enable prepsense-food-import
sudo systemctl start prepsense-food-import

# Check status
sudo systemctl status prepsense-food-import
```

## Data Sources

### USDA FoodData Central
- **Coverage**: ~400,000 foods
- **Quality**: High - government curated
- **Best for**: Basic ingredients, raw foods, nutrition data
- **API Limit**: 1,000 requests/day (free tier)
- **Import Focus**: Foundation and SR Legacy food types

### Open Food Facts
- **Coverage**: ~2 million products worldwide
- **Quality**: Variable - crowdsourced
- **Best for**: Packaged/branded products, barcodes
- **API Limit**: 10,000 requests/day
- **Import Focus**: Products with good data quality

## Import Process

1. **Rate Limit Check**: Verifies API usage is within limits
2. **Data Fetching**: Retrieves food data in batches
3. **Normalization**: Standardizes food names and categories
4. **Deduplication**: Checks for existing items
5. **Quality Scoring**: Calculates confidence based on data completeness
6. **Storage**: Saves to PostgreSQL with appropriate categorization
7. **Unit Mapping**: Assigns valid units based on food category
8. **Statistics**: Updates import metrics

## Data Quality

### Confidence Scoring
Each food item receives a confidence score (0-1) based on:
- Data completeness (nutrition info, brand, barcode)
- Source reliability (USDA > Spoonacular > Open Food Facts > Patterns)
- User corrections (highest confidence)

### Category Mapping
Foods are mapped to PrepSense categories:
- `produce_countable`: Apples, bananas, etc.
- `produce_measurable`: Lettuce, spinach, etc.
- `liquids`: Milk, oil, juice, etc.
- `dry_goods`: Flour, rice, pasta, etc.
- `meat_seafood`: Chicken, beef, fish, etc.
- `dairy`: Cheese, yogurt, etc.
- `bakery`: Bread, cakes, etc.
- `snacks_bars`: Cereal bars, protein bars, etc.
- `packaged_snacks`: Chips, crackers, etc.
- `other`: Everything else

## Monitoring

### Check Import Statistics
```sql
-- View recent imports
SELECT * FROM food_import_statistics 
ORDER BY import_date DESC LIMIT 10;

-- Check API usage
SELECT * FROM api_usage_stats;

-- Find most corrected items
SELECT * FROM most_corrected_foods LIMIT 20;
```

### Log Files
```bash
# Check import logs
tail -f logs/imports/usda.log
tail -f logs/imports/off.log
tail -f logs/imports/full.log
```

## Troubleshooting

### Common Issues

1. **"API key not configured"**
   - Set USDA_API_KEY environment variable
   - Check ~/.bashrc or ~/.zshrc for persistence

2. **"Rate limit exceeded"**
   - Wait for daily reset (midnight UTC)
   - Check api_rate_limits table
   - Consider upgrading API tier

3. **"Import takes too long"**
   - Use --test flag for smaller batches
   - Import specific sources instead of all
   - Check network connectivity

4. **"Duplicate key violations"**
   - Normal for updates - pipeline handles gracefully
   - Check logs for specific items

### Manual Cleanup

```sql
-- Reset API counters
UPDATE api_rate_limits 
SET requests_today = 0, last_reset = CURRENT_TIMESTAMP 
WHERE api_name = 'usda';

-- Remove low-quality old data
DELETE FROM food_items_cache 
WHERE confidence_score < 0.3 
AND updated_at < CURRENT_DATE - INTERVAL '6 months';
```

## Integration with PrepSense

The imported data is used by:
1. **Food Categorization Service**: For categorizing pantry items
2. **Unit Validation Service**: For validating appropriate units
3. **Recipe Matching**: For ingredient recognition
4. **Nutritional Tracking**: For calorie/macro calculations

## Performance Considerations

- **Batch Processing**: Processes foods in batches of 100
- **Concurrent Requests**: Limited to 5 simultaneous API calls
- **Caching**: In-memory cache reduces database queries
- **Incremental Updates**: Only updates changed data
- **Cleanup**: Automatically removes stale data

## Future Enhancements

1. **Machine Learning**: Train custom categorization model on user corrections
2. **Image Recognition**: Import food images for visual identification
3. **Barcode Scanner**: Direct barcode lookup integration
4. **More Sources**: Integration with Nutritionix, Edamam APIs
5. **Real-time Sync**: Webhook-based updates instead of polling

## API Reference

### Import Pipeline Methods

```python
# Run import from specific sources
results = await pipeline.run_import_pipeline(['usda', 'openfoodfacts'])

# Results format
{
    'success': 1523,     # Items imported
    'failed': 12,        # Items failed
    'skipped': 456,      # Items already up-to-date
    'errors': [...]      # Error messages
}
```

### Database Schema

See `create_food_categorization_tables.sql` for complete schema.

## Contributing

When adding new data sources:
1. Implement source-specific import method
2. Add category mapping logic
3. Update confidence scoring
4. Add to rate limiting table
5. Document API requirements