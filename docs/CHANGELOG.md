# PrepSense Development Changelog

## 2025-01-27 - Fixed Foreign Key Constraint Issue for External Recipes

### Problem:
- Error when saving Spoonacular recipes: "user_recipes_recipe_id_fkey" foreign key constraint violation
- The `user_recipes` table had a foreign key constraint requiring `recipe_id` to exist in the local `recipes` table
- External recipes (from Spoonacular) don't exist in the local database, causing failures

### Solution:
- Dropped the foreign key constraint on `user_recipes.recipe_id`
- Created migration script `run_drop_recipe_fk.py` to safely remove the constraint
- Updated documentation to reflect this database change

### Technical Details:
- The `recipes` table exists but is not actively used - all recipe data is stored in the `recipe_data` JSONB column
- The app supports three recipe sources: 'spoonacular', 'chat'/'generated', and 'custom'/'manual'
- Removing the constraint allows flexible storage of external recipe IDs without local table dependencies

### Files Changed:
- Created: `backend_gateway/scripts/drop_recipe_fk_constraint.sql`
- Created: `run_drop_recipe_fk.py`
- Updated: `docs/Doc_FastApi_Routers.md`

## 2025-07-27 - USDA Unit Mapping Implementation

### Added: Data-Driven Unit Validation System

**Problem**: Unit validation was using hardcoded rules in `smart_unit_validator.py`, leading to inflexible and potentially incorrect unit suggestions for different food types.

**Solution**: Created a data-driven approach using USDA FoodData Central:

**Changes Made**:
1. **backend_gateway/scripts/import_usda_unit_mappings.py** (new):
   - Analyzes USDA food_portion.csv to determine unit usage patterns
   - Creates category-to-unit mappings based on actual data
   - Generates confidence scores based on usage frequency
   - Stores results in new `usda_category_unit_mappings` table

2. **backend_gateway/routers/usda_unit_router.py** (new):
   - `/validate` - Validates if a unit is appropriate for a food
   - `/category/{id}/units` - Returns common units for a food category
   - `/suggest-units` - Provides AI-powered unit suggestions
   - `/unit-types` - Lists all available unit types

3. **Database Changes**:
   - Added `usda_category_unit_mappings` table
   - Created `validate_unit_for_food()` SQL function
   - Links to existing USDA tables for comprehensive validation

**Technical Details**:
- Analyzes 3.3M+ food portions from USDA data
- Creates mappings showing which units are used what % of time per category
- Marks top 3 units per category as "preferred"
- Provides confidence scores for validation results

**Result**: Unit validation now based on real USDA data patterns rather than assumptions, providing more accurate and flexible unit suggestions for different food types.

## 2025-01-25 - OCR Category Assignment Fix

### Fixed: Items Being Miscategorized as "dry_goods"

**Problem**: All items scanned via OCR were being categorized as "dry_goods" regardless of their actual type (milk → dry_goods, bananas → dry_goods, etc.)

**Root Cause**: 
- Vision service correctly identified categories from OpenAI (Dairy, Produce, Snacks, etc.)
- OCR router was overriding these with PracticalFoodCategorizationService
- Pattern matching service defaulted to "dry_goods" when no patterns matched

**Changes Made**:
1. **backend_gateway/routers/ocr_router.py** (lines 508-522):
   - Added check for existing OpenAI category before re-categorization
   - Trust OpenAI's category when provided and not "Other"
   - Only use pattern-based categorization as fallback
   - Added logging to track which categorization method was used

**Result**: Items now retain their correct categories from OpenAI Vision API, with pattern matching only used as a fallback for edge cases.

## 2025-01-25 - UI Improvements

### Enhanced: Expiration Date Visibility on Home Screen

**Problem**: Expiration dates on pantry items were hard to see - small gray text that didn't stand out, making it difficult to quickly identify items that need attention.

**Changes Made**:
1. **ios-app/components/home/PantryItem.tsx**:
   - Added clock icon (`time-outline`) for better visual recognition
   - Increased font size from 14px to 15px with medium font weight (500)
   - Created dedicated expiry container with rounded background and padding
   - Implemented color-coded urgency system:
     - Gray background for normal items (>3 days)
     - Orange background for expiring soon (≤3 days) 
     - Red background for expired items (≤0 days)
   - Enhanced text contrast with stronger font weights (600 for expiring, 700 for expired)
   - Improved spacing and visual hierarchy

**Result**: Expiration dates now prominently display with clear visual urgency indicators, making it easy to identify items that need immediate attention.

### Fixed: Recipe Completion Modal Styling

**Problem**: Missing ingredients displayed with redundant pink background, red border, and X icon that took up unnecessary space and looked cluttered.

**Changes Made**:
1. **ios-app/components/modals/RecipeCompletionModal.tsx**:
   - Removed aggressive pink background and red border styling
   - Changed to subtle opacity (0.7) with white background
   - Removed red X icon for missing ingredients (only show green checkmark for available)
   - Softened text color from harsh red to neutral gray
   - Reduced vertical padding for more compact display

**Result**: Missing ingredients now have clean, minimal styling that clearly indicates unavailability without visual clutter.

## 2025-01-24 - iOS Warning Suppression

### Added: iOS Simulator Warning Control System

**Problem**: iOS simulator displays distracting yellow/red warning boxes during development, making it hard to focus on actual UI work.

**Changes Made**:
1. **ios-app/app/_layout.tsx**:
   - Added `LogBox` import from react-native
   - Implemented conditional warning suppression based on `EXPO_PUBLIC_SUPPRESS_WARNINGS` env var
   - When true: Suppresses ALL logs in simulator
   - When false: Only ignores specific common warnings (React lifecycle, VirtualizedLists, etc.)

2. **.env**:
   - Added `EXPO_PUBLIC_SUPPRESS_WARNINGS=false` configuration option

3. **toggle_warnings.sh**:
   - Created shell script for easy warning toggle
   - Commands: `on` (show warnings), `off` (hide warnings), no args (check status)
   - Made executable with chmod +x

**Result**: Developers can now hide simulator warnings while keeping terminal warnings visible for debugging. Toggle with `./toggle_warnings.sh on/off`.

## 2025-01-24 - Backend Fixes and Updates

### Fixed: Random Recipes 500 Internal Server Error

**Problem**: `/api/v1/recipes/random` endpoint was returning 500 errors with message "'RecipeCacheService' object has no attribute 'get_recipe_data'".

**Changes Made**:
1. **backend_gateway/services/recipe_cache_service.py**:
   - Added `_simple_cache` dictionary for key-value caching
   - Implemented `get_recipe_data()` method for retrieving cached data with expiry check
   - Implemented `cache_recipe_data()` method for storing data with TTL support
   - Both methods are async to match router expectations

**Result**: Random recipes endpoint now works correctly with 30-minute caching for improved performance.

### Fixed: User Preferences 404 Not Found Error

**Problem**: `/api/v1/preferences/` endpoints were returning 404 errors because the preferences router wasn't registered in app.py.

**Changes Made**:
1. **backend_gateway/app.py**:
   - Added import for preferences_router
   - Registered router with API prefix and "User Preferences" tag

**Note**: The preferences router already existed but uses a different database schema than expected by the frontend. May need further updates to align database structure.

## 2025-01-25 - Mock Toggle API Fix

### Fixed: MockStateResponse Validation Error

**Problem**: The `/api/v1/remote-control/toggle-all` endpoint was returning 500 errors with Pydantic validation errors. The error message indicated that `MockStateResponse` expected boolean values for the `states` field but was receiving dictionaries containing metadata.

**Root Cause**: The `enable_all_mocks()` and `disable_all_mocks()` functions in `RemoteControl_7.py` were returning the full state dictionary from `get_all_states()` which included `states`, `last_changed`, and `changed_by` fields. The router was passing this entire structure as the `states` field to `MockStateResponse`, which expected only `Dict[str, bool]`.

**Changes Made**:
1. **backend_gateway/RemoteControl_7.py**:
   - Modified `enable_all_mocks()` to return only `_remote_control._mock_states.copy()` instead of the full state dictionary
   - Modified `disable_all_mocks()` to return only `_remote_control._mock_states.copy()` instead of the full state dictionary
   - Both functions now return clean `Dict[str, bool]` without metadata

**Result**: The toggle-all endpoint now works correctly. The iOS app admin page can successfully toggle all mock data features on/off without validation errors.

### Added: Mock Recipe System for Testing

**Problem**: Need consistent test recipes for pantry item subtraction when completing recipes (Quick Complete and Start Cooking features).

**Changes Made**:
1. **backend_gateway/routers/mock_recipe_router.py**:
   - Created new router with 3 test recipes (Carbonara, Cookies, Chicken)
   - Added enable/disable endpoint for mock mode
   - Recipes include proper Spoonacular format with ingredients and instructions

2. **backend_gateway/services/recipe_advisor_service.py**:
   - Added mock recipe injection in process_message method
   - When mock mode enabled, returns test recipes instead of real ones

3. **backend_gateway/app.py**:
   - Registered mock_recipe_router

**Usage**:
- Enable: `POST /api/v1/mock/enable-mock-recipes?enable=true`
- Disable: `POST /api/v1/mock/enable-mock-recipes?enable=false`
- View recipes: `GET /api/v1/mock/test-recipes`
- Chat will recommend these recipes when mock mode is enabled
- Recipe completion will properly subtract ingredients from pantry

### Added: Centralized Remote Control for Mock Data

**Problem**: Multiple mock data toggles were scattered across different routers, making it difficult to manage test data consistently.

**Changes Made**:
1. **backend_gateway/RemoteControl_7.py**:
   - Created centralized control for all mock data toggles
   - Tracks state, last changed time, and who changed each toggle
   - Provides convenience functions for each feature

2. **backend_gateway/routers/remote_control_router.py**:
   - Unified API for controlling all mock features
   - `/remote-control/toggle-all` enables/disables all at once
   - `/remote-control/toggle` for individual features
   - `/remote-control/status` shows current state

3. **Updated existing routers**:
   - OCR router now uses `is_ocr_mock_enabled()`
   - Pantry router uses `is_recipe_completion_mock_enabled()`
   - Mock recipe router uses `is_chat_recipes_mock_enabled()`

4. **ios-app/app/(tabs)/admin.tsx**:
   - Admin page toggle now uses unified `/remote-control/toggle-all`
   - Single toggle controls OCR, recipe completion, and chat recipes

**Features controlled**:
- `ocr_scan`: Mock OCR receipt/item scanning
- `recipe_completion`: Mock pantry subtraction responses  
- `chat_recipes`: Mock recipe recommendations in chat
- `pantry_items`: (Future) Mock pantry items
- `spoonacular_api`: (Future) Mock Spoonacular API

### Added: Mock Mode Parameter to run_app.py

**Problem**: Developers needed to manually toggle mock data in the admin page after starting the app.

**Changes Made**:
1. **run_app.py**:
   - Added `-mock` or `--mock` command line parameter
   - Automatically enables all mock data after backend starts
   - Works with both full mode and backend-only mode
   - Shows mock status in startup output

**Usage**:
```bash
python run_app.py -mock           # Start app with mock data enabled
python run_app.py --backend -mock # Backend only with mock data
```

**Mock data includes**:
- OCR scanning returns test receipt items
- Recipe completion returns mock pantry subtraction
- Chat recommends test recipes (Carbonara, Cookies, Chicken)

## 2025-01-24 - OCR Authentication and Model Updates

### Fixed: OCR 500 Internal Server Error

**Problem**: OCR endpoints were returning 500 errors when OpenAI authentication failed, making it difficult to diagnose API key issues.

**Changes Made**:
1. **backend_gateway/routers/ocr_router.py**:
   - Added `from openai import OpenAI, AuthenticationError`
   - Added specific exception handling for `AuthenticationError` (returns 401)
   - Updated model from deprecated `gpt-4-vision-preview` to `gpt-4o-mini`

### Fixed: Environment Configuration Loading

**Problem**: Backend was looking for `.env` in backend_gateway directory instead of project root.

**Changes Made**:
1. **backend_gateway/core/config.py**:
   - Changed `env_file = ".env"` to `env_file = "../.env"`
2. Removed duplicate `backend_gateway/.env` file

### Fixed: API Key Management System

**Problem**: API keys were being commented out and not properly validated or cycled between file references and actual keys.

**Changes Made**:
1. **Key_Loader_7.py** - Complete rewrite:
   - Added `validate_openai_key()` function using `client.models.list()`
   - Implemented proper key cycling logic:
     - Validates existing OPENAI_API_KEY on startup
     - If invalid, reverts to `OPENAI_API_KEY_FILE=config/openai_key.txt`
     - Reads and validates key from file
     - Only replaces file reference with actual key if valid
   - Added `ensure_key_not_commented()` to prevent key commenting
   - Added `update_env_file()` for clean .env updates

**Result**: OCR endpoints now properly handle authentication errors, automatically manage API keys, and prevent manual intervention.

## 2025-01-16 - Unit Conversion System Overhaul

### Fixed: Unit Conversion Errors for Eggs and Broccoli

**Problem**: Recipe completion was failing when ingredients had descriptive words like "4 large eggs" or "2 cups fresh broccoli" because the system was treating "large" and "fresh" as units instead of descriptors.

**Changes Made**:

1. **Enhanced Spoonacular Integration** (`backend_gateway/services/spoonacular_service.py`)
   - Added `parse_ingredients()` method that correctly identifies descriptive words as metadata, not units
   - Implemented `convert_amount()` for ingredient-specific unit conversions
   - Added mock functionality for testing without API calls

2. **Created AI-Powered Unit Conversion Service** (`backend_gateway/services/unit_conversion_service.py`)
   - Built intelligent conversion with multiple fallback strategies:
     1. Spoonacular API (95% confidence)
     2. Internal conversion system (85% confidence)
     3. AI agent conversion (70% confidence)
     4. Fallback with warning (0% confidence)
   - Handles edge cases like "large" → "each" for countable items

3. **Updated Frontend Parser** (`ios-app/utils/ingredientParser.ts`)
   - Added list of descriptive words: ['large', 'medium', 'small', 'fresh', 'ripe', 'frozen', etc.]
   - Modified parsing logic to detect descriptors and prevent treating them as units
   - Better regex patterns for "4 large eggs" type ingredients

4. **Enhanced Recipe Completion Service** (`backend_gateway/services/recipe_completion_service.py`)
   - Integrated new unit conversion service in `calculate_quantity_to_use()`
   - Added ingredient name parameter for context-aware conversions
   - Improved error handling with detailed conversion metadata

5. **Added New API Endpoints** (`backend_gateway/routers/pantry_router.py`)
   - `POST /api/v1/pantry/validate-unit` - Validates if a unit is appropriate for an ingredient
   - `POST /api/v1/pantry/convert-unit` - Intelligent unit conversion
   - `POST /api/v1/pantry/parse-ingredients` - Parse ingredient strings with proper unit handling

**Result**: System now correctly handles:
- "4 large eggs" → 4 each eggs
- "2 cups fresh broccoli" → 2 cups broccoli  
- "3 medium onions" → 3 each onions

### Added: Unit Validation in UI

**Problem**: Users could select inappropriate units for items (e.g., "kg" for eggs, "each" for milk).

**Changes Made**:

1. **Real-time Unit Validation** (`ios-app/app/add-item.tsx`)
   - Added `useEffect` hook that validates unit when item name or unit changes
   - Calls `/api/v1/pantry/validate-unit` endpoint
   - Shows visual feedback: red warning icon (⚠️) for invalid units
   - Loading spinner while validating

2. **Smart Unit Suggestions**
   - When invalid unit detected, shows alert with recommended units
   - User can choose to "Keep Current" or "Use Recommended"
   - Displays suggested units below the unit selector

3. **Visual Indicators**
   - Invalid units show in red color (#EF4444)
   - Warning icon appears next to invalid units
   - Helper text shows suggested units

**How it works**:
1. User types "eggs" and selects "kg" as unit
2. System detects mismatch and shows warning
3. Alert suggests better units: "each, dozen, large, medium, small"
4. User can accept suggestion or keep their choice

### Optimized: API Call Efficiency

**Problem**: Unit validation was making API calls on every character typed.

**Solution**:
- Validation now only triggers when:
  1. User changes the unit (primary validation point)
  2. User finishes typing item name (onBlur event)
- Added caching to prevent duplicate validations
- Removed unnecessary debouncing

**Result**: 
- Before: 10+ API calls while typing "cereal bar"
- After: 1-2 API calls (on blur and unit change)

---

## 2025-01-15 - User Preferences System

### Added: Complete User Preferences for Allergens and Dietary Restrictions

**Changes Made**:
1. Created preferences API endpoint with PostgreSQL persistence
2. Added UserPreferencesModal in mobile app
3. Integrated preferences with AI recipe recommendations
4. Fixed authentication issues with mock token support

---

## Previous Changes

- Fixed React Router warnings for missing default exports
- Fixed health endpoint routing (/api/v1/health)
- Improved recipe image matching logic
- Added AI recipe validation to filter unrealistic suggestions