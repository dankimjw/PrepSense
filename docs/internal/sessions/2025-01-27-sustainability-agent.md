# Sustainability Agent Integration

## Overview
Added a Sustainability Agent to the CrewAI recipe generation system that evaluates environmental impact and promotes food waste reduction using existing PrepSense sustainability data.

## Implementation Details

### New Agent: Sustainability Agent

**Role**: Environmental and food waste expert  
**Goal**: Evaluate environmental impact and food waste reduction potential of recipes  
**Tools**: SustainabilityTool (custom)

#### Responsibilities:
1. Calculate carbon footprint (GHG emissions) for each recipe
2. Assess water and land usage impact
3. Prioritize recipes using expiring ingredients to reduce waste
4. Provide eco-friendly recommendations

#### Scoring Guidelines:
- **Low emissions** (<5 kg CO2e): Excellent eco-score (A)
- **Medium emissions** (5-15 kg CO2e): Moderate eco-score (B-C)
- **High emissions** (>15 kg CO2e): Poor eco-score (D-E)
- Bonus points for using expiring ingredients
- Favor plant-based over animal products

### SustainabilityTool

Custom tool that integrates with existing services:
- **EnvironmentalImpactService**: Uses Our World in Data (OWID) for emissions data
- **FoodWasteService**: Uses FAO data for food loss rates

#### Features:
1. **Impact Calculation**:
   - Converts ingredient quantities to kg
   - Calculates GHG emissions, water usage, land usage
   - Aggregates total environmental impact

2. **Waste Reduction Scoring**:
   - Identifies ingredients expiring within 3 days
   - Awards bonus points for using soon-to-expire items
   - Provides specific waste reduction tips

3. **Unit Conversion**:
   - Handles all common units (lb, oz, g, kg, l, ml, gallon, etc.)
   - Ensures accurate impact calculations

### Integration with Recipe Flow

The sustainability evaluation happens after recipe scoring:
1. Pantry Scan → Filter → Search → Nutrition → Preferences → Scoring
2. **NEW: Sustainability Evaluation** ← Added here
3. Response Formatting (now includes eco-scores)

### Output Format Enhancement

Recipes now include:
```json
{
  "name": "Vegetable Stir Fry",
  "ingredients": [...],
  "instructions": [...],
  "nutrition": {...},
  "sustainability": {
    "eco_score": "A",
    "carbon_footprint": 3.2,
    "water_usage": 450,
    "land_usage": 2.1,
    "waste_reduction_bonus": 10,
    "sustainability_tips": [
      "Using bell peppers helps prevent food waste (expires in 2 days)",
      "Low carbon footprint recipe!"
    ]
  }
}
```

## Environmental Data Sources

### Our World in Data (OWID)
- Greenhouse gas emissions per kg
- Land use per kg
- Freshwater withdrawals per kg
- Eutrophying emissions per kg

### FAO Food Loss & Waste Data
- Loss rates by commodity group
- Supply chain waste percentages
- Regional waste variations

## Benefits

1. **Environmental Awareness**: Users see the carbon footprint of their meals
2. **Waste Reduction**: Prioritizes recipes using expiring ingredients
3. **Sustainable Choices**: Encourages plant-based alternatives
4. **Education**: Provides actionable sustainability tips
5. **Measurable Impact**: Tracks emissions saved over time

## Testing the Sustainability Agent

```bash
# Generate recipes with sustainability scoring
curl -X POST "http://localhost:8001/api/v1/ai-recipes/generate" \
  -H "Authorization: Bearer <token>" \
  -d '{"max_recipes": 3}'

# Response includes sustainability data:
{
  "recipes": [{
    "name": "Plant-Based Pasta",
    "sustainability": {
      "eco_score": "A",
      "carbon_footprint": 2.8,
      "sustainability_tips": [
        "This recipe has 75% lower emissions than beef-based alternatives",
        "Using expiring tomatoes reduces food waste"
      ]
    }
  }]
}
```

## Future Enhancements

1. **Seasonal Scoring**: Favor in-season produce
2. **Local Sourcing**: Consider food miles
3. **Packaging Impact**: Include packaging waste metrics
4. **Water Scarcity**: Regional water stress considerations
5. **Biodiversity**: Impact on ecosystem health

## Configuration

No additional configuration needed - uses existing services:
- Environmental impact data is pre-loaded from OWID
- Food waste data is available from FAO imports
- Automatically integrates with pantry expiration dates