import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Image,
  RefreshControl,
  Alert,
  Dimensions,
  Modal,
  Pressable,
  Animated,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Config } from '../../config';
import { useItems } from '../../context/ItemsContext';
import { useAuth } from '../../context/AuthContext';
import { calculateIngredientAvailability, validateIngredientCounts } from '../../utils/ingredientMatcher';
import { isValidRecipe } from '../../utils/contentValidation';

const { width } = Dimensions.get('window');

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

export default function RecipesScreen() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [savedRecipes, setSavedRecipes] = useState<SavedRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'pantry' | 'discover' | 'my-recipes'>('pantry');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [myRecipesFilter, setMyRecipesFilter] = useState<'all' | 'thumbs_up' | 'thumbs_down' | 'favorites'>('all');
  const [myRecipesTab, setMyRecipesTab] = useState<'saved' | 'cooked'>('saved');
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [showSortModal, setShowSortModal] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);
  const [scrollOffset, setScrollOffset] = useState(0);
  const filterHeight = useRef(new Animated.Value(1)).current;
  const [pantryIngredients, setPantryIngredients] = useState<string[]>([]);
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { items } = useItems();
  const { user, token, isAuthenticated } = useAuth();

  const dietaryFilters = [
    { id: 'vegetarian', label: 'Vegetarian', icon: '🥗' },
    { id: 'vegan', label: 'Vegan', icon: '🌱' },
    { id: 'gluten-free', label: 'Gluten-Free', icon: '🌾' },
    { id: 'dairy-free', label: 'Dairy-Free', icon: '🥛' },
    { id: 'low-carb', label: 'Low Carb', icon: '🥖' },
    { id: 'keto', label: 'Keto', icon: '🥑' },
    { id: 'paleo', label: 'Paleo', icon: '🍖' },
    { id: 'mediterranean', label: 'Mediterranean', icon: '🫒' },
  ];

  const cuisineFilters = [
    { id: 'italian', label: 'Italian', icon: '🍝' },
    { id: 'mexican', label: 'Mexican', icon: '🌮' },
    { id: 'asian', label: 'Asian', icon: '🥢' },
    { id: 'american', label: 'American', icon: '🍔' },
    { id: 'indian', label: 'Indian', icon: '🍛' },
    { id: 'french', label: 'French', icon: '🥐' },
    { id: 'japanese', label: 'Japanese', icon: '🍱' },
    { id: 'thai', label: 'Thai', icon: '🍜' },
  ];

  const mealTypeFilters = [
    { id: 'breakfast', label: 'Breakfast', icon: '🍳' },
    { id: 'lunch', label: 'Lunch', icon: '🥪' },
    { id: 'dinner', label: 'Dinner', icon: '🍽️' },
    { id: 'snack', label: 'Snack', icon: '🍿' },
    { id: 'dessert', label: 'Dessert', icon: '🍰' },
    { id: 'appetizer', label: 'Appetizer', icon: '🥟' },
    { id: 'soup', label: 'Soup', icon: '🍲' },
    { id: 'salad', label: 'Salad', icon: '🥗' },
  ];

  const sortOptions = [
    { value: 'name', label: 'Name (A-Z)', icon: 'alphabetical' },
    { value: 'date', label: 'Recently Added', icon: 'clock-outline' },
    { value: 'rating', label: 'Highest Rated', icon: 'star' },
    { value: 'missing', label: 'Fewest Missing', icon: 'checkbox-marked-circle' },
  ];

  const toggleFilter = (filterId: string) => {
    setSelectedFilters(prev => 
      prev.includes(filterId) 
        ? prev.filter(f => f !== filterId)
        : [...prev, filterId]
    );
  };

  // Recalculate ingredient counts based on actual pantry items using standardized matching
  const recalculateIngredientCounts = (recipe: Recipe, pantryItems: string[]) => {
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
  };

  const fetchRecipesFromPantry = useCallback(async () => {
    console.log('fetchRecipesFromPantry called');
    try {
      setLoading(true);
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
        setPantryIngredients(pantryNames);
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
      setRecipes(recipesWithCorrectCounts);
    } catch (error) {
      console.error('Error fetching recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const searchRecipes = async (query: string = searchQuery) => {
    if (!query.trim() && activeTab === 'discover') {
      // If no search query in discover tab, fetch random recipes
      await fetchRandomRecipes();
      return;
    }

    if (!query.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          number: 20,
          diet: selectedFilters.length > 0 ? selectedFilters.join(',') : undefined,
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
      
      setRecipes(spoonacularRecipes);
    } catch (error) {
      console.error('Error searching recipes:', error);
      Alert.alert('Error', 'Failed to search recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRandomRecipes = async () => {
    try {
      setLoading(true);
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
      
      setRecipes(spoonacularRecipes);
    } catch (error) {
      console.error('Error fetching random recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMyRecipes = async () => {
    try {
      setLoading(true);
      // Authentication temporarily disabled - using hardcoded user_id = 111
      // if (!token || !isAuthenticated) {
      //   Alert.alert('Error', 'Please login to view your saved recipes.');
      //   return;
      // }

      let filterParam = '';
      // Add status filter based on current tab
      if (myRecipesTab === 'saved') {
        filterParam = '?status=saved';
      } else if (myRecipesTab === 'cooked') {
        filterParam = '?status=cooked';
      }
      
      // Add additional filters
      if (myRecipesFilter === 'favorites') {
        filterParam += filterParam ? '&is_favorite=true' : '?is_favorite=true';
      } else if (myRecipesFilter !== 'all') {
        filterParam += filterParam ? `&rating=${myRecipesFilter}` : `?rating=${myRecipesFilter}`;
      }
      
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes${filterParam}`, {
        headers: {
          // 'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch saved recipes');
      }
      
      const data = await response.json();
      console.log('Fetched saved recipes with filter:', myRecipesFilter, 'API returned:', data?.length || 0, 'recipes');
      // Mock recipes removed to prevent 404 errors with invalid Spoonacular IDs
      const mockRecipes: SavedRecipe[] = []; /*[
        {
          id: 'mock-1',
          recipe_id: 100001,
          recipe_title: 'Classic Spaghetti Carbonara',
          recipe_image: 'https://img.spoonacular.com/recipes/715769-556x370.jpg',
          recipe_data: {
            id: 100001,
            title: 'Classic Spaghetti Carbonara',
            readyInMinutes: 30,
            servings: 4,
            summary: 'A classic Italian pasta dish made with eggs, cheese, and bacon. Quick, easy, and absolutely delicious!',
            instructions: [
              'Bring a large pot of salted water to boil and cook spaghetti according to package directions.',
              'While pasta cooks, fry bacon until crispy. Remove and set aside.',
              'In a bowl, whisk together eggs, grated Parmesan cheese, and black pepper.',
              'When pasta is al dente, reserve 1 cup pasta water and drain.',
              'Quickly toss hot pasta with bacon and fat, then remove from heat.',
              'Add egg mixture and toss rapidly, adding pasta water as needed for creamy sauce.',
              'Serve immediately with extra Parmesan and black pepper.'
            ],
            extendedIngredients: [
              { name: 'spaghetti', amount: 400, unit: 'g' },
              { name: 'bacon', amount: 200, unit: 'g' },
              { name: 'eggs', amount: 4, unit: '' },
              { name: 'Parmesan cheese', amount: 100, unit: 'g' },
              { name: 'black pepper', amount: 1, unit: 'tsp' }
            ]
          },
          rating: 'thumbs_up',
          is_favorite: true,
          status: 'cooked',
          source: 'spoonacular',
          created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
          updated_at: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: 'mock-2',
          recipe_id: 100002,
          recipe_title: 'Thai Green Curry Chicken',
          recipe_image: 'https://img.spoonacular.com/recipes/663050-556x370.jpg',
          recipe_data: {
            id: 100002,
            title: 'Thai Green Curry Chicken',
            readyInMinutes: 45,
            servings: 4,
            summary: 'Authentic Thai green curry with tender chicken, vegetables, and aromatic herbs in coconut milk.',
            instructions: [
              'Heat oil in a large pan or wok over medium-high heat.',
              'Add green curry paste and fry for 1-2 minutes until fragrant.',
              'Add chicken pieces and stir-fry until they change color.',
              'Pour in coconut milk and bring to a simmer.',
              'Add vegetables, fish sauce, and palm sugar. Simmer for 15 minutes.',
              'Add Thai basil leaves and lime juice just before serving.',
              'Serve hot with jasmine rice.'
            ],
            extendedIngredients: [
              { name: 'chicken breast', amount: 500, unit: 'g' },
              { name: 'green curry paste', amount: 3, unit: 'tbsp' },
              { name: 'coconut milk', amount: 400, unit: 'ml' },
              { name: 'Thai basil', amount: 1, unit: 'cup' },
              { name: 'fish sauce', amount: 2, unit: 'tbsp' },
              { name: 'vegetables (eggplant, bamboo shoots)', amount: 300, unit: 'g' }
            ]
          },
          rating: 'thumbs_up',
          is_favorite: false,
          source: 'spoonacular',
          created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
          updated_at: new Date(Date.now() - 172800000).toISOString(),
        },
        {
          id: 'mock-3',
          recipe_id: 100003,
          recipe_title: 'Homemade Margherita Pizza',
          recipe_image: 'https://img.spoonacular.com/recipes/680975-556x370.jpg',
          recipe_data: {
            id: 100003,
            title: 'Homemade Margherita Pizza',
            readyInMinutes: 120,
            servings: 2,
            summary: 'Classic Italian pizza with fresh mozzarella, basil, and homemade tomato sauce on a crispy crust.',
            instructions: [
              'Make pizza dough: Mix flour, yeast, salt, water, and olive oil. Knead for 10 minutes.',
              'Let dough rise in a warm place for 1-2 hours until doubled in size.',
              'Preheat oven to 250°C (480°F) with pizza stone if available.',
              'Roll out dough to desired thickness.',
              'Spread tomato sauce, leaving border for crust.',
              'Add torn mozzarella and drizzle with olive oil.',
              'Bake for 10-12 minutes until crust is golden and cheese bubbles.',
              'Top with fresh basil leaves before serving.'
            ],
            extendedIngredients: [
              { name: 'pizza dough', amount: 1, unit: 'batch' },
              { name: 'tomato sauce', amount: 200, unit: 'ml' },
              { name: 'fresh mozzarella', amount: 250, unit: 'g' },
              { name: 'fresh basil', amount: 10, unit: 'leaves' },
              { name: 'olive oil', amount: 2, unit: 'tbsp' }
            ]
          },
          rating: 'neutral',
          is_favorite: true,
          source: 'spoonacular',
          created_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
          updated_at: new Date(Date.now() - 259200000).toISOString(),
        },
        {
          id: 'mock-4',
          recipe_id: 100004,
          recipe_title: 'Vegan Buddha Bowl',
          recipe_image: 'https://img.spoonacular.com/recipes/1095753-556x370.jpg',
          recipe_data: {
            id: 100004,
            title: 'Vegan Buddha Bowl',
            readyInMinutes: 35,
            servings: 2,
            summary: 'Colorful and nutritious bowl packed with quinoa, roasted vegetables, chickpeas, and tahini dressing.',
            instructions: [
              'Cook quinoa according to package directions.',
              'Preheat oven to 200°C (400°F).',
              'Toss sweet potatoes and chickpeas with olive oil, cumin, and paprika.',
              'Roast for 25 minutes until golden and crispy.',
              'Steam or blanch broccoli until tender-crisp.',
              'Make tahini dressing: whisk tahini, lemon juice, garlic, and water.',
              'Assemble bowls with quinoa base, then arrange vegetables and chickpeas.',
              'Drizzle with tahini dressing and sprinkle with seeds.'
            ],
            extendedIngredients: [
              { name: 'quinoa', amount: 200, unit: 'g' },
              { name: 'sweet potato', amount: 1, unit: 'large' },
              { name: 'chickpeas', amount: 400, unit: 'g' },
              { name: 'broccoli', amount: 200, unit: 'g' },
              { name: 'tahini', amount: 3, unit: 'tbsp' },
              { name: 'mixed seeds', amount: 2, unit: 'tbsp' }
            ]
          },
          rating: 'thumbs_up',
          is_favorite: false,
          source: 'generated',
          created_at: new Date(Date.now() - 345600000).toISOString(), // 4 days ago
          updated_at: new Date(Date.now() - 345600000).toISOString(),
        },
        {
          id: 'mock-5',
          recipe_id: 100005,
          recipe_title: 'Chocolate Lava Cake',
          recipe_image: 'https://img.spoonacular.com/recipes/1096230-556x370.jpg',
          recipe_data: {
            id: 100005,
            title: 'Chocolate Lava Cake',
            readyInMinutes: 25,
            servings: 4,
            summary: 'Decadent individual chocolate cakes with a molten center. Perfect for special occasions!',
            instructions: [
              'Preheat oven to 200°C (400°F). Butter and flour 4 ramekins.',
              'Melt chocolate and butter together in double boiler or microwave.',
              'Whisk eggs, egg yolks, and sugar until thick and pale.',
              'Fold chocolate mixture into egg mixture.',
              'Sift in flour and fold gently until just combined.',
              'Divide batter among ramekins, filling 3/4 full.',
              'Bake for 12-14 minutes until edges are firm but center jiggles.',
              'Let rest 1 minute, then invert onto plates. Serve immediately.'
            ],
            extendedIngredients: [
              { name: 'dark chocolate', amount: 200, unit: 'g' },
              { name: 'butter', amount: 150, unit: 'g' },
              { name: 'eggs', amount: 2, unit: '' },
              { name: 'egg yolks', amount: 2, unit: '' },
              { name: 'sugar', amount: 60, unit: 'g' },
              { name: 'flour', amount: 60, unit: 'g' }
            ]
          },
          rating: 'thumbs_down',
          is_favorite: false,
          source: 'spoonacular',
          created_at: new Date(Date.now() - 432000000).toISOString(), // 5 days ago
          updated_at: new Date(Date.now() - 432000000).toISOString(),
        }
      ];*/

      // Mock recipes processing commented out
      /*
      // Add status to mock recipes based on rating
      mockRecipes.forEach(recipe => {
        if (!recipe.status) {
          // If has rating, it was cooked
          recipe.status = (recipe.rating === 'thumbs_up' || recipe.rating === 'thumbs_down') ? 'cooked' : 'saved';
        }
      });
      
      // Filter mock recipes based on current tab and filter
      let filteredMockRecipes = mockRecipes;
      */
      
      // Use empty array instead of mock recipes
      let filteredMockRecipes: SavedRecipe[] = [];
      
      // Mock recipes filtering commented out - no mock recipes to filter
      /*
      // First filter by status (tab)
      if (myRecipesTab === 'saved') {
        filteredMockRecipes = mockRecipes.filter(recipe => recipe.status === 'saved');
      } else if (myRecipesTab === 'cooked') {
        filteredMockRecipes = mockRecipes.filter(recipe => recipe.status === 'cooked');
      }
      
      // Then apply additional filters
      if (myRecipesFilter === 'favorites') {
        filteredMockRecipes = filteredMockRecipes.filter(recipe => recipe.is_favorite);
      } else if (myRecipesFilter === 'thumbs_up') {
        filteredMockRecipes = filteredMockRecipes.filter(recipe => recipe.rating === 'thumbs_up');
      } else if (myRecipesFilter === 'thumbs_down') {
        filteredMockRecipes = filteredMockRecipes.filter(recipe => recipe.rating === 'thumbs_down');
      }
      
      console.log('Mock recipes filtered:', filteredMockRecipes.length, 'out of', mockRecipes.length, 'for filter:', myRecipesFilter);
      */
      
      // Combine real data with filtered mock data
      const combinedData = [...(data || []), ...filteredMockRecipes];
      setSavedRecipes(combinedData);
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      Alert.alert('Error', 'Failed to load saved recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveRecipe = async (recipe: Recipe) => {
    try {
      // Authentication temporarily disabled - using hardcoded user_id = 111
      // if (!token || !isAuthenticated) {
      //   Alert.alert('Error', 'Please login to save recipes.');
      //   return;
      // }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: {
          // 'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipe_id: recipe.id,
          recipe_title: recipe.title,
          recipe_image: recipe.image,
          recipe_data: recipe,
          source: 'spoonacular',
          rating: 'neutral',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        if (error.detail?.includes('already saved')) {
          Alert.alert('Info', 'Recipe is already in your collection.');
          return;
        }
        throw new Error('Failed to save recipe');
      }
      
      Alert.alert('Success', 'Recipe saved to My Recipes ▸ Saved');
      // Refresh my recipes if on that tab
      if (activeTab === 'my-recipes') {
        await fetchMyRecipes();
      }
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe. Please try again.');
    }
  };

  const updateRecipeRating = async (recipeId: string, rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => {
    try {
      // Authentication temporarily disabled - using hardcoded user_id = 111
      // if (!token || !isAuthenticated) {
      //   Alert.alert('Error', 'Please login to rate recipes.');
      //   return;
      // }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/rating`, {
        method: 'PUT',
        headers: {
          // 'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rating }),
      });

      if (!response.ok) {
        throw new Error('Failed to update rating');
      }
      
      // Refresh the list
      await fetchMyRecipes();
    } catch (error) {
      console.error('Error updating rating:', error);
      Alert.alert('Error', 'Failed to update rating. Please try again.');
    }
  };

  const toggleFavorite = async (recipeId: string, isFavorite: boolean) => {
    try {
      // Authentication temporarily disabled - using hardcoded user_id = 111
      // if (!token || !isAuthenticated) {
      //   Alert.alert('Error', 'Please login to favorite recipes.');
      //   return;
      // }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/favorite`, {
        method: 'PUT',
        headers: {
          // 'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_favorite: isFavorite }),
      });

      if (!response.ok) {
        throw new Error('Failed to update favorite status');
      }
      
      // Update local state
      setSavedRecipes(prevRecipes => 
        prevRecipes.map(recipe => 
          recipe.id === recipeId ? { ...recipe, is_favorite: isFavorite } : recipe
        )
      );
      
      // Show feedback
      if (isFavorite) {
        Alert.alert('Added to Favorites', 'This recipe will be used to improve your recommendations.');
      }
    } catch (error) {
      console.error('Error updating favorite:', error);
      Alert.alert('Error', 'Failed to update favorite status. Please try again.');
    }
  };

  const deleteRecipe = async (recipeId: string) => {
    try {
      // Authentication temporarily disabled - using hardcoded user_id = 111
      // if (!token || !isAuthenticated) {
      //   Alert.alert('Error', 'Please login to delete recipes.');
      //   return;
      // }

      Alert.alert(
        'Delete Recipe',
        'Are you sure you want to remove this recipe from your collection?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: async () => {
              const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}`, {
                method: 'DELETE',
                headers: {
                  // 'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
              });

              if (!response.ok) {
                throw new Error('Failed to delete recipe');
              }
              
              Alert.alert('Success', 'Recipe removed from your collection.');
              await fetchMyRecipes();
            },
          },
        ]
      );
    } catch (error) {
      console.error('Error deleting recipe:', error);
      Alert.alert('Error', 'Failed to delete recipe. Please try again.');
    }
  };

  // Filter recipes based on search query
  const getFilteredRecipes = () => {
    console.log('getFilteredRecipes called, recipes:', recipes.length, 'activeTab:', activeTab);
    let filteredRecipes = [...recipes];
    
    if (searchQuery && activeTab === 'pantry') {
      filteredRecipes = recipes.filter(recipe => 
        recipe.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Sort recipes
    if (sortBy === 'name') {
      filteredRecipes.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sortBy === 'missing') {
      filteredRecipes.sort((a, b) => 
        (a.missedIngredientCount || 0) - (b.missedIngredientCount || 0)
      );
    }
    
    console.log('Filtered recipes count:', filteredRecipes.length);
    return filteredRecipes;
  };

  // Filter saved recipes based on search query
  const getFilteredSavedRecipes = () => {
    let filteredRecipes = [...savedRecipes];
    
    if (searchQuery) {
      filteredRecipes = savedRecipes.filter(recipe => 
        recipe.recipe_title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Sort recipes
    if (sortBy === 'name') {
      filteredRecipes.sort((a, b) => a.recipe_title.localeCompare(b.recipe_title));
    } else if (sortBy === 'date') {
      filteredRecipes.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    } else if (sortBy === 'rating') {
      filteredRecipes.sort((a, b) => {
        const ratingOrder = { thumbs_up: 2, neutral: 1, thumbs_down: 0 };
        return ratingOrder[b.rating] - ratingOrder[a.rating];
      });
    }
    
    return filteredRecipes;
  };

  useEffect(() => {
    if (activeTab === 'pantry') {
      fetchRecipesFromPantry();
    } else if (activeTab === 'discover') {
      if (searchQuery) {
        searchRecipes();
      } else {
        fetchRandomRecipes();
      }
    } else if (activeTab === 'my-recipes') {
      fetchMyRecipes();
    }
  }, [activeTab, fetchRecipesFromPantry, selectedFilters, myRecipesFilter]);

  // Add separate effect to handle filter and tab changes on my-recipes tab
  useEffect(() => {
    if (activeTab === 'my-recipes') {
      fetchMyRecipes();
    }
  }, [myRecipesFilter, myRecipesTab]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeTab === 'pantry') {
      await fetchRecipesFromPantry();
    } else if (activeTab === 'discover') {
      if (searchQuery) {
        await searchRecipes();
      } else {
        await fetchRandomRecipes();
      }
    } else if (activeTab === 'my-recipes') {
      await fetchMyRecipes();
    }
    setRefreshing(false);
  }, [activeTab, searchQuery, fetchRecipesFromPantry]);

  const navigateToRecipeDetail = (recipe: Recipe | SavedRecipe) => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      if (recipe.source === 'chat') {
        // Chat-generated recipes should go to recipe-details
        router.push({
          pathname: '/recipe-details',
          params: { recipe: JSON.stringify(recipe.recipe_data) },
        });
      } else {
        // Spoonacular recipes go to recipe-spoonacular-detail
        // Check if recipe_id exists (might be null for external recipes)
        const recipeId = recipe.recipe_id || recipe.recipe_data?.external_recipe_id || recipe.recipe_data?.id;
        if (recipeId) {
          router.push({
            pathname: '/recipe-spoonacular-detail',
            params: { recipeId: recipeId.toString() },
          });
        } else {
          console.error('No recipe ID found for saved recipe:', recipe);
          Alert.alert('Error', 'Unable to open recipe details');
        }
      }
    } else {
      // This is a regular recipe from search/discovery
      router.push({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: recipe.id.toString() },
      });
    }
  };

  const handleScroll = (event: any) => {
    const currentOffset = event.nativeEvent.contentOffset.y;
    const scrollDiff = currentOffset - scrollOffset;
    
    // Collapse filters when scrolling down after 30px with velocity check
    if (activeTab === 'discover') {
      if (currentOffset > 30 && scrollDiff > 2 && !filtersCollapsed) {
        // Scrolling down fast - collapse
        setFiltersCollapsed(true);
        Animated.spring(filterHeight, {
          toValue: 0,
          useNativeDriver: false,
          tension: 50,
          friction: 10,
        }).start();
      } else if ((currentOffset < 20 || scrollDiff < -5) && filtersCollapsed) {
        // Scrolling up or near top - expand
        setFiltersCollapsed(false);
        Animated.spring(filterHeight, {
          toValue: 1,
          useNativeDriver: false,
          tension: 50,
          friction: 10,
        }).start();
      }
    }
    
    setScrollOffset(currentOffset);
  };

  const renderRecipeCard = (recipe: Recipe, index: number) => (
    <View key={recipe.id} testID={`recipe-card-wrapper-${recipe.id}`} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        testID={`recipe-card-${recipe.id}`}
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(recipe)}
      >
      <Image source={{ uri: recipe.image }} style={styles.recipeImage} />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradient}
      />
      <View style={styles.recipeInfo}>
        <Text testID={`recipe-title-${recipe.id}`} style={styles.recipeTitle} numberOfLines={2}>
          {recipe.title}
        </Text>
        <View testID={`recipe-stats-${recipe.id}`} style={styles.recipeStats}>
          <View testID={`have-badge-${recipe.id}`} style={styles.stat}>
            <MaterialCommunityIcons 
              name="check-circle" 
              size={16} 
              color="#4CAF50" 
              accessibilityLabel="Ingredients available"
            />
            <Text testID={`have-count-${recipe.id}`} style={styles.statText}>{recipe.usedIngredientCount || 0} have</Text>
          </View>
          <View testID={`missing-badge-${recipe.id}`} style={styles.stat}>
            <MaterialCommunityIcons 
              name="close-circle" 
              size={16} 
              color="#F44336" 
              accessibilityLabel="Ingredients missing"
            />
            <Text testID={`missing-count-${recipe.id}`} style={styles.statText}>{recipe.missedIngredientCount || 0} missing</Text>
          </View>
        </View>
      </View>
      <TouchableOpacity 
        testID={`bookmark-button-${recipe.id}`}
        style={styles.saveButton}
        onPress={() => saveRecipe(recipe)}
      >
        <Ionicons name="bookmark-outline" size={20} color="#fff" accessibilityLabel="Save recipe" />
      </TouchableOpacity>
      </TouchableOpacity>
    </View>
  );

  const renderSavedRecipeCard = (savedRecipe: SavedRecipe, index: number) => (
    <View key={savedRecipe.id} testID={`saved-recipe-card-wrapper-${savedRecipe.id}`} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        testID={`saved-recipe-card-${savedRecipe.id}`}
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(savedRecipe)}
      >
        <Image source={{ uri: savedRecipe.recipe_image }} style={styles.recipeImage} />
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />
        <View style={styles.recipeInfo}>
          <Text testID={`saved-recipe-title-${savedRecipe.id}`} style={styles.recipeTitle} numberOfLines={2}>
            {savedRecipe.recipe_title}
          </Text>
          {/* Only show rating buttons in Cooked tab */}
          {myRecipesTab === 'cooked' && (
            <View testID={`rating-buttons-${savedRecipe.id}`} style={styles.ratingButtons}>
              <TouchableOpacity 
                testID={`thumbs-up-button-${savedRecipe.id}`}
                style={[
                  styles.ratingButton,
                  savedRecipe.rating === 'thumbs_up' && styles.ratingButtonActive
                ]}
                onPress={() => updateRecipeRating(
                  savedRecipe.id, 
                  savedRecipe.rating === 'thumbs_up' ? 'neutral' : 'thumbs_up'
                )}
              >
                <Ionicons 
                  name="thumbs-up" 
                  size={16} 
                  color={savedRecipe.rating === 'thumbs_up' ? '#4CAF50' : '#fff'} 
                  accessibilityLabel="Rate recipe positively"
                />
              </TouchableOpacity>
              <TouchableOpacity 
                testID={`thumbs-down-button-${savedRecipe.id}`}
                style={[
                  styles.ratingButton,
                  savedRecipe.rating === 'thumbs_down' && styles.ratingButtonActive
                ]}
                onPress={() => updateRecipeRating(
                  savedRecipe.id, 
                  savedRecipe.rating === 'thumbs_down' ? 'neutral' : 'thumbs_down'
                )}
              >
                <Ionicons 
                  name="thumbs-down" 
                  size={16} 
                  color={savedRecipe.rating === 'thumbs_down' ? '#F44336' : '#fff'} 
                  accessibilityLabel="Rate recipe negatively"
                />
              </TouchableOpacity>
            </View>
          )}
        </View>
        <View testID={`card-actions-${savedRecipe.id}`} style={styles.cardActions}>
          <TouchableOpacity 
            testID={`favorite-button-${savedRecipe.id}`}
            style={[styles.favoriteButton, savedRecipe.is_favorite && styles.favoriteButtonActive]}
            onPress={() => toggleFavorite(savedRecipe.id, !savedRecipe.is_favorite)}
          >
            <Ionicons 
              name={savedRecipe.is_favorite ? "heart" : "heart-outline"} 
              size={16} 
              color={savedRecipe.is_favorite ? "#FF4444" : "#fff"} 
              accessibilityLabel={savedRecipe.is_favorite ? "Remove from favorites" : "Add to favorites"}
            />
          </TouchableOpacity>
          <TouchableOpacity 
            testID={`delete-button-${savedRecipe.id}`}
            style={styles.deleteButton}
            onPress={() => deleteRecipe(savedRecipe.id)}
          >
            <Ionicons name="trash-outline" size={14} color="#fff" accessibilityLabel="Delete recipe" />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text testID="header-title" style={styles.headerTitle}>Recipes</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity testID="sort-button" onPress={() => setShowSortModal(true)} style={styles.headerButton}>
            <MaterialCommunityIcons name="sort" size={24} color="#297A56" accessibilityLabel="Sort recipes" />
          </TouchableOpacity>
          <TouchableOpacity testID="chat-button" onPress={() => router.push('/chat')} style={styles.headerButton}>
            <MaterialCommunityIcons name="chef-hat" size={24} color="#297A56" accessibilityLabel="Open recipe chat" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View testID="search-container" style={styles.searchContainer}>
        <View style={[styles.searchBar, searchFocused && styles.searchBarFocused]}>
          <Ionicons name="search" size={20} color="#666" accessibilityLabel="Search icon" />
          <TextInput
            testID="search-input"
            style={styles.searchInput}
            placeholder={`Search ${activeTab === 'pantry' ? 'pantry recipes' : activeTab === 'discover' ? 'all recipes' : 'your recipes'}...`}
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={() => activeTab === 'discover' && searchRecipes()}
            returnKeyType="search"
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity testID="clear-search-button" onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#666" accessibilityLabel="Clear search" />
            </TouchableOpacity>
          )}
        </View>
        {activeTab === 'discover' && searchQuery.length > 0 && (
          <TouchableOpacity testID="search-submit-button" style={styles.searchButton} onPress={() => searchRecipes()}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        )}
      </View>

      <View testID="tab-container" style={styles.tabContainer}>
        <TouchableOpacity
          testID="pantry-tab"
          style={[styles.tab, activeTab === 'pantry' && styles.activeTab]}
          onPress={() => setActiveTab('pantry')}
        >
          <Text style={[styles.tabText, activeTab === 'pantry' && styles.activeTabText]}>
            From Pantry
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="discover-tab"
          style={[styles.tab, activeTab === 'discover' && styles.activeTab]}
          onPress={() => setActiveTab('discover')}
        >
          <Text style={[styles.tabText, activeTab === 'discover' && styles.activeTabText]}>
            Discover
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="my-recipes-tab"
          style={[styles.tab, activeTab === 'my-recipes' && styles.activeTab]}
          onPress={() => setActiveTab('my-recipes')}
        >
          <Text style={[styles.tabText, activeTab === 'my-recipes' && styles.activeTabText]}>
            My Recipes
          </Text>
        </TouchableOpacity>
      </View>

      {/* Filter Grid */}
      {activeTab === 'my-recipes' ? (
        <View style={styles.myRecipesTabContainer}>
          {/* Saved/Cooked Tabs */}
          <View testID="my-recipes-tabs" style={styles.myRecipesTabs}>
            <TouchableOpacity
              testID="saved-tab"
              style={[
                styles.myRecipesTab,
                myRecipesTab === 'saved' && styles.myRecipesTabActive
              ]}
              onPress={() => {
                setMyRecipesTab('saved');
                setMyRecipesFilter('all'); // Reset filter when switching tabs
              }}
            >
              <Text style={[
                styles.myRecipesTabText,
                myRecipesTab === 'saved' && styles.myRecipesTabTextActive
              ]}>
                🔖 Saved
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="cooked-tab"
              style={[
                styles.myRecipesTab,
                myRecipesTab === 'cooked' && styles.myRecipesTabActive
              ]}
              onPress={() => {
                setMyRecipesTab('cooked');
                setMyRecipesFilter('all'); // Reset filter when switching tabs
              }}
            >
              <Text style={[
                styles.myRecipesTabText,
                myRecipesTab === 'cooked' && styles.myRecipesTabTextActive
              ]}>
                🍳 Cooked
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Only show rating filters in Cooked tab */}
          {myRecipesTab === 'cooked' && (
            <View style={styles.filterContainer}>
              <ScrollView 
                horizontal
                style={styles.filterScrollView}
                contentContainerStyle={styles.filterContent}
                showsHorizontalScrollIndicator={false}
              >
                <TouchableOpacity
                  testID="filter-all"
                  style={[
                    styles.filterButton,
                    myRecipesFilter === 'all' && styles.filterButtonActive
                  ]}
                  onPress={() => setMyRecipesFilter('all')}
                >
                  <Text style={styles.filterIcon}>📋</Text>
                  <Text style={[
                    styles.filterText,
                    myRecipesFilter === 'all' && styles.filterTextActive
                  ]}>
                    All
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  testID="filter-thumbs-up"
                  style={[
                    styles.filterButton,
                    myRecipesFilter === 'thumbs_up' && styles.filterButtonActive
                  ]}
                  onPress={() => setMyRecipesFilter('thumbs_up')}
                >
                  <Text style={styles.filterIcon}>👍</Text>
                  <Text style={[
                    styles.filterText,
                    myRecipesFilter === 'thumbs_up' && styles.filterTextActive
                  ]}>
                    Liked
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  testID="filter-thumbs-down"
                  style={[
                    styles.filterButton,
                    myRecipesFilter === 'thumbs_down' && styles.filterButtonActive
                  ]}
                  onPress={() => setMyRecipesFilter('thumbs_down')}
                >
                  <Text style={styles.filterIcon}>👎</Text>
                  <Text style={[
                    styles.filterText,
                    myRecipesFilter === 'thumbs_down' && styles.filterTextActive
                  ]}>
                    Disliked
                  </Text>
                </TouchableOpacity>
              </ScrollView>
            </View>
          )}
        </View>
      ) : activeTab === 'discover' ? (
        <Animated.View 
          style={[
            styles.discoverFiltersContainer,
            {
              maxHeight: filterHeight.interpolate({
                inputRange: [0, 1],
                outputRange: [32, 150],
              }),
            }
          ]}
        >
          <TouchableOpacity 
            style={styles.collapsedFilterBar}
            onPress={() => {
              if (filtersCollapsed) {
                setFiltersCollapsed(false);
                Animated.timing(filterHeight, {
                  toValue: 1,
                  duration: 300,
                  useNativeDriver: false,
                }).start();
              }
            }}
            activeOpacity={filtersCollapsed ? 0.7 : 1}
          >
            {selectedFilters.length > 0 && (
              <Text style={styles.collapsedFilterText}>
                {selectedFilters.length} filters active
              </Text>
            )}
            <Animated.View
              style={{
                transform: [{
                  rotate: filterHeight.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0deg', '180deg'],
                  })
                }]
              }}
            >
              <Ionicons name="chevron-down" size={20} color="#666" />
            </Animated.View>
          </TouchableOpacity>
          <Animated.View
            style={{
              opacity: filterHeight,
              transform: [{
                translateY: filterHeight.interpolate({
                  inputRange: [0, 1],
                  outputRange: [-20, 0],
                })
              }]
            }}
          >
          {/* Dietary Filters Row */}
          <View style={styles.filterRow}>
            <ScrollView 
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.filterRowContent}
            >
              {dietaryFilters.map(filter => (
                <TouchableOpacity
                  key={filter.id}
                  testID={`dietary-filter-${filter.id}`}
                  style={[
                    styles.filterButton,
                    selectedFilters.includes(filter.id) && styles.filterButtonActive
                  ]}
                  onPress={() => toggleFilter(filter.id)}
                >
                  <Text style={styles.filterIcon}>{filter.icon}</Text>
                  <Text style={[
                    styles.filterText,
                    selectedFilters.includes(filter.id) && styles.filterTextActive
                  ]}>
                    {filter.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Cuisine Filters Row */}
          <View style={styles.filterRow}>
            <ScrollView 
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.filterRowContent}
            >
              {cuisineFilters.map(filter => (
                <TouchableOpacity
                  key={filter.id}
                  testID={`cuisine-filter-${filter.id}`}
                  style={[
                    styles.filterButton,
                    selectedFilters.includes(filter.id) && styles.filterButtonActive
                  ]}
                  onPress={() => toggleFilter(filter.id)}
                >
                  <Text style={styles.filterIcon}>{filter.icon}</Text>
                  <Text style={[
                    styles.filterText,
                    selectedFilters.includes(filter.id) && styles.filterTextActive
                  ]}>
                    {filter.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Meal Type Filters Row */}
          <View style={styles.filterRow}>
            <ScrollView 
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.filterRowContent}
            >
              {mealTypeFilters.map(filter => (
                <TouchableOpacity
                  key={filter.id}
                  testID={`meal-type-filter-${filter.id}`}
                  style={[
                    styles.filterButton,
                    selectedFilters.includes(filter.id) && styles.filterButtonActive
                  ]}
                  onPress={() => toggleFilter(filter.id)}
                >
                  <Text style={styles.filterIcon}>{filter.icon}</Text>
                  <Text style={[
                    styles.filterText,
                    selectedFilters.includes(filter.id) && styles.filterTextActive
                  ]}>
                    {filter.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
          </Animated.View>
        </Animated.View>
      ) : activeTab === 'pantry' ? (
        <View style={styles.filterContainer}>
          <ScrollView 
            horizontal
            style={styles.filterScrollView}
            contentContainerStyle={styles.filterContent}
            showsHorizontalScrollIndicator={false}
          >
            {mealTypeFilters.slice(0, 4).map(filter => (
              <TouchableOpacity
                key={filter.id}
                testID={`pantry-filter-${filter.id}`}
                style={[
                  styles.filterButton,
                  selectedFilters.includes(filter.id) && styles.filterButtonActive
                ]}
                onPress={() => toggleFilter(filter.id)}
              >
                <Text style={styles.filterIcon}>{filter.icon}</Text>
                <Text style={[
                  styles.filterText,
                  selectedFilters.includes(filter.id) && styles.filterTextActive
                ]}>
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      ) : null}

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#297A56" />
          <Text style={styles.loadingText}>
            {activeTab === 'my-recipes' ? 'Loading your saved recipes...' : 'Finding delicious recipes...'}
          </Text>
        </View>
      ) : (
        <ScrollView
          testID="recipes-scroll-view"
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={['#297A56']}
              tintColor="#297A56"
            />
          }
          showsVerticalScrollIndicator={false}
        >
          {activeTab === 'my-recipes' ? (
            getFilteredSavedRecipes().length === 0 ? (
              <View testID="empty-my-recipes" style={styles.emptyContainer}>
                <MaterialCommunityIcons name="bookmark-off" size={64} color="#ccc" accessibilityLabel="No saved recipes" />
                <Text testID="empty-my-recipes-text" style={styles.emptyText}>
                  {searchQuery 
                    ? `No recipes found matching "${searchQuery}"`
                    : myRecipesTab === 'saved'
                    ? 'Bookmarks save recipes you want to try. Tap the bookmark icon on any recipe to add one.'
                    : myRecipesTab === 'cooked' && myRecipesFilter === 'all'
                    ? 'Nothing cooked yet. After you finish cooking a recipe it will appear here, ready for you to rate.'
                    : myRecipesFilter === 'thumbs_up'
                    ? 'No liked recipes yet. Cook some recipes and rate them!'
                    : myRecipesFilter === 'thumbs_down'
                    ? 'No disliked recipes yet.'
                    : 'No recipes found'}
                </Text>
              </View>
            ) : (
              <View testID="my-recipes-grid" style={styles.recipesGrid}>
                {getFilteredSavedRecipes().map((recipe, index) => renderSavedRecipeCard(recipe, index))}
              </View>
            )
          ) : (
            getFilteredRecipes().length === 0 ? (
              <View testID="empty-recipes" style={styles.emptyContainer}>
                <MaterialCommunityIcons name="food-off" size={64} color="#ccc" accessibilityLabel="No recipes found" />
                <Text testID="empty-recipes-text" style={styles.emptyText}>
                  {searchQuery
                    ? `No recipes found matching "${searchQuery}"`
                    : activeTab === 'pantry'
                    ? 'No recipes found with your pantry items'
                    : 'Pull to refresh for new recipes'}
                </Text>
              </View>
            ) : (
              <View testID="recipes-grid" style={styles.recipesGrid}>
                {getFilteredRecipes().map((recipe, index) => renderRecipeCard(recipe, index))}
              </View>
            )
          )}
        </ScrollView>
      )}

      {/* Sort Modal */}
      <Modal
        testID="sort-modal"
        visible={showSortModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSortModal(false)}
      >
        <Pressable testID="sort-modal-overlay" style={styles.modalOverlay} onPress={() => setShowSortModal(false)}>
          <View testID="sort-modal-content" style={styles.modalContent}>
            <Text testID="sort-modal-title" style={styles.modalTitle}>Sort By</Text>
            {sortOptions.map(option => (
              <TouchableOpacity
                key={option.value}
                testID={`sort-option-${option.value}`}
                style={[styles.sortOption, sortBy === option.value && styles.sortOptionActive]}
                onPress={() => {
                  setSortBy(option.value as SortOption);
                  setShowSortModal(false);
                }}
              >
                <MaterialCommunityIcons 
                  name={option.icon as any} 
                  size={24} 
                  color={sortBy === option.value ? '#297A56' : '#666'} 
                  accessibilityLabel={`Sort by ${option.label}`}
                />
                <Text style={[
                  styles.sortOptionText,
                  sortBy === option.value && styles.sortOptionTextActive
                ]}>
                  {option.label}
                </Text>
                {sortBy === option.value && (
                  <Ionicons name="checkmark" size={24} color="#297A56" accessibilityLabel="Selected" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#297A56',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerButton: {
    padding: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 40,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  searchBarFocused: {
    borderColor: '#297A56',
    backgroundColor: '#fff',
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  searchButton: {
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#297A56',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#297A56',
    fontWeight: '600',
  },
  filterContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  myRecipesTabContainer: {
    backgroundColor: '#fff',
  },
  myRecipesTabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  myRecipesTab: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  myRecipesTabActive: {
    backgroundColor: '#297A56',
  },
  myRecipesTabText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  myRecipesTabTextActive: {
    color: '#fff',
  },
  discoverFiltersContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    overflow: 'hidden',
  },
  collapsedFilterBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    height: 32,
  },
  collapsedFilterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
    marginRight: 8,
  },
  filterRow: {
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  filterRowTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  filterRowContent: {
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  filterScrollView: {
    flexGrow: 0,
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
    minWidth: 90,
    justifyContent: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#E6F7F0',
    borderWidth: 1,
    borderColor: '#297A56',
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  filterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#297A56',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  recipeCardWrapper: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  recipeCard: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 100,
  },
  recipeInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  recipeStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#fff',
  },
  saveButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20,
    padding: 8,
  },
  deleteButton: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
    borderRadius: 16,
    padding: 6,
  },
  ratingButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  ratingButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 16,
    padding: 6,
    paddingHorizontal: 10,
  },
  ratingButtonActive: {
    backgroundColor: 'rgba(255,255,255,0.9)',
  },
  cardActions: {
    position: 'absolute',
    top: 8,
    right: 8,
    flexDirection: 'row',
    gap: 6,
  },
  favoriteButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 16,
    padding: 6,
  },
  favoriteButtonActive: {
    backgroundColor: 'rgba(255,255,255,0.9)',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 10,
    marginBottom: 8,
  },
  sortOptionActive: {
    backgroundColor: '#E6F7F0',
  },
  sortOptionText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    marginLeft: 16,
  },
  sortOptionTextActive: {
    color: '#297A56',
    fontWeight: '600',
  },
});