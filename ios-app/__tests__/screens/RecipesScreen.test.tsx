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

  describe('Data Population', () => {
    it('should load and display pantry recipes correctly', async () => {
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

    it('should display saved recipes when My Recipes tab is selected', async () => {
      render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('Saved Lasagna')).toBeTruthy();
      });

      // Verify API call was made
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/user-recipes'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should show have and missing badges correctly', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Find the recipe cards and check for badge icons
      const checkIcons = screen.getAllByTestId('check-circle-icon');
      const missedIcons = screen.getAllByTestId('close-circle-icon');
      
      expect(checkIcons.length).toBeGreaterThan(0);
      expect(missedIcons.length).toBeGreaterThan(0);
    });

    it('should handle empty recipe list', async () => {
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

    it('should display loading state while fetching recipes', () => {
      // Mock a delayed response
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(<RecipesScreen />);

      expect(screen.getByText('Finding delicious recipes...')).toBeTruthy();
      expect(screen.getByTestId('loading-indicator')).toBeTruthy();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch between tabs correctly', async () => {
      render(<RecipesScreen />);

      // Initially on pantry tab
      expect(screen.getByText('From Pantry')).toBeTruthy();

      // Switch to discover tab
      fireEvent.press(screen.getByText('Discover'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/random'),
          expect.any(Object)
        );
      });

      // Switch to my recipes tab
      fireEvent.press(screen.getByText('My Recipes'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.any(Object)
        );
      });
    });

    it('should show active tab styling', () => {
      render(<RecipesScreen />);

      const fromPantryTab = screen.getByText('From Pantry');
      const discoverTab = screen.getByText('Discover');

      // From Pantry should be active by default
      expect(fromPantryTab.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ color: '#297A56' })
        ])
      );

      fireEvent.press(discoverTab);

      // Discover should now be active
      expect(discoverTab.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ color: '#297A56' })
        ])
      );
    });
  });

  describe('Search Functionality', () => {
    it('should filter pantry recipes by search query', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
        expect(screen.getByText('Vegetable Stir Fry')).toBeTruthy();
      });

      // Search for "chicken"
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

      // Switch to discover tab
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

    it('should clear search when clear button is pressed', async () => {
      render(<RecipesScreen />);

      const searchInput = screen.getByPlaceholderText('Search pantry recipes...');
      fireEvent.changeText(searchInput, 'test query');

      // Clear button should appear
      const clearButton = screen.getByTestId('clear-search-button');
      fireEvent.press(clearButton);

      expect(searchInput.props.value).toBe('');
    });
  });

  describe('Filter Functionality', () => {
    it('should show filter options in discover tab', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('Discover'));

      // Check for dietary filters
      expect(screen.getByText('Vegetarian')).toBeTruthy();
      expect(screen.getByText('Vegan')).toBeTruthy();
      expect(screen.getByText('Gluten-Free')).toBeTruthy();

      // Check for cuisine filters
      expect(screen.getByText('Italian')).toBeTruthy();
      expect(screen.getByText('Mexican')).toBeTruthy();
      expect(screen.getByText('Asian')).toBeTruthy();
    });

    it('should toggle filter selection', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('Discover'));

      const vegetarianFilter = screen.getByText('Vegetarian');
      fireEvent.press(vegetarianFilter);

      // Filter should be selected (active styling)
      expect(vegetarianFilter.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ color: '#297A56' })
        ])
      );
    });

    it('should show my recipes filters in cooked tab', () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));
      fireEvent.press(screen.getByText('🍳 Cooked'));

      // Should show rating filters
      expect(screen.getByText('All')).toBeTruthy();
      expect(screen.getByText('Liked')).toBeTruthy();
      expect(screen.getByText('Disliked')).toBeTruthy();
    });
  });

  describe('Button Functionality', () => {
    it('should navigate to recipe detail when recipe card is pressed', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      const recipeCard = screen.getByText('Chicken Alfredo Pasta');
      fireEvent.press(recipeCard);

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: '1' }
      });
    });

    it('should save recipe when bookmark button is pressed', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      const bookmarkButton = screen.getByTestId('bookmark-button-1');
      fireEvent.press(bookmarkButton);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/user-recipes'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Chicken Alfredo Pasta')
        })
      );
    });

    it('should open sort modal when sort button is pressed', () => {
      render(<RecipesScreen />);

      const sortButton = screen.getByTestId('sort-button');
      fireEvent.press(sortButton);

      expect(screen.getByText('Sort By')).toBeTruthy();
      expect(screen.getByText('Name (A-Z)')).toBeTruthy();
      expect(screen.getByText('Recently Added')).toBeTruthy();
      expect(screen.getByText('Highest Rated')).toBeTruthy();
      expect(screen.getByText('Fewest Missing')).toBeTruthy();
    });

    it('should navigate to chat when chef hat button is pressed', () => {
      render(<RecipesScreen />);

      const chatButton = screen.getByTestId('chat-button');
      fireEvent.press(chatButton);

      expect(mockPush).toHaveBeenCalledWith('/chat');
    });

    it('should refresh recipes when pull to refresh is triggered', async () => {
      render(<RecipesScreen />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      
      // Simulate pull to refresh
      fireEvent(scrollView, 'refresh');

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/from-pantry'),
          expect.any(Object)
        );
      });
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

    it('should show empty state when no recipes match search', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Search for something that won't match
      const searchInput = screen.getByPlaceholderText('Search pantry recipes...');
      fireEvent.changeText(searchInput, 'nonexistent recipe');

      await waitFor(() => {
        expect(screen.getByText('No recipes found matching "nonexistent recipe"')).toBeTruthy();
      });
    });
  });

  describe('Recipe Management', () => {
    it('should update recipe rating in My Recipes', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));
      fireEvent.press(screen.getByText('🍳 Cooked'));

      await waitFor(() => {
        expect(screen.getByText('Saved Lasagna')).toBeTruthy();
      });

      const thumbsUpButton = screen.getByTestId('thumbs-up-button-saved-1');
      fireEvent.press(thumbsUpButton);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/user-recipes/saved-1/rating'),
        expect.objectContaining({
          method: 'PUT',
          body: expect.stringContaining('thumbs_up')
        })
      );
    });

    it('should toggle favorite status', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('Saved Lasagna')).toBeTruthy();
      });

      const favoriteButton = screen.getByTestId('favorite-button-saved-1');
      fireEvent.press(favoriteButton);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/user-recipes/saved-1/favorite'),
        expect.objectContaining({
          method: 'PUT'
        })
      );
    });

    it('should delete recipe when delete button is pressed', async () => {
      render(<RecipesScreen />);

      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('Saved Lasagna')).toBeTruthy();
      });

      const deleteButton = screen.getByTestId('delete-button-saved-1');
      fireEvent.press(deleteButton);

      // Should show confirmation dialog
      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Recipe',
        'Are you sure you want to remove this recipe from your collection?',
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel' }),
          expect.objectContaining({ text: 'Delete' })
        ])
      );
    });
  });

  describe('Sorting', () => {
    it('should sort recipes by name', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Open sort modal
      fireEvent.press(screen.getByTestId('sort-button'));
      fireEvent.press(screen.getByText('Name (A-Z)'));

      // Recipes should be sorted alphabetically
      const recipeTexts = screen.getAllByTestId('recipe-title');
      expect(recipeTexts[0].props.children).toBe('Chicken Alfredo Pasta');
      expect(recipeTexts[1].props.children).toBe('Vegetable Stir Fry');
    });

    it('should sort recipes by missing ingredient count', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      });

      // Open sort modal
      fireEvent.press(screen.getByTestId('sort-button'));
      fireEvent.press(screen.getByText('Fewest Missing'));

      // Recipes should be sorted by missing count (ascending)
      const recipeTexts = screen.getAllByTestId('recipe-title');
      expect(recipeTexts[0].props.children).toBe('Vegetable Stir Fry'); // 1 missing
      expect(recipeTexts[1].props.children).toBe('Chicken Alfredo Pasta'); // 2 missing
    });
  });
});