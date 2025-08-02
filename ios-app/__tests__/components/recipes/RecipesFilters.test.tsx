import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { Animated } from 'react-native';
import RecipesFilters from '../../../components/recipes/RecipesFilters';

// Mock Animated to avoid issues in tests
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Animated: {
      ...RN.Animated,
      Value: jest.fn(() => ({
        interpolate: jest.fn(() => 1),
      })),
      timing: jest.fn(() => ({
        start: jest.fn(),
      })),
      spring: jest.fn(() => ({
        start: jest.fn(),
      })),
      View: RN.View,
    },
  };
});

describe('RecipesFilters', () => {
  const defaultProps = {
    activeTab: 'pantry' as const,
    selectedFilters: [],
    myRecipesFilter: 'all' as const,
    myRecipesTab: 'saved' as const,
    filtersCollapsed: false,
    onFiltersChange: jest.fn(),
    onMyRecipesFilterChange: jest.fn(),
    onMyRecipesTabChange: jest.fn(),
    onFiltersCollapsedChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Pantry Tab Filters', () => {
    it('should render meal type filters for pantry tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="pantry" />);

      expect(screen.getByTestId('pantry-filter-breakfast')).toBeTruthy();
      expect(screen.getByTestId('pantry-filter-lunch')).toBeTruthy();
      expect(screen.getByTestId('pantry-filter-dinner')).toBeTruthy();
      expect(screen.getByTestId('pantry-filter-snack')).toBeTruthy();

      expect(screen.getByText('Breakfast')).toBeTruthy();
      expect(screen.getByText('Lunch')).toBeTruthy();
      expect(screen.getByText('Dinner')).toBeTruthy();
      expect(screen.getByText('Snack')).toBeTruthy();
    });

    it('should handle filter selection in pantry tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="pantry" />);

      fireEvent.press(screen.getByTestId('pantry-filter-breakfast'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['breakfast']);

      fireEvent.press(screen.getByTestId('pantry-filter-dinner'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['dinner']);
    });

    it('should show active state for selected filters in pantry tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="pantry" selectedFilters={['breakfast']} />);

      const breakfastFilter = screen.getByTestId('pantry-filter-breakfast');
      expect(breakfastFilter.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#E6F7F0',
            borderWidth: 1,
            borderColor: '#297A56'
          })
        ])
      );
    });

    it('should handle filter deselection in pantry tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="pantry" selectedFilters={['breakfast', 'lunch']} />);

      fireEvent.press(screen.getByTestId('pantry-filter-breakfast'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['lunch']);
    });
  });

  describe('Discover Tab Filters', () => {
    it('should render collapsed filter bar for discover tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={true} />);

      expect(screen.getByText('0 filters active')).toBeFalsy(); // No active filters
    });

    it('should show active filter count when filters are selected', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian', 'italian']} filtersCollapsed={true} />);

      expect(screen.getByText('2 filters active')).toBeTruthy();
    });

    it('should render all dietary filters when expanded', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Dietary filters
      expect(screen.getByTestId('dietary-filter-vegetarian')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-vegan')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-gluten-free')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-dairy-free')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-low-carb')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-keto')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-paleo')).toBeTruthy();
      expect(screen.getByTestId('dietary-filter-mediterranean')).toBeTruthy();

      expect(screen.getByText('Vegetarian')).toBeTruthy();
      expect(screen.getByText('Vegan')).toBeTruthy();
      expect(screen.getByText('Gluten-Free')).toBeTruthy();
    });

    it('should render all cuisine filters when expanded', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Cuisine filters
      expect(screen.getByTestId('cuisine-filter-italian')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-mexican')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-asian')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-american')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-indian')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-french')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-japanese')).toBeTruthy();
      expect(screen.getByTestId('cuisine-filter-thai')).toBeTruthy();

      expect(screen.getByText('Italian')).toBeTruthy();
      expect(screen.getByText('Mexican')).toBeTruthy();
      expect(screen.getByText('Asian')).toBeTruthy();
    });

    it('should render all meal type filters when expanded', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Meal type filters
      expect(screen.getByTestId('meal-type-filter-breakfast')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-lunch')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-dinner')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-snack')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-dessert')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-appetizer')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-soup')).toBeTruthy();
      expect(screen.getByTestId('meal-type-filter-salad')).toBeTruthy();

      expect(screen.getByText('Dessert')).toBeTruthy();
      expect(screen.getByText('Appetizer')).toBeTruthy();
      expect(screen.getByText('Soup')).toBeTruthy();
    });

    it('should handle dietary filter selection', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegetarian']);

      fireEvent.press(screen.getByTestId('dietary-filter-vegan'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegan']);
    });

    it('should handle cuisine filter selection', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('cuisine-filter-italian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['italian']);

      fireEvent.press(screen.getByTestId('cuisine-filter-mexican'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['mexican']);
    });

    it('should handle meal type filter selection', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('meal-type-filter-breakfast'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['breakfast']);

      fireEvent.press(screen.getByTestId('meal-type-filter-dessert'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['dessert']);
    });

    it('should handle multiple filter selections', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian']} filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('cuisine-filter-italian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegetarian', 'italian']);
    });

    it('should handle filter deselection', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian', 'italian']} filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['italian']);
    });

    it('should show active state for selected filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian']} filtersCollapsed={false} />);

      const vegetarianFilter = screen.getByTestId('dietary-filter-vegetarian');
      expect(vegetarianFilter.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#E6F7F0',
            borderWidth: 1,
            borderColor: '#297A56'
          })
        ])
      );
    });

    it('should handle collapse bar press to expand filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={true} />);

      const collapseBar = screen.getByRole('button'); // TouchableOpacity acts as button
      fireEvent.press(collapseBar);

      expect(defaultProps.onFiltersCollapsedChange).toHaveBeenCalledWith(false);
    });

    it('should trigger animation when expanding filters', () => {
      const mockTiming = Animated.timing as jest.Mock;
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={true} />);

      const collapseBar = screen.getByRole('button');
      fireEvent.press(collapseBar);

      expect(mockTiming).toHaveBeenCalled();
    });
  });

  describe('My Recipes Tab Filters', () => {
    it('should render saved/cooked tabs for my-recipes', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" />);

      expect(screen.getByTestId('my-recipes-tabs')).toBeTruthy();
      expect(screen.getByTestId('saved-tab')).toBeTruthy();
      expect(screen.getByTestId('cooked-tab')).toBeTruthy();

      expect(screen.getByText('🔖 Saved')).toBeTruthy();
      expect(screen.getByText('🍳 Cooked')).toBeTruthy();
    });

    it('should show active state for selected my-recipes tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="saved" />);

      const savedTab = screen.getByTestId('saved-tab');
      expect(savedTab.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#297A56'
          })
        ])
      );
    });

    it('should handle my-recipes tab change to saved', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      fireEvent.press(screen.getByTestId('saved-tab'));
      expect(defaultProps.onMyRecipesTabChange).toHaveBeenCalledWith('saved');
    });

    it('should handle my-recipes tab change to cooked', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="saved" />);

      fireEvent.press(screen.getByTestId('cooked-tab'));
      expect(defaultProps.onMyRecipesTabChange).toHaveBeenCalledWith('cooked');
    });

    it('should show rating filters only in cooked tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="saved" />);

      expect(screen.queryByTestId('filter-all')).toBeFalsy();
      expect(screen.queryByTestId('filter-thumbs-up')).toBeFalsy();
      expect(screen.queryByTestId('filter-thumbs-down')).toBeFalsy();
    });

    it('should render rating filters in cooked tab', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      expect(screen.getByTestId('filter-all')).toBeTruthy();
      expect(screen.getByTestId('filter-thumbs-up')).toBeTruthy();
      expect(screen.getByTestId('filter-thumbs-down')).toBeTruthy();

      expect(screen.getByText('All')).toBeTruthy();
      expect(screen.getByText('Liked')).toBeTruthy();
      expect(screen.getByText('Disliked')).toBeTruthy();
    });

    it('should handle rating filter selection', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      fireEvent.press(screen.getByTestId('filter-thumbs-up'));
      expect(defaultProps.onMyRecipesFilterChange).toHaveBeenCalledWith('thumbs_up');

      fireEvent.press(screen.getByTestId('filter-thumbs-down'));
      expect(defaultProps.onMyRecipesFilterChange).toHaveBeenCalledWith('thumbs_down');

      fireEvent.press(screen.getByTestId('filter-all'));
      expect(defaultProps.onMyRecipesFilterChange).toHaveBeenCalledWith('all');
    });

    it('should show active state for selected rating filter', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" myRecipesFilter="thumbs_up" />);

      const thumbsUpFilter = screen.getByTestId('filter-thumbs-up');
      expect(thumbsUpFilter.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#E6F7F0',
            borderWidth: 1,
            borderColor: '#297A56'
          })
        ])
      );
    });
  });

  describe('Filter State Management', () => {
    it('should handle adding filters to empty array', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={[]} filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegetarian']);
    });

    it('should handle removing filters from array', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian', 'vegan', 'italian']} filtersCollapsed={false} />);

      fireEvent.press(screen.getByTestId('dietary-filter-vegan'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegetarian', 'italian']);
    });

    it('should handle toggling same filter multiple times', () => {
      const { rerender } = render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={[]} filtersCollapsed={false} />);

      // Add filter
      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith(['vegetarian']);

      // Rerender with new state
      rerender(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={['vegetarian']} filtersCollapsed={false} />);

      // Remove filter
      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      expect(defaultProps.onFiltersChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Accessibility and Icons', () => {
    it('should display correct icons for dietary filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Check that filter buttons contain emoji icons
      const vegetarianButton = screen.getByTestId('dietary-filter-vegetarian');
      expect(vegetarianButton).toContainElement(screen.getByText('🥗'));

      const veganButton = screen.getByTestId('dietary-filter-vegan');
      expect(veganButton).toContainElement(screen.getByText('🌱'));
    });

    it('should display correct icons for cuisine filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      const italianButton = screen.getByTestId('cuisine-filter-italian');
      expect(italianButton).toContainElement(screen.getByText('🍝'));

      const mexicanButton = screen.getByTestId('cuisine-filter-mexican');
      expect(mexicanButton).toContainElement(screen.getByText('🌮'));
    });

    it('should display correct icons for meal type filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      const breakfastButton = screen.getByTestId('meal-type-filter-breakfast');
      expect(breakfastButton).toContainElement(screen.getByText('🍳'));

      const dessertButton = screen.getByTestId('meal-type-filter-dessert');
      expect(dessertButton).toContainElement(screen.getByText('🍰'));
    });

    it('should display correct icons for rating filters', () => {
      render(<RecipesFilters {...defaultProps} activeTab="my-recipes" myRecipesTab="cooked" />);

      const allFilter = screen.getByTestId('filter-all');
      expect(allFilter).toContainElement(screen.getByText('📋'));

      const thumbsUpFilter = screen.getByTestId('filter-thumbs-up');
      expect(thumbsUpFilter).toContainElement(screen.getByText('👍'));

      const thumbsDownFilter = screen.getByTestId('filter-thumbs-down');
      expect(thumbsDownFilter).toContainElement(screen.getByText('👎'));
    });
  });

  describe('Edge Cases', () => {
    it('should return null for unknown active tab', () => {
      const { container } = render(<RecipesFilters {...defaultProps} activeTab={'unknown' as any} />);
      expect(container.children).toHaveLength(0);
    });

    it('should handle empty selected filters array', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" selectedFilters={[]} filtersCollapsed={false} />);

      // No filters should be in active state
      const vegetarianFilter = screen.getByTestId('dietary-filter-vegetarian');
      expect(vegetarianFilter.props.style).not.toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#E6F7F0'
          })
        ])
      );
    });

    it('should handle filter collapse when already collapsed', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={true} />);

      const collapseBar = screen.getByRole('button');
      fireEvent.press(collapseBar);

      // Should still try to expand
      expect(defaultProps.onFiltersCollapsedChange).toHaveBeenCalledWith(false);
    });

    it('should maintain scroll behavior in filter lists', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Check that ScrollViews are horizontal and don't show scroll indicators
      const scrollViews = screen.getAllByTestId(new RegExp('.*'));
      scrollViews.forEach(scrollView => {
        if (scrollView.type === 'RCTScrollView') {
          expect(scrollView.props.horizontal).toBe(true);
          expect(scrollView.props.showsHorizontalScrollIndicator).toBe(false);
        }
      });
    });
  });

  describe('Animation Integration', () => {
    it('should initialize animated value correctly', () => {
      const mockValue = Animated.Value as jest.Mock;
      render(<RecipesFilters {...defaultProps} activeTab="discover" />);

      expect(mockValue).toHaveBeenCalledWith(1);
    });

    it('should use animated values for height interpolation', () => {
      render(<RecipesFilters {...defaultProps} activeTab="discover" filtersCollapsed={false} />);

      // Component should render without throwing errors related to animation
      expect(screen.getByTestId('dietary-filter-vegetarian')).toBeTruthy();
    });
  });
});