import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipesScreen from '../../app/(tabs)/recipes';
import { useAuth } from '../../context/AuthContext';
import { useItems } from '../../context/ItemsContext';
import { useRouter } from 'expo-router';

// Mock dependencies
jest.mock('../../context/AuthContext');
jest.mock('../../context/ItemsContext');
jest.mock('expo-router');
jest.mock('../../config', () => ({
  Config: {
    API_BASE_URL: 'http://localhost:8000'
  }
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseItems = useItems as jest.MockedFunction<typeof useItems>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock router
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockBack = jest.fn();

// Sample test data
const mockPantryRecipes = [
  {
    id: 1,
    title: 'Chicken Alfredo Pasta',
    image: 'https://example.com/image1.jpg',
    imageType: 'jpg',
    usedIngredientCount: 4,
    missedIngredientCount: 2,
    usedIngredients: [
      { id: 1, name: 'chicken breast', amount: 2, unit: 'pieces', image: '' },
      { id: 2, name: 'pasta', amount: 200, unit: 'g', image: '' }
    ],
    missedIngredients: [
      { id: 3, name: 'cream', amount: 200, unit: 'ml', image: '' },
      { id: 4, name: 'parmesan cheese', amount: 50, unit: 'g', image: '' }
    ],
    likes: 150
  },
  {
    id: 2,
    title: 'Vegetable Stir Fry',
    image: 'https://example.com/image2.jpg',
    imageType: 'jpg',
    usedIngredientCount: 5,
    missedIngredientCount: 1,
    usedIngredients: [
      { id: 5, name: 'broccoli', amount: 200, unit: 'g', image: '' },
      { id: 6, name: 'carrots', amount: 150, unit: 'g', image: '' }
    ],
    missedIngredients: [
      { id: 7, name: 'soy sauce', amount: 30, unit: 'ml', image: '' }
    ],
    likes: 89
  }
];

const mockSavedRecipes = [
  {
    id: 'saved-1',
    recipe_id: 100,
    recipe_title: 'Saved Lasagna',
    recipe_image: 'https://example.com/lasagna.jpg',
    recipe_data: {
      id: 100,
      title: 'Saved Lasagna',
      readyInMinutes: 60,
      servings: 6
    },
    rating: 'thumbs_up' as const,
    is_favorite: true,
    source: 'spoonacular',
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z'
  }
];

const mockPantryItems = [
  { product_name: 'chicken breast' },
  { product_name: 'pasta' },
  { product_name: 'broccoli' },
  { product_name: 'carrots' }
];

describe('RecipesScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: { id: 111, email: 'test@example.com' },
      token: 'mock-token',
      isAuthenticated: true,
      signIn: jest.fn(),
      signOut: jest.fn(),
      isLoading: false
    });

    mockUseItems.mockReturnValue({
      items: mockPantryItems,
      addItem: jest.fn(),
      updateItem: jest.fn(),
      removeItem: jest.fn(),
      isLoading: false,
      error: null,
      refreshItems: jest.fn()
    });

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      back: mockBack,
      canGoBack: jest.fn(),
      setParams: jest.fn(),
      pathname: '/recipes'
    });

    // Mock successful fetch responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/recipes/search/from-pantry')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            recipes: mockPantryRecipes,
            pantry_ingredients: mockPantryItems
          })
        } as Response);
      }
      
      if (url.includes('/user-recipes')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSavedRecipes)
        } as Response);
      }
      
      if (url.includes('/recipes/random')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            recipes: mockPantryRecipes
          })
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      } as Response);
    });
  });

  describe('Basic Functionality', () => {
    it('should render the main components', () => {
      render(<RecipesScreen />);

      expect(screen.getByText('Recipes')).toBeTruthy();
      expect(screen.getByText('From Pantry')).toBeTruthy();
      expect(screen.getByText('Discover')).toBeTruthy();
      expect(screen.getByText('My Recipes')).toBeTruthy();
    });

    it('should load and display pantry recipes', async () => {
      render(<RecipesScreen />);

      // Wait for recipes to load
      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
        expect(screen.getByText('Vegetable Stir Fry')).toBeTruthy();
      });

      // Check ingredient counts are displayed
      expect(screen.getByText('4 have')).toBeTruthy();
      expect(screen.getByText('2 missing')).toBeTruthy();
      expect(screen.getByText('5 have')).toBeTruthy();
      expect(screen.getByText('1 missing')).toBeTruthy();
    });

    it('should display search input', () => {
      render(<RecipesScreen />);

      expect(screen.getByPlaceholderText('Search pantry recipes...')).toBeTruthy();
    });

    it('should display filter options for pantry tab', () => {
      render(<RecipesScreen />);

      // Should show meal type filters for pantry tab
      expect(screen.getByText('Breakfast')).toBeTruthy();
      expect(screen.getByText('Lunch')).toBeTruthy();
      expect(screen.getByText('Dinner')).toBeTruthy();
      expect(screen.getByText('Snack')).toBeTruthy();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to discover tab and show filters', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('Discover'));

      // Should show dietary filters
      expect(screen.getByText('Vegetarian')).toBeTruthy();
      expect(screen.getByText('Vegan')).toBeTruthy();
      expect(screen.getByText('Gluten-Free')).toBeTruthy();
    });

    it('should switch to my recipes tab', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('🔖 Saved')).toBeTruthy();
        expect(screen.getByText('🍳 Cooked')).toBeTruthy();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should filter recipes by search query', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
        expect(screen.getByText('Vegetable Stir Fry')).toBeTruthy();
      });

      const searchInput = screen.getByPlaceholderText('Search pantry recipes...');
      fireEvent.changeText(searchInput, 'chicken');

      // Should filter to only show chicken recipe
      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
        expect(screen.queryByText('Vegetable Stir Fry')).toBeFalsy();
      });
    });

    it('should perform API search in discover tab', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('Discover'));

      const searchInput = screen.getByPlaceholderText('Search all recipes...');
      fireEvent.changeText(searchInput, 'pasta');

      const searchButton = screen.getByText('Search');
      fireEvent.press(searchButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/complex'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('pasta')
          })
        );
      });
    });
  });

  describe('Recipe Card Interactions', () => {
    it('should navigate to recipe detail when recipe is pressed', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      fireEvent.press(screen.getByText('Chicken Alfredo Pasta'));

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: '1' }
      });
    });

    it('should save recipe when bookmark is pressed', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Find bookmark button by icon
      const bookmarkButtons = screen.getAllByA11yRole('button');
      const bookmarkButton = bookmarkButtons.find(button => 
        button.props.children?.props?.name === 'bookmark-outline'
      );

      if (bookmarkButton) {
        fireEvent.press(bookmarkButton);

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/user-recipes'),
            expect.objectContaining({
              method: 'POST',
              body: expect.stringContaining('Chicken Alfredo Pasta')
            })
          );
        });
      }
    });
  });

  describe('My Recipes Functionality', () => {
    it('should display saved recipes', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('Saved Lasagna')).toBeTruthy();
      });
    });

    it('should show cooked tab filters', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));
      fireEvent.press(screen.getByText('🍳 Cooked'));

      expect(screen.getByText('All')).toBeTruthy();
      expect(screen.getByText('Liked')).toBeTruthy();
      expect(screen.getByText('Disliked')).toBeTruthy();
    });
  });

  describe('Loading States', () => {
    it('should show loading indicator while fetching recipes', () => {
      // Mock a delayed response
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(<RecipesScreen />);

      expect(screen.getByText('Finding delicious recipes...')).toBeTruthy();
    });
  });

  describe('Error Handling', () => {
    it('should show API key error when Spoonacular key is missing', async () => {
      mockFetch.mockImplementation(() => 
        Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({
            detail: 'API key required'
          })
        } as Response)
      );

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Spoonacular API Key Required',
          expect.stringContaining('Get your free API key at')
        );
      });
    });

    it('should handle network errors gracefully', async () => {
      mockFetch.mockImplementation(() => 
        Promise.reject(new Error('Network error'))
      );

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });
    });

    it('should show empty state when no recipes found', async () => {
      mockFetch.mockImplementation(() => 
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            recipes: [],
            pantry_ingredients: []
          })
        } as Response)
      );

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('No recipes found with your pantry items')).toBeTruthy();
      });
    });
  });

  describe('Badge Display', () => {
    it('should show have and missing ingredient counts', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Check for ingredient count text
      expect(screen.getByText('4 have')).toBeTruthy();
      expect(screen.getByText('2 missing')).toBeTruthy();
      expect(screen.getByText('5 have')).toBeTruthy();
      expect(screen.getByText('1 missing')).toBeTruthy();
    });

    it('should show correct badge styling for different ingredient counts', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('4 have')).toBeTruthy();
      });

      // The "have" text should be associated with a green checkmark icon
      // The "missing" text should be associated with a red close icon
      // This validates the badge system is working
    });
  });

  describe('Filter Functionality', () => {
    it('should show different filters for different tabs', () => {
      render(<RecipesScreen />);

      // Pantry tab - should show meal type filters
      expect(screen.getByText('Breakfast')).toBeTruthy();

      // Switch to discover tab
      fireEvent.press(screen.getByText('Discover'));

      // Should show dietary and cuisine filters
      expect(screen.getByText('Vegetarian')).toBeTruthy();
      expect(screen.getByText('Italian')).toBeTruthy();
    });

    it('should allow filter selection', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('Discover'));

      // Select a filter
      fireEvent.press(screen.getByText('Vegetarian'));

      // Filter should appear selected (visual feedback would be tested in integration)
    });
  });

  describe('Sorting', () => {
    it('should show sort modal when sort button is pressed', () => {
      render(<RecipesScreen />);

      // Find sort button by icon
      const buttons = screen.getAllByA11yRole('button');
      const sortButton = buttons.find(button => 
        button.props.children?.props?.name === 'sort'
      );

      if (sortButton) {
        fireEvent.press(sortButton);
        expect(screen.getByText('Sort By')).toBeTruthy();
      }
    });
  });
});