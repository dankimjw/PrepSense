import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { View, Text } from 'react-native';

// Mock the complex components for now
jest.mock('../../../components/recipes/RecipesTabs', () => 'RecipesTabs');
jest.mock('../../../components/recipes/RecipesFilters', () => 'RecipesFilters');
jest.mock('../../../components/recipes/RecipesList', () => 'RecipesList');

// Mock all contexts
jest.mock('../../../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 111 },
    token: 'test-token',
    isAuthenticated: true
  })
}));

jest.mock('../../../context/ItemsContext', () => ({
  useItems: () => ({
    items: [{ item_name: 'test item' }]
  })
}));

jest.mock('../../../context/TabDataProvider', () => ({
  useTabData: () => ({
    recipesData: null
  })
}));

jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn()
  })
}));

// Mock utils
jest.mock('../../../utils/ingredientMatcher', () => ({
  calculateIngredientAvailability: jest.fn(() => ({
    availableCount: 3,
    missingCount: 2
  })),
  validateIngredientCounts: jest.fn(() => true)
}));

jest.mock('../../../utils/contentValidation', () => ({
  isValidRecipe: jest.fn(() => true)
}));

import RecipesContainer from '../../../components/recipes/RecipesContainer';

describe('RecipesContainer Simple', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ recipes: [] })
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    const { container } = render(<RecipesContainer />);
    
    // Just check that it renders without throwing
    expect(container).toBeTruthy();
  });

  it('should call fetch on mount', () => {
    render(<RecipesContainer />);
    
    // Should call fetch for pantry recipes
    expect(global.fetch).toHaveBeenCalled();
  });
});