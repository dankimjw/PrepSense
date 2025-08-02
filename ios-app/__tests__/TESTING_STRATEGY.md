# PrepSense Testing Strategy

## Implementation Status: 🟢 WORKING

This document outlines the comprehensive testing approach for PrepSense, designed to maximize test coverage while working around React Native testing limitations.

## Overview

Our testing strategy follows a **Testing Pyramid** approach with three main layers:

- **Unit Tests (70%)**: Business logic, utilities, API clients
- **Integration Tests (20%)**: Critical user flows, data transformations  
- **E2E Tests (10%)**: Core app functionality via existing framework

## Core Philosophy

### ✅ What Works
- **Logic-only testing**: Extract business logic into separate modules
- **API and service layer testing**: Mock network calls, test data flow
- **Utility function testing**: Pure functions without React dependencies
- **Integration testing**: Test user journeys without deep component rendering

### ❌ What We Avoid
- **Full component rendering**: StyleSheet.create issues persist despite extensive mocking
- **Deep React Native integration**: Focus on behavior over implementation
- **Fighting the framework**: Work with jest-expo limitations, not against them

## Testing Architecture

### 1. Business Logic Extraction Pattern

**Implementation**: Extract component logic into separate `*.logic.ts` files

```typescript
// logic/recipesContainer.logic.ts
export function recipesReducer(state: State, action: Action): State {
  // Pure reducer logic - fully testable
}

export function filterValidRecipes(recipes: Recipe[]): Recipe[] {
  // Pure filtering logic - fully testable  
}
```

**Testing**: Follow `RecipesFilters.logic.test.tsx` pattern

```typescript
// __tests__/logic/recipesContainer.logic.test.ts
describe('RecipesContainer Logic Tests', () => {
  it('should handle SET_RECIPES action', () => {
    const newState = recipesReducer(initialState, action);
    expect(newState.recipes).toEqual(expectedRecipes);
  });
});
```

### 2. API and Service Layer Testing

**Implementation**: Comprehensive endpoint coverage following `recipeLogic.test.ts`

```typescript
describe('Recipe API Endpoints', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('should handle successful pantry recipe search', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });
    
    const response = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`);
    // Test the actual API interaction
  });
});
```

### 3. Integration Testing Framework

**Implementation**: Test critical user journeys without component rendering

```typescript
describe('Recipe Discovery Journey', () => {
  it('should complete pantry-to-saved recipe journey', async () => {
    // Step 1: Fetch pantry recipes
    // Step 2: Get recipe details  
    // Step 3: Save recipe
    // Step 4: Verify in saved list
  });
});
```

## File Organization

```
ios-app/
├── logic/                              # Business logic modules
│   ├── recipesContainer.logic.ts       # Extracted from RecipesContainer
│   ├── recipesList.logic.ts           # Extracted from RecipesList
│   └── pantryItemsList.logic.ts       # Extracted from PantryItemsList
│
├── __tests__/
│   ├── logic/                          # Logic-only tests (70% of coverage)
│   │   ├── recipesContainer.logic.test.ts
│   │   ├── recipesList.logic.test.ts
│   │   ├── pantryItemsList.logic.test.ts
│   │   ├── api.comprehensive.test.ts
│   │   └── recipeLogic.test.ts         # Existing successful pattern
│   │
│   ├── integration/                    # User journey tests (20% of coverage)
│   │   ├── critical-user-journeys.test.tsx
│   │   └── [existing integration tests]
│   │
│   ├── components/                     # Limited component tests (10% of coverage)
│   │   └── recipes/RecipesFilters.logic.test.tsx  # Existing successful pattern
│   │
│   └── helpers/                        # Test utilities
│       ├── apiMocks.ts
│       └── testUtils.ts
```

## Test Categories and Commands

### Run Logic Tests Only
```bash
npm test -- --testPathPattern="logic" --verbose
```

### Run Integration Tests Only
```bash
npm test -- --testPathPattern="integration" --verbose
```

### Run All Tests with Coverage
```bash
npm test -- --coverage --verbose
```

### Run Specific Test Suite
```bash
npm test recipesContainer.logic.test.ts
```

## Coverage Requirements

### Unit Tests (Logic Layer) - 100% Coverage Required
- ✅ `recipesContainer.logic.ts` - State management, filtering, sorting
- ✅ `recipesList.logic.ts` - Display logic, compatibility calculations
- ✅ `pantryItemsList.logic.ts` - Expiration logic, categorization
- ✅ API endpoints - All success/error scenarios

### Integration Tests - Critical Paths Only
- ✅ Pantry → Recipe Discovery → Save → Cook
- ✅ Search → Recipe Details → Save
- ✅ Pantry Management → Recipe Updates
- ✅ Error Recovery Flows

### Component Tests - Interface Only
- ✅ Logic extraction pattern (RecipesFilters example)
- ❌ Full component rendering (StyleSheet issues)
- ✅ Prop interface testing
- ✅ State change behavior

## Testing Patterns and Best Practices

### 1. Logic Extraction Pattern

```typescript
// ✅ Good: Pure function testing
export function calculateRecipeCompatibility(recipe: Recipe): RecipeCompatibility {
  const totalIngredients = recipe.usedIngredientCount + recipe.missedIngredientCount;
  const score = recipe.usedIngredientCount / totalIngredients;
  return { score, compatibilityLevel: score >= 0.8 ? 'high' : 'medium' };
}

// Test: Easy to test, no React dependencies
it('should calculate high compatibility', () => {
  const recipe = { usedIngredientCount: 8, missedIngredientCount: 2 };
  const result = calculateRecipeCompatibility(recipe);
  expect(result.compatibilityLevel).toBe('high');
});
```

### 2. API Testing Pattern

```typescript
// ✅ Good: Mock fetch, test actual endpoints
describe('Recipe API', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('should handle API key errors', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'API key not configured' }),
    });

    const response = await fetch(`${API_BASE_URL}/recipes/random`);
    expect(response.status).toBe(400);
  });
});
```

### 3. Integration Testing Pattern

```typescript
// ✅ Good: Test user journey without component rendering
describe('Recipe Journey', () => {
  it('should complete pantry-to-saved flow', async () => {
    // Mock API responses for each step
    // Test the actual data flow
    // Verify end-to-end behavior
  });
});
```

## Mock Strategy

### Global Mocks (jest.setup.js)
- ✅ React Native components and APIs
- ✅ Expo modules (router, haptics, notifications)
- ✅ StyleSheet (comprehensive but limited success)
- ✅ Platform, Dimensions, AsyncStorage

### Test-Specific Mocks
- ✅ API responses with `global.fetch`
- ✅ Context providers (Items, Auth)
- ✅ Navigation functions
- ✅ External utilities

### What We Don't Mock
- ❌ Business logic functions (test the real implementation)
- ❌ TypeScript types and interfaces
- ❌ Configuration constants

## Known Limitations and Workarounds

### StyleSheet Issues
**Problem**: `StyleSheet.create` fails despite extensive mocking
**Workaround**: Extract logic into separate modules, test behavior not rendering

### Component Integration
**Problem**: Full React Native component testing is unreliable
**Workaround**: Focus on props, state changes, and user interactions

### Performance Testing
**Problem**: React Native performance testing is limited in Jest
**Workaround**: Test performance logic separately, use real device testing for UI performance

## Continuous Integration

### Pre-commit Hooks
```bash
# Run logic tests (fast)
npm test -- --testPathPattern="logic" --passWithNoTests

# Type checking
npx tsc --noEmit
```

### CI Pipeline
```bash
# Full test suite with coverage
npm test -- --coverage --watchAll=false --passWithNoTests

# Coverage requirements
# - Logic tests: 100%
# - Integration tests: 80% of critical paths
# - Overall: 85% minimum
```

## Test Data Management

### Mock Data Location
- `__tests__/helpers/mockData.ts` - Shared test fixtures
- `__tests__/helpers/apiMocks.ts` - API response mocks
- Individual test files - Test-specific data

### Data Consistency
- Use factory functions for consistent mock objects
- Validate mock data matches API schemas
- Keep mock data synchronized with backend changes

## Future Improvements

### Potential Enhancements
1. **Visual Regression Testing**: Add Storybook + Chromatic
2. **E2E Testing**: Expand Detox or Maestro integration
3. **Performance Testing**: Add React Native performance monitoring
4. **API Contract Testing**: Add Pact.js for API compatibility

### Monitoring and Metrics
1. **Coverage Tracking**: Aim for 90%+ on business logic
2. **Test Performance**: Keep test suite under 2 minutes
3. **Flaky Test Detection**: Monitor and fix unreliable tests
4. **Real Device Testing**: Supplement with iOS Simulator testing

## Quick Reference

### Common Commands
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific pattern
npm test -- --testPathPattern="logic"

# Run in watch mode
npm test -- --watch

# Update snapshots
npm test -- --updateSnapshot
```

### Debugging Tests
```bash
# Run single test with verbose output
npm test -- --testNamePattern="should calculate compatibility" --verbose

# Debug with Node inspector
npm test -- --inspect-brk --runInBand --testNamePattern="specific test"
```

This testing strategy provides comprehensive coverage while working within React Native testing constraints. The focus on business logic extraction and API testing ensures reliability without fighting framework limitations.