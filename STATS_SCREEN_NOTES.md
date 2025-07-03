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

## Update: 2025-07-03 - New Stats Screen Analytics Implementation

### New Metrics & Calculations from stats_screenv2.ipynb

#### 1. Enhanced Pantry Analytics
- **Expired Items Tracking** - REAL DATA
  - Query counts items where `expiration_date < CURRENT_DATE()`
  - Provides clear feedback when no items are expired
  - Example output: "🥳 Zero expired items. Your pantry deserves a standing ovation!"

- **Category Distribution with Personality** - REAL DATA
  - Groups items by category and calculates proportions
  - Adds personality-based comments based on percentage:
    - >40%: "Basically your whole pantry"
    - 25-40%: "Dominating the shelf space!"
    - 10-25%: "Respectably stocked"
    - <10%: "Just a sprinkle"
  - Example output: "🧪 Uncategorized: 68.2% — Basically your whole pantry"

- **Top Products** - REAL DATA (Last 30 Days)
  - Shows most frequently added items with emoji ranking
  - Uses fun emoji ranking (🥇, 🥈, 🥉, 🔥, 💥)
  - Example: "🥇 Red Apple — 60 times"

#### 2. New Sustainability Metrics
- **Food Waste Prevention** - CALCULATED
  - Formula: `unexpired_items * 0.3` (0.3kg average weight per item)
  - Shows estimated food saved from expiration in kg

- **CO₂ Emissions Savings** - CALCULATED
  - Formula: `kg_saved * 2.5` (2.5kg CO₂ per kg of food)
  - Provides environmental impact metric

#### 3. Improved Expiry Tracking
- **Expiring Soon** - REAL DATA
  - Shows items expiring in next 7 days
  - Friendly message when nothing is expiring soon
  - Example: "🎉 Great news! Nothing is expiring in the next 7 days. Your pantry is under control. 👏😎"

### Implementation Notes
- Uses BigQuery for data processing
- All calculations happen server-side for performance
- Emoji-based UI elements for better engagement
- Clear, conversational language for user feedback

### Implementation Plan

#### 1. Stats Screen Integration
- **Location**: `ios-app/app/(tabs)/stats.tsx`
- **Components to Update**:
  - Create new `PantryInsightsCard` component for top products
  - Add `SustainabilityStats` component for waste/CO₂ metrics
  - Update existing `StatsCard` to support emoji indicators
- **Data Fetching**:
  ```typescript
  // Example API call structure
  const fetchPantryAnalytics = async () => {
    const response = await fetch(`${Config.API_BASE_URL}/analytics/pantry`);
    return response.json(); // { expiredCount, categoryDistribution, topProducts }
  };
  ```

#### 2. Category Distribution Visualization
- **Library**: `react-native-svg` or `victory-native`
- **Implementation**:
  - Interactive pie/donut chart
  - Tappable segments showing category details
  - Animation on initial load
- **Data Format**:
  ```typescript
  interface CategoryData {
    category: string;
    count: number;
    percentage: number;
    color: string; // Predefined color palette
  }
  ```

#### 3. CO₂ Savings Visualization
- **Visual Elements**:
  - Animated counter for kg of CO₂ saved
  - Equivalent metrics (e.g., "Like planting X trees")
  - Progress circle showing monthly goal
- **Implementation**:
  ```typescript
  // Example calculation
  const calculateCO2Savings = (unexpiredItems: number) => {
    const KG_PER_ITEM = 0.3;
    const CO2_PER_KG = 2.5;
    return (unexpiredItems * KG_PER_ITEM * CO2_PER_KG).toFixed(1);
  };
  ```

#### 4. Trend Analysis
- **Time Frames**: Week/Month/Year toggles
- **Data Points**:
  - Items saved from expiration
  - CO₂ savings over time
  - Category distribution trends
- **Implementation**:
  - Use `react-native-chart-kit` for line/bar charts
  - Cache historical data locally
  - Add pull-to-refresh for latest data

#### 5. Performance Considerations
- **Caching**:
  - Cache API responses for 1 hour
  - Use React Query for state management
  - Implement skeleton loaders
- **Batch Updates**:
  - Update stats in background
  - Debounce rapid filter changes
  - Virtualize long lists

#### 6. Testing Plan
1. **Unit Tests**:
   - Calculation functions
   - Data transformation logic
   - Edge cases (empty pantry, all expired, etc.)

2. **Integration Tests**:
   - API response handling
   - Component interactions
   - State updates

3. **Performance Testing**:
   - Large pantry datasets
   - Slow network conditions
   - Memory usage with multiple charts

#### 7. Accessibility
- Add proper labels for screen readers
- Ensure sufficient color contrast
- Support dynamic text sizing
- Add haptic feedback for interactions
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