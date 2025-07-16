# PrepSense Test Plan

## Overview
This test plan covers all features in the PrepSense app for debugging and quality assurance. Each section includes test cases, expected results, and common issues to check.

## Test Environment Setup

### Prerequisites
- [ ] PostgreSQL database running with demo users created
- [ ] Backend server running (`python run_app.py`)
- [ ] iOS simulator or device ready
- [ ] `.env` file configured with correct `DEMO_USER_ID`
- [ ] Network connectivity between iOS app and backend

### Test Users
- **Samantha** (samantha-1): Admin user for demo
- **John** (john-2): Regular user
- **Jane** (jane-3): Regular user  
- **Bob** (bob-4): Regular user

---

## 1. Authentication & User Management

### 1.1 Login Flow
- [ ] **Test**: App launches with mock authentication
- [ ] **Expected**: Automatically logged in as user from `DEMO_USER_ID`
- [ ] **Debug Check**: Verify correct user ID in API calls

### 1.2 User Profile
- [ ] **Test**: View user profile information
- [ ] **Expected**: Shows correct name, email, preferences
- [ ] **Debug Check**: Check `/api/v1/users/me` endpoint response

---

## 2. Pantry Management

### 2.1 View Pantry Items
- [ ] **Test**: Navigate to Pantry tab
- [ ] **Expected**: Display all items for current user
- [ ] **Debug Check**: 
  - API call to `/api/v1/pantry/{user_id}/items`
  - Verify PostgreSQL query returns correct user's items

### 2.2 Add Pantry Item
- [ ] **Test**: Add new item manually
- [ ] **Input**: Item name, quantity, unit, expiration date
- [ ] **Expected**: Item appears in pantry list
- [ ] **Debug Check**:
  - POST to `/api/v1/pantry/items`
  - Database insert in `pantry_items` table
  - UI updates without refresh

### 2.3 Barcode Scanning
- [ ] **Test**: Scan product barcode
- [ ] **Expected**: Product details auto-populate
- [ ] **Debug Check**:
  - Camera permissions
  - Barcode API integration
  - Product lookup in `products` table

### 2.4 Edit Pantry Item
- [ ] **Test**: Update quantity, expiration date
- [ ] **Expected**: Changes persist
- [ ] **Debug Check**:
  - PUT to `/api/v1/pantry/items/{item_id}`
  - Optimistic UI update

### 2.5 Delete Pantry Item
- [ ] **Test**: Remove item from pantry
- [ ] **Expected**: Item removed, confirmation shown
- [ ] **Debug Check**:
  - DELETE to `/api/v1/pantry/items/{item_id}`
  - Soft delete vs hard delete logic

### 2.6 Expiration Tracking
- [ ] **Test**: View items by expiration status
- [ ] **Expected**: Color coding (red=expired, yellow=expiring soon)
- [ ] **Debug Check**: Date comparison logic

---

## 3. Recipe Recommendations

### 3.1 Get AI Recommendations
- [ ] **Test**: Tap "Get Recommendations" button
- [ ] **Expected**: Mix of saved recipes and AI-generated recipes
- [ ] **Debug Check**:
  - POST to `/api/v1/recipes/recommendations`
  - CrewAI/RecipeAdvisor agent execution
  - Response time (<5 seconds)

### 3.2 Recipe Filtering
- [ ] **Test**: Filter by dietary preferences
- [ ] **Expected**: Only matching recipes shown
- [ ] **Debug Check**:
  - User preferences loaded correctly
  - Filter logic in recommendation engine

### 3.3 Recipe Details
- [ ] **Test**: Tap on recipe card
- [ ] **Expected**: Full recipe with ingredients, instructions
- [ ] **Debug Check**:
  - Spoonacular API integration
  - Ingredient matching with pantry

### 3.4 Pantry Match Indicator
- [ ] **Test**: View ingredient availability
- [ ] **Expected**: Green=have, Red=missing, Yellow=partial
- [ ] **Debug Check**: Pantry comparison algorithm

---

## 4. My Recipes (Saved Recipes)

### 4.1 Save Recipe
- [ ] **Test**: Save recipe from recommendations
- [ ] **Expected**: Recipe added to "My Recipes"
- [ ] **Debug Check**:
  - POST to `/api/v1/user-recipes`
  - `user_recipes` table insert

### 4.2 View Saved Recipes
- [ ] **Test**: Navigate to My Recipes section
- [ ] **Expected**: Grid/list of saved recipes
- [ ] **Debug Check**:
  - GET `/api/v1/user-recipes`
  - Pagination if >20 recipes

### 4.3 Favorite Recipe
- [ ] **Test**: Mark recipe as favorite
- [ ] **Expected**: Star icon filled, sorts to top
- [ ] **Debug Check**:
  - PUT `/api/v1/user-recipes/{recipe_id}/favorite`
  - `is_favorite` field update

### 4.4 Delete Saved Recipe
- [ ] **Test**: Remove from saved recipes
- [ ] **Expected**: Recipe removed from list
- [ ] **Debug Check**: Soft delete implementation

### 4.5 Recipe Notes
- [ ] **Test**: Add/edit personal notes on recipe
- [ ] **Expected**: Notes persist across sessions
- [ ] **Debug Check**: JSONB field storage

---

## 5. Shopping List

### 5.1 Generate Shopping List
- [ ] **Test**: Create list from recipe
- [ ] **Expected**: Missing ingredients added to list
- [ ] **Debug Check**:
  - Ingredient subtraction logic
  - Quantity calculations

### 5.2 Manual Add to List
- [ ] **Test**: Add custom items
- [ ] **Expected**: Items appear in list
- [ ] **Debug Check**: Shopping list API endpoints

### 5.3 Check Off Items
- [ ] **Test**: Mark items as purchased
- [ ] **Expected**: Visual indication, move to completed
- [ ] **Debug Check**: State persistence

### 5.4 Add to Pantry
- [ ] **Test**: Move purchased items to pantry
- [ ] **Expected**: Items removed from list, added to pantry
- [ ] **Debug Check**: Transaction handling

---

## 6. User Preferences

### 6.1 Dietary Restrictions
- [ ] **Test**: Set vegetarian, vegan, gluten-free, etc.
- [ ] **Expected**: Preferences saved and applied
- [ ] **Debug Check**:
  - PUT `/api/v1/users/preferences`
  - Recipe filtering respects preferences

### 6.2 Cuisine Preferences
- [ ] **Test**: Select favorite cuisines
- [ ] **Expected**: Recommendations prioritize selections
- [ ] **Debug Check**: Preference weighting in AI

### 6.3 Notification Settings
- [ ] **Test**: Toggle expiration alerts
- [ ] **Expected**: Settings persist
- [ ] **Debug Check**: Local storage + backend sync

---

## 7. Search & Discovery

### 7.1 Recipe Search
- [ ] **Test**: Search recipes by name/ingredient
- [ ] **Expected**: Relevant results from Spoonacular
- [ ] **Debug Check**:
  - Search API rate limiting
  - Result caching

### 7.2 Ingredient Search
- [ ] **Test**: Search while adding pantry items
- [ ] **Expected**: Autocomplete suggestions
- [ ] **Debug Check**: Product database queries

---

## 8. Admin Features

### 8.1 Admin Panel Access
- [ ] **Test**: Access admin tab (admin users only)
- [ ] **Expected**: User management interface
- [ ] **Debug Check**: Role-based access control

### 8.2 BigQuery Tester
- [ ] **Test**: Execute SQL queries
- [ ] **Expected**: Results displayed (PostgreSQL now)
- [ ] **Debug Check**:
  - Query validation
  - Read-only enforcement

### 8.3 User Management
- [ ] **Test**: View all users, toggle admin status
- [ ] **Expected**: Changes reflected immediately
- [ ] **Debug Check**: Permission checks

---

## 9. Performance & Edge Cases

### 9.1 Offline Handling
- [ ] **Test**: Disable network, use app
- [ ] **Expected**: Graceful degradation, cached data shown
- [ ] **Debug Check**: Error boundaries, retry logic

### 9.2 Large Pantry
- [ ] **Test**: Add 100+ items
- [ ] **Expected**: Smooth scrolling, search works
- [ ] **Debug Check**: Pagination, virtualization

### 9.3 Concurrent Updates
- [ ] **Test**: Two users modify same pantry
- [ ] **Expected**: Last write wins, no corruption
- [ ] **Debug Check**: Database transaction logs

### 9.4 Session Timeout
- [ ] **Test**: Leave app idle for extended period
- [ ] **Expected**: Re-authentication or refresh
- [ ] **Debug Check**: Token expiration handling

---

## 10. Integration Points

### 10.1 Spoonacular API
- [ ] **Test**: Recipe search and details
- [ ] **Expected**: <2 second response
- [ ] **Debug Check**: API key validity, rate limits

### 10.2 OpenAI API
- [ ] **Test**: AI recipe generation
- [ ] **Expected**: Coherent recipe output
- [ ] **Debug Check**: Token usage, fallback handling

### 10.3 PostgreSQL Connection
- [ ] **Test**: Database queries under load
- [ ] **Expected**: Connection pooling works
- [ ] **Debug Check**: Connection leaks, timeouts

---

## Common Debug Commands

### Backend Logs
```bash
# View real-time logs
tail -f backend.log

# Check for errors
grep ERROR backend.log

# Database queries
grep "SELECT\|INSERT\|UPDATE\|DELETE" backend.log
```

### Database Checks
```sql
-- Check user's pantry items
SELECT * FROM pantry_items WHERE pantry_id IN 
  (SELECT pantry_id FROM pantries WHERE user_id = 1);

-- View recent recipes
SELECT * FROM user_recipes WHERE user_id = 1 
ORDER BY saved_at DESC LIMIT 10;

-- Check for orphaned records
SELECT * FROM pantry_items WHERE pantry_id NOT IN 
  (SELECT pantry_id FROM pantries);
```

### iOS Debug
```javascript
// In React Native Debugger
console.log(JSON.stringify(apiResponse, null, 2));

// Check AsyncStorage
AsyncStorage.getAllKeys().then(console.log);
```

---

## Bug Report Template

When reporting issues, include:

1. **User**: Which `DEMO_USER_ID` was used
2. **Feature**: Which section of test plan
3. **Steps**: Exact reproduction steps
4. **Expected**: What should happen
5. **Actual**: What actually happened
6. **Logs**: Relevant backend/console logs
7. **Screenshots**: If UI issue

---

## Test Execution Tracking

| Feature | Tester | Date | Pass/Fail | Notes |
|---------|---------|------|-----------|-------|
| Login | | | | |
| Pantry View | | | | |
| Add Item | | | | |
| Recipes | | | | |
| Shopping List | | | | |
| Preferences | | | | |
| Admin | | | | |

---

## Notes
- Always test with fresh data after schema changes
- Run `python create_demo_users.py` to reset test users
- Check `.env` file for correct environment settings
- Monitor backend logs during testing for errors
