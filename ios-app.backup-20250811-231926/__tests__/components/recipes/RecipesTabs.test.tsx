import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import RecipesTabs from '../../../components/recipes/RecipesTabs';
import { createMockNavigation } from '../../helpers/recipeTestUtils';

describe('RecipesTabs', () => {
  const defaultProps = {
    activeTab: 'pantry' as const,
    searchQuery: '',
    searchFocused: false,
    showSortModal: false,
    sortBy: 'name' as const,
    onTabChange: jest.fn(),
    onSearchQueryChange: jest.fn(),
    onSearchFocusChange: jest.fn(),
    onSortModalToggle: jest.fn(),
    onSortChange: jest.fn(),
    onSearchSubmit: jest.fn(),
    router: createMockNavigation(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Header Section', () => {
    it('should render header title and action buttons', () => {
      render(<RecipesTabs {...defaultProps} />);

      expect(screen.getByTestId('header-title')).toBeTruthy();
      expect(screen.getByText('Recipes')).toBeTruthy();
      expect(screen.getByTestId('sort-button')).toBeTruthy();
      expect(screen.getByTestId('chat-button')).toBeTruthy();
    });

    it('should handle sort button press', () => {
      render(<RecipesTabs {...defaultProps} />);

      fireEvent.press(screen.getByTestId('sort-button'));
      expect(defaultProps.onSortModalToggle).toHaveBeenCalledWith(true);
    });

    it('should handle chat button press and navigate to chat', () => {
      render(<RecipesTabs {...defaultProps} />);

      fireEvent.press(screen.getByTestId('chat-button'));
      expect(defaultProps.router.push).toHaveBeenCalledWith('/chat');
    });

    it('should have proper accessibility labels', () => {
      render(<RecipesTabs {...defaultProps} />);

      const sortButton = screen.getByLabelText('Sort recipes');
      const chatButton = screen.getByLabelText('Open recipe chat');
      
      expect(sortButton).toBeTruthy();
      expect(chatButton).toBeTruthy();
    });
  });

  describe('Search Bar', () => {
    it('should render search bar with correct placeholder for pantry tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="pantry" />);

      expect(screen.getByTestId('search-container')).toBeTruthy();
      expect(screen.getByPlaceholderText('Search pantry recipes...')).toBeTruthy();
    });

    it('should render search bar with correct placeholder for discover tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="discover" />);

      expect(screen.getByPlaceholderText('Search all recipes...')).toBeTruthy();
    });

    it('should render search bar with correct placeholder for my-recipes tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="my-recipes" />);

      expect(screen.getByPlaceholderText('Search your recipes...')).toBeTruthy();
    });

    it('should handle search input changes', () => {
      render(<RecipesTabs {...defaultProps} />);

      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, 'pasta');

      expect(defaultProps.onSearchQueryChange).toHaveBeenCalledWith('pasta');
    });

    it('should handle search focus events', () => {
      render(<RecipesTabs {...defaultProps} />);

      const searchInput = screen.getByTestId('search-input');
      
      fireEvent(searchInput, 'focus');
      expect(defaultProps.onSearchFocusChange).toHaveBeenCalledWith(true);

      fireEvent(searchInput, 'blur');
      expect(defaultProps.onSearchFocusChange).toHaveBeenCalledWith(false);
    });

    it('should handle search submission', () => {
      render(<RecipesTabs {...defaultProps} />);

      const searchInput = screen.getByTestId('search-input');
      fireEvent(searchInput, 'submitEditing');

      expect(defaultProps.onSearchSubmit).toHaveBeenCalled();
    });

    it('should show focused style when search is focused', () => {
      render(<RecipesTabs {...defaultProps} searchFocused={true} />);

      const searchBar = screen.getByTestId('search-container').children[0];
      expect(searchBar.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            borderColor: '#297A56',
            backgroundColor: '#fff'
          })
        ])
      );
    });

    it('should show clear button when search query exists', () => {
      render(<RecipesTabs {...defaultProps} searchQuery="pasta" />);

      expect(screen.getByTestId('clear-search-button')).toBeTruthy();
    });

    it('should handle clear button press', () => {
      render(<RecipesTabs {...defaultProps} searchQuery="pasta" />);

      fireEvent.press(screen.getByTestId('clear-search-button'));
      expect(defaultProps.onSearchQueryChange).toHaveBeenCalledWith('');
    });

    it('should not show clear button when search query is empty', () => {
      render(<RecipesTabs {...defaultProps} searchQuery="" />);

      expect(screen.queryByTestId('clear-search-button')).toBeFalsy();
    });

    it('should show search submit button only in discover tab with query', () => {
      // Should not show in pantry tab
      render(<RecipesTabs {...defaultProps} activeTab="pantry" searchQuery="pasta" />);
      expect(screen.queryByTestId('search-submit-button')).toBeFalsy();

      // Should show in discover tab with query
      render(<RecipesTabs {...defaultProps} activeTab="discover" searchQuery="pasta" />);
      expect(screen.getByTestId('search-submit-button')).toBeTruthy();

      // Should not show in discover tab without query
      render(<RecipesTabs {...defaultProps} activeTab="discover" searchQuery="" />);
      expect(screen.queryByTestId('search-submit-button')).toBeFalsy();
    });

    it('should handle search submit button press', () => {
      render(<RecipesTabs {...defaultProps} activeTab="discover" searchQuery="pasta" />);

      fireEvent.press(screen.getByTestId('search-submit-button'));
      expect(defaultProps.onSearchSubmit).toHaveBeenCalled();
    });
  });

  describe('Tab Navigation', () => {
    it('should render all three tabs', () => {
      render(<RecipesTabs {...defaultProps} />);

      expect(screen.getByTestId('tab-container')).toBeTruthy();
      expect(screen.getByTestId('pantry-tab')).toBeTruthy();
      expect(screen.getByTestId('discover-tab')).toBeTruthy();
      expect(screen.getByTestId('my-recipes-tab')).toBeTruthy();
    });

    it('should show correct tab labels', () => {
      render(<RecipesTabs {...defaultProps} />);

      expect(screen.getByText('From Pantry')).toBeTruthy();
      expect(screen.getByText('Discover')).toBeTruthy();
      expect(screen.getByText('My Recipes')).toBeTruthy();
    });

    it('should highlight active tab correctly', () => {
      render(<RecipesTabs {...defaultProps} activeTab="pantry" />);

      const pantryTab = screen.getByTestId('pantry-tab');
      expect(pantryTab.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            borderBottomWidth: 2,
            borderBottomColor: '#297A56'
          })
        ])
      );

      const pantryTabText = screen.getByText('From Pantry');
      expect(pantryTabText.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            color: '#297A56',
            fontWeight: '600'
          })
        ])
      );
    });

    it('should handle tab change for pantry tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="discover" />);

      fireEvent.press(screen.getByTestId('pantry-tab'));
      expect(defaultProps.onTabChange).toHaveBeenCalledWith('pantry');
    });

    it('should handle tab change for discover tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="pantry" />);

      fireEvent.press(screen.getByTestId('discover-tab'));
      expect(defaultProps.onTabChange).toHaveBeenCalledWith('discover');
    });

    it('should handle tab change for my-recipes tab', () => {
      render(<RecipesTabs {...defaultProps} activeTab="pantry" />);

      fireEvent.press(screen.getByTestId('my-recipes-tab'));
      expect(defaultProps.onTabChange).toHaveBeenCalledWith('my-recipes');
    });

    it('should show inactive tab styling for non-active tabs', () => {
      render(<RecipesTabs {...defaultProps} activeTab="pantry" />);

      const discoverTab = screen.getByTestId('discover-tab');
      expect(discoverTab.props.style).not.toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            borderBottomWidth: 2,
            borderBottomColor: '#297A56'
          })
        ])
      );

      const discoverTabText = screen.getByText('Discover');
      expect(discoverTabText.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            color: '#666',
            fontWeight: '500'
          })
        ])
      );
    });
  });

  describe('Sort Modal', () => {
    it('should not show sort modal by default', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={false} />);

      expect(screen.getByTestId('sort-modal')).toHaveProp('visible', false);
    });

    it('should show sort modal when showSortModal is true', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      expect(screen.getByTestId('sort-modal')).toHaveProp('visible', true);
    });

    it('should render sort modal content correctly', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      expect(screen.getByTestId('sort-modal-overlay')).toBeTruthy();
      expect(screen.getByTestId('sort-modal-content')).toBeTruthy();
      expect(screen.getByTestId('sort-modal-title')).toBeTruthy();
      expect(screen.getByText('Sort By')).toBeTruthy();
    });

    it('should render all sort options', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      expect(screen.getByTestId('sort-option-name')).toBeTruthy();
      expect(screen.getByTestId('sort-option-date')).toBeTruthy();
      expect(screen.getByTestId('sort-option-rating')).toBeTruthy();
      expect(screen.getByTestId('sort-option-missing')).toBeTruthy();

      expect(screen.getByText('Name (A-Z)')).toBeTruthy();
      expect(screen.getByText('Recently Added')).toBeTruthy();
      expect(screen.getByText('Highest Rated')).toBeTruthy();
      expect(screen.getByText('Fewest Missing')).toBeTruthy();
    });

    it('should highlight active sort option', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} sortBy="name" />);

      const nameOption = screen.getByTestId('sort-option-name');
      expect(nameOption.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            backgroundColor: '#E6F7F0'
          })
        ])
      );

      // Should show checkmark for active option
      expect(screen.getByLabelText('Selected')).toBeTruthy();
    });

    it('should handle sort option selection', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} sortBy="name" />);

      fireEvent.press(screen.getByTestId('sort-option-rating'));
      
      expect(defaultProps.onSortChange).toHaveBeenCalledWith('rating');
      expect(defaultProps.onSortModalToggle).toHaveBeenCalledWith(false);
    });

    it('should close modal when overlay is pressed', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      fireEvent.press(screen.getByTestId('sort-modal-overlay'));
      expect(defaultProps.onSortModalToggle).toHaveBeenCalledWith(false);
    });

    it('should have proper accessibility labels for sort options', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      expect(screen.getByLabelText('Sort by Name (A-Z)')).toBeTruthy();
      expect(screen.getByLabelText('Sort by Recently Added')).toBeTruthy();
      expect(screen.getByLabelText('Sort by Highest Rated')).toBeTruthy();
      expect(screen.getByLabelText('Sort by Fewest Missing')).toBeTruthy();
    });

    it('should show correct icons for sort options', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} sortBy="rating" />);

      // Check that non-active options have default color
      const nameOption = screen.getByTestId('sort-option-name');
      const nameIcon = nameOption.children[0];
      expect(nameIcon.props.color).toBe('#666');

      // Check that active option has active color
      const ratingOption = screen.getByTestId('sort-option-rating');
      const ratingIcon = ratingOption.children[0];
      expect(ratingIcon.props.color).toBe('#297A56');
    });

    it('should handle modal request close', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      const modal = screen.getByTestId('sort-modal');
      fireEvent(modal, 'requestClose');
      
      expect(defaultProps.onSortModalToggle).toHaveBeenCalledWith(false);
    });
  });

  describe('Search Input Accessibility', () => {
    it('should have proper accessibility properties', () => {
      render(<RecipesTabs {...defaultProps} />);

      const searchIcon = screen.getByLabelText('Search icon');
      const clearButton = screen.queryByLabelText('Clear search');
      
      expect(searchIcon).toBeTruthy();
      // Clear button only shows when there's text
      expect(clearButton).toBeFalsy();
    });

    it('should show clear button accessibility label when query exists', () => {
      render(<RecipesTabs {...defaultProps} searchQuery="test" />);

      expect(screen.getByLabelText('Clear search')).toBeTruthy();
    });
  });

  describe('Component Integration', () => {
    it('should update search input value from props', () => {
      const { rerender } = render(<RecipesTabs {...defaultProps} searchQuery="" />);

      const searchInput = screen.getByTestId('search-input');
      expect(searchInput.props.value).toBe('');

      rerender(<RecipesTabs {...defaultProps} searchQuery="pasta" />);
      expect(searchInput.props.value).toBe('pasta');
    });

    it('should handle rapid tab switches', () => {
      render(<RecipesTabs {...defaultProps} />);

      fireEvent.press(screen.getByTestId('discover-tab'));
      fireEvent.press(screen.getByTestId('my-recipes-tab'));
      fireEvent.press(screen.getByTestId('pantry-tab'));

      expect(defaultProps.onTabChange).toHaveBeenCalledTimes(3);
      expect(defaultProps.onTabChange).toHaveBeenNthCalledWith(1, 'discover');
      expect(defaultProps.onTabChange).toHaveBeenNthCalledWith(2, 'my-recipes');
      expect(defaultProps.onTabChange).toHaveBeenNthCalledWith(3, 'pantry');
    });

    it('should handle multiple sort option selections', () => {
      render(<RecipesTabs {...defaultProps} showSortModal={true} />);

      fireEvent.press(screen.getByTestId('sort-option-date'));
      expect(defaultProps.onSortChange).toHaveBeenCalledWith('date');
      expect(defaultProps.onSortModalToggle).toHaveBeenCalledWith(false);
      
      // Reset mocks and test another selection
      jest.clearAllMocks();
      render(<RecipesTabs {...defaultProps} showSortModal={true} sortBy="date" />);
      
      fireEvent.press(screen.getByTestId('sort-option-missing'));
      expect(defaultProps.onSortChange).toHaveBeenCalledWith('missing');
    });
  });
});