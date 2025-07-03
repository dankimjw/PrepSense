# Stats Screen Implementation Notes

## Overview
The Stats screen provides comprehensive analytics for the PrepSense app, tracking pantry items, recipes, shopping habits, and user achievements.

## Current Implementation Status

### ✅ Completed Features

#### 1. **Pantry Analytics**
- **Total Items Count** - REAL DATA
  - Source: `fetchPantryItems(111)` from backend
  - Displays actual count of items in user's pantry
  
- **Expiring Soon** - REAL DATA  
  - Calculates items expiring within 7 days
  - Uses actual `expiration_date` from pantry items
  
- **Recently Added** - REAL DATA
  - Shows items added in last 7 days
  - Uses `created_at` timestamp from items
  
- **Most Common Categories** - REAL DATA
  - Groups items by `category` field
  - Shows top 5 categories with item counts
  
- **Pantry Value** - MOCK DATA
  - Currently: `items.length * $3.50`
  - Needs: Actual item prices from backend

#### 2. **Recipe & Cooking Stats**
- **Recipes This Week/Month** - REAL DATA
  - Filters saved recipes by `created_at` date
  - Only shows data if user is authenticated
  
- **Total Recipes Cooked** - REAL DATA
  - Count of all saved recipes from user-recipes endpoint
  
- **Cooking Streak** - REAL DATA (with limitations)
  - Calculates consecutive days with recipes
  - Limited by when recipes were saved, not cooked
  
- **Top Recipes** - REAL DATA
  - Groups saved recipes by title
  - Shows most frequently saved recipes
  
- **Average Prep Time** - MOCK DATA (35 min)
- **Success Rate** - MOCK DATA (95%)
- **Average Nutrition** - MOCK DATA (420 cal, 25g protein)

#### 3. **Shopping Insights**
- **List Completion Rate** - REAL DATA
  - Calculates from local AsyncStorage shopping list
  - `checked items / total items * 100`
  
- **Shopping Frequency** - MOCK DATA ("Weekly")
- **Average Spend** - MOCK DATA ($85.50)
- **Most Purchased Items** - MOCK DATA
- **Savings from Pantry** - MOCK DATA

#### 4. **Achievements & Gamification**
- **Milestones** - PARTIALLY REAL
  - Based on real recipe/pantry counts
  - Achievements: First Recipe, 10 Recipes, Master Chef, etc.
  
- **Waste Reduction Score** - MOCK DATA (85%)
- **Pantry Optimization Score** - MOCK DATA (78%)
- **Cooking Streak Days** - REAL DATA

#### 5. **Visual Features**
- **Charts** - MOCK DATA
  - Weekly cooking frequency line chart
  - Currently shows hardcoded data [2,1,3,2,4,3,5]
  
- **Progress Bars** - REAL DATA
  - Category distribution uses actual percentages

## Data Sources

### Backend APIs
1. `/api/v1/pantry/user/{user_id}/items` - Pantry items
2. `/api/v1/user-recipes` - Saved recipes (requires auth)

### Local Storage
1. `@PrepSense_ShoppingList` - Shopping list items

### Hardcoded User ID
- Currently using `user_id = 111` for demo purposes
- Should be replaced with actual authenticated user ID

## TODO: Features Needing Implementation

### 1. **Backend Requirements**
- [ ] Add price tracking to pantry items
- [ ] Track actual recipe completion (not just saves)
- [ ] Store recipe prep times in database
- [ ] Track shopping history and purchases
- [ ] Implement waste tracking (expired items)
- [ ] Store nutrition data for completed recipes

### 2. **Enhanced Tracking**
- [ ] Track when recipes are actually cooked vs saved
- [ ] Monitor pantry usage patterns
- [ ] Calculate real savings based on recipe ingredients used
- [ ] Track shopping frequency from actual purchases
- [ ] Monitor ingredient usage frequency

### 3. **UI Improvements Needed**
Based on UI reference images (UI_Notes_1.jpeg):

#### Recipe Details Screen Improvements:
- [ ] Implement collapsible recipe instructions with numbered steps (01, 02, 03)
- [ ] Add ingredient checkboxes with expandable details
- [ ] Include user profile avatar and "Follow" button for recipe creators
- [ ] Add bookmark icon in top-right corner of recipe cards
- [ ] Show follower count and likes inline with recipe info
- [ ] Implement "Popular >" section for related recipes

#### Filter & Category Icons (from "What Do You Want To Cook Today?"):
- [ ] Replace text filters with icon-based categories:
  - 🍔 Western
  - 🍜 Bread  
  - 🥗 Salad
  - 🍲 Soup
  - 🥤 Dessert
  - 🍹 Cocktail
  - 🍜 Noodles
  - ☕ Coffee
- [ ] Add "14 Recommendations" counter
- [ ] Implement "See More >" expandable sections

#### From Color_UI.jpeg (Grocery/Shopping app style):
- [ ] Add colorful category pills (Featured, New & Popular, Let's Grill, Snacks)
- [ ] Implement promotional banners ("Unlimited Free Delivery", "15% Off")
- [ ] Show savings/points earned ("You could earn 468 points")
- [ ] Add estimated totals with details dropdown
- [ ] Include "Hot this week!" section with visual cards

#### Stats Screen Specific Improvements:
- [ ] Replace current filter buttons with icon-based navigation
- [ ] Add recipe cards with:
  - Bookmark icon overlay
  - Creator avatar
  - Prep time and difficulty badges
- [ ] Implement tabbed navigation for time periods (Week/Month/Year)
- [ ] Add visual recipe cards showing actual food images
- [ ] Include user avatars for social proof

### 4. **Real-time Analytics**
- [ ] Connect cooking frequency chart to real data
- [ ] Add monthly/yearly view toggles
- [ ] Implement pantry value trends over time
- [ ] Show nutrition trends from actual recipes

### 5. **Missing Calculations**
- [ ] Actual cost savings calculation
- [ ] Real waste tracking percentage
- [ ] Pantry efficiency score algorithm
- [ ] Shopping list optimization suggestions

## Technical Debt
1. Remove hardcoded `user_id = 111`
2. Move calculations to backend for consistency
3. Implement proper TypeScript types for all API responses
4. Add error boundaries for failed data fetches
5. Cache stats data to reduce API calls

## Performance Considerations
- Currently fetches all data on mount and refresh
- Consider implementing:
  - Pagination for large datasets
  - Background refresh
  - Incremental loading
  - Data caching strategy

## UI Design Patterns from Reference Images

### Key Visual Elements to Implement:

1. **Recipe Cards (from UI_Notes_1.jpeg)**
   - Large food photography with rounded corners
   - Overlay text with semi-transparent background
   - Bottom bar showing: prep time, serving size, difficulty
   - Bookmark icon in top-right corner
   - User avatar with name for recipe creator

2. **Category Navigation**
   - Icon-based categories instead of text
   - Horizontal scrollable row
   - Visual hierarchy with icons above labels
   - Counter badges for recommendations

3. **Instruction Steps**
   - Numbered steps (01, 02, 03) in circles
   - Expandable/collapsible sections
   - Checkboxes for ingredient preparation
   - Clear typography hierarchy

4. **Stats Cards Enhancement**
   - Add small icons to each stat card (like the grocery app)
   - Use color coding for different categories
   - Include trend arrows (↑↓) for changes
   - Add sparkline mini-charts where applicable

5. **From Grocery App (Color_UI.jpeg)**
   - Colorful pill-shaped category filters
   - Promotional banner cards with gradients
   - Price/savings prominently displayed
   - Rating stars inline with items
   - "Add to cart" (+) buttons on cards

## Future Enhancements
1. **Predictive Analytics**
   - Predict when items will run out
   - Suggest optimal shopping times
   - Recipe recommendations based on patterns

2. **Social Features**
   - Compare stats with friends
   - Community averages
   - Achievement sharing
   - Follow other users' cooking journeys

3. **Export Capabilities**
   - Monthly reports
   - CSV export
   - PDF summaries

4. **Smart Insights**
   - AI-powered recommendations
   - Waste reduction tips
   - Budget optimization suggestions

5. **Gamification Elements**
   - Points system (like "468 points earned")
   - Badges for milestones
   - Leaderboards
   - Challenges and goals