import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Dimensions,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import * as api from '../../services/api';

const { width } = Dimensions.get('window');

interface Recipe {
  id: number;
  title: string;
  image?: string;
  summary?: string;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
  spoonacularSourceUrl?: string;
  usedIngredients?: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  missedIngredients?: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
}

interface SavedRecipe {
  id: number;
  user_id: number;
  recipe_id?: number;
  source: 'spoonacular' | 'chat' | 'openai';
  recipe_data: any;
  created_at: string;
  updated_at: string;
  rating?: 'thumbs_up' | 'thumbs_down' | 'neutral';
  is_favorite?: boolean;
}

interface RecipesListProps {
  recipes: (Recipe | SavedRecipe)[];
  isLoading: boolean;
  onRefresh: () => void;
  refreshing: boolean;
  listType: 'fromPantry' | 'myRecipes';
}

const RecipesList: React.FC<RecipesListProps> = ({
  recipes,
  isLoading,
  onRefresh,
  refreshing,
  listType,
}) => {
  const [deletingRecipeId, setDeletingRecipeId] = useState<number | null>(null);

  const deleteRecipe = async (recipeId: number) => {
    try {
      setDeletingRecipeId(recipeId);
      await api.deleteRecipe(recipeId);
      await onRefresh(); // Refresh the list to remove the deleted recipe
    } catch (error) {
      console.error('Error deleting recipe:', error);
      Alert.alert('Error', 'Failed to delete recipe. Please try again.');
    } finally {
      setDeletingRecipeId(null);
    }
  };

  const confirmDelete = (recipeId: number, recipeName: string) => {
    Alert.alert(
      'Delete Recipe',
      `Are you sure you want to delete "${recipeName}"?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteRecipe(recipeId),
        },
      ],
      { cancelable: true }
    );
  };

  const saveRecipe = async (recipe: Recipe) => {
    try {
      const response = await fetch(`${api.Config?.API_BASE_URL || 'http://127.0.0.1:8002/api/v1'}/user-recipes`, {
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
      
      Alert.alert('Success', 'Recipe saved to My Recipes!');
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe. Please try again.');
    }
  };

  const getRecipeTitle = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      return recipe.recipe_data?.title || recipe.recipe_data?.name || 'Untitled Recipe';
    }
    // This is a regular recipe
    return recipe.title || 'Untitled Recipe';
  };

  const getRecipeImage = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      return recipe.recipe_data?.image || recipe.recipe_data?.image_url || '';
    }
    // This is a regular recipe
    return recipe.image || '';
  };

  const getIngredientCounts = (recipe: Recipe | SavedRecipe) => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe - try to get ingredient count from recipe_data
      const ingredients = recipe.recipe_data?.ingredients || recipe.recipe_data?.extendedIngredients || [];
      return {
        have: ingredients.length,
        missing: 0
      };
    }
    // This is a regular recipe from Spoonacular
    return {
      have: recipe.usedIngredientCount || 0,
      missing: recipe.missedIngredientCount || 0
    };
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
      if (recipe.id) {
        router.push({
          pathname: '/recipe-spoonacular-detail',
          params: { recipeId: recipe.id.toString() },
        });
      } else {
        console.error('No recipe ID found for regular recipe:', recipe);
        Alert.alert('Error', 'Unable to open recipe details - missing recipe ID');
      }
    }
  };

  const toggleFavorite = async (recipeId: number, isFavorite: boolean) => {
    try {
      const response = await fetch(`${api.Config?.API_BASE_URL || 'http://127.0.0.1:8002/api/v1'}/user-recipes/${recipeId}/favorite`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_favorite: isFavorite }),
      });

      if (!response.ok) {
        throw new Error('Failed to update favorite status');
      }
      
      if (isFavorite) {
        Alert.alert('Added to Favorites', 'This recipe will be used to improve your recommendations.');
      }
      
      // Refresh the list
      onRefresh();
    } catch (error) {
      console.error('Error updating favorite:', error);
      Alert.alert('Error', 'Failed to update favorite status. Please try again.');
    }
  };

  const updateRecipeRating = async (recipeId: number, rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => {
    try {
      const response = await fetch(`${api.Config?.API_BASE_URL || 'http://127.0.0.1:8002/api/v1'}/user-recipes/${recipeId}/rating`, {
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
      onRefresh();
    } catch (error) {
      console.error('Error updating rating:', error);
      Alert.alert('Error', 'Failed to update rating. Please try again.');
    }
  };

  // Original Spoonacular Recipe Card Component
  const renderRecipeCard = (recipe: Recipe, index: number) => (
    <View key={recipe.id} style={styles.recipeCardWrapper}>
      <TouchableOpacity
        style={styles.recipeCard}
        onPress={() => navigateToRecipeDetail(recipe)}
        activeOpacity={0.9}
      >
        <Image 
          source={{ uri: getRecipeImage(recipe) }} 
          style={styles.recipeImage}
        />
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {getRecipeTitle(recipe)}
          </Text>
          <View style={styles.recipeStats}>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="check-circle" 
                size={16} 
                color="#4CAF50"
              />
              <Text style={styles.statText}>{getIngredientCounts(recipe).have} have</Text>
            </View>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="close-circle" 
                size={16} 
                color="#F44336"
              />
              <Text style={styles.statText}>{getIngredientCounts(recipe).missing} missing</Text>
            </View>
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

  // Original Spoonacular Saved Recipe Card Component
  const renderSavedRecipeCard = (savedRecipe: SavedRecipe, index: number) => {
    const isDeleting = deletingRecipeId === savedRecipe.id;
    
    return (
      <View key={savedRecipe.id} style={styles.recipeCardWrapper}>
        <TouchableOpacity
          style={styles.recipeCard}
          onPress={() => navigateToRecipeDetail(savedRecipe)}
          activeOpacity={0.9}
        >
          <Image 
            source={{ uri: getRecipeImage(savedRecipe) }} 
            style={styles.recipeImage}
          />
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.8)']}
            style={styles.gradient}
          />
          <View style={styles.recipeInfo}>
            <Text style={styles.recipeTitle} numberOfLines={2}>
              {getRecipeTitle(savedRecipe)}
            </Text>
            {/* Rating buttons for saved recipes */}
            {listType === 'myRecipes' && (
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
            )}
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
              onPress={() => confirmDelete(savedRecipe.id, getRecipeTitle(savedRecipe))}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Ionicons name="trash-outline" size={14} color="#fff" />
              )}
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading recipes...</Text>
      </View>
    );
  }

  if (!recipes || recipes.length === 0) {
    return (
      <ScrollView
        contentContainerStyle={styles.emptyContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Ionicons
          name={listType === 'fromPantry' ? 'restaurant' : 'bookmark'}
          size={64}
          color="#ccc"
        />
        <Text style={styles.emptyText}>
          {listType === 'fromPantry'
            ? 'No recipes found based on your pantry ingredients'
            : 'No saved recipes yet'}
        </Text>
        <Text style={styles.emptySubtext}>
          {listType === 'fromPantry'
            ? 'Try adding more ingredients to your pantry'
            : 'Save recipes from the "From Pantry" tab to see them here'}
        </Text>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.scrollView}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.recipesGrid}>
        {recipes.map((recipe, index) => {
          if ('recipe_data' in recipe) {
            return renderSavedRecipeCard(recipe as SavedRecipe, index);
          } else {
            return renderRecipeCard(recipe as Recipe, index);
          }
        })}
      </View>
    </ScrollView>
  );
};

// Original Spoonacular Recipe Card Styles
const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
    paddingHorizontal: 20,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginTop: 16,
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 20,
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
  ratingButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  ratingButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 16,
    padding: 6,
  },
  ratingButtonActive: {
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  cardActions: {
    position: 'absolute',
    top: 8,
    right: 8,
    flexDirection: 'column',
    gap: 4,
  },
  favoriteButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 16,
    padding: 6,
  },
  favoriteButtonActive: {
    backgroundColor: 'rgba(255,68,68,0.8)',
  },
  deleteButton: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
    borderRadius: 16,
    padding: 6,
  },
});

export default RecipesList;