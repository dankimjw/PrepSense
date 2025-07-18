# Recipe Compatibility Badges Implementation

## Overview

The Recipe Compatibility Badges feature provides visual indicators on recipe cards to show at-a-glance compatibility with user preferences, dietary restrictions, and allergen requirements. This improves recipe discovery and helps users quickly identify safe recipes.

## Frontend Implementation

### Badge Types

1. **Dietary Badges**
   - 🥗 Vegetarian (Green #4CAF50)
   - 🌱 Vegan (Dark Green #388E3C)
   - 🌾 Gluten-Free (Orange #FF9800)
   - 🥛 Dairy-Free (Blue #2196F3)

2. **Safety Badges**
   - ✓ Safe - No allergens detected (Green #4CAF50) - HIGH PRIORITY
   - ⚠️ Check - Contains potential allergens (Red #FF5722) - HIGH PRIORITY

3. **Compatibility Score** (Future Enhancement)
   - Percentage match with user preferences
   - Color-coded from red (low) to green (high)

### Display Rules

- Maximum 3 badges per recipe card to avoid clutter
- Priority badges (Safe/Check) always shown first
- Badges positioned in top-left corner, leaving room for save button
- Semi-transparent background with colored text for visibility

### React Native Components

```typescript
// Badge data structure
interface CompatibilityBadge {
  icon: string;
  label: string;
  color: string;
  priority?: boolean;
}

// Recipe interface extension
interface Recipe {
  // ... existing fields
  vegetarian?: boolean;
  vegan?: boolean;
  glutenFree?: boolean;
  dairyFree?: boolean;
  allergenFree?: boolean;
  compatibilityScore?: number;
  compatibilityWarnings?: string[];
}
```

### Styling

```typescript
badgesContainer: {
  position: 'absolute',
  top: 8,
  left: 8,
  flexDirection: 'row',
  flexWrap: 'wrap',
  gap: 4,
  maxWidth: '70%',
}

compatibilityBadge: {
  flexDirection: 'row',
  alignItems: 'center',
  paddingHorizontal: 8,
  paddingVertical: 4,
  borderRadius: 12,
  gap: 4,
  backgroundColor: '{color}20', // 20% opacity
}
```

## Backend Implementation

### Data Sources

1. **Spoonacular API**
   - Provides vegetarian, vegan, glutenFree, dairyFree flags
   - Returns in recipe information endpoint

2. **User Preferences**
   - Stored in `user_preferences` table
   - Includes allergens and dietary restrictions

3. **Compatibility Calculation**
   - Cross-references recipe ingredients with user allergens
   - Checks dietary compliance
   - Generates warnings for potential issues

### API Response Enhancement

The backend should enrich recipe responses with:

```json
{
  "id": 123456,
  "title": "Recipe Name",
  // ... existing fields
  "vegetarian": true,
  "vegan": false,
  "glutenFree": true,
  "dairyFree": false,
  "allergenFree": true,
  "compatibilityScore": 85,
  "compatibilityWarnings": []
}
```

### Database Schema

```sql
-- Store recipe compatibility cache
CREATE TABLE IF NOT EXISTS recipe_compatibility_cache (
    recipe_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    vegetarian BOOLEAN,
    vegan BOOLEAN,
    gluten_free BOOLEAN,
    dairy_free BOOLEAN,
    allergen_free BOOLEAN,
    compatibility_score INTEGER,
    warnings JSONB,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## User Experience Flow

1. **Recipe List View**
   - Badges appear on recipe cards
   - Quick visual scan for compatible recipes
   - Priority given to allergen safety

2. **Recipe Detail View**
   - Expanded compatibility information
   - Detailed allergen analysis
   - Ingredient-level warnings

3. **Filtering**
   - Users can filter by badge types
   - Sort by compatibility score
   - Hide incompatible recipes

## Performance Considerations

1. **Caching**
   - Cache compatibility calculations
   - Update on preference changes
   - Batch process for efficiency

2. **Lazy Loading**
   - Calculate badges on demand
   - Prioritize visible recipes
   - Background processing for rest

## Future Enhancements

1. **Custom Badges**
   - User-defined dietary requirements
   - Cultural/religious restrictions
   - Personal preferences

2. **Detailed Warnings**
   - Specific allergen identification
   - Cross-contamination risks
   - Substitution suggestions

3. **Machine Learning**
   - Improve allergen detection
   - Learn from user corrections
   - Predict preferences

## Testing

### Unit Tests
- Badge rendering logic
- Compatibility calculation
- Priority sorting

### Integration Tests
- API response enrichment
- Database caching
- User preference integration

### UI Tests
- Badge visibility
- Layout responsiveness
- Performance with many badges

## Accessibility

- Screen reader support for badge meanings
- High contrast mode compatibility
- Alternative text descriptions
- Touch target size compliance

## Monitoring

- Track badge click-through rates
- Monitor false positive/negative rates
- User feedback on accuracy
- Performance metrics for calculation