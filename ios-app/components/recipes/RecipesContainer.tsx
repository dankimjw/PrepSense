import React, { useReducer, useCallback, useEffect } from 'react';
import { View, Alert, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Config } from '../../config';
import { useItems } from '../../context/ItemsContext';
import { useAuth } from '../../context/AuthContext';
import { useTabData } from '../../context/TabDataProvider';
import { useUserPreferences } from '../../context/UserPreferencesContext';
import { calculateIngredientAvailability, validateIngredientCounts } from '../../utils/ingredientMatcher';
import { isValidRecipe } from '../../utils/contentValidation';
import RecipesTabs from './RecipesTabs';
import RecipesFilters from './RecipesFilters';
import RecipesList from './RecipesList';

interface Recipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
  usedIngredientCount: number;
  missedIngredientCount: number;
  missedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  usedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  likes: number;
}

interface SavedRecipe {
  id: string;
  recipe_id: number;
  recipe_title: string;
  recipe_image: string;
  recipe_data: any;
  rating: 'thumbs_up' | 'thumbs_down' | 'neutral';
  is_favorite?: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

type SortOption = 'name' | 'date' | 'rating' | 'missing';
type ActiveTab = 'pantry' | 'discover' | 'my-recipes';
type MyRecipesFilter = 'all' | 'thumbs_up' | 'thumbs_down' | 'favorites';
type MyRecipesTab = 'saved' | 'cooked';

interface State {
  recipes: Recipe[];
  savedRecipes: SavedRecipe[];
  loading: boolean;
  refreshing: boolean;
  searchQuery: string;
  activeTab: ActiveTab;
  selectedFilters: string[];
  myRecipesFilter: MyRecipesFilter;
  myRecipesTab: MyRecipesTab;
  sortBy: SortOption;
  showSortModal: boolean;
  searchFocused: boolean;
  filtersCollapsed: boolean;
  scrollOffset: number;
  pantryIngredients: string[];
}

type Action =
  | { type: 'SET_RECIPES'; payload: Recipe[] }
  | { type: 'SET_SAVED_RECIPES'; payload: SavedRecipe[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_REFRESHING'; payload: boolean }
  | { type: 'SET_SEARCH_QUERY'; payload: string }
  | { type: 'SET_ACTIVE_TAB'; payload: ActiveTab }
  | { type: 'SET_SELECTED_FILTERS'; payload: string[] }
  | { type: 'SET_MY_RECIPES_FILTER'; payload: MyRecipesFilter }
  | { type: 'SET_MY_RECIPES_TAB'; payload: MyRecipesTab }
  | { type: 'SET_SORT_BY'; payload: SortOption }
  | { type: 'SET_SHOW_SORT_MODAL'; payload: boolean }
  | { type: 'SET_SEARCH_FOCUSED'; payload: boolean }
  | { type: 'SET_FILTERS_COLLAPSED'; payload: boolean }
  | { type: 'SET_SCROLL_OFFSET'; payload: number }
  | { type: 'SET_PANTRY_INGREDIENTS'; payload: string[] }
  | { type: 'UPDATE_SAVED_RECIPE'; payload: { id: string; updates: Partial<SavedRecipe> } };

const initialState: State = {
  recipes: [],
  savedRecipes: [],
  loading: false,
  refreshing: false,
  searchQuery: '',
  activeTab: 'pantry',
  selectedFilters: [],
  myRecipesFilter: 'all',
  myRecipesTab: 'saved',
  sortBy: 'name',
  showSortModal: false,
  searchFocused: false,
  filtersCollapsed: false,
  scrollOffset: 0,
  pantryIngredients: [],
};

function recipesReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_RECIPES':
      return { ...state, recipes: action.payload };
    case 'SET_SAVED_RECIPES':
      return { ...state, savedRecipes: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_REFRESHING':
      return { ...state, refreshing: action.payload };
    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.payload };
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'SET_SELECTED_FILTERS':
      return { ...state, selectedFilters: action.payload };
    case 'SET_MY_RECIPES_FILTER':
      return { ...state, myRecipesFilter: action.payload };
    case 'SET_MY_RECIPES_TAB':
      return { ...state, myRecipesTab: action.payload };
    case 'SET_SORT_BY':
      return { ...state, sortBy: action.payload };
    case 'SET_SHOW_SORT_MODAL':
      return { ...state, showSortModal: action.payload };
    case 'SET_SEARCH_FOCUSED':
      return { ...state, searchFocused: action.payload };
    case 'SET_FILTERS_COLLAPSED':
      return { ...state, filtersCollapsed: action.payload };
    case 'SET_SCROLL_OFFSET':
      return { ...state, scrollOffset: action.payload };
    case 'SET_PANTRY_INGREDIENTS':
      return { ...state, pantryIngredients: action.payload };
    case 'UPDATE_SAVED_RECIPE':
      return {
        ...state,
        savedRecipes: state.savedRecipes.map(recipe => 
          recipe.id === action.payload.id 
            ? { ...recipe, ...action.payload.updates }
            : recipe
        )
      };
    default:
      return state;
  }
}

export default function RecipesContainer() {
  const [state, dispatch] = useReducer(recipesReducer, initialState);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { items } = useItems();
  const { user, token, isAuthenticated } = useAuth();
  const { recipesData } = useTabData();
  const { preferences } = useUserPreferences();

  // Recalculate ingredient counts based on actual pantry items using standardized matching
  const recalculateIngredientCounts = useCallback((recipe: Recipe, pantryItems: string[]) => {
    // Convert pantry items to the expected format
    const pantryItemObjects = pantryItems.map(item => ({ product_name: item }));
    
    // Combine all ingredients into a single array with the expected format
    const allIngredients = [
      ...(recipe.usedIngredients || []),
      ...(recipe.missedIngredients || [])
    ].map((ingredient, index) => ({
      id: ingredient.id || index, // Use ingredient ID or fallback to index
      name: ingredient.name,
      original: ingredient.original || ingredient.name // Use original text if available
    }));

    // Use the standardized ingredient matching utility
    const result = calculateIngredientAvailability(allIngredients, pantryItemObjects);
    
    // Validate that counts add up correctly
    if (!validateIngredientCounts(result)) {
      console.warn('Ingredient count validation failed in recipes list:', result);
    }

    return { 
      usedCount: result.availableCount, 
      missedCount: result.missingCount 
    };
  }, []);

  // Filter recipes based on user preferences (allergens, dietary preferences, cuisines)
  const filterRecipesByPreferences = useCallback((recipes: SavedRecipe[]) => {
    if (!preferences || (!preferences.allergens.length && !preferences.dietaryPreferences.length && !preferences.cuisines.length)) {
      return recipes; // No preferences set, show all recipes
    }

    return recipes.filter(recipe => {
      const recipeData = recipe.recipe_data || {};
      const title = (recipe.recipe_title || '').toLowerCase();
      const ingredients = (recipeData.extendedIngredients || []).map((ing: any) => (ing.name || '').toLowerCase());
      const dishTypes = (recipeData.dishTypes || []).map((type: string) => type.toLowerCase());
      const cuisines = (recipeData.cuisines || []).map((cuisine: string) => cuisine.toLowerCase());
      
      // Check allergens - if recipe contains allergens, exclude it
      if (preferences.allergens.length > 0) {
        const hasAllergen = preferences.allergens.some(allergen => {
          const allergenLower = allergen.toLowerCase();
          return (
            title.includes(allergenLower) ||
            ingredients.some(ing => ing.includes(allergenLower)) ||
            dishTypes.some(type => type.includes(allergenLower))
          );
        });
        if (hasAllergen) {
          console.log(`Filtering out recipe "${recipe.recipe_title}" due to allergen`);
          return false;
        }
      }

      // Check dietary preferences - if preferences set, recipe must match at least one
      if (preferences.dietaryPreferences.length > 0) {
        const matchesDietaryPref = preferences.dietaryPreferences.some(pref => {
          const prefLower = pref.toLowerCase();
          const tags = (recipeData.diets || []).map((diet: string) => diet.toLowerCase());
          return (
            tags.includes(prefLower) ||
            title.includes(prefLower) ||
            dishTypes.some(type => type.includes(prefLower))
          );
        });
        if (!matchesDietaryPref) {
          console.log(`Filtering out recipe "${recipe.recipe_title}" - doesn't match dietary preferences`);
          return false;
        }
      }

      // Check cuisine preferences - if preferences set, recipe must match at least one
      if (preferences.cuisines.length > 0) {
        const matchesCuisine = preferences.cuisines.some(cuisine => {
          const cuisineLower = cuisine.toLowerCase();
          return (
            cuisines.includes(cuisineLower) ||
            title.includes(cuisineLower) ||
            dishTypes.some(type => type.includes(cuisineLower))
          );
        });
        if (!matchesCuisine) {
          console.log(`Filtering out recipe "${recipe.recipe_title}" - doesn't match cuisine preferences`);
          return false;
        }
      }

      return true; // Recipe passes all preference filters
    });
  }, [preferences]);

  const fetchRecipesFromPantry = useCallback(async () => {
    console.log('fetchRecipesFromPantry called');
    
    // Use preloaded data if available and fresh
    if (recipesData?.pantryRecipes && !state.refreshing) {
      const pantryItemNames = items.map(item => item.item_name);
      const processedRecipes = recipesData.pantryRecipes.map(recipe => {
        const counts = recalculateIngredientCounts(recipe, pantryItemNames);
        return { 
          ...recipe, 
          usedIngredientCount: counts.usedCount, 
          missedIngredientCount: counts.missedCount 
        };
      });
      dispatch({ type: 'SET_RECIPES', payload: processedRecipes });
      dispatch({ type: 'SET_PANTRY_INGREDIENTS', payload: pantryItemNames });
      return;
    }
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      console.log('Fetching from:', `${Config.API_BASE_URL}/recipes/search/from-pantry`);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111, // Default demo user
          max_missing_ingredients: 10, // Increased since we now filter by at least 1 matching ingredient
          use_expiring_first: true,
        }),
      });

      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error response:', errorData);
        if (response.status === 400 && errorData.detail?.includes('API key')) {
          Alert.alert(
            'Spoonacular API Key Required',
            'To use recipe features, you need to add a Spoonacular API key.\n\n1. Get your free API key at:\nhttps://spoonacular.com/food-api\n\n2. Add it to your .env file:\nSPOONACULAR_API_KEY=your_key_here',
            [{ text: 'OK' }]
          );
          return;
        }
        throw new Error('Failed to fetch recipes');
      }
      
      const data = await response.json();
      console.log('Data received:', data);
      console.log('Number of recipes:', data.recipes?.length || 0);
      console.log('Pantry ingredients count:', data.pantry_ingredients?.length || 0);
      
      // Store pantry ingredients for count calculation
      if (data.pantry_ingredients) {
        const pantryNames = data.pantry_ingredients.map((item: any) => item.name);
        dispatch({ type: 'SET_PANTRY_INGREDIENTS', payload: pantryNames });
      }
      
      // Filter to only include Spoonacular recipes (safety check)
      const spoonacularRecipes = (data.recipes || []).filter((recipe: Recipe) => {
        // Only include recipes that have a valid Spoonacular ID
        return recipe.id && typeof recipe.id === 'number' && recipe.id > 0;
      });
      console.log('Spoonacular recipes after filter:', spoonacularRecipes.length);
      
      // Update recipes with recalculated counts
      // Don't validate pantry recipes since they don't include instructions yet
      const recipesWithCorrectCounts = spoonacularRecipes
        .map((recipe: Recipe) => {
          if (data.pantry_ingredients) {
            const pantryNames = data.pantry_ingredients.map((item: any) => item.name);
            const { usedCount, missedCount } = recalculateIngredientCounts(recipe, pantryNames);
            return {
              ...recipe,
              usedIngredientCount: usedCount,
              missedIngredientCount: missedCount
            };
          }
          return recipe;
        });
      
      console.log('Final recipes count:', recipesWithCorrectCounts.length);
      dispatch({ type: 'SET_RECIPES', payload: recipesWithCorrectCounts });
    } catch (error) {
      console.error('Error fetching recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [items, recipesData, state.refreshing, recalculateIngredientCounts]);

  const searchRecipes = useCallback(async (query: string = state.searchQuery) => {
    if (!query.trim() && state.activeTab === 'discover') {
      // If no search query in discover tab, fetch random recipes
      await fetchRandomRecipes();
      return;
    }

    if (!query.trim()) return;

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          number: 20,
          diet: state.selectedFilters.length > 0 ? state.selectedFilters.join(',') : undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 400 && errorData.detail?.includes('API key')) {
          Alert.alert(
            'Spoonacular API Key Required',
            'To use recipe features, you need to add a Spoonacular API key.\n\n1. Get your free API key at:\nhttps://spoonacular.com/food-api\n\n2. Add it to your .env file:\nSPOONACULAR_API_KEY=your_key_here',
            [{ text: 'OK' }]
          );
          return;
        }
        throw new Error('Failed to search recipes');
      }
      
      const data = await response.json();
      
      // Filter to only include valid Spoonacular recipes
      const spoonacularRecipes = (data.results || []).filter((recipe: Recipe) => {
        // Only include recipes that have a valid Spoonacular ID and meet quality standards
        return recipe.id && typeof recipe.id === 'number' && recipe.id > 0 && isValidRecipe(recipe);
      });
      
      dispatch({ type: 'SET_RECIPES', payload: spoonacularRecipes });
    } catch (error) {
      console.error('Error searching recipes:', error);
      Alert.alert('Error', 'Failed to search recipes. Please try again.');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.searchQuery, state.activeTab, state.selectedFilters]);

  const fetchRandomRecipes = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await fetch(`${Config.API_BASE_URL}/recipes/random?number=20`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 400 && errorData.detail?.includes('API key')) {
          Alert.alert(
            'Spoonacular API Key Required',
            'To use recipe features, you need to add a Spoonacular API key.\n\n1. Get your free API key at:\nhttps://spoonacular.com/food-api\n\n2. Add it to your .env file:\nSPOONACULAR_API_KEY=your_key_here',
            [{ text: 'OK' }]
          );
          return;
        }
        throw new Error('Failed to fetch random recipes');
      }
      
      const data = await response.json();
      
      // Filter to only include valid Spoonacular recipes
      const spoonacularRecipes = (data.recipes || []).filter((recipe: Recipe) => {
        // Only include recipes that have a valid Spoonacular ID and meet quality standards
        return recipe.id && typeof recipe.id === 'number' && recipe.id > 0 && isValidRecipe(recipe);
      });
      
      dispatch({ type: 'SET_RECIPES', payload: spoonacularRecipes });
    } catch (error) {
      console.error('Error fetching random recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const fetchMyRecipes = useCallback(async () => {
    // Use preloaded data if available and fresh
    if (recipesData?.myRecipes && !state.refreshing) {
      const filterMap = {
        'all': recipesData.myRecipes,
        'thumbs_up': recipesData.myRecipes.filter(r => r.rating === 'thumbs_up'),
        'thumbs_down': recipesData.myRecipes.filter(r => r.rating === 'thumbs_down'),
        'favorites': recipesData.myRecipes.filter(r => r.is_favorite)
      };
      const filteredRecipes = filterMap[state.myRecipesFilter] || recipesData.myRecipes;
      
      // Apply user preference filtering to show only recipes matching Lily's preferences
      const preferencesFilteredRecipes = filterRecipesByPreferences(filteredRecipes);
      console.log(`Filtered ${filteredRecipes.length} recipes to ${preferencesFilteredRecipes.length} based on user preferences`);
      
      dispatch({ type: 'SET_SAVED_RECIPES', payload: preferencesFilteredRecipes });
      return;
    }
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      let filterParam = '';
      // Add status filter based on current tab
      if (state.myRecipesTab === 'saved') {
        filterParam = '?status=saved';
      } else if (state.myRecipesTab === 'cooked') {
        filterParam = '?status=cooked';
      }
      
      // Add additional filters
      if (state.myRecipesFilter === 'favorites') {
        filterParam += filterParam ? '&is_favorite=true' : '?is_favorite=true';
      } else if (state.myRecipesFilter !== 'all') {
        filterParam += filterParam ? `&rating=${state.myRecipesFilter}` : `?rating=${state.myRecipesFilter}`;
      }
      
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes${filterParam}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch saved recipes');
      }
      
      const data = await response.json();
      console.log('Fetched saved recipes with filter:', state.myRecipesFilter, 'API returned:', data?.length || 0, 'recipes');
      
      // Apply user preference filtering to show only recipes matching Lily's preferences
      const preferencesFilteredRecipes = filterRecipesByPreferences(data || []);
      console.log(`Filtered ${(data || []).length} recipes to ${preferencesFilteredRecipes.length} based on user preferences`);
      
      dispatch({ type: 'SET_SAVED_RECIPES', payload: preferencesFilteredRecipes });
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      Alert.alert('Error', 'Failed to load saved recipes. Please try again.');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [recipesData, state.refreshing, state.myRecipesFilter, state.myRecipesTab, filterRecipesByPreferences]);

  const onRefresh = useCallback(async () => {
    dispatch({ type: 'SET_REFRESHING', payload: true });
    if (state.activeTab === 'pantry') {
      await fetchRecipesFromPantry();
    } else if (state.activeTab === 'discover') {
      if (state.searchQuery) {
        await searchRecipes();
      } else {
        await fetchRandomRecipes();
      }
    } else if (state.activeTab === 'my-recipes') {
      await fetchMyRecipes();
    }
    dispatch({ type: 'SET_REFRESHING', payload: false });
  }, [state.activeTab, state.searchQuery, fetchRecipesFromPantry, searchRecipes, fetchRandomRecipes, fetchMyRecipes]);

  // Effects for data fetching
  useEffect(() => {
    if (state.activeTab === 'pantry') {
      fetchRecipesFromPantry();
    } else if (state.activeTab === 'discover') {
      if (state.searchQuery) {
        searchRecipes();
      } else {
        fetchRandomRecipes();
      }
    } else if (state.activeTab === 'my-recipes') {
      fetchMyRecipes();
    }
  }, [state.activeTab, fetchRecipesFromPantry, state.selectedFilters, state.myRecipesFilter]);

  // Add separate effect to handle filter and tab changes on my-recipes tab
  useEffect(() => {
    if (state.activeTab === 'my-recipes') {
      fetchMyRecipes();
    }
  }, [state.myRecipesFilter, state.myRecipesTab, fetchMyRecipes]);

  return (
    <View style={styles.container}>
      <RecipesTabs
        activeTab={state.activeTab}
        searchQuery={state.searchQuery}
        searchFocused={state.searchFocused}
        showSortModal={state.showSortModal}
        sortBy={state.sortBy}
        onTabChange={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
        onSearchQueryChange={(query) => dispatch({ type: 'SET_SEARCH_QUERY', payload: query })}
        onSearchFocusChange={(focused) => dispatch({ type: 'SET_SEARCH_FOCUSED', payload: focused })}
        onSortModalToggle={(show) => dispatch({ type: 'SET_SHOW_SORT_MODAL', payload: show })}
        onSortChange={(sort) => dispatch({ type: 'SET_SORT_BY', payload: sort })}
        onSearchSubmit={() => state.activeTab === 'discover' && searchRecipes()}
        router={router}
      />

      <RecipesFilters
        activeTab={state.activeTab}
        selectedFilters={state.selectedFilters}
        myRecipesFilter={state.myRecipesFilter}
        myRecipesTab={state.myRecipesTab}
        filtersCollapsed={state.filtersCollapsed}
        onFiltersChange={(filters) => dispatch({ type: 'SET_SELECTED_FILTERS', payload: filters })}
        onMyRecipesFilterChange={(filter) => dispatch({ type: 'SET_MY_RECIPES_FILTER', payload: filter })}
        onMyRecipesTabChange={(tab) => {
          dispatch({ type: 'SET_MY_RECIPES_TAB', payload: tab });
          dispatch({ type: 'SET_MY_RECIPES_FILTER', payload: 'all' });
        }}
        onFiltersCollapsedChange={(collapsed) => dispatch({ type: 'SET_FILTERS_COLLAPSED', payload: collapsed })}
      />

      <RecipesList
        recipes={state.recipes}
        savedRecipes={state.savedRecipes}
        loading={state.loading}
        refreshing={state.refreshing}
        searchQuery={state.searchQuery}
        activeTab={state.activeTab}
        myRecipesTab={state.myRecipesTab}
        sortBy={state.sortBy}
        scrollOffset={state.scrollOffset}
        filtersCollapsed={state.filtersCollapsed}
        onRefresh={onRefresh}
        onScrollOffsetChange={(offset) => dispatch({ type: 'SET_SCROLL_OFFSET', payload: offset })}
        onFiltersCollapsedChange={(collapsed) => dispatch({ type: 'SET_FILTERS_COLLAPSED', payload: collapsed })}
        onSavedRecipeUpdate={(id, updates) => dispatch({ type: 'UPDATE_SAVED_RECIPE', payload: { id, updates } })}
        fetchMyRecipes={fetchMyRecipes}
        router={router}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
});