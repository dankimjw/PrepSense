# CrewAI Integration for AI-Powered Recipe Generation

## Overview
Implemented a sophisticated multi-agent AI system using CrewAI to generate personalized recipe suggestions based on users' pantry inventory, dietary preferences, and nutritional requirements.

## Architecture

### Multi-Agent System
The implementation uses 7 specialized AI agents that work together:

1. **Pantry Scan Agent** - Retrieves available ingredients from PostgreSQL
2. **Ingredient Filter Agent** - Filters out expired/unusable items
3. **Recipe Search Agent** - Finds recipes using available ingredients
4. **Nutritional Agent** - Evaluates nutritional balance
5. **User Preferences Agent** - Applies dietary restrictions and allergens
6. **Recipe Scoring Agent** - Ranks recipes by quality match
7. **Response Formatting Agent** - Formats results for API response

### Key Components

#### 1. CrewAI Service (`backend_gateway/services/crew_ai_service.py`)
- Main service orchestrating all AI agents
- Converts BigQuery queries from notebook to PostgreSQL
- Implements custom tools for database interaction
- Handles agent coordination and task execution

#### 2. AI Recipe Cache Service (`backend_gateway/services/ai_recipe_cache_service.py`)
- PostgreSQL-based caching for 7 days
- Reduces API costs by avoiding duplicate generations
- Cache key based on pantry items, preferences, and recipe count
- Automatic cache invalidation when pantry changes

#### 3. API Router (`backend_gateway/routers/ai_recipes_router.py`)
- RESTful endpoints for recipe generation
- Supports synchronous and asynchronous generation
- Includes health check endpoint
- Protected by user authentication

## API Endpoints

### 1. Generate Recipes
```bash
POST /api/v1/ai-recipes/generate
{
  "max_recipes": 3
}
```

### 2. Get Pantry Summary
```bash
GET /api/v1/ai-recipes/pantry-summary
```

### 3. Generate Async (with webhook)
```bash
POST /api/v1/ai-recipes/generate-async
{
  "max_recipes": 5,
  "webhook_url": "https://myapp.com/webhook"
}
```

### 4. Health Check
```bash
GET /api/v1/ai-recipes/health
```

## Database Schema

### AI Recipe Cache Table
```sql
CREATE TABLE ai_recipe_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    cache_key VARCHAR(64) NOT NULL,
    pantry_snapshot JSONB NOT NULL,
    preferences_snapshot JSONB NOT NULL,
    recipes JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, cache_key)
);
```

## Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` - For AI agent reasoning (required)
- `SERPER_API_KEY` - For web search capabilities (optional)

## Dependencies

Updated `requirements.txt`:
- `crewai==0.119.0` (upgraded from 0.5.0)
- `crewai-tools==0.44.0` (new)

## Current Status

**Note**: The AI recipes router is currently commented out in `app.py` pending installation of CrewAI dependencies. To activate:

1. Install dependencies: `pip install -r requirements.txt`
2. Uncomment lines 181-182 in `backend_gateway/app.py`
3. Add required API keys to `.env` file:
   - `OPENAI_API_KEY=your-key-here`
   - `SERPER_API_KEY=your-key-here` (optional)

## Implementation Notes

### 1. Database Migration
- Converted all BigQuery queries to PostgreSQL
- Adapted to PrepSense's existing schema
- Uses `pantry_items` and `user_preferences` tables

### 2. Error Handling
- Graceful degradation if external APIs unavailable
- Returns cached results when possible
- Comprehensive error messages for debugging

### 3. Performance Optimizations
- 7-day cache reduces API calls
- Async endpoint for long-running tasks
- Efficient database queries with proper indexing

## Future Enhancements

1. **Frontend Integration** - Add UI components for AI recipe display
2. **Recipe Storage** - Save generated recipes to user's collection
3. **Feedback Loop** - Learn from user preferences over time
4. **Image Generation** - Add recipe images using AI
5. **Shopping List** - Generate shopping lists for missing ingredients

## Testing Requirements

1. **Unit Tests** - Test each agent tool independently
2. **Integration Tests** - Test full crew execution
3. **API Tests** - Test all endpoints with mocked AI responses
4. **Cache Tests** - Verify caching behavior

## Usage Example

```python
# Generate recipes for user 111
curl -X POST "http://localhost:8001/api/v1/ai-recipes/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"max_recipes": 3}'

# Response includes:
# - Recipe names and ingredients
# - Step-by-step instructions
# - Nutritional information
# - Match scores based on available ingredients
```

## Monitoring

The health endpoint provides real-time status of:
- All AI agents initialization
- Database tool availability
- External API configuration
- Cache statistics

This implementation brings advanced AI capabilities to PrepSense, enabling intelligent recipe suggestions that reduce food waste and promote healthy eating based on what users actually have available.