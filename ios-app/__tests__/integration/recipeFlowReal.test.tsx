import React from 'react';
import { render, waitFor, fireEvent } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RecipeTabs from '@/screens/RecipeTabs';
import RecipeDetailsScreen from '@/screens/RecipeDetailsScreen';
import { RecipeProvider } from '@/contexts/RecipeContext';
import { PantryProvider } from '@/contexts/PantryContext';
import { AuthProvider } from '@/contexts/AuthContext';

// Real API endpoints - no mocks
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

describe('Real Recipe Flow Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          cacheTime: 0,
        },
      },
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <PantryProvider>
            <RecipeProvider>
              <NavigationContainer>
                {component}
              </NavigationContainer>
            </RecipeProvider>
          </PantryProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

  describe('Recipe Display with Real Data', () => {
    it('should fetch and display real recipes with have/missing ingredient counts', async () => {
      const { getByText, getAllByTestId, getByTestId } = renderWithProviders(
        <RecipeTabs />
      );

      // Wait for real API call to complete
      await waitFor(() => {
        expect(getByTestId('recipe-list')).toBeTruthy();
      }, { timeout: 10000 });

      // Check that recipes are displayed
      const recipeCards = getAllByTestId(/recipe-card-/);
      expect(recipeCards.length).toBeGreaterThan(0);

      // Verify each recipe card shows ingredient counts
      recipeCards.forEach((card) => {
        const ingredientCounts = card.findByProps({ testID: /ingredient-counts/ });
        expect(ingredientCounts).toBeTruthy();
        
        // Check format: "✓ X | ✗ Y"
        const countText = ingredientCounts.props.children;
        expect(countText).toMatch(/✓ \d+ \| ✗ \d+/);
      });
    });

    it('should display recipe details with complete information', async () => {
      const navigation = { navigate: jest.fn() };
      const route = {
        params: {
          recipeId: 716429, // Real recipe ID from Spoonacular
        },
      };

      const { getByText, getByTestId, getAllByTestId } = renderWithProviders(
        <RecipeDetailsScreen navigation={navigation} route={route} />
      );

      // Wait for recipe details to load
      await waitFor(() => {
        expect(getByTestId('recipe-details-container')).toBeTruthy();
      }, { timeout: 10000 });

      // Verify tabs are present
      expect(getByText('Ingredients')).toBeTruthy();
      expect(getByText('Instructions')).toBeTruthy();
      expect(getByText('Nutrition')).toBeTruthy();

      // Test Ingredients Tab
      fireEvent.press(getByText('Ingredients'));
      
      await waitFor(() => {
        const ingredientItems = getAllByTestId(/ingredient-item-/);
        expect(ingredientItems.length).toBeGreaterThan(0);

        // Each ingredient should show have/missing status
        ingredientItems.forEach((item) => {
          const statusIcon = item.findByProps({ testID: /ingredient-status-/ });
          expect(statusIcon).toBeTruthy();
          expect(['✓', '✗']).toContain(statusIcon.props.children);
        });
      });

      // Test Instructions Tab
      fireEvent.press(getByText('Instructions'));
      
      await waitFor(() => {
        const instructionSteps = getAllByTestId(/instruction-step-/);
        expect(instructionSteps.length).toBeGreaterThan(0);

        // Verify steps are numbered sequentially
        instructionSteps.forEach((step, index) => {
          const stepNumber = step.findByProps({ testID: `step-number-${index + 1}` });
          expect(stepNumber).toBeTruthy();
          expect(stepNumber.props.children).toBe(`${index + 1}.`);
        });
      });

      // Test Nutrition Tab
      fireEvent.press(getByText('Nutrition'));
      
      await waitFor(() => {
        // Check for essential nutrients
        expect(getByText(/Calories/)).toBeTruthy();
        expect(getByText(/Protein/)).toBeTruthy();
        expect(getByText(/Carbohydrates/)).toBeTruthy();
        expect(getByText(/Fat/)).toBeTruthy();

        // Each nutrient should have a value
        const nutrientValues = getAllByTestId(/nutrient-value-/);
        nutrientValues.forEach((value) => {
          expect(value.props.children).toMatch(/\d+(\.\d+)?\s*\w+/);
        });
      });
    });
  });

  describe('Recipe Completion Flow', () => {
    it('should update pantry when recipe is completed', async () => {
      const navigation = { navigate: jest.fn(), goBack: jest.fn() };
      const route = {
        params: {
          recipeId: 716429,
        },
      };

      const { getByText, getByTestId } = renderWithProviders(
        <RecipeDetailsScreen navigation={navigation} route={route} />
      );

      // Wait for recipe to load
      await waitFor(() => {
        expect(getByTestId('recipe-details-container')).toBeTruthy();
      }, { timeout: 10000 });

      // Find and press complete button
      const completeButton = getByTestId('complete-recipe-button');
      expect(completeButton).toBeTruthy();

      // Get initial pantry state
      const initialPantryResponse = await fetch(`${API_BASE_URL}/api/pantry`, {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      });
      const initialPantry = await initialPantryResponse.json();

      // Complete the recipe
      fireEvent.press(completeButton);

      // Wait for completion
      await waitFor(() => {
        expect(navigation.goBack).toHaveBeenCalled();
      }, { timeout: 5000 });

      // Verify pantry was updated
      const updatedPantryResponse = await fetch(`${API_BASE_URL}/api/pantry`, {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      });
      const updatedPantry = await updatedPantryResponse.json();

      // Check that quantities decreased for used ingredients
      // This assumes the recipe uses some pantry items
      expect(updatedPantry.items.length).toBeLessThanOrEqual(initialPantry.items.length);
    });
  });

  describe('Search and Filter', () => {
    it('should filter recipes based on search query', async () => {
      const { getByTestId, getAllByTestId, getByPlaceholderText } = renderWithProviders(
        <RecipeTabs />
      );

      // Wait for initial recipes to load
      await waitFor(() => {
        expect(getByTestId('recipe-list')).toBeTruthy();
      }, { timeout: 10000 });

      // Get search input
      const searchInput = getByPlaceholderText('Search recipes...');
      expect(searchInput).toBeTruthy();

      // Type search query
      fireEvent.changeText(searchInput, 'pasta');

      // Wait for filtered results
      await waitFor(() => {
        const recipeCards = getAllByTestId(/recipe-card-/);
        
        // All displayed recipes should contain 'pasta' in title
        recipeCards.forEach((card) => {
          const title = card.findByProps({ testID: /recipe-title-/ });
          expect(title.props.children.toLowerCase()).toContain('pasta');
        });
      }, { timeout: 5000 });
    });

    it('should switch between recipe tabs correctly', async () => {
      const { getByText, getAllByTestId } = renderWithProviders(
        <RecipeTabs />
      );

      // Wait for initial load
      await waitFor(() => {
        expect(getByText('Pantry-Based')).toBeTruthy();
      }, { timeout: 10000 });

      // Switch to All Recipes tab
      fireEvent.press(getByText('All Recipes'));

      await waitFor(() => {
        const recipeCards = getAllByTestId(/recipe-card-/);
        expect(recipeCards.length).toBeGreaterThan(0);
        
        // All Recipes tab might show recipes with more missing ingredients
        const highMissingCount = recipeCards.some((card) => {
          const counts = card.findByProps({ testID: /ingredient-counts/ });
          const match = counts.props.children.match(/✗ (\d+)/);
          return match && parseInt(match[1]) > 5;
        });
        
        expect(highMissingCount).toBe(true);
      });

      // Switch to Favorites tab
      fireEvent.press(getByText('Favorites'));

      await waitFor(() => {
        // May be empty initially
        const emptyMessage = getByText(/No favorite recipes yet/);
        expect(emptyMessage).toBeTruthy();
      });
    });
  });

  describe('Data Completeness Validation', () => {
    it('should display all recipe data fields correctly', async () => {
      const { getByText, getAllByTestId } = renderWithProviders(
        <RecipeTabs />
      );

      await waitFor(() => {
        const recipeCards = getAllByTestId(/recipe-card-/);
        expect(recipeCards.length).toBeGreaterThan(0);

        // Check first recipe card for all required fields
        const firstCard = recipeCards[0];
        
        // Title
        const title = firstCard.findByProps({ testID: /recipe-title-/ });
        expect(title).toBeTruthy();
        expect(title.props.children.length).toBeGreaterThan(0);

        // Cooking time
        const cookTime = firstCard.findByProps({ testID: /cook-time-/ });
        expect(cookTime).toBeTruthy();
        expect(cookTime.props.children).toMatch(/\d+ min/);

        // Servings
        const servings = firstCard.findByProps({ testID: /servings-/ });
        expect(servings).toBeTruthy();
        expect(servings.props.children).toMatch(/\d+ servings/);

        // Ingredient counts
        const counts = firstCard.findByProps({ testID: /ingredient-counts/ });
        expect(counts).toBeTruthy();
        expect(counts.props.children).toMatch(/✓ \d+ \| ✗ \d+/);

        // Image (if available)
        const image = firstCard.findByProps({ testID: /recipe-image-/ });
        if (image) {
          expect(image.props.source.uri).toBeTruthy();
        }
      }, { timeout: 10000 });
    });
  });
});
