import React, { useMemo, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  RefreshControl,
  Alert,
  Animated,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Router } from 'expo-router';
import { Config } from '../../config';

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
type MyRecipesTab = 'saved' | 'cooked';

interface RecipesListProps {
  recipes: Recipe[];
  savedRecipes: SavedRecipe[];
  loading: boolean;
  refreshing: boolean;
  searchQuery: string;
  activeTab: ActiveTab;
  myRecipesTab: MyRecipesTab;
  sortBy: SortOption;
  scrollOffset: number;
  filtersCollapsed: boolean;
  onRefresh: () => Promise<void>;
  onScrollOffsetChange: (offset: number) => void;
  onFiltersCollapsedChange: (collapsed: boolean) => void;
  onSavedRecipeUpdate: (id: string, updates: Partial<SavedRecipe>) => void;
  fetchMyRecipes: () => Promise<void>;
  router: Router;
}

export default function RecipesList({
  recipes,
  savedRecipes,
  loading,
  refreshing,
  searchQuery,
  activeTab,
  myRecipesTab,
  sortBy,
  scrollOffset,
  filtersCollapsed,
  onRefresh,
  onScrollOffsetChange,
  onFiltersCollapsedChange,
  onSavedRecipeUpdate,
  fetchMyRecipes,
  router,
}: RecipesListProps) {
  const filterHeight = useRef(new Animated.Value(1)).current;

  // Memoize filtered recipes to prevent unnecessary recalculations
  const filteredRecipes = useMemo(() => {
    let filtered = [...recipes];
    
    if (searchQuery && activeTab === 'pantry') {
      filtered = recipes.filter(recipe => 
        recipe.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Sort recipes
    if (sortBy === 'name') {
      filtered.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sortBy === 'missing') {
      filtered.sort((a, b) => 
        (a.missedIngredientCount || 0) - (b.missedIngredientCount || 0)
      );
    }
    
    return filtered;
  }, [recipes, searchQuery, activeTab, sortBy]);

  // Memoize filtered saved recipes to prevent unnecessary recalculations
  const filteredSavedRecipes = useMemo(() => {
    let filtered = [...savedRecipes];
    
    if (searchQuery) {
      filtered = savedRecipes.filter(recipe => 
        recipe.recipe_title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Sort recipes
    if (sortBy === 'name') {
      filtered.sort((a, b) => a.recipe_title.localeCompare(b.recipe_title));
    } else if (sortBy === 'date') {
      filtered.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    } else if (sortBy === 'rating') {
      filtered.sort((a, b) => {
        const ratingOrder = { thumbs_up: 2, neutral: 1, thumbs_down: 0 };
        return ratingOrder[b.rating] - ratingOrder[a.rating];
      });
    }
    
    return filtered;
  }, [savedRecipes, searchQuery, sortBy]);

  const saveRecipe = async (recipe: Recipe) => {
    try {
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: {
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
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/rating`, {
        method: 'PUT',
        headers: {
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
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/favorite`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_favorite: isFavorite }),
      });

      if (!response.ok) {
        throw new Error('Failed to update favorite status');
      }
      
      // Update local state
      onSavedRecipeUpdate(recipeId, { is_favorite: isFavorite });
      
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
        onFiltersCollapsedChange(true);
        Animated.spring(filterHeight, {
          toValue: 0,
          useNativeDriver: false,
          tension: 50,
          friction: 10,
        }).start();
      } else if ((currentOffset < 20 || scrollDiff < -5) && filtersCollapsed) {
        // Scrolling up or near top - expand
        onFiltersCollapsedChange(false);
        Animated.spring(filterHeight, {
          toValue: 1,
          useNativeDriver: false,
          tension: 50,
          friction: 10,
        }).start();
      }
    }
    
    onScrollOffsetChange(currentOffset);
  };

  const getRecipeImageUri = (recipe: Recipe | SavedRecipe) => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe - use recipe_image first, then recipe_data.image as fallback
      return recipe.recipe_image || recipe.recipe_data?.image || 'https://via.placeholder.com/300x200?text=No+Image';
    } else {
      // This is a regular recipe
      return recipe.image || 'https://via.placeholder.com/300x200?text=No+Image';
    }
  };

  const renderRecipeCard = (recipe: Recipe, index: number) => (
    <View key={recipe.id} testID={`recipe-card-wrapper-${recipe.id}`} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        testID={`recipe-card-${recipe.id}`}
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(recipe)}
      >
      <Image source={{ uri: getRecipeImageUri(recipe) }} style={styles.recipeImage} />
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
        <Image source={{ uri: getRecipeImageUri(savedRecipe) }} style={styles.recipeImage} />
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

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
        <Text style={styles.loadingText}>
          {activeTab === 'my-recipes' ? 'Loading your saved recipes...' : 'Finding delicious recipes...'}
        </Text>
      </View>
    );
  }

  return (
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
        filteredSavedRecipes.length === 0 ? (
          <View testID="empty-my-recipes" style={styles.emptyContainer}>
            <MaterialCommunityIcons name="bookmark-off" size={64} color="#ccc" accessibilityLabel="No saved recipes" />
            <Text testID="empty-my-recipes-text" style={styles.emptyText}>
              {searchQuery 
                ? `No recipes found matching "${searchQuery}"`
                : myRecipesTab === 'saved'
                ? 'Bookmarks save recipes you want to try. Tap the bookmark icon on any recipe to add one.'
                : myRecipesTab === 'cooked'
                ? 'Nothing cooked yet. After you finish cooking a recipe it will appear here, ready for you to rate.'
                : 'No recipes found'}
            </Text>
          </View>
        ) : (
          <View testID="my-recipes-grid" style={styles.recipesGrid}>
            {filteredSavedRecipes.map((recipe, index) => renderSavedRecipeCard(recipe, index))}
          </View>
        )
      ) : (
        filteredRecipes.length === 0 ? (
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
            {filteredRecipes.map((recipe, index) => renderRecipeCard(recipe, index))}
          </View>
        )
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
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
});