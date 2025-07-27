# Complete CrewAI Agent System Documentation

## Overview
PrepSense uses a sophisticated 10-agent CrewAI system for intelligent recipe generation with proper categorization, unit validation, and sustainability scoring.

## All Agents (10 Total)

### 1. Pantry Scan Agent
- **Role**: Pantry Scan Agent
- **Goal**: Retrieve available ingredients from PostgreSQL database
- **Tools**: PostgresPantryTool
- **Output**: Raw pantry data with all items

### 2. Food Categorization Agent 🆕
- **Role**: Food Category Expert
- **Goal**: Accurately categorize food items
- **Tools**: FoodCategorizationTool
- **Key Rules**:
  - Chicken Broth → Soups & Broths (NOT Meat)
  - Strawberries → Produce (NOT Beverages)
  - Tomato Sauce → Condiments (NOT Produce)
- **Output**: Items with corrected categories

### 3. Unit Correction Agent 🆕
- **Role**: Unit Measurement Expert
- **Goal**: Suggest appropriate units based on category
- **Tools**: UnitCorrectionTool
- **Key Rules**:
  - Produce: lb, oz, each (NEVER ml)
  - Liquids: fl oz, quart, gallon (NEVER each)
  - Eggs: dozen, each (NEVER by weight)
- **Output**: Items with retail-standard units

### 4. Ingredient Filter Agent
- **Role**: Ingredient Filter Agent
- **Goal**: Filter expired/unusable items
- **Tools**: IngredientFilterTool
- **Output**: Only fresh, available ingredients

### 5. Recipe Search Agent
- **Role**: Recipe Search Agent
- **Goal**: Find recipes using available ingredients
- **Tools**: SerperDevTool, ScrapeWebsiteTool
- **Output**: Recipe suggestions with proper units

### 6. Nutritional Agent
- **Role**: Nutritional Agent
- **Goal**: Evaluate nutritional balance
- **Tools**: SerperDevTool (optional)
- **Unit Awareness**: Converts units for nutrition calculations
- **Output**: Nutritional analysis per recipe

### 7. User Preferences Agent
- **Role**: User Preferences Agent
- **Goal**: Apply dietary restrictions/allergens
- **Tools**: UserRestrictionTool
- **Output**: Filtered recipes safe for user

### 8. Recipe Scoring Agent
- **Role**: Recipe Scoring Agent
- **Goal**: Rank recipes by quality match
- **Tools**: None (uses analysis from other agents)
- **Output**: Scored and ranked recipes

### 9. Sustainability Agent
- **Role**: Sustainability Agent
- **Goal**: Evaluate environmental impact
- **Tools**: SustainabilityTool
- **Metrics**:
  - GHG emissions (kg CO2e)
  - Water usage (liters)
  - Land usage (m²)
  - Waste reduction bonus
- **Output**: Eco-scores and sustainability tips

### 10. Response Formatting Agent
- **Role**: Response Formatting Agent
- **Goal**: Format final output
- **Output**: JSON with:
  - Corrected categories
  - Proper units
  - Nutritional data
  - Eco-scores
  - Sustainability tips

## Workflow Sequence

```
1. Pantry Scan → Retrieves all items
2. Food Categorization → Fixes categories (chicken broth → soup)
3. Unit Correction → Fixes units (strawberries ml → lb)
4. Ingredient Filter → Removes expired items
5. Recipe Search → Finds matching recipes
6. Nutritional Agent → Analyzes nutrition
7. User Preferences → Filters by dietary needs
8. Recipe Scoring → Ranks by quality
9. Sustainability → Adds eco-scores
10. Response Formatting → Creates final JSON
```

## Example Corrections

### Before Categorization:
- "Pacific Organic Chicken Broth" - Category: Meat ❌
- "Fresh Strawberries" - Unit: 500 ml ❌

### After Categorization & Unit Correction:
- "Pacific Organic Chicken Broth" - Category: Soups & Broths ✅
- "Fresh Strawberries" - Unit: 1 lb ✅

## Tools Overview

### Database Tools:
1. **PostgresPantryTool** - Fetches pantry items
2. **IngredientFilterTool** - Filters non-expired
3. **UserRestrictionTool** - Gets dietary preferences
4. **FoodCategorizationTool** - Categorizes foods
5. **UnitCorrectionTool** - Validates units

### External Tools:
1. **SerperDevTool** - Web search for recipes
2. **ScrapeWebsiteTool** - Extract recipe details

### Analysis Tools:
1. **SustainabilityTool** - Environmental impact
2. **SmartUnitValidator** - Unit validation rules

## Configuration

All agents work together automatically when calling:
```python
POST /api/v1/ai-recipes/generate
```

The system ensures:
- ✅ Correct food categories (broth ≠ meat)
- ✅ Proper units (strawberries in lb, not ml)
- ✅ Nutritional accuracy
- ✅ Sustainability scoring
- ✅ Dietary compliance

## Benefits

1. **Accuracy**: No more "500 ml of strawberries"
2. **Intelligence**: Understands chicken broth is liquid, not meat
3. **Sustainability**: Promotes eco-friendly choices
4. **Waste Reduction**: Prioritizes expiring items
5. **User Safety**: Respects allergies and preferences