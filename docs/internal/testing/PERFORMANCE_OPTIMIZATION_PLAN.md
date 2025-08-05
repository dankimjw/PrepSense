# Performance Optimization Plan - PrepSense Tab Navigation

## Performance Issues Identified

### 1. Multiple Simultaneous API Calls
- **Stats Screen**: Makes up to 3 API calls on each navigation
  - `/stats/comprehensive` 
  - `/cooking-history/trends`
  - `/user-recipes`
- **Recipes Screen**: Makes 2-3 API calls
  - `/recipes/search/from-pantry`
  - `/user-recipes`  
- **Home Screen**: Makes 1-2 API calls
  - `/pantry/user/111/items`

### 2. Heavy Component Rendering
- Complex animations in `_layout.tsx` with fade/slide transitions
- Stats screen has extensive data processing that blocks UI thread
- Recipe screen renders large filter lists and processes ingredient matching

### 3. Network Bottlenecks
- TabDataProvider preload takes 1.7 seconds
- Screens make fresh API calls despite cached data being available
- No proper loading states during transitions

## Optimization Strategy

### Phase 1: Fix TabDataProvider Usage
**Files to Modify:**
- `ios-app/app/(tabs)/stats.tsx`
- `ios-app/app/(tabs)/recipes.tsx` 
- `ios-app/app/(tabs)/index.tsx`
- `ios-app/context/TabDataProvider.tsx`

**Changes:**
1. Make screens properly use preloaded data
2. Only fetch fresh data when cache is stale
3. Implement proper loading states

### Phase 2: Optimize Animations
**Files to Modify:**
- `ios-app/app/(tabs)/_layout.tsx`
- `ios-app/components/navigation/TabScreenTransition.tsx`

**Changes:**
1. Use native driver for animations
2. Reduce animation complexity
3. Implement skeleton loading states

### Phase 3: Network Optimization
**Files to Modify:**
- `ios-app/context/TabDataProvider.tsx`
- Backend API endpoints

**Changes:**
1. Implement background refresh
2. Reduce API response sizes
3. Better caching strategies

## Expected Performance Improvements
- Tab transitions: < 300ms (currently 1-2 seconds)
- API calls: Reduced by 70% through proper caching
- UI responsiveness: Eliminate blocking operations

## Testing Plan
1. Measure baseline performance with React DevTools
2. Implement changes incrementally
3. Test on both simulator and physical device
4. Verify smooth navigation between all tabs

## Branch Management
- **Main worktree** (`animations`): Continue animation work
- **Performance worktree** (`performance-optimization`): This optimization work
- **Testzone worktree** (`testzone`): Test performance improvements

---
*Created: 2025-07-28*
*Branch: performance-optimization*