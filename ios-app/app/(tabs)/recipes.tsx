import React, { useState, useEffect, useCallback } from 'react';
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
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Config } from '../../config';
import { useItems } from '../../context/ItemsContext';
import { useAuth } from '../../context/AuthContext';

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
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [showSortModal, setShowSortModal] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);
  
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

  const fetchRecipesFromPantry = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111, // Default demo user
          max_missing_ingredients: 5,
          use_expiring_first: true,
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
        throw new Error('Failed to fetch recipes');
      }
      
      const data = await response.json();
      setRecipes(data.recipes || []);
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
      setRecipes(data.results || []);
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
      setRecipes(data.recipes || []);
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
      if (!token || !isAuthenticated) {
        Alert.alert('Error', 'Please login to view your saved recipes.');
        return;
      }

      let filterParam = '';
      if (myRecipesFilter === 'favorites') {
        filterParam = '?is_favorite=true';
      } else if (myRecipesFilter !== 'all') {
        filterParam = `?rating_filter=${myRecipesFilter}`;
      }
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes${filterParam}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch saved recipes');
      }
      
      const data = await response.json();
      setSavedRecipes(data.recipes || []);
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      Alert.alert('Error', 'Failed to load saved recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveRecipe = async (recipe: Recipe) => {
    try {
      if (!token || !isAuthenticated) {
        Alert.alert('Error', 'Please login to save recipes.');
        return;
      }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
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
      
      Alert.alert('Success', 'Recipe saved to your collection!');
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe. Please try again.');
    }
  };

  const updateRecipeRating = async (recipeId: string, rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => {
    try {
      if (!token || !isAuthenticated) {
        Alert.alert('Error', 'Please login to rate recipes.');
        return;
      }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/rating`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
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
      if (!token || !isAuthenticated) {
        Alert.alert('Error', 'Please login to favorite recipes.');
        return;
      }

      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/favorite`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
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
      if (!token || !isAuthenticated) {
        Alert.alert('Error', 'Please login to delete recipes.');
        return;
      }

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
                  'Authorization': `Bearer ${token}`,
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
        router.push({
          pathname: '/recipe-spoonacular-detail',
          params: { recipeId: recipe.recipe_id.toString() },
        });
      }
    } else {
      // This is a regular recipe from search/discovery
      router.push({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: recipe.id.toString() },
      });
    }
  };

  const renderRecipeCard = (recipe: Recipe, index: number) => (
    <View key={recipe.id} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(recipe)}
      >
      <Image source={{ uri: recipe.image }} style={styles.recipeImage} />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradient}
      />
      <View style={styles.recipeInfo}>
        <Text style={styles.recipeTitle} numberOfLines={2}>
          {recipe.title}
        </Text>
        <View style={styles.recipeStats}>
          <View style={styles.stat}>
            <MaterialCommunityIcons name="check-circle" size={16} color="#4CAF50" />
            <Text style={styles.statText}>{recipe.usedIngredientCount || 0} have</Text>
          </View>
          <View style={styles.stat}>
            <MaterialCommunityIcons name="close-circle" size={16} color="#F44336" />
            <Text style={styles.statText}>{recipe.missedIngredientCount || 0} missing</Text>
          </View>
          {recipe.likes > 0 && (
            <View style={styles.stat}>
              <MaterialCommunityIcons name="heart" size={16} color="#E91E63" />
              <Text style={styles.statText}>{recipe.likes}</Text>
            </View>
          )}
        </View>
      </View>
      <TouchableOpacity 
        style={styles.saveButton}
        onPress={() => saveRecipe(recipe)}
      >
        <Ionicons name="bookmark-outline" size={20} color="#fff" />
      </TouchableOpacity>
      </TouchableOpacity>
    </View>
  );

  const renderSavedRecipeCard = (savedRecipe: SavedRecipe, index: number) => (
    <View key={savedRecipe.id} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(savedRecipe)}
      >
        <Image source={{ uri: savedRecipe.recipe_image }} style={styles.recipeImage} />
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {savedRecipe.recipe_title}
          </Text>
          <View style={styles.ratingButtons}>
            <TouchableOpacity 
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
              />
            </TouchableOpacity>
            <TouchableOpacity 
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
              />
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.cardActions}>
          <TouchableOpacity 
            style={[styles.favoriteButton, savedRecipe.is_favorite && styles.favoriteButtonActive]}
            onPress={() => toggleFavorite(savedRecipe.id, !savedRecipe.is_favorite)}
          >
            <Ionicons 
              name={savedRecipe.is_favorite ? "heart" : "heart-outline"} 
              size={16} 
              color={savedRecipe.is_favorite ? "#FF4444" : "#fff"} 
            />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.deleteButton}
            onPress={() => deleteRecipe(savedRecipe.id)}
          >
            <Ionicons name="trash-outline" size={14} color="#fff" />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recipes</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={() => setShowSortModal(true)} style={styles.headerButton}>
            <MaterialCommunityIcons name="sort" size={24} color="#297A56" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => router.push('/chat')} style={styles.headerButton}>
            <MaterialCommunityIcons name="chef-hat" size={24} color="#297A56" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={[styles.searchBar, searchFocused && styles.searchBarFocused]}>
          <Ionicons name="search" size={20} color="#666" />
          <TextInput
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
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#666" />
            </TouchableOpacity>
          )}
        </View>
        {activeTab === 'discover' && searchQuery.length > 0 && (
          <TouchableOpacity style={styles.searchButton} onPress={() => searchRecipes()}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'pantry' && styles.activeTab]}
          onPress={() => setActiveTab('pantry')}
        >
          <Text style={[styles.tabText, activeTab === 'pantry' && styles.activeTabText]}>
            From Pantry
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'discover' && styles.activeTab]}
          onPress={() => setActiveTab('discover')}
        >
          <Text style={[styles.tabText, activeTab === 'discover' && styles.activeTabText]}>
            Discover
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'my-recipes' && styles.activeTab]}
          onPress={() => setActiveTab('my-recipes')}
        >
          <Text style={[styles.tabText, activeTab === 'my-recipes' && styles.activeTabText]}>
            My Recipes
          </Text>
        </TouchableOpacity>
      </View>

      {/* Filter Grid */}
      <View style={[styles.filterContainer, activeTab === 'discover' && filtersCollapsed && styles.filterContainerCollapsed]}>
        {activeTab === 'discover' && (
          <TouchableOpacity 
            style={styles.filterToggle}
            onPress={() => setFiltersCollapsed(!filtersCollapsed)}
          >
            <Text style={styles.filterToggleText}>
              {filtersCollapsed ? 'Show Filters' : 'Hide Filters'}
            </Text>
            <Ionicons 
              name={filtersCollapsed ? "chevron-down" : "chevron-up"} 
              size={20} 
              color="#666" 
            />
          </TouchableOpacity>
        )}
        {!filtersCollapsed && (
          <ScrollView 
            style={styles.filterScrollView}
            contentContainerStyle={styles.filterContent}
            showsHorizontalScrollIndicator={false}
            showsVerticalScrollIndicator={false}
          >
          {activeTab === 'my-recipes' ? (
          <View style={[styles.filterGrid, { paddingHorizontal: 16, marginHorizontal: 0 }]}>
            <TouchableOpacity
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
              style={[
                styles.filterButton,
                myRecipesFilter === 'favorites' && styles.filterButtonActive
              ]}
              onPress={() => setMyRecipesFilter('favorites')}
            >
              <Text style={styles.filterIcon}>❤️</Text>
              <Text style={[
                styles.filterText,
                myRecipesFilter === 'favorites' && styles.filterTextActive
              ]}>
                Favorites
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
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
          </View>
        ) : activeTab === 'discover' ? (
          <>
            {/* Dietary Filters Row */}
            <View style={[styles.filterSection, { paddingHorizontal: 16 }]}>
              <Text style={styles.filterSectionTitle}>Dietary</Text>
              <View style={styles.filterGrid}>
                {dietaryFilters.map(filter => (
                  <TouchableOpacity
                    key={filter.id}
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
              </View>
            </View>

            {/* Cuisine Filters Row */}
            <View style={[styles.filterSection, { paddingHorizontal: 16 }]}>
              <Text style={styles.filterSectionTitle}>Cuisine</Text>
              <View style={styles.filterGrid}>
                {cuisineFilters.map(filter => (
                  <TouchableOpacity
                    key={filter.id}
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
              </View>
            </View>

            {/* Meal Type Filters Row */}
            <View style={[styles.filterSection, { paddingHorizontal: 16 }]}>
              <Text style={styles.filterSectionTitle}>Meal Type</Text>
              <View style={styles.filterGrid}>
                {mealTypeFilters.map(filter => (
                  <TouchableOpacity
                    key={filter.id}
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
              </View>
            </View>
          </>
        ) : activeTab === 'pantry' ? (
          <View style={[styles.filterGrid, { paddingHorizontal: 16, marginHorizontal: 0 }]}>
            {mealTypeFilters.slice(0, 4).map(filter => (
              <TouchableOpacity
                key={filter.id}
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
          </View>
        ) : null}
        </ScrollView>
        )}
      </View>

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#297A56" />
          <Text style={styles.loadingText}>
            {activeTab === 'my-recipes' ? 'Loading your saved recipes...' : 'Finding delicious recipes...'}
          </Text>
        </View>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
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
              <View style={styles.emptyContainer}>
                <MaterialCommunityIcons name="bookmark-off" size={64} color="#ccc" />
                <Text style={styles.emptyText}>
                  {searchQuery 
                    ? `No recipes found matching "${searchQuery}"`
                    : myRecipesFilter === 'all' 
                    ? 'No saved recipes yet. Save recipes from other tabs to see them here!'
                    : myRecipesFilter === 'favorites'
                    ? 'No favorite recipes yet. Tap the heart icon on recipes you love!'
                    : `No ${myRecipesFilter === 'thumbs_up' ? 'liked' : 'disliked'} recipes found`}
                </Text>
              </View>
            ) : (
              <View style={styles.recipesGrid}>
                {getFilteredSavedRecipes().map((recipe, index) => renderSavedRecipeCard(recipe, index))}
              </View>
            )
          ) : (
            getFilteredRecipes().length === 0 ? (
              <View style={styles.emptyContainer}>
                <MaterialCommunityIcons name="food-off" size={64} color="#ccc" />
                <Text style={styles.emptyText}>
                  {searchQuery
                    ? `No recipes found matching "${searchQuery}"`
                    : activeTab === 'pantry'
                    ? 'No recipes found with your pantry items'
                    : 'Pull to refresh for new recipes'}
                </Text>
              </View>
            ) : (
              <View style={styles.recipesGrid}>
                {getFilteredRecipes().map((recipe, index) => renderRecipeCard(recipe, index))}
              </View>
            )
          )}
        </ScrollView>
      )}

      {/* Sort Modal */}
      <Modal
        visible={showSortModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSortModal(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setShowSortModal(false)}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Sort By</Text>
            {sortOptions.map(option => (
              <TouchableOpacity
                key={option.value}
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
                />
                <Text style={[
                  styles.sortOptionText,
                  sortBy === option.value && styles.sortOptionTextActive
                ]}>
                  {option.label}
                </Text>
                {sortBy === option.value && (
                  <Ionicons name="checkmark" size={24} color="#297A56" />
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
  filterContainerCollapsed: {
    maxHeight: 50,
  },
  filterToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  filterToggleText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
    marginRight: 8,
  },
  filterScrollView: {
    maxHeight: 150,
  },
  filterContent: {
    paddingVertical: 10,
  },
  filterSection: {
    marginBottom: 12,
  },
  filterSectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 0,
  },
  filterGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginHorizontal: 4,
    marginBottom: 8,
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