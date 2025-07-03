# AI Bulk Edit Backend Implementation Guide

## Overview
The AI Bulk Edit feature allows users to select multiple pantry items and apply AI-powered corrections and enhancements in bulk.

## Endpoint Specification

### `POST /api/v1/ai/bulk-correct-items`

**Request Body:**
```json
{
  "user_id": 111,
  "item_ids": ["101105", "101109", "101112"],
  "options": {
    "correct_units": true,
    "update_categories": true,
    "estimate_expirations": true,
    "enable_recurring": true,
    "recurring_options": {
      "add_to_shopping_list": true,
      "days_before_expiry": 7
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "processed_items": 3,
  "corrections": [
    {
      "item_id": "101105",
      "changes": {
        "unit": { "from": "each", "to": "gallon" },
        "category": { "from": "Other", "to": "Dairy" },
        "expiration": { "from": null, "to": "2024-01-20" }
      }
    }
  ],
  "recurring_items_created": 2,
  "cost": 0.006
}
```

## Implementation Steps

### 1. AI Corrections Logic

#### Unit Correction
```python
def correct_unit(item_name: str, current_unit: str) -> str:
    """
    Use GPT to determine the most appropriate unit for an item.
    
    Examples:
    - "Milk" with unit "each" → "gallon"
    - "Apples" with unit "item" → "each"
    - "Rice" with unit "piece" → "pound"
    """
    prompt = f"What is the most appropriate unit of measurement for '{item_name}'? Current: {current_unit}"
    # Call OpenAI API
    return corrected_unit
```

#### Category Assignment
```python
def assign_category(item_name: str) -> str:
    """
    Use GPT to categorize items correctly.
    
    Categories: Dairy, Meat, Produce, Grains, Beverages, Snacks, Condiments, Other
    """
    prompt = f"Categorize '{item_name}' into one of these categories: [list]"
    # Call OpenAI API
    return category
```

#### Expiration Estimation
```python
def estimate_expiration(item_name: str, category: str) -> date:
    """
    Estimate typical shelf life based on item type.
    
    Examples:
    - Fresh milk: 7-10 days
    - Canned goods: 2 years
    - Fresh produce: 3-7 days
    """
    prompt = f"Estimate shelf life for '{item_name}' in category '{category}'"
    # Call OpenAI API and calculate date
    return expiration_date
```

### 2. Recurring Shopping List

For items with `enable_recurring = true`:

1. Create a `recurring_items` table:
```sql
CREATE TABLE recurring_items (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  item_name VARCHAR(255) NOT NULL,
  quantity_amount DECIMAL(10,2),
  quantity_unit VARCHAR(50),
  days_before_expiry INTEGER DEFAULT 7,
  last_added_date DATE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. Set up a daily cron job to check expiring items and add to shopping list:
```python
def check_recurring_items():
    """Run daily to add items to shopping list before they expire"""
    for item in get_active_recurring_items():
        if should_add_to_shopping_list(item):
            add_to_shopping_list(item)
            update_last_added_date(item)
```

### 3. Batch Processing

To handle multiple items efficiently:

```python
async def bulk_correct_items(request: BulkCorrectRequest):
    # Fetch all items in one query
    items = await get_pantry_items_by_ids(request.item_ids)
    
    # Process in parallel
    corrections = await asyncio.gather(*[
        process_item_corrections(item, request.options) 
        for item in items
    ])
    
    # Batch update database
    await bulk_update_items(corrections)
    
    # Handle recurring items if enabled
    if request.options.enable_recurring:
        await create_recurring_items(items, request.options.recurring_options)
    
    return BulkCorrectResponse(corrections=corrections)
```

### 4. Cost Calculation

Track API usage for transparency:

```python
def calculate_cost(num_items: int, options: dict) -> float:
    """
    Estimate cost based on OpenAI API usage
    Approximate: $0.002 per item for all corrections
    """
    base_cost_per_item = 0.002
    return num_items * base_cost_per_item
```

### 5. Error Handling

- Validate item ownership before processing
- Handle OpenAI API rate limits with exponential backoff
- Log all corrections for audit trail
- Provide detailed error messages for partial failures

## Testing

1. Unit tests for each correction function
2. Integration tests with mock OpenAI responses
3. Load testing for bulk operations (100+ items)
4. Test recurring item creation and scheduling

## Security Considerations

1. Verify user owns all items before processing
2. Rate limit bulk operations (max 100 items per request)
3. Sanitize item names before sending to OpenAI
4. Store API costs per user for billing/limits

## Future Enhancements

1. **Smart Grouping**: Detect similar items (e.g., "Milk 2%", "2% Milk") and merge
2. **Nutritional Data**: Add nutritional information during processing
3. **Price Tracking**: Estimate item costs based on location
4. **Waste Reduction**: Track which items frequently expire and adjust recurring settings
5. **Batch Scheduling**: Allow users to schedule bulk corrections during off-peak hours