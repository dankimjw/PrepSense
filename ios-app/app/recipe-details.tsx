// app/recipe-details.tsx - Recipe detail screen for PrepSense
import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Image, 
  TouchableOpacity,
  ActivityIndicator,
  Alert
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { Recipe, generateRecipeImage, addToShoppingList, ShoppingListItem, completeRecipe, RecipeIngredient, fetchPantryItems, PantryItem } from '../services/api';
import { Config } from '../config';
import { useAuth } from '../context/AuthContext';
import { parseIngredientsList } from '../utils/ingredientParser';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { RecipeCompletionModal } from '../components/modals/RecipeCompletionModal';
import { formatQuantity, formatIngredientQuantity } from '../utils/numberFormatting';
// Removed instruction validation/filtering
// import { validateInstructions } from '../utils/contentValidation';

export default function RecipeDetailsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [imageLoading, setImageLoading] = useState(false); // Don't block initial render
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [useGenerated, setUseGenerated] = useState(true); // Default to AI generated images
  const [isFavorite, setIsFavorite] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [isLoadingPantry, setIsLoadingPantry] = useState(false);
  const [isCompletingRecipe, setIsCompletingRecipe] = useState(false);
  const [rating, setRating] = useState<'thumbs_up' | 'thumbs_down' | 'neutral'>('neutral');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (params.recipe) {
      try {
        const recipeData = JSON.parse(params.recipe as string);
        setRecipe(recipeData);
        
        // Load image asynchronously without blocking
        if (recipeData.image) {
          setGeneratedImageUrl(recipeData.image);
        } else {
          // Start loading image in background
          setImageLoading(true);
          generateImageForRecipe(recipeData.name, useGenerated);
        }
      } catch (error) {
        console.error('Error parsing recipe data:', error);
      }
    }
  }, [params.recipe, useGenerated]);

  const generateImageForRecipe = async (recipeName: string, useAI: boolean = false) => {
    try {
      setImageError(null);
      
      // Check cache first
      const cacheKey = `recipe_image_${recipeName}_${useAI}`;
      const cachedData = await AsyncStorage.getItem(cacheKey);
      
      if (cachedData) {
        const { url, timestamp } = JSON.parse(cachedData);
        // Use cached image if less than 7 days old
        if (Date.now() - timestamp < 7 * 24 * 60 * 60 * 1000) {
          setGeneratedImageUrl(url);
          setImageLoading(false);
          return;
        }
      }
      
      // Generate new image
      const imageResponse = await generateRecipeImage(
        recipeName, 
        "professional food photography, beautifully plated, appetizing",
        useAI
      );
      
      // Cache the result
      await AsyncStorage.setItem(cacheKey, JSON.stringify({
        url: imageResponse.image_url,
        timestamp: Date.now()
      }));
      
      setGeneratedImageUrl(imageResponse.image_url);
    } catch (error) {
      console.error('Error generating recipe image:', error);
      setImageError('Failed to generate recipe image');
    } finally {
      setImageLoading(false);
    }
  };

  const loadPantryItems = async () => {
    try {
      setIsLoadingPantry(true);
      const items = await fetchPantryItems(111); // TODO: Get actual user ID
      
      // Transform backend response to match frontend expectations
      const transformedItems = items.map(item => ({
        id: item.pantry_item_id || item.id,
        item_name: item.product_name || item.item_name || 'Unknown Item',
        quantity_amount: item.quantity || item.quantity_amount || 0,
        quantity_unit: item.unit_of_measurement || item.quantity_unit || 'unit',
        expected_expiration: item.expiration_date || item.expected_expiration,
        category: item.food_category || item.category || 'Other',
        ...item // Keep any additional fields
      }));
      
      setPantryItems(transformedItems);
    } catch (error) {
      console.error('Error loading pantry items:', error);
    } finally {
      setIsLoadingPantry(false);
    }
  };

  if (!recipe) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
        <Text style={styles.loadingText}>Loading recipe...</Text>
      </View>
    );
  }


  // Get instructions from recipe data - no filtering
  const getInstructions = (recipe: Recipe) => {
    // Return instructions as-is without validation/filtering
    return recipe.instructions || [];
  };

  const instructions = getInstructions(recipe);

  // Simple hash function to generate consistent ID from recipe name
  const generateRecipeId = (name: string): number => {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      const char = name.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  };

  const handleStartCooking = () => {
    if (recipe.missing_ingredients.length > 0) {
      Alert.alert(
        'Missing Ingredients',
        `You are missing ${recipe.missing_ingredients.length} ingredient${recipe.missing_ingredients.length > 1 ? 's' : ''}:\n\n${recipe.missing_ingredients.join('\n')}\n\nDo you want to continue anyway?`,
        [
          {
            text: 'Cancel',
            style: 'cancel'
          },
          {
            text: 'Add to Shopping List',
            onPress: () => {
              router.push({
                pathname: '/select-ingredients',
                params: { 
                  ingredients: JSON.stringify(recipe.missing_ingredients),
                  recipeName: recipe.name
                }
              });
            }
          },
          {
            text: 'Continue',
            onPress: () => {
              navigateToCookingMode();
            }
          }
        ]
      );
    } else {
      navigateToCookingMode();
    }
  };

  const navigateToCookingMode = () => {
    router.push({
      pathname: '/cooking-mode',
      params: {
        recipe: JSON.stringify(recipe)
      }
    });
  };

  const handleAddToShoppingList = async () => {
    // Use missing_ingredients if available, otherwise use all ingredients if none are available
    const ingredientsToAdd = recipe.missing_ingredients.length > 0 
      ? recipe.missing_ingredients 
      : (recipe.available_ingredients.length === 0 ? recipe.ingredients : []);
    
    if (ingredientsToAdd.length === 0) {
      Alert.alert('Shopping List', 'All ingredients are already in your pantry!');
      return;
    }

    try {
      // Get existing shopping list from AsyncStorage
      const STORAGE_KEY = '@PrepSense_ShoppingList';
      const savedList = await AsyncStorage.getItem(STORAGE_KEY);
      let existingItems = [];
      
      if (savedList) {
        existingItems = JSON.parse(savedList);
      }

      // Convert missing ingredients to shopping list items
      const newItems = ingredientsToAdd.map((ingredient, index) => {
        // Clean up the ingredient string first
        const cleanedIngredient = ingredient.trim();
        
        // Try to parse quantity from ingredient string
        const parsed = parseIngredientsList([cleanedIngredient])[0];
        
        // Use a cleaner approach for the shopping list
        let displayName = '';
        let displayQuantity = '';
        
        if (parsed && parsed.name && parsed.name.trim()) {
          // If we successfully parsed the ingredient
          displayName = parsed.name;
          if (parsed.quantity && parsed.unit && parsed.unit !== 'piece') {
            // Use proper fraction formatting
            const formattedQuantity = formatIngredientQuantity(parsed.quantity, parsed.unit);
            displayQuantity = formattedQuantity ? `${formattedQuantity} ${parsed.unit}` : `${parsed.quantity} ${parsed.unit}`;
          } else if (parsed.quantity && parsed.unit === 'piece') {
            // Use proper fraction formatting for piece quantities
            displayQuantity = formatIngredientQuantity(parsed.quantity, '') || `${parsed.quantity}`;
          } else if (parsed.quantity) {
            // Use proper fraction formatting for quantity only
            displayQuantity = formatIngredientQuantity(parsed.quantity, '') || `${parsed.quantity}`;
          }
        } else {
          // If parsing failed, try a simple split approach
          // Check for patterns like "ingredient name (quantity)"
          const parenMatch = cleanedIngredient.match(/^(.+?)\s*\(([^)]+)\)\s*$/);
          if (parenMatch) {
            displayName = parenMatch[1].trim();
            displayQuantity = parenMatch[2].trim();
          } else {
            // Use the original string as the name
            displayName = cleanedIngredient;
          }
        }
        
        // Final cleanup - ensure name doesn't have leading/trailing special chars
        displayName = displayName.replace(/^[-,\s]+|[-,\s]+$/g, '').trim();
        
        return {
          id: `${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`,
          name: displayName || cleanedIngredient, // Fallback to original if name is empty
          quantity: displayQuantity || undefined,
          checked: false,
          addedAt: new Date(),
        };
      });

      // Combine with existing items
      const updatedList = [...existingItems, ...newItems];
      
      // Save back to AsyncStorage
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updatedList));

      Alert.alert(
        'Added to Shopping List',
        `${ingredientsToAdd.length} item${ingredientsToAdd.length > 1 ? 's' : ''} added to your shopping list.`,
        [
          { 
            text: 'View List', 
            onPress: () => router.push('/(tabs)/shopping-list') 
          },
          { text: 'OK' }
        ]
      );
    } catch (error) {
      console.error('Error adding to shopping list:', error);
      Alert.alert('Error', 'Failed to add items to shopping list. Please try again.');
    }
  };

  const handleQuickComplete = async () => {
    // Always load pantry items to ensure we have the latest data
    await loadPantryItems();
    
    // Show the completion modal
    setShowCompletionModal(true);
  };

  const handleRecipeCompletionConfirm = async (ingredientUsages: any[]) => {
    try {
      setIsCompletingRecipe(true);
      
      // Convert ingredient usages to the format needed by the API
      const ingredients: RecipeIngredient[] = ingredientUsages
        .filter(usage => usage.selectedAmount > 0)
        .map(usage => ({
          ingredient_name: usage.ingredientName,
          quantity: usage.selectedAmount,
          unit: usage.requestedUnit,
        }));

      if (ingredients.length === 0) {
        Alert.alert('No Ingredients Selected', 'Please select at least some ingredients to use.');
        return;
      }

      const result = await completeRecipe({
        user_id: 111, // TODO: Get actual user ID
        recipe_name: recipe.name,
        ingredients: ingredients,
      });

      // Handle different response scenarios
      let alertTitle = 'Recipe Completed! ✅';
      let alertMessage = result.summary;
      
      if (result.insufficient_items && result.insufficient_items.length > 0) {
        alertTitle = 'Recipe Completed with Warnings ⚠️';
        const insufficientList = result.insufficient_items.map(
          item => `• ${item.ingredient}: needed ${formatQuantity(item.needed)} ${item.needed_unit}, had ${formatQuantity(item.consumed)}`
        ).join('\n');
        alertMessage += `\n\nInsufficient quantities:\n${insufficientList}`;
      }
      
      if (result.errors && result.errors.length > 0) {
        alertMessage += `\n\nErrors:\n${result.errors.join('\n')}`;
      }

      // Close modal first
      setShowCompletionModal(false);

      Alert.alert(
        alertTitle,
        alertMessage,
        [
          {
            text: 'OK',
            onPress: () => {
              // Optionally navigate back or refresh
            }
          }
        ]
      );
    } catch (error) {
      console.error('Error completing recipe:', error);
      Alert.alert('Error', 'Failed to update pantry. Please try again.');
    } finally {
      setIsCompletingRecipe(false);
    }
  };

  const handleToggleFavorite = async () => {
    try {
      setIsSaving(true);
      const recipeId = generateRecipeId(recipe.name);

      if (!isFavorite) {
        // First save the recipe to user's collection
        const saveResponse = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            recipe_id: recipeId,
            recipe_title: recipe.name,
            recipe_image: generatedImageUrl || '',
            recipe_data: recipe,
            source: 'generated',
            rating: rating,
            is_favorite: true,
          }),
        });

        if (!saveResponse.ok) {
          const error = await saveResponse.json();
          if (error.detail?.includes('already saved')) {
            // Recipe already saved, just toggle favorite
            const toggleResponse = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/favorite`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
              },
            });
            if (!toggleResponse.ok) {
              throw new Error('Failed to update favorite status');
            }
          } else {
            throw new Error('Failed to save recipe');
          }
        }
        setIsFavorite(true);
      } else {
        // Toggle favorite status
        const toggleResponse = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/favorite`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!toggleResponse.ok) {
          throw new Error('Failed to update favorite status');
        }
        setIsFavorite(false);
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      Alert.alert('Error', 'Failed to update favorite status. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRating = async (newRating: 'thumbs_up' | 'thumbs_down') => {
    try {
      setIsSaving(true);
      const recipeId = generateRecipeId(recipe.name);
      
      // Toggle rating - if same rating clicked, set to neutral
      const finalRating = rating === newRating ? 'neutral' : newRating;

      // First ensure recipe is saved
      const saveResponse = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipe_id: recipeId,
          recipe_title: recipe.name,
          recipe_image: generatedImageUrl || '',
          recipe_data: recipe,
          source: 'generated',
          rating: finalRating,
          is_favorite: isFavorite,
        }),
      });

      if (!saveResponse.ok) {
        const error = await saveResponse.json();
        if (error.detail?.includes('already saved')) {
          // Recipe already saved, update rating
          const updateResponse = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipeId}/rating`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              rating: finalRating,
            }),
          });
          if (!updateResponse.ok) {
            throw new Error('Failed to update rating');
          }
        } else {
          throw new Error('Failed to save recipe');
        }
      }

      setRating(finalRating);
      
      if (finalRating !== 'neutral') {
        Alert.alert(
          'Rating Saved',
          `Your ${finalRating === 'thumbs_up' ? 'positive' : 'negative'} feedback helps improve future recommendations!`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error updating rating:', error);
      Alert.alert('Error', 'Failed to update rating. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <View testID="recipe-details-container" style={styles.container}>
      {/* Header */}
      <View testID="recipe-details-header" style={styles.header}>
        <TouchableOpacity 
          testID="back-button"
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#333" accessibilityLabel="Go back" />
        </TouchableOpacity>
        <Text testID="header-title" style={styles.headerTitle}>Recipe Details</Text>
        <View testID="header-actions" style={styles.headerActions}>
          <TouchableOpacity 
            testID="close-button"
            style={styles.closeButton}
            onPress={() => {
              // Navigate back to main screen or close modal
              router.replace('/(tabs)');
            }}
          >
            <Ionicons name="close" size={24} color="#333" accessibilityLabel="Close recipe details" />
          </TouchableOpacity>
          <TouchableOpacity 
            testID="thumbs-up-button"
            style={[styles.ratingButton, rating === 'thumbs_up' && styles.ratingButtonActive]} 
            onPress={() => handleRating('thumbs_up')}
            disabled={isSaving}
          >
            <Ionicons 
              name="thumbs-up" 
              size={20} 
              color={rating === 'thumbs_up' ? "#297A56" : "#666"} 
              accessibilityLabel="Rate recipe positively"
            />
          </TouchableOpacity>
          <TouchableOpacity 
            testID="thumbs-down-button"
            style={[styles.ratingButton, rating === 'thumbs_down' && styles.ratingButtonActive]} 
            onPress={() => handleRating('thumbs_down')}
            disabled={isSaving}
          >
            <Ionicons 
              name="thumbs-down" 
              size={20} 
              color={rating === 'thumbs_down' ? "#DC2626" : "#666"} 
              accessibilityLabel="Rate recipe negatively"
            />
          </TouchableOpacity>
          <TouchableOpacity 
            testID="favorite-button"
            style={styles.favoriteButton} 
            onPress={handleToggleFavorite}
            disabled={isSaving}
          >
            <Ionicons 
              name={isFavorite ? "bookmark" : "bookmark-outline"} 
              size={22} 
              color={isFavorite ? "#297A56" : "#333"} 
              accessibilityLabel={isFavorite ? "Remove from favorites" : "Add to favorites"}
            />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView testID="recipe-details-scroll" style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Recipe Image - Always show container with placeholder */}
        <View testID="recipe-image-container" style={styles.imageContainer}>
          {generatedImageUrl && !imageError ? (
            <Image
              testID="recipe-image"
              source={{ uri: generatedImageUrl }}
              style={styles.recipeImage}
              onError={() => setImageError('Failed to load generated image')}
            />
          ) : (
            <View testID="image-placeholder" style={styles.imagePlaceholder}>
              {imageLoading ? (
                <>
                  <ActivityIndicator size="large" color="#297A56" />
                  <Text testID="image-loading-text" style={styles.imageLoadingText}>Loading image...</Text>
                </>
              ) : imageError ? (
                <>
                  <Ionicons name="image-outline" size={64} color="#ccc" accessibilityLabel="Image failed to load" />
                  <Text testID="image-error-text" style={styles.imageErrorText}>Image generation failed</Text>
                  <TouchableOpacity 
                    testID="retry-image-button"
                    style={styles.retryButton}
                    onPress={() => generateImageForRecipe(recipe.name, useGenerated)}
                  >
                    <Text style={styles.retryButtonText}>Retry</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <Ionicons name="image-outline" size={64} color="#ccc" accessibilityLabel="No image available" />
                  <Text testID="no-image-text" style={styles.imageErrorText}>No image available</Text>
                </>
              )}
            </View>
          )}
        </View>

        {/* Recipe Info Card */}
        <View testID="recipe-info-card" style={styles.recipeCard}>
          <Text testID="recipe-title" style={styles.recipeTitle}>{recipe.name}</Text>
          
          <View testID="recipe-metrics" style={styles.recipeMetrics}>
            <View testID="time-metric" style={styles.metricItem}>
              <Ionicons name="time" size={20} color="#666" accessibilityLabel="Cooking time" />
              <Text testID="time-text" style={styles.metricText}>{recipe.time} min</Text>
            </View>
            <View testID="calories-metric" style={styles.metricItem}>
              <Ionicons name="fitness" size={20} color="#666" accessibilityLabel="Calories" />
              <Text testID="calories-text" style={styles.metricText}>{recipe.nutrition.calories} cal</Text>
            </View>
            <View testID="protein-metric" style={styles.metricItem}>
              <MaterialIcons name="fitness-center" size={20} color="#666" accessibilityLabel="Protein content" />
              <Text testID="protein-text" style={styles.metricText}>{recipe.nutrition.protein}g protein</Text>
            </View>
            <View testID="match-metric" style={styles.metricItem}>
              <Ionicons name="checkmark-circle" size={20} color="#297A56" accessibilityLabel="Recipe match score" />
              <Text testID="match-text" style={styles.metricText}>{Math.round(recipe.match_score * 100)}% match</Text>
            </View>
          </View>

          {/* Ingredients Section */}
          <View testID="ingredients-section" style={styles.section}>
            <Text testID="ingredients-title" style={styles.sectionTitle}>Ingredients</Text>
            
            {/* Complete ingredients list */}
            <View testID="ingredients-list" style={styles.ingredientGroup}>
              <Text testID="ingredients-list-title" style={styles.ingredientGroupTitle}>📝 Complete ingredient list:</Text>
              {recipe.ingredients.map((ingredient, index) => {
                // Simply check if this exact ingredient string is in the available list
                // The backend already does the smart matching
                const isAvailable = recipe.available_ingredients.includes(ingredient);
                return (
                  <View key={index} testID={`ingredient-item-${index}`} style={styles.ingredientItem}>
                    <Ionicons 
                      name={isAvailable ? "checkmark-circle" : "add-circle-outline"} 
                      size={16} 
                      color={isAvailable ? "#297A56" : "#DC2626"} 
                      accessibilityLabel={isAvailable ? "Ingredient available" : "Ingredient missing"}
                    />
                    <Text testID={`ingredient-text-${index}`} style={isAvailable ? styles.availableIngredient : styles.missingIngredient}>
                      {ingredient}
                    </Text>
                  </View>
                );
              })}
            </View>
            
            {/* Summary of what's missing */}
            {recipe.missing_ingredients.length > 0 && (
              <View testID="missing-ingredients-summary" style={[styles.ingredientGroup, styles.missingSummary]}>
                <Text testID="missing-ingredients-title" style={styles.ingredientGroupTitle}>
                  🛒 Shopping list ({recipe.missing_ingredients.length} items):
                </Text>
                {recipe.missing_ingredients.map((ingredient, index) => (
                  <View key={index} testID={`missing-ingredient-item-${index}`} style={styles.ingredientItem}>
                    <Text testID={`missing-ingredient-text-${index}`} style={styles.missingIngredient}>• {ingredient}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          {/* Instructions Section */}
          <View testID="instructions-section" style={styles.section}>
            <Text testID="instructions-title" style={styles.sectionTitle}>Instructions</Text>
            {instructions.length > 0 ? (
              instructions.map((instruction, index) => (
                <View key={index} testID={`instruction-item-${index + 1}`} style={styles.instructionItem}>
                  <View style={styles.stepNumber} testID={`step-number-${index + 1}`}>
                    <Text testID={`step-number-text-${index + 1}`} style={styles.stepNumberText}>{index + 1}</Text>
                  </View>
                  <Text testID={`instruction-text-${index + 1}`} style={styles.instructionText}>{instruction}</Text>
                </View>
              ))
            ) : (
              <Text testID="no-instructions-text" style={styles.noInstructionsText}>No instructions available for this recipe.</Text>
            )}
          </View>

          {/* Action Buttons */}
          {recipe.available_ingredients.length > 0 ? (
            <>
              <View style={styles.actionButtons}>
                <TouchableOpacity 
                  style={[
                    styles.startCookingButton,
                    recipe.missing_ingredients.length > 0 && styles.startCookingButtonDisabled
                  ]}
                  onPress={() => handleStartCooking()}
                >
                  <Ionicons name="play" size={20} color="#fff" />
                  <Text style={styles.startCookingText}>Start Cooking</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.quickCompleteButton}
                  onPress={() => handleQuickComplete()}
                >
                  <Ionicons name="checkmark-circle-outline" size={20} color="#297A56" />
                  <Text style={styles.quickCompleteText}>Quick Complete</Text>
                </TouchableOpacity>
              </View>
              
              {/* Cook Without Tracking Button */}
              <TouchableOpacity 
                style={styles.cookWithoutTrackingButton}
                onPress={() => navigateToCookingMode()}
              >
                <Ionicons name="restaurant-outline" size={20} color="#666" />
                <Text style={styles.cookWithoutTrackingText}>Cook Without Tracking Ingredients</Text>
              </TouchableOpacity>

              {recipe.missing_ingredients.length > 0 && (
                <TouchableOpacity 
                  style={styles.addToListButton}
                  onPress={() => router.push({
                    pathname: '/select-ingredients',
                    params: { 
                      ingredients: JSON.stringify(recipe.missing_ingredients),
                      recipeName: recipe.name
                    }
                  })}
                >
                  <Ionicons name="cart" size={20} color="#297A56" />
                  <Text style={styles.addToListText}>Add to Shopping List</Text>
                </TouchableOpacity>
              )}
            </>
          ) : (
            /* All ingredients are missing */
            <View style={styles.allMissingContainer}>
              <Ionicons name="alert-circle" size={48} color="#297A56" />
              <Text style={styles.allMissingTitle}>No ingredients available</Text>
              <Text style={styles.allMissingSubtitle}>
                You'll need to shop for all {recipe.ingredients.length} ingredients first
              </Text>
              <TouchableOpacity 
                style={styles.addAllToListButton}
                onPress={() => router.push({
                  pathname: '/select-ingredients',
                  params: { 
                    ingredients: JSON.stringify(recipe.ingredients),
                    recipeName: recipe.name
                  }
                })}
              >
                <Ionicons name="cart" size={20} color="#fff" />
                <Text style={styles.addAllToListText}>Add to Shopping List</Text>
              </TouchableOpacity>
              
              {/* Cook Without Tracking Option */}
              <TouchableOpacity 
                testID="cook-without-tracking-alt-button"
                style={styles.cookWithoutTrackingButtonAlt}
                onPress={() => navigateToCookingMode()}
              >
                <Ionicons name="restaurant-outline" size={20} color="#297A56" accessibilityLabel="Cook without tracking ingredients" />
                <Text style={styles.cookWithoutTrackingTextAlt}>Cook Without Tracking</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Recipe Completion Modal */}
      <RecipeCompletionModal
        testID="recipe-completion-modal"
        visible={showCompletionModal}
        onClose={() => setShowCompletionModal(false)}
        onConfirm={handleRecipeCompletionConfirm}
        recipe={recipe}
        pantryItems={pantryItems}
        loading={isCompletingRecipe}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 10,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  ratingButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  ratingButtonActive: {
    backgroundColor: '#E8F5F0',
  },
  favoriteButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 4,
  },
  content: {
    flex: 1,
  },
  imageContainer: {
    position: 'relative',
    height: 250,
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imageLoadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipeCard: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    marginTop: -24,
    paddingTop: 24,
    paddingHorizontal: 20,
    paddingBottom: 40,
    minHeight: 500,
  },
  recipeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  recipeMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
    paddingVertical: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontWeight: '500',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  ingredientGroup: {
    marginBottom: 16,
  },
  missingSummary: {
    backgroundColor: '#FEF2F2',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FCA5A5',
  },
  ingredientGroupTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  ingredientItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
  },
  availableIngredient: {
    fontSize: 14,
    color: '#297A56',
    marginLeft: 8,
    textTransform: 'capitalize',
  },
  missingIngredient: {
    fontSize: 14,
    color: '#DC2626',
    marginLeft: 8,
    textTransform: 'capitalize',
  },
  instructionItem: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#297A56',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  stepNumberText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  instructionText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
  },
  noInstructionsText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 20,
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  startCookingButton: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  startCookingText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  quickCompleteButton: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#f0f7f4',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#297A56',
  },
  quickCompleteText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  addToListButton: {
    flexDirection: 'row',
    backgroundColor: '#f0f7f4',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#297A56',
    marginTop: 12,
    gap: 8,
  },
  addToListText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
  },
  startCookingButtonDisabled: {
    backgroundColor: '#A0A0A0',
  },
  cookWithoutTrackingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ddd',
    marginTop: 12,
    gap: 8,
  },
  cookWithoutTrackingText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '500',
  },
  allMissingContainer: {
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 40,
    backgroundColor: '#f0f7f4',
    marginTop: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#297A56',
  },
  allMissingTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 16,
  },
  allMissingSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  addAllToListButton: {
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addAllToListText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  cookWithoutTrackingButtonAlt: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#297A56',
    marginTop: 12,
    gap: 8,
  },
  cookWithoutTrackingTextAlt: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '500',
  },
  addToListButton: {
    flexDirection: 'row',
    backgroundColor: '#f0f7f4',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#297A56',
    marginTop: 12,
  },
  addToListText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
  },
  startCookingButtonDisabled: {
    backgroundColor: '#A0A0A0',
  },
  cookWithoutTrackingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ddd',
    marginTop: 12,
    gap: 8,
  },
  cookWithoutTrackingText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '500',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  imageLoadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  imageErrorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 12,
    backgroundColor: '#297A56',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});