# FastAPI Backend Routers Documentation

## 🚨 CRITICAL INSTRUCTIONS FOR ALL CLAUDE INSTANCES 🚨

**BEFORE making any changes to backend routers:**
1. **READ** this entire document to understand existing endpoints
2. **CHECK** the actual router files for latest implementation
3. **TEST** endpoints using curl or Swagger UI before documenting
4. **UPDATE** this document immediately after adding/modifying endpoints
5. **VERIFY** request/response formats match actual implementation

**This is LIVE DOCUMENTATION** - Keep it synchronized with backend_gateway/routers/*.py files!

---

## Base Configuration

- **Base URL**: `http://localhost:8001` (development)
- **API Prefix**: `/api/v1`
- **Swagger UI**: `http://localhost:8001/docs`
- **Authentication**: Bearer token for protected endpoints

---

## Router Index

### 1. Pantry Router (`/api/v1/pantry`)
**File**: `backend_gateway/routers/pantry_router.py`

#### Endpoints:
- `GET /user/{user_id}/items` - Get all pantry items for a user
  ```bash
  curl -X GET "http://localhost:8001/api/v1/pantry/user/111/items"
  ```
  
- `POST /items` - Add new pantry item
  ```bash
  curl -X POST "http://localhost:8001/api/v1/pantry/items" \
    -H "Content-Type: application/json" \
    -d '{"user_id": 111, "product_name": "Milk", "quantity": 1, "unit": "gallon"}'
  ```

- `PUT /items/{item_id}` - Update pantry item
  ```bash
  curl -X PUT "http://localhost:8001/api/v1/pantry/items/123" \
    -H "Content-Type: application/json" \
    -d '{"quantity": 0.5}'
  ```

- `DELETE /items/{item_id}` - Delete pantry item
- `POST /validate-unit` - Validate unit for food category
- `GET /consumption/history` - Get consumption history

### 2. Recipe Router (`/api/v1/recipes`)
**File**: `backend_gateway/routers/spoonacular_router.py`

#### Endpoints:
- `GET /search` - Search recipes based on pantry items
  ```bash
  curl -X GET "http://localhost:8001/api/v1/recipes/search?user_id=111&diet_type=vegetarian"
  ```

- `GET /{recipe_id}` - Get recipe details
- `GET /random` - Get random recipes
- `POST /quick-complete/{recipe_id}` - Quick complete recipe selection

### 3. OCR Router (`/api/v1/ocr`)
**File**: `backend_gateway/routers/ocr_router.py`
**Note**: Uses OpenAI GPT-4o (updated from gpt-4o-mini) for improved accuracy

#### Endpoints:
- `POST /scan-receipt` - Scan receipt and extract items
  ```bash
  curl -X POST "http://localhost:8001/api/v1/ocr/scan-receipt" \
    -H "Content-Type: application/json" \
    -d '{"image_base64": "<base64_image_data>", "user_id": 111}'
  ```
  
- `POST /scan-items` - Scan items from product images
  ```bash
  curl -X POST "http://localhost:8001/api/v1/ocr/scan-items" \
    -H "Content-Type: application/json" \
    -d '{"image_base64": "<base64_image_data>"}'
  ```
  
- `POST /add-scanned-items` - Add scanned items to pantry
  ```bash
  curl -X POST "http://localhost:8001/api/v1/ocr/add-scanned-items" \
    -H "Content-Type: application/json" \
    -d '{"items": [{"name": "Milk", "quantity": 1, "unit": "gallon"}], "user_id": 111}'
  ```

### 4. User Router (`/api/v1/users`)
**File**: `backend_gateway/routers/users.py`

#### Endpoints:
- `GET /` - List all users
- `GET /{user_id}` - Get user details
- `POST /` - Create new user
- `PUT /{user_id}` - Update user
- `DELETE /{user_id}` - Delete user

### 5. Preferences Router (`/api/v1/preferences`)
**File**: `backend_gateway/routers/preferences_router.py`

#### Endpoints:
- `GET /{user_id}` - Get user preferences
- `PUT /{user_id}` - Update user preferences
  ```bash
  curl -X PUT "http://localhost:8001/api/v1/preferences/111" \
    -H "Content-Type: application/json" \
    -d '{"dietary_preference": ["vegetarian"], "allergens": ["nuts"]}'
  ```

### 6. Chat Router (`/api/v1/chat`)
**File**: `backend_gateway/routers/chat_router.py`

#### Endpoints:
- `POST /message` - Send chat message for recipe recommendations
- `POST /generate-recipe-image` - Generate AI recipe image

### 7. Shopping List Router (`/api/v1/shopping-list`)
**File**: `backend_gateway/routers/shopping_list_router.py`

#### Endpoints:
- `GET /{user_id}` - Get shopping list
- `POST /add` - Add items to shopping list
- `PUT /update/{item_id}` - Update shopping list item
- `DELETE /remove/{item_id}` - Remove from shopping list
- `POST /clear/{user_id}` - Clear entire shopping list

### 8. Cooking History Router (`/api/v1/cooking-history`)
**File**: `backend_gateway/routers/cooking_history_router.py`

#### Endpoints:
- `GET /trends` - Get cooking history trends
  ```bash
  curl -X GET "http://localhost:8001/api/v1/cooking-history/trends?user_id=111&days=7"
  ```
- `GET /calendar` - Get cooking calendar

### 9. User Recipes Router (`/api/v1/user-recipes`)
**File**: `backend_gateway/routers/user_recipes_router.py`

**Important Database Note**: The `user_recipes` table no longer has a foreign key constraint on `recipe_id`. This allows storing external recipe IDs (e.g., from Spoonacular) without requiring them in the local `recipes` table. The constraint was dropped on 2025-01-27 to fix issues with saving external recipes.

#### Endpoints:
- `GET /` - Get user's saved recipes
- `POST /` - Save a new recipe (supports external recipe IDs)
- `PUT /{recipe_id}/rating` - Update recipe rating
- `PUT /{recipe_id}/favorite` - Toggle favorite status
- `PUT /{recipe_id}/mark-cooked` - Mark recipe as cooked
- `DELETE /{recipe_id}` - Delete saved recipe
- `GET /{recipe_id}` - Get specific recipe

### 10. Stats Router (`/api/v1/stats`)
**File**: `backend_gateway/routers/stats_router.py`

#### Endpoints:
- `GET /comprehensive` - Get comprehensive stats (**Currently returns 404**)
  ```bash
  curl -X GET "http://localhost:8001/api/v1/stats/comprehensive?user_id=111&timeframe=month"
  ```

### 11. Units Router (`/api/v1/units`)
**File**: `backend_gateway/routers/units_router.py`

#### Endpoints:
- `GET /` - List all units
- `GET /food-category-rules/{category}` - Get unit rules for category
- `POST /suggest-unit` - Suggest appropriate unit
- `POST /validate-conversion` - Validate unit conversion

### 12. Nutrition Router (`/api/v1/nutrition`)
**File**: `backend_gateway/routers/nutrition_router.py`

#### Endpoints:
- `POST /analyze` - Analyze food nutrition (**Returns mock data**)
- `GET /nutrition-goals` - Get nutrition goals
- `GET /nutrition-insights` - Get nutrition insights

### 13. Remote Control Router (`/api/v1/remote-control`)
**File**: `backend_gateway/routers/remote_control_router.py`

#### Endpoints:
- `GET /status` - Get mock data status
- `POST /toggle/{feature}` - Toggle specific feature
- `POST /toggle-all` - Toggle all mock features

### 14. Demo Router (`/api/v1/demo`)
**File**: `backend_gateway/routers/demo_router.py`

#### Endpoints:
- `GET /recipes` - Get demo recipes
- `POST /reset-demo` - Reset demo data
- `GET /pantry-status` - Get pantry status

### 15. Admin Router (`/api/v1/admin`)
**File**: `backend_gateway/routers/admin_router.py`

#### Endpoints:
- `POST /check-tables` - Check database tables
- `POST /run-migration` - Run database migration

### 16. Health Router (`/api/v1/health`)
**File**: `backend_gateway/routers/health_router.py`

### 17. USDA Router (`/api/v1/usda`)
**File**: `backend_gateway/routers/usda_router.py`

#### Endpoints:
- `GET /search` - Search USDA food database
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/search?query=strawberries&limit=10"
  ```

- `GET /food/{fdc_id}` - Get detailed food information
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/food/167512"
  ```

- `GET /nutrients/{food_name}` - Get nutritional info by name
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/nutrients/chicken%20breast?serving_size=100"
  ```

### 18. USDA Unit Router (`/api/v1/usda/units`)
**File**: `backend_gateway/routers/usda_unit_router.py`

#### Endpoints:
- `GET /validate` - Validate unit for food item
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/units/validate?food_name=strawberries&unit=ml"
  ```
  Response:
  ```json
  {
    "is_valid": false,
    "confidence": 0.0,
    "suggested_units": ["lb", "oz", "container"],
    "reason": "Unit not commonly used for this food category",
    "food_name": "strawberries",
    "unit": "ml"
  }
  ```

- `GET /category/{category_id}/units` - Get units for food category
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/units/category/1/units?preferred_only=true"
  ```

- `GET /suggest-units` - AI-powered unit suggestions
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/units/suggest-units?food_name=chicken%20breast&limit=5"
  ```
  Response:
  ```json
  {
    "food_name": "chicken breast",
    "category": "Poultry Products",
    "suggested_units": [
      {"name": "lb", "confidence": 0.85},
      {"name": "oz", "confidence": 0.75},
      {"name": "piece", "confidence": 0.65}
    ]
  }
  ```

- `GET /unit-types` - Get all unit types
  ```bash
  curl -X GET "http://localhost:8001/api/v1/usda/units/unit-types"
  ```

### 19. AI Recipes Router (`/api/v1/ai-recipes`) - **NOT YET ACTIVE**
**File**: `backend_gateway/routers/ai_recipes_router.py`
**Status**: Commented out in app.py - requires CrewAI dependencies installation

#### Endpoints:
- `POST /generate` - Generate AI-powered recipe suggestions
  ```bash
  curl -X POST "http://localhost:8001/api/v1/ai-recipes/generate" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"max_recipes": 3}'
  ```
  Response:
  ```json
  {
    "success": true,
    "data": {
      "user_id": 111,
      "generated_at": "2025-07-27T10:30:00",
      "recipes": [
        {
          "name": "Vegetable Stir Fry",
          "ingredients": ["rice", "eggs", "vinegar"],
          "instructions": ["Heat oil...", "Add vegetables..."],
          "nutrition": {"calories": 250, "protein": 12},
          "match_score": 0.95
        }
      ],
      "recipe_count": 3
    }
  }
  ```

- `GET /pantry-summary` - Get pantry summary for recipe generation
  ```bash
  curl -X GET "http://localhost:8001/api/v1/ai-recipes/pantry-summary" \
    -H "Authorization: Bearer <token>"
  ```
  Response:
  ```json
  {
    "success": true,
    "data": {
      "user_id": 111,
      "total_items": 10,
      "fresh_items": 8,
      "preferences": {
        "dietary_preferences": ["vegetarian", "low-carb"],
        "allergens": ["gluten"]
      },
      "items_by_category": {
        "Dairy": ["milk", "eggs"],
        "Grains": ["rice"],
        "Condiments": ["vinegar", "sugar"]
      }
    }
  }
  ```

- `POST /generate-async` - Generate recipes asynchronously (long-running)
  ```bash
  curl -X POST "http://localhost:8001/api/v1/ai-recipes/generate-async" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{
      "max_recipes": 5,
      "webhook_url": "https://myapp.com/webhook/ai-recipes"
    }'
  ```
  Response:
  ```json
  {
    "success": true,
    "data": {
      "task_id": "ai_recipe_111_1234567890",
      "status": "processing",
      "message": "Recipe generation started. Check back for results."
    }
  }
  ```

- `GET /health` - Check AI recipe service health
  ```bash
  curl -X GET "http://localhost:8001/api/v1/ai-recipes/health"
  ```
  Response:
  ```json
  {
    "status": "healthy",
    "service": "AI Recipe Generation",
    "timestamp": "2025-07-27T10:30:00",
    "details": {
      "tools": {
        "pantry_tool": true,
        "ingredient_filter_tool": true,
        "user_restriction_tool": true,
        "search_tool": false,
        "scrape_tool": false
      },
      "agents": {
        "pantry_scan_agent": true,
        "ingredient_filter_agent": true,
        "recipe_search_agent": true,
        "nutritional_agent": true,
        "user_preferences_agent": true,
        "recipe_scoring_agent": true,
        "response_formatting_agent": true
      },
      "external_apis": {
        "serper_configured": false,
        "openai_configured": true
      }
    }
  }
  ```

#### Required Environment Variables:
- `OPENAI_API_KEY` - Required for AI agent reasoning
- `SERPER_API_KEY` - Optional, enables web search for recipes

#### Features:
- **Multi-agent system** using CrewAI for intelligent recipe generation
- **Caching** for 7 days to reduce API costs
- **Pantry-aware** - Only suggests recipes with available ingredients
- **Dietary restrictions** - Respects user preferences and allergens
- **Nutritional analysis** - Evaluates recipe healthiness
- **Async support** - For long-running generation tasks

#### Endpoints:
- `GET /health` - Health check endpoint
- `GET /` - Root health check

---

## Recently Added Routers (NOT YET ACTIVE)

These routers exist in code but are NOT registered in app.py:

### Supply Chain Impact Router
**File**: `backend_gateway/routers/supply_chain_impact_router.py`
- Would be at `/api/v1/supply-chain-impact/*`
- Currently registered but has bugs

### Waste Reduction Router  
**File**: `backend_gateway/routers/waste_reduction_router.py`
- Would be at `/api/v1/waste-reduction/*`
- Not registered in app.py

### USDA Router
**File**: `backend_gateway/routers/usda_router.py`
- Would be at `/api/v1/usda/*`
- Commented out in app.py

---

## Common Response Formats

### Success Response:
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response:
```json
{
  "detail": "Error message here"
}
```

### Pagination (where applicable):
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## Authentication

Most endpoints require user_id parameter. Future implementation will use Bearer tokens:
```
Authorization: Bearer <token>
```

---

## Testing Endpoints

Always test endpoints after changes:
```bash
# Quick test
curl -X GET "http://localhost:8001/api/v1/health"

# With jq for pretty printing
curl -s "http://localhost:8001/api/v1/pantry/user/111/items" | jq

# POST with data
curl -X POST "http://localhost:8001/api/v1/endpoint" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

---

**Last Updated**: 2025-07-27 (Added AI Recipes router with CrewAI integration)
**Next Review**: When adding new routers or modifying endpoints

<!-- AUTO‑DOC‑MAINTAINER: routers -->
<!-- END -->