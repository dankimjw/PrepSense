# Recipe Recommendation System

## Overview

PrepSense uses an intelligent hybrid recipe recommendation system that combines user's saved recipes, AI-generated suggestions, and smart pantry analysis to provide personalized meal recommendations.

## Architecture

### Core Components

1. **CrewAIService** (`backend_gateway/services/crew_ai_service.py`)
   - Main service handling recipe recommendations
   - Coordinates between saved recipes and AI generation
   - Manages user preferences and dietary restrictions

2. **RecipeAdvisor** (Single Agent)
   - Analyzes pantry composition
   - Evaluates recipe fit based on multiple factors
   - Generates contextual advice for users

3. **UserRecipesService** (`backend_gateway/services/user_recipes_service.py`)
   - Manages saved recipes database
   - Matches saved recipes with current pantry items
   - Tracks user ratings and favorites

## Key Features

### 1. Hybrid Recipe Sources

The system intelligently combines recipes from multiple sources:

- **Saved Recipes**: User's previously saved recipes that match current pantry
- **AI-Generated**: Fresh recipe ideas from OpenAI based on available ingredients
- **Priority System**: 
  - Checks saved recipes first (faster, personalized)
  - Generates 2-5 AI recipes to complement
  - Removes duplicates intelligently

### 2. Smart Pantry Analysis

The RecipeAdvisor agent analyzes your pantry to understand:

- **Expiring Items**: Items expiring within 7 days
- **Ingredient Categories**: Proteins, vegetables, staples, etc.
- **Nutritional Balance**: Identifies protein sources and vegetables
- **Expired Items**: Tracks items past expiration

### 3. Intelligent Ranking

Recipes are ranked based on practical factors:

1. **User's liked saved recipes** (highest priority)
2. **User's favorite recipes**
3. **Recipes using expiring ingredients**
4. **Recipes you can make without shopping**
5. **Good nutritional balance**
6. **High ingredient match percentage**
7. **Fewer missing ingredients**

### 4. User Preferences & Safety

- **Dietary Restrictions**: Vegetarian, vegan, gluten-free, etc.
- **Allergen Detection**: Never suggests recipes with user's allergens
- **Cuisine Preferences**: Prioritizes preferred cuisine types
- **Comprehensive allergen mapping** for common allergens:
  - Dairy, nuts, eggs, soy, gluten, shellfish, fish

### 5. Recipe Evaluation

Each recipe is evaluated for:

- **Uses Expiring**: Does it help reduce food waste?
- **Nutritional Balance**: Good (protein + vegetables), Fair, or Unknown
- **Cooking Complexity**: Easy (≤4 steps), Medium (5-8 steps), Complex (>8 steps)
- **Meal Variety**: Diverse cuisine options

### 6. Contextual Advice

The system provides helpful advice based on context:

- Expiring items alerts and recipe prioritization
- Quick meal suggestions when requested
- Cuisine variety recommendations
- Nutritional balance insights

## API Endpoints

### Primary Endpoint

**POST** `/chat/message`
```json
{
  "message": "What can I make for dinner?",
  "user_id": 111,
  "use_preferences": true
}
```

**Response**:
```json
{
  "response": "Based on your pantry items, here are my recommendations!",
  "recipes": [...],
  "pantry_items": [...],
  "user_preferences": {...}
}
```

## Recipe Data Structure

Each recipe includes:

```typescript
{
  name: string;
  ingredients: string[];
  instructions: string[];
  nutrition: { calories: number; protein: number };
  time: number;  // minutes
  meal_type: string;
  cuisine_type: string;
  dietary_tags: string[];
  
  // Matching data
  available_ingredients: string[];
  missing_ingredients: string[];
  missing_count: number;
  available_count: number;
  match_score: number;  // 0-1 percentage
  
  // Evaluation data
  evaluation: {
    uses_expiring: boolean;
    nutritional_balance: string;
    cooking_complexity: string;
  };
  
  // Source data
  source: 'saved' | 'ai_generated';
  saved_recipe_id?: number;
  is_favorite?: boolean;
  user_rating?: string;
}
```

## User Experience Flow

1. **User Query**: "What can I make for dinner?"

2. **System Process**:
   - Fetches user's pantry items
   - Analyzes pantry composition
   - Searches saved recipes for matches
   - Generates AI recipes to fill gaps
   - Evaluates and ranks all options
   - Generates contextual advice

3. **Response**:
   - Top 5 recipe recommendations
   - Clear match percentages
   - Missing ingredients listed
   - Helpful advice about choices
   - Notes about saved favorites

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for AI recipe generation
- `DB_TYPE`: Database type (postgres/bigquery)
- Database connection settings

### User Preferences Storage

Preferences are stored in the `user_preferences` table:
- Dietary restrictions
- Allergens
- Cuisine preferences

## Performance Optimizations

1. **Saved Recipes First**: No API calls needed, instant results
2. **Reduced AI Calls**: Only generates what's needed
3. **Efficient Matching**: Optimized ingredient comparison
4. **Smart Caching**: Pantry data cached during session

## Future Enhancements

1. **Learning System**: Track which recommendations users actually cook
2. **Seasonal Awareness**: Suggest recipes based on season
3. **Budget Optimization**: Consider ingredient costs
4. **Meal Planning**: Weekly meal plan generation
5. **Community Recipes**: Share recipes between users

## Technical Notes

- The system no longer uses complex "joy scores"
- Focus is on practical, actionable recommendations
- Allergen detection is kept for safety reasons
- RecipeAdvisor provides intelligence without over-complexity