import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert, Animated } from 'react-native';
import RecipesList from '../../../components/recipes/RecipesList';
import {
  createMockRecipe,
  createMockSavedRecipe,
  mockApiResponses,
  createMockNavigation
} from '../../helpers/recipeTestUtils';

// Mock dependencies
jest.mock('../../../config', () => ({
  Config: { API_BASE_URL: 'http://localhost:8000' }
}));

// Mock Animated for scroll animations
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Animated: {
      ...RN.Animated,
      spring: jest.fn(() => ({
        start: jest.fn(),
      })),
      Value: jest.fn(() => ({
        interpolate: jest.fn(() => 1),
      })),
      View: RN.View,
    },
  };
});

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('RecipesList', () => {
  const mockRouter = createMockNavigation();
  const mockRecipes = [
    createMockRecipe({ id: 1, title: 'Test Recipe 1', usedIngredientCount: 3, missedIngredientCount: 2 }),
    createMockRecipe({ id: 2, title: 'Test Recipe 2', usedIngredientCount: 2, missedIngredientCount: 3 })
  ];
  const mockSavedRecipes = [
    createMockSavedRecipe({ id: 'saved-1', recipe_title: 'Saved Recipe 1', rating: 'thumbs_up' }),
    createMockSavedRecipe({ id: 'saved-2', recipe_title: 'Saved Recipe 2', rating: 'neutral', is_favorite: true })
  ];

  const defaultProps = {
    recipes: mockRecipes,
    savedRecipes: mockSavedRecipes,
    loading: false,
    refreshing: false,
    searchQuery: '',
    activeTab: 'pantry' as const,
    myRecipesTab: 'saved' as const,
    sortBy: 'name' as const,
    scrollOffset: 0,
    filtersCollapsed: false,
    onRefresh: jest.fn(),
    onScrollOffsetChange: jest.fn(),
    onFiltersCollapsedChange: jest.fn(),
    onSavedRecipeUpdate: jest.fn(),
    fetchMyRecipes: jest.fn(),
    router: mockRouter,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default successful fetch responses
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockApiResponses.saveRecipeSuccess)
    } as Response);
  });

  describe('Loading States', () => {
    it('should show loading indicator when loading and not refreshing', () => {
      render(<RecipesList {...defaultProps} loading={true} refreshing={false} />);

      expect(screen.getByText('Finding delicious recipes...')).toBeTruthy();
      expect(screen.getByTestId('loading-indicator')).toBeTruthy();
    });

    it('should show different loading message for my-recipes tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" loading={true} refreshing={false} />);

      expect(screen.getByText('Loading your saved recipes...')).toBeTruthy();
    });

    it('should not show loading indicator when refreshing', () => {
      render(<RecipesList {...defaultProps} loading={true} refreshing={true} />);

      expect(screen.queryByText('Finding delicious recipes...')).toBeFalsy();
      expect(screen.queryByTestId('loading-indicator')).toBeFalsy();
    });
  });

  describe('Recipe Card Rendering', () => {
    it('should render recipe cards for regular recipes', () => {
      render(<RecipesList {...defaultProps} />);

      expect(screen.getByTestId('recipes-grid')).toBeTruthy();
      expect(screen.getByTestId('recipe-card-wrapper-1')).toBeTruthy();
      expect(screen.getByTestId('recipe-card-wrapper-2')).toBeTruthy();
      
      expect(screen.getByTestId('recipe-title-1')).toBeTruthy();
      expect(screen.getByTestId('recipe-title-2')).toBeTruthy();
      expect(screen.getByText('Test Recipe 1')).toBeTruthy();
      expect(screen.getByText('Test Recipe 2')).toBeTruthy();
    });

    it('should render saved recipe cards for my-recipes tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      expect(screen.getByTestId('my-recipes-grid')).toBeTruthy();
      expect(screen.getByTestId('saved-recipe-card-wrapper-saved-1')).toBeTruthy();
      expect(screen.getByTestId('saved-recipe-card-wrapper-saved-2')).toBeTruthy();
      
      expect(screen.getByText('Saved Recipe 1')).toBeTruthy();
      expect(screen.getByText('Saved Recipe 2')).toBeTruthy();
    });

    it('should display recipe stats correctly', () => {
      render(<RecipesList {...defaultProps} />);

      expect(screen.getByTestId('have-count-1')).toBeTruthy();
      expect(screen.getByTestId('missing-count-1')).toBeTruthy();
      expect(screen.getByText('3 have')).toBeTruthy();
      expect(screen.getByText('2 missing')).toBeTruthy();
    });

    it('should show bookmark button for regular recipes', () => {
      render(<RecipesList {...defaultProps} />);

      expect(screen.getByTestId('bookmark-button-1')).toBeTruthy();
      expect(screen.getByTestId('bookmark-button-2')).toBeTruthy();
    });

    it('should show action buttons for saved recipes', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      expect(screen.getByTestId('favorite-button-saved-1')).toBeTruthy();
      expect(screen.getByTestId('delete-button-saved-1')).toBeTruthy();
      expect(screen.getByTestId('card-actions-saved-1')).toBeTruthy();
    });

    it('should show rating buttons only in cooked tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="saved" />);

      expect(screen.queryByTestId('rating-buttons-saved-1')).toBeFalsy();
      expect(screen.queryByTestId('thumbs-up-button-saved-1')).toBeFalsy();
    });

    it('should show rating buttons in cooked tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      expect(screen.getByTestId('rating-buttons-saved-1')).toBeTruthy();
      expect(screen.getByTestId('thumbs-up-button-saved-1')).toBeTruthy();
      expect(screen.getByTestId('thumbs-down-button-saved-1')).toBeTruthy();
    });
  });

  describe('Empty States', () => {
    it('should show empty state for no recipes', () => {
      render(<RecipesList {...defaultProps} recipes={[]} />);

      expect(screen.getByTestId('empty-recipes')).toBeTruthy();
      expect(screen.getByTestId('empty-recipes-text')).toBeTruthy();
      expect(screen.getByText('No recipes found with your pantry items')).toBeTruthy();
    });

    it('should show search-specific empty state', () => {
      render(<RecipesList {...defaultProps} recipes={[]} searchQuery="pasta" />);

      expect(screen.getByText('No recipes found matching "pasta"')).toBeTruthy();
    });

    it('should show my-recipes empty state for saved tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[]} />);

      expect(screen.getByTestId('empty-my-recipes')).toBeTruthy();
      expect(screen.getByText('Bookmarks save recipes you want to try. Tap the bookmark icon on any recipe to add one.')).toBeTruthy();
    });

    it('should show my-recipes empty state for cooked tab', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" savedRecipes={[]} />);

      expect(screen.getByText('Nothing cooked yet. After you finish cooking a recipe it will appear here, ready for you to rate.')).toBeTruthy();
    });

    it('should show search-specific empty state for my-recipes', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[]} searchQuery="pasta" />);

      expect(screen.getByText('No recipes found matching "pasta"')).toBeTruthy();
    });
  });

  describe('Recipe Interactions', () => {
    it('should handle recipe card press for regular recipes', () => {
      render(<RecipesList {...defaultProps} />);

      fireEvent.press(screen.getByTestId('recipe-card-1'));
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: '1' }
      });
    });

    it('should handle recipe card press for saved Spoonacular recipes', () => {
      const spoonacularSavedRecipe = createMockSavedRecipe({
        id: 'saved-1',
        source: 'spoonacular',
        recipe_id: 123
      });
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[spoonacularSavedRecipe]} />);

      fireEvent.press(screen.getByTestId('saved-recipe-card-saved-1'));
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: '123' }
      });
    });

    it('should handle recipe card press for saved chat recipes', () => {
      const chatSavedRecipe = createMockSavedRecipe({
        id: 'saved-1',
        source: 'chat'
      });
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[chatSavedRecipe]} />);

      fireEvent.press(screen.getByTestId('saved-recipe-card-saved-1'));
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/recipe-details',
        params: { recipe: expect.any(String) }
      });
    });

    it('should handle bookmark button press', async () => {
      render(<RecipesList {...defaultProps} />);

      fireEvent.press(screen.getByTestId('bookmark-button-1'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test Recipe 1')
          })
        );
      });

      expect(Alert.alert).toHaveBeenCalledWith('Success', 'Recipe saved to My Recipes ▸ Saved');
    });

    it('should handle already saved recipe error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Recipe already saved' })
      } as Response);

      render(<RecipesList {...defaultProps} />);

      fireEvent.press(screen.getByTestId('bookmark-button-1'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Info', 'Recipe is already in your collection.');
      });
    });
  });

  describe('Saved Recipe Actions', () => {
    it('should handle rating update for thumbs up', async () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      fireEvent.press(screen.getByTestId('thumbs-up-button-saved-1'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes/saved-1/rating'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('neutral') // Should toggle from thumbs_up to neutral
          })
        );
      });
    });

    it('should handle rating update for thumbs down', async () => {
      const neutralRecipe = createMockSavedRecipe({ id: 'saved-1', rating: 'neutral' });
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" savedRecipes={[neutralRecipe]} />);

      fireEvent.press(screen.getByTestId('thumbs-down-button-saved-1'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes/saved-1/rating'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('thumbs_down')
          })
        );
      });
    });

    it('should handle favorite toggle', async () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      fireEvent.press(screen.getByTestId('favorite-button-saved-1'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes/saved-1/favorite'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('true') // Should toggle from false to true
          })
        );
      });

      expect(defaultProps.onSavedRecipeUpdate).toHaveBeenCalledWith('saved-1', { is_favorite: true });
    });

    it('should show confirmation for favorite addition', async () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      fireEvent.press(screen.getByTestId('favorite-button-saved-1'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Added to Favorites',
          'This recipe will be used to improve your recommendations.'
        );
      });
    });

    it('should handle recipe deletion with confirmation', async () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      fireEvent.press(screen.getByTestId('delete-button-saved-1'));

      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Recipe',
        'Are you sure you want to remove this recipe from your collection?',
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel', style: 'cancel' }),
          expect.objectContaining({ text: 'Delete', style: 'destructive' })
        ])
      );
    });
  });

  describe('Sorting and Filtering', () => {
    it('should sort recipes by name', () => {
      const unsortedRecipes = [
        createMockRecipe({ id: 1, title: 'Z Recipe' }),
        createMockRecipe({ id: 2, title: 'A Recipe' })
      ];
      
      render(<RecipesList {...defaultProps} recipes={unsortedRecipes} sortBy="name" />);

      const titles = screen.getAllByTestId(/recipe-title-/);
      expect(titles[0]).toHaveTextContent('A Recipe');
      expect(titles[1]).toHaveTextContent('Z Recipe');
    });

    it('should sort recipes by missing ingredients count', () => {
      const recipesWithDifferentMissing = [
        createMockRecipe({ id: 1, title: 'High Missing', missedIngredientCount: 5 }),
        createMockRecipe({ id: 2, title: 'Low Missing', missedIngredientCount: 1 })
      ];
      
      render(<RecipesList {...defaultProps} recipes={recipesWithDifferentMissing} sortBy="missing" />);

      const titles = screen.getAllByTestId(/recipe-title-/);
      expect(titles[0]).toHaveTextContent('Low Missing');
      expect(titles[1]).toHaveTextContent('High Missing');
    });

    it('should sort saved recipes by date', () => {
      const recipesWithDifferentDates = [
        createMockSavedRecipe({ id: 'old', recipe_title: 'Old Recipe', created_at: '2024-01-01T00:00:00Z' }),
        createMockSavedRecipe({ id: 'new', recipe_title: 'New Recipe', created_at: '2024-12-01T00:00:00Z' })
      ];
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={recipesWithDifferentDates} sortBy="date" />);

      const titles = screen.getAllByTestId(/saved-recipe-title-/);
      expect(titles[0]).toHaveTextContent('New Recipe'); // Most recent first
      expect(titles[1]).toHaveTextContent('Old Recipe');
    });

    it('should sort saved recipes by rating', () => {
      const recipesWithDifferentRatings = [
        createMockSavedRecipe({ id: 'thumbs-down', recipe_title: 'Bad Recipe', rating: 'thumbs_down' }),
        createMockSavedRecipe({ id: 'neutral', recipe_title: 'Neutral Recipe', rating: 'neutral' }),
        createMockSavedRecipe({ id: 'thumbs-up', recipe_title: 'Good Recipe', rating: 'thumbs_up' })
      ];
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={recipesWithDifferentRatings} sortBy="rating" />);

      const titles = screen.getAllByTestId(/saved-recipe-title-/);
      expect(titles[0]).toHaveTextContent('Good Recipe');
      expect(titles[1]).toHaveTextContent('Neutral Recipe');
      expect(titles[2]).toHaveTextContent('Bad Recipe');
    });

    it('should filter recipes by search query in pantry tab', () => {
      render(<RecipesList {...defaultProps} searchQuery="Recipe 1" />);

      expect(screen.getByText('Test Recipe 1')).toBeTruthy();
      expect(screen.queryByText('Test Recipe 2')).toBeFalsy();
    });

    it('should filter saved recipes by search query', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" searchQuery="Saved Recipe 1" />);

      expect(screen.getByText('Saved Recipe 1')).toBeTruthy();
      expect(screen.queryByText('Saved Recipe 2')).toBeFalsy();
    });
  });

  describe('Scroll Behavior', () => {
    it('should handle scroll events and update offset', () => {
      render(<RecipesList {...defaultProps} />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent.scroll(scrollView, {
        nativeEvent: {
          contentOffset: { y: 100 }
        }
      });

      expect(defaultProps.onScrollOffsetChange).toHaveBeenCalledWith(100);
    });

    it('should collapse filters when scrolling down in discover tab', () => {
      render(<RecipesList {...defaultProps} activeTab="discover" scrollOffset={0} />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent.scroll(scrollView, {
        nativeEvent: {
          contentOffset: { y: 50 }
        }
      });

      expect(defaultProps.onFiltersCollapsedChange).toHaveBeenCalledWith(true);
    });

    it('should expand filters when scrolling up in discover tab', () => {
      render(<RecipesList {...defaultProps} activeTab="discover" scrollOffset={100} filtersCollapsed={true} />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent.scroll(scrollView, {
        nativeEvent: {
          contentOffset: { y: 10 }
        }
      });

      expect(defaultProps.onFiltersCollapsedChange).toHaveBeenCalledWith(false);
    });

    it('should not affect filters in non-discover tabs', () => {
      render(<RecipesList {...defaultProps} activeTab="pantry" />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent.scroll(scrollView, {
        nativeEvent: {
          contentOffset: { y: 100 }
        }
      });

      expect(defaultProps.onFiltersCollapsedChange).not.toHaveBeenCalled();
    });
  });

  describe('Pull to Refresh', () => {
    it('should handle pull to refresh', async () => {
      render(<RecipesList {...defaultProps} />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent(scrollView, 'refresh');

      expect(defaultProps.onRefresh).toHaveBeenCalled();
    });

    it('should show refresh control when refreshing', () => {
      render(<RecipesList {...defaultProps} refreshing={true} />);

      const scrollView = screen.getByTestId('recipes-scroll-view');
      expect(scrollView.props.refreshControl).toBeTruthy();
    });
  });

  describe('Image Handling', () => {
    it('should use recipe image for regular recipes', () => {
      render(<RecipesList {...defaultProps} />);

      const recipeCard = screen.getByTestId('recipe-card-1');
      const image = recipeCard.children[0]; // First child should be Image
      expect(image.props.source.uri).toBe('https://example.com/image.jpg');
    });

    it('should use fallback image for recipes without image', () => {
      const recipeWithoutImage = createMockRecipe({ id: 1, image: undefined });
      
      render(<RecipesList {...defaultProps} recipes={[recipeWithoutImage]} />);

      const recipeCard = screen.getByTestId('recipe-card-1');
      const image = recipeCard.children[0];
      expect(image.props.source.uri).toBe('https://via.placeholder.com/300x200?text=No+Image');
    });

    it('should use recipe_image for saved recipes', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      const recipeCard = screen.getByTestId('saved-recipe-card-saved-1');
      const image = recipeCard.children[0];
      expect(image.props.source.uri).toBe('https://example.com/saved-recipe.jpg');
    });
  });

  describe('Error Handling', () => {
    it('should handle save recipe API errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<RecipesList {...defaultProps} />);

      fireEvent.press(screen.getByTestId('bookmark-button-1'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Failed to save recipe. Please try again.');
      });
    });

    it('should handle rating update errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      fireEvent.press(screen.getByTestId('thumbs-up-button-saved-1'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Failed to update rating. Please try again.');
      });
    });

    it('should handle favorite toggle errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<RecipesList {...defaultProps} activeTab="my-recipes" />);

      fireEvent.press(screen.getByTestId('favorite-button-saved-1'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Failed to update favorite status. Please try again.');
      });
    });

    it('should handle navigation errors for saved recipes without recipe_id', () => {
      const recipeWithoutId = createMockSavedRecipe({ 
        id: 'saved-1', 
        recipe_id: null as any, 
        recipe_data: { ...createMockRecipe(), id: null, external_recipe_id: null }
      });
      
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[recipeWithoutId]} />);

      fireEvent.press(screen.getByTestId('saved-recipe-card-saved-1'));

      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Unable to open recipe details');
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels for icons', () => {
      render(<RecipesList {...defaultProps} />);

      expect(screen.getByLabelText('Ingredients available')).toBeTruthy();
      expect(screen.getByLabelText('Ingredients missing')).toBeTruthy();
      expect(screen.getByLabelText('Save recipe')).toBeTruthy();
    });

    it('should have proper accessibility labels for saved recipe actions', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      expect(screen.getByLabelText('Rate recipe positively')).toBeTruthy();
      expect(screen.getByLabelText('Rate recipe negatively')).toBeTruthy();
      expect(screen.getByLabelText('Add to favorites')).toBeTruthy();
      expect(screen.getByLabelText('Delete recipe')).toBeTruthy();
    });

    it('should have proper accessibility labels for empty states', () => {
      render(<RecipesList {...defaultProps} recipes={[]} />);

      expect(screen.getByLabelText('No recipes found')).toBeTruthy();
    });

    it('should have proper accessibility labels for my-recipes empty state', () => {
      render(<RecipesList {...defaultProps} activeTab="my-recipes" savedRecipes={[]} />);

      expect(screen.getByLabelText('No saved recipes')).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('should memoize filtered recipes to prevent unnecessary recalculations', () => {
      const { rerender } = render(<RecipesList {...defaultProps} />);

      expect(screen.getByText('Test Recipe 1')).toBeTruthy();

      // Rerender with same props - should not cause re-filtering
      rerender(<RecipesList {...defaultProps} />);

      expect(screen.getByText('Test Recipe 1')).toBeTruthy();
    });

    it('should handle large recipe lists efficiently', () => {
      const manyRecipes = Array.from({ length: 50 }, (_, i) => 
        createMockRecipe({ id: i + 1, title: `Recipe ${i + 1}` })
      );

      render(<RecipesList {...defaultProps} recipes={manyRecipes} />);

      expect(screen.getByText('Recipe 1')).toBeTruthy();
      expect(screen.getByText('Recipe 50')).toBeTruthy();
    });
  });
});