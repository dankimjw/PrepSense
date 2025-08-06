import React, { useState, useCallback, memo, useMemo } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Dimensions,
  StyleSheet,
  TouchableOpacity,
  Image,
  ListRenderItem,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import * as api from '../../services/api';
import { Config } from '../../config';

const { width } = Dimensions.get('window');

// Fallback image URL for recipes with missing or invalid images
const FALLBACK_RECIPE_IMAGE = 'https://img.spoonacular.com/recipes/default-312x231.jpg';

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
  usedIngredients?: {
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }[];
  missedIngredients?: {
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }[];
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

// Memoized individual card components for better performance
const RecipeCard = memo<{ recipe: Recipe; index: number }>(function RecipeCard({ recipe, index }) {
  const getRecipeTitle = useCallback(() => recipe.title || 'Untitled Recipe', [recipe.title]);
  const getRecipeImage = useCallback(() => recipe.image || FALLBACK_RECIPE_IMAGE, [recipe.image]);
  const getIngredientCounts = useCallback(() => ({
    have: recipe.usedIngredientCount || 0,
    missing: recipe.missedIngredientCount || 0
  }), [recipe.usedIngredientCount, recipe.missedIngredientCount]);

  const saveRecipe = useCallback(async () => {
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
      
      Alert.alert('Success', 'Recipe saved to My Recipes!');
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe. Please try again.');
    }
  }, [recipe]);

  const navigateToRecipeDetail = useCallback(() => {
    if (recipe.id) {
      router.push({
        pathname: '/recipe-details',
        params: { recipeId: recipe.id.toString() },
      });
    } else {
      Alert.alert('Error', 'Unable to open recipe details - missing recipe ID');
    }
  }, [recipe.id]);

  const title = getRecipeTitle();
  const imageUrl = getRecipeImage();
  const counts = getIngredientCounts();

  return (
    <TouchableOpacity
      style={styles.recipeCard}
      onPress={navigateToRecipeDetail}
      activeOpacity={0.9}
    >
      <Image 
        source={{ uri: imageUrl }} 
        style={styles.recipeImage}
      />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradient}
      />
      <View style={styles.recipeInfo}>
        <Text style={styles.recipeTitle} numberOfLines={2}>
          {title}
        </Text>
        <View style={styles.recipeStats}>
          <View style={styles.stat}>
            <MaterialCommunityIcons 
              name="check-circle" 
              size={16} 
              color="#4CAF50"
            />
            <Text style={styles.statText}>{counts.have} have</Text>
          </View>
          <View style={styles.stat}>
            <MaterialCommunityIcons 
              name="close-circle" 
              size={16} 
              color="#F44336"
            />
            <Text style={styles.statText}>{counts.missing} missing</Text>
          </View>
        </View>
      </View>
      <TouchableOpacity 
        style={styles.saveButton}
        onPress={saveRecipe}
      >
        <Ionicons name="bookmark-outline" size={20} color="#fff" />
      </TouchableOpacity>
    </TouchableOpacity>
  );
});

const SavedRecipeCard = memo<{ savedRecipe: SavedRecipe; index: number; listType: string; onRefresh: () => void }>(function SavedRecipeCard({ savedRecipe, index, listType, onRefresh }) {
  const [deletingRecipeId, setDeletingRecipeId] = useState<number | null>(null);

  const getRecipeTitle = useCallback(() => 
    savedRecipe.recipe_data?.title || savedRecipe.recipe_data?.name || 'Untitled Recipe',
    [savedRecipe.recipe_data?.title, savedRecipe.recipe_data?.name]
  );

  const getRecipeImage = useCallback(() => {
    const imageUrl = savedRecipe.recipe_data?.image || savedRecipe.recipe_data?.image_url || '';
    return (!imageUrl || imageUrl.trim() === '') ? FALLBACK_RECIPE_IMAGE : imageUrl;
  }, [savedRecipe.recipe_data?.image, savedRecipe.recipe_data?.image_url]);

  const deleteRecipe = useCallback(async (recipeId: number) => {
    try {
      setDeletingRecipeId(recipeId);
      await api.deleteRecipe(recipeId);
      await onRefresh();
    } catch (error) {
      console.error('Error deleting recipe:', error);
      Alert.alert('Error', 'Failed to delete recipe. Please try again.');
    } finally {
      setDeletingRecipeId(null);
    }
  }, [onRefresh]);

  const confirmDelete = useCallback((recipeId: number, recipeName: string) => {
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
  }, [deleteRecipe]);

  const navigateToRecipeDetail = useCallback(() => {
    if (savedRecipe.source === 'chat') {
      router.push({
        pathname: '/recipe-details',
        params: { recipe: JSON.stringify(savedRecipe.recipe_data) },
      });
    } else {
      const recipeId = savedRecipe.recipe_id || savedRecipe.recipe_data?.external_recipe_id || savedRecipe.recipe_data?.id;
      if (recipeId) {
        router.push({
          pathname: '/recipe-details',
          params: { recipeId: recipeId.toString() },
        });
      } else {
        console.error('No recipe ID found for saved recipe:', savedRecipe);
        Alert.alert('Error', 'Unable to open recipe details');
      }
    }
  }, [savedRecipe]);

  const toggleFavorite = useCallback(async (recipeId: number, isFavorite: boolean) => {
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
      
      if (isFavorite) {
        Alert.alert('Added to Favorites', 'This recipe will be used to improve your recommendations.');
      }
      
      onRefresh();
    } catch (error) {
      console.error('Error updating favorite:', error);
      Alert.alert('Error', 'Failed to update favorite status. Please try again.');
    }
  }, [onRefresh]);

  const updateRecipeRating = useCallback(async (recipeId: number, rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => {
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
      
      onRefresh();
    } catch (error) {
      console.error('Error updating rating:', error);
      Alert.alert('Error', 'Failed to update rating. Please try again.');
    }
  }, [onRefresh]);

  const isDeleting = deletingRecipeId === savedRecipe.id;
  const title = getRecipeTitle();
  const imageUrl = getRecipeImage();

  return (
    <TouchableOpacity
      style={styles.recipeCard}
      onPress={navigateToRecipeDetail}
      activeOpacity={0.9}
    >
      <Image 
        source={{ uri: imageUrl }} 
        style={styles.recipeImage}
      />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradient}
      />
      <View style={styles.recipeInfo}>
        <Text style={styles.recipeTitle} numberOfLines={2}>
          {title}
        </Text>
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
          onPress={() => confirmDelete(savedRecipe.id, title)}
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
  );
});

const RecipesList: React.FC<RecipesListProps> = memo(function RecipesList({
  recipes,
  isLoading,
  onRefresh,
  refreshing,
  listType,
}) {
  // Optimized data structure for FlatList
  const flatListData = useMemo(() => 
    recipes.map((recipe, index) => ({
      recipe,
      index,
      key: `${'recipe_data' in recipe ? 'saved' : 'recipe'}-${recipe.id || 'unknown'}-${index}`,
      isSaved: 'recipe_data' in recipe
    }))
  , [recipes]);

  const renderFlatListItem: ListRenderItem<typeof flatListData[0]> = useCallback(({ item }) => {
    return item.isSaved 
      ? <SavedRecipeCard 
          savedRecipe={item.recipe as SavedRecipe} 
          index={item.index}
          listType={listType}
          onRefresh={onRefresh}
        />
      : <RecipeCard 
          recipe={item.recipe as Recipe} 
          index={item.index}
        />;
  }, [listType, onRefresh]);

  const keyExtractor = useCallback((item: typeof flatListData[0]) => item.key, []);

  const getItemLayout = useCallback((data: any, index: number) => ({
    length: 236, // 220 height + 16 margin
    offset: 236 * Math.floor(index / 2),
    index,
  }), []);

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
      <FlatList
        contentContainerStyle={styles.emptyContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        data={[]}
        renderItem={() => null}
        ListEmptyComponent={
          <View style={styles.emptyContent}>
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
          </View>
        }
      />
    );
  }

  return (
    <FlatList
      style={styles.scrollView}
      data={flatListData}
      renderItem={renderFlatListItem}
      keyExtractor={keyExtractor}
      numColumns={2}
      contentContainerStyle={styles.recipesGrid}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      removeClippedSubviews={true}
      maxToRenderPerBatch={10}
      windowSize={10}
      initialNumToRender={8}
      getItemLayout={getItemLayout}
      showsVerticalScrollIndicator={false}
    />
  );
});

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
  emptyContent: {
    alignItems: 'center',
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
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 20,
  },
  recipeCard: {
    width: (width - 48) / 2, // Account for padding and gap
    height: 220,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    marginHorizontal: 8,
    marginBottom: 16,
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