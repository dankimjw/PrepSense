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
  source: string;
  created_at: string;
  updated_at: string;
}

export default function RecipesScreen() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [savedRecipes, setSavedRecipes] = useState<SavedRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'pantry' | 'search' | 'random' | 'my-recipes'>('pantry');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [myRecipesFilter, setMyRecipesFilter] = useState<'all' | 'thumbs_up' | 'thumbs_down'>('all');
  
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

  const searchRecipes = async () => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
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

      const filterParam = myRecipesFilter !== 'all' ? `?rating_filter=${myRecipesFilter}` : '';
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

  useEffect(() => {
    if (activeTab === 'pantry') {
      fetchRecipesFromPantry();
    } else if (activeTab === 'random') {
      fetchRandomRecipes();
    } else if (activeTab === 'search' && searchQuery) {
      searchRecipes();
    } else if (activeTab === 'my-recipes') {
      fetchMyRecipes();
    }
  }, [activeTab, fetchRecipesFromPantry, selectedFilters, myRecipesFilter]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeTab === 'pantry') {
      await fetchRecipesFromPantry();
    } else if (activeTab === 'random') {
      await fetchRandomRecipes();
    } else if (activeTab === 'search' && searchQuery) {
      await searchRecipes();
    } else if (activeTab === 'my-recipes') {
      await fetchMyRecipes();
    }
    setRefreshing(false);
  }, [activeTab, searchQuery, fetchRecipesFromPantry]);

  const navigateToRecipeDetail = (recipe: Recipe | SavedRecipe) => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      router.push({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: recipe.recipe_id.toString() },
      });
    } else {
      // This is a regular recipe
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
          {recipe.likes && (
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
        <TouchableOpacity 
          style={styles.deleteButton}
          onPress={() => deleteRecipe(savedRecipe.id)}
        >
          <Ionicons name="trash-outline" size={18} color="#fff" />
        </TouchableOpacity>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recipes</Text>
        <TouchableOpacity onPress={() => router.push('/chat')}>
          <MaterialCommunityIcons name="chef-hat" size={24} color="#297A56" />
        </TouchableOpacity>
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
          style={[styles.tab, activeTab === 'search' && styles.activeTab]}
          onPress={() => setActiveTab('search')}
        >
          <Text style={[styles.tabText, activeTab === 'search' && styles.activeTabText]}>
            Search
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'random' && styles.activeTab]}
          onPress={() => setActiveTab('random')}
        >
          <Text style={[styles.tabText, activeTab === 'random' && styles.activeTabText]}>
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

      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        {activeTab === 'my-recipes' ? (
          <>
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
          </>
        ) : (
          dietaryFilters.map(filter => (
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
          ))
        )}
      </ScrollView>

      {activeTab === 'search' && (
        <View style={styles.searchContainer}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#666" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search recipes..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={searchRecipes}
              returnKeyType="search"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={20} color="#666" />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity style={styles.searchButton} onPress={searchRecipes}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>
      )}

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
            savedRecipes.length === 0 ? (
              <View style={styles.emptyContainer}>
                <MaterialCommunityIcons name="bookmark-off" size={64} color="#ccc" />
                <Text style={styles.emptyText}>
                  {myRecipesFilter === 'all' 
                    ? 'No saved recipes yet. Save recipes from other tabs to see them here!'
                    : `No ${myRecipesFilter === 'thumbs_up' ? 'liked' : 'disliked'} recipes found`}
                </Text>
              </View>
            ) : (
              <View style={styles.recipesGrid}>
                {savedRecipes.map((recipe, index) => renderSavedRecipeCard(recipe, index))}
              </View>
            )
          ) : (
            recipes.length === 0 ? (
              <View style={styles.emptyContainer}>
                <MaterialCommunityIcons name="food-off" size={64} color="#ccc" />
                <Text style={styles.emptyText}>
                  {activeTab === 'pantry'
                    ? 'No recipes found with your pantry items'
                    : activeTab === 'search'
                    ? 'Search for recipes by name or ingredient'
                    : 'Pull to refresh for new recipes'}
                </Text>
              </View>
            ) : (
              <View style={styles.recipesGrid}>
                {recipes.map((recipe, index) => renderRecipeCard(recipe, index))}
              </View>
            )
          )}
        </ScrollView>
      )}
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
    maxHeight: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
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
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 10,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 40,
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
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
    borderRadius: 20,
    padding: 8,
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
});