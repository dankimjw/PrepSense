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
import { Config } from '../../config';

const { width } = Dimensions.get('window');

// Working fallback image URL for recipes with missing or invalid images
const FALLBACK_RECIPE_IMAGE = 'https://via.placeholder.com/312x231/E5E5E5/666666?text=Recipe+Image';

// Use the Recipe interface from the API module to avoid conflicts
type Recipe = api.Recipe;

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
      const response = await fetch(`${api.Config?.API_BASE_URL || Config.API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipe_id: recipe.id,
          recipe_title: recipe.title || recipe.name,
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
      const title = recipe.recipe_data?.title || recipe.recipe_data?.name || 'Untitled Recipe';
      console.log('📝 Saved recipe title extraction:', {
        recipe_id: recipe.id,
        recipe_data_title: recipe.recipe_data?.title,
        recipe_data_name: recipe.recipe_data?.name,
        final_title: title,
        raw_recipe_data: JSON.stringify(recipe.recipe_data, null, 2).slice(0, 200) + '...'
      });
      return title;
    }
    // This is a regular recipe from Spoonacular API - handle both direct and nested structures
    const title = recipe.title || recipe.name || 'Untitled Recipe';
    console.log('📝 Spoonacular recipe title extraction:', {
      recipe_id: recipe.id,
      title: recipe.title,
      name: recipe.name,
      final_title: title
    });
    return title;
  };

  // Enhanced image URL generation with better fallback handling
  const getRecipeImage = (recipe: Recipe | SavedRecipe): string => {
    let imageUrl = '';
    let recipeId: number | null = null;
    
    if ('recipe_data' in recipe) {
      // This is a saved recipe
      imageUrl = recipe.recipe_data?.image || recipe.recipe_data?.image_url || '';
      // Try to get recipe ID for Spoonacular URL generation
      recipeId = recipe.recipe_id || recipe.recipe_data?.id || recipe.recipe_data?.external_recipe_id || null;
      
      console.log('🖼️ Saved recipe image URL processing:', {
        recipe_id: recipe.id,
        spoonacular_id: recipeId,
        recipe_data_image: recipe.recipe_data?.image,
        recipe_data_image_url: recipe.recipe_data?.image_url,
        initial_url: imageUrl
      });
    } else {
      // This is a regular recipe from Spoonacular API
      imageUrl = recipe.image || '';
      recipeId = recipe.id || null;
      
      console.log('🖼️ Spoonacular recipe image URL processing:', {
        recipe_id: recipe.id,
        image: recipe.image,
        initial_url: imageUrl
      });
    }
    
    // Fix relative URLs for backend-served images
    if (imageUrl && !imageUrl.startsWith('http')) {
      const baseUrl = Config.API_BASE_URL.replace('/api/v1', '');
      imageUrl = `${baseUrl}${imageUrl.startsWith('/') ? '' : '/'}${imageUrl}`;
      console.log('🔧 Fixed relative URL:', imageUrl);
    }
    
    // Enhanced Spoonacular image URL handling
    if (recipeId && typeof recipeId === 'number' && recipeId > 0) {
      // If no image URL or it's a broken default URL, generate proper Spoonacular URL
      if (!imageUrl || imageUrl === 'https://img.spoonacular.com/recipes/default-312x231.jpg') {
        imageUrl = `https://img.spoonacular.com/recipes/${recipeId}-312x231.jpg`;
        console.log('🖼️ Generated Spoonacular image URL:', imageUrl);
      }
      // Fix malformed Spoonacular URLs that don't include the recipe ID
      else if (imageUrl.includes('spoonacular.com') && !imageUrl.includes(`${recipeId}-`)) {
        imageUrl = `https://img.spoonacular.com/recipes/${recipeId}-312x231.jpg`;
        console.log('🔧 Fixed malformed Spoonacular URL:', imageUrl);
      }
    }
    
    // Use working fallback image if we still don't have a valid URL
    if (!imageUrl || imageUrl === 'https://img.spoonacular.com/recipes/default-312x231.jpg') {
      imageUrl = FALLBACK_RECIPE_IMAGE;
      console.log('🖼️ Using working fallback image for recipe:', getRecipeTitle(recipe));
    }
    
    return imageUrl;
  };

  const getRecipeId = (recipe: Recipe | SavedRecipe): number | null => {
    if ('recipe_data' in recipe) {
      // This is a saved recipe - try multiple ID fields
      return recipe.recipe_id || recipe.recipe_data?.id || recipe.recipe_data?.external_recipe_id || recipe.id || null;
    }
    // This is a regular recipe
    return recipe.id || null;
  };

  const handleRecipePress = (recipe: Recipe | SavedRecipe) => {
    const recipeId = getRecipeId(recipe);
    const recipeTitle = getRecipeTitle(recipe);
    
    if (recipeId) {
      console.log('📱 Navigating to recipe details:', {
        recipe_id: recipeId,
        title: recipeTitle,
        source: 'recipe_list'
      });
      
      router.push({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: recipeId.toString() },
      });
    } else {
      console.error('❌ Cannot navigate - no valid recipe ID found:', {
        recipe: JSON.stringify(recipe, null, 2).slice(0, 300) + '...'
      });
      
      Alert.alert(
        'Error', 
        'Unable to open recipe details. This recipe may be missing information.',
        [{ text: 'OK', style: 'default' }]
      );
    }
  };

  const renderRecipeCard = (recipe: Recipe | SavedRecipe, index: number) => {
    const title = getRecipeTitle(recipe);
    const imageUrl = getRecipeImage(recipe);
    const recipeId = getRecipeId(recipe);
    
    return (
      <TouchableOpacity
        key={`${listType}-${index}-${recipeId || 'no-id'}`}
        style={styles.recipeCard}
        onPress={() => handleRecipePress(recipe)}
        activeOpacity={0.8}
      >
        <View style={styles.imageContainer}>
          <Image 
            source={{ uri: imageUrl }}
            style={styles.recipeImage}
            resizeMode="cover"
            onError={(error) => {
              console.log(`🚨 Recipe image failed to load:`, {
                attempted_url: imageUrl,
                recipe_id: recipeId,
                recipe_title: title,
                error: error.nativeEvent.error || 'Unknown error'
              });
            }}
            onLoad={() => {
              console.log(`✅ Recipe image loaded successfully:`, {
                url: imageUrl,
                recipe_id: recipeId,
                recipe_title: title
              });
            }}
          />
          
          {/* Gradient overlay for better text readability */}
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.7)']}
            style={styles.gradient}
          />
          
          {/* Save/Delete button overlay */}
          <View style={styles.actionButtonContainer}>
            {listType === 'fromPantry' && (
              <TouchableOpacity
                style={styles.saveButton}
                onPress={(e) => {
                  e.stopPropagation();
                  saveRecipe(recipe as Recipe);
                }}
              >
                <Ionicons name="bookmark-outline" size={20} color="white" />
              </TouchableOpacity>
            )}
            
            {listType === 'myRecipes' && (
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={(e) => {
                  e.stopPropagation();
                  confirmDelete(recipeId || 0, title);
                }}
                disabled={deletingRecipeId === recipeId}
              >
                {deletingRecipeId === recipeId ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Ionicons name="trash-outline" size={20} color="white" />
                )}
              </TouchableOpacity>
            )}
          </View>
          
          {/* Recipe info overlay */}
          <View style={styles.recipeInfo}>
            <Text style={styles.recipeTitle} numberOfLines={2}>
              {title}
            </Text>
            
            {/* Show ingredient availability for pantry recipes */}
            {listType === 'fromPantry' && 'usedIngredientCount' in recipe && (
              <View style={styles.ingredientInfo}>
                <View style={styles.ingredientStat}>
                  <MaterialCommunityIcons 
                    name="check-circle" 
                    size={16} 
                    color="#4CAF50" 
                  />
                  <Text style={styles.ingredientText}>
                    {(recipe as Recipe).usedIngredientCount || 0} available
                  </Text>
                </View>
                <View style={styles.ingredientStat}>
                  <MaterialCommunityIcons 
                    name="close-circle" 
                    size={16} 
                    color="#F44336" 
                  />
                  <Text style={styles.ingredientText}>
                    {(recipe as Recipe).missedIngredientCount || 0} missing
                  </Text>
                </View>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  if (isLoading && recipes.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading recipes...</Text>
      </View>
    );
  }

  if (recipes.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <MaterialCommunityIcons 
          name="chef-hat" 
          size={80} 
          color="#CCCCCC" 
          style={styles.emptyIcon}
        />
        <Text style={styles.emptyTitle}>
          {listType === 'fromPantry' ? 'No Pantry Recipes Found' : 'No Saved Recipes'}
        </Text>
        <Text style={styles.emptyMessage}>
          {listType === 'fromPantry' 
            ? 'Add items to your pantry to discover recipes you can make!'
            : 'Save recipes from the Pantry tab to see them here.'
          }
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          colors={['#007AFF']}
          tintColor="#007AFF"
        />
      }
    >
      <View style={styles.recipesGrid}>
        {recipes.map((recipe, index) => renderRecipeCard(recipe, index))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 100,
  },
  recipesGrid: {
    gap: 16,
  },
  recipeCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    marginBottom: 16,
  },
  imageContainer: {
    height: 200,
    position: 'relative',
  },
  recipeImage: {
    width: '100%',
    height: '100%',
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 100,
  },
  actionButtonContainer: {
    position: 'absolute',
    top: 12,
    right: 12,
  },
  saveButton: {
    backgroundColor: 'rgba(0, 122, 255, 0.8)',
    borderRadius: 20,
    padding: 8,
    backdropFilter: 'blur(10px)',
  },
  deleteButton: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
    borderRadius: 20,
    padding: 8,
    backdropFilter: 'blur(10px)',
  },
  recipeInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
  },
  recipeTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginBottom: 8,
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  ingredientInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ingredientStat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ingredientText: {
    fontSize: 12,
    color: 'white',
    fontWeight: '500',
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 32,
  },
  emptyIcon: {
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
    marginBottom: 12,
  },
  emptyMessage: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
  },
});

export default RecipesList;