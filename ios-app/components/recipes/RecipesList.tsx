import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Dimensions,
  StyleSheet,
} from 'react-native';
import { TouchableOpacity } from 'react-native-gesture-handler';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as api from '../../services/api';

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
}

interface SavedRecipe {
  id: number;
  user_id: number;
  recipe_id?: number;
  source: 'spoonacular' | 'chat' | 'openai';
  recipe_data: any;
  created_at: string;
  updated_at: string;
}

interface RecipesListProps {
  recipes: (Recipe | SavedRecipe)[];
  isLoading: boolean;
  onRefresh: () => void;
  refreshing: boolean;
  listType: 'fromPantry' | 'myRecipes';
}

const { width: screenWidth } = Dimensions.get('window');

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

  const getRecipeTitle = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      return recipe.recipe_data?.title || recipe.recipe_data?.name || 'Untitled Recipe';
    }
    // This is a regular recipe
    return recipe.title || 'Untitled Recipe';
  };

  const getRecipeImage = (recipe: Recipe | SavedRecipe): string | undefined => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      return recipe.recipe_data?.image || recipe.recipe_data?.image_url;
    }
    // This is a regular recipe
    return recipe.image;
  };

  const getIngredientCount = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe - try to get ingredient count from recipe_data
      const ingredients = recipe.recipe_data?.ingredients || recipe.recipe_data?.extendedIngredients || [];
      return `${ingredients.length} ingredients`;
    }
    // This is a regular recipe from Spoonacular
    const used = recipe.usedIngredientCount || 0;
    const missed = recipe.missedIngredientCount || 0;
    const total = used + missed;
    
    if (total > 0) {
      return `${used}/${total} ingredients from pantry`;
    }
    
    return 'View ingredients';
  };

  const getCookingInfo = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      const time = recipe.recipe_data?.readyInMinutes || recipe.recipe_data?.cooking_time;
      const servings = recipe.recipe_data?.servings || recipe.recipe_data?.yield;
      
      const parts = [];
      if (time) parts.push(`${time} min`);
      if (servings) parts.push(`${servings} servings`);
      
      return parts.length > 0 ? parts.join(' • ') : '';
    }
    // This is a regular recipe
    const parts = [];
    if (recipe.readyInMinutes) parts.push(`${recipe.readyInMinutes} min`);
    if (recipe.servings) parts.push(`${recipe.servings} servings`);
    
    return parts.length > 0 ? parts.join(' • ') : '';
  };

  const getRecipeSource = (recipe: Recipe | SavedRecipe): string => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      switch (recipe.source) {
        case 'chat':
          return 'AI Generated';
        case 'openai':
          return 'OpenAI Recipe';
        case 'spoonacular':
          return 'Spoonacular';
        default:
          return 'Saved Recipe';
      }
    }
    // This is a regular recipe from API
    return 'Spoonacular';
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
      // Add safety check for recipe.id
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

  const handleScroll = (event: any) => {
    const currentOffset = event.nativeEvent.contentOffset.y;
    // Could implement infinite scroll here
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
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      onScroll={handleScroll}
      scrollEventThrottle={400}
    >
      {recipes.map((recipe, index) => {
        const title = getRecipeTitle(recipe);
        const imageUrl = getRecipeImage(recipe);
        const ingredientInfo = getIngredientCount(recipe);
        const cookingInfo = getCookingInfo(recipe);
        const source = getRecipeSource(recipe);
        const isDeleting = 'id' in recipe && deletingRecipeId === recipe.id;

        return (
          <View key={index} style={styles.recipeCard}>
            <TouchableOpacity
              style={styles.cardContent}
              onPress={() => navigateToRecipeDetail(recipe)}
              activeOpacity={0.7}
            >
              {/* Recipe Image */}
              <View style={styles.imageContainer}>
                {imageUrl ? (
                  <Image
                    source={{ uri: imageUrl }}
                    style={styles.recipeImage}
                    contentFit="cover"
                    placeholder={{ uri: 'https://via.placeholder.com/150x150?text=No+Image' }}
                  />
                ) : (
                  <View style={styles.placeholderImage}>
                    <Ionicons name="image-outline" size={40} color="#ccc" />
                  </View>
                )}
                
                {/* Recipe Source Badge */}
                <View style={styles.sourceBadge}>
                  <Text style={styles.sourceBadgeText}>{source}</Text>
                </View>
              </View>

              {/* Recipe Details */}
              <View style={styles.recipeDetails}>
                <Text style={styles.recipeTitle} numberOfLines={2}>
                  {title}
                </Text>
                
                <Text style={styles.ingredientInfo}>
                  {ingredientInfo}
                </Text>
                
                {cookingInfo && (
                  <Text style={styles.cookingInfo}>
                    {cookingInfo}
                  </Text>
                )}
              </View>
            </TouchableOpacity>

            {/* Delete Button for Saved Recipes */}
            {listType === 'myRecipes' && 'id' in recipe && (
              <TouchableOpacity
                style={[styles.deleteButton, isDeleting && styles.deleteButtonDisabled]}
                onPress={() => confirmDelete(recipe.id, title)}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Ionicons name="trash-outline" size={20} color="#fff" />
                )}
              </TouchableOpacity>
            )}
          </View>
        );
      })}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 50,
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
  recipeCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
    overflow: 'hidden',
  },
  cardContent: {
    flexDirection: 'row',
    padding: 0,
  },
  imageContainer: {
    width: 120,
    height: 120,
    position: 'relative',
  },
  recipeImage: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sourceBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  sourceBadgeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
  },
  recipeDetails: {
    flex: 1,
    padding: 12,
    justifyContent: 'flex-start',
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    lineHeight: 20,
  },
  ingredientInfo: {
    fontSize: 13,
    color: '#4CAF50',
    marginBottom: 4,
    fontWeight: '500',
  },
  cookingInfo: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  deleteButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(244, 67, 54, 0.9)',
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonDisabled: {
    opacity: 0.5,
  },
});

export default RecipesList;