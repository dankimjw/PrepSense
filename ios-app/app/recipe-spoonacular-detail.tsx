import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Config } from '../config';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../context/AuthContext';
import { completeRecipe, RecipeIngredient } from '../services/api';
import { parseIngredientsList } from '../utils/ingredientParser';
import { calculateIngredientAvailability, validateIngredientCounts } from '../utils/ingredientMatcher';
import { validateInstructions, getDefaultInstructions, isInappropriateContent } from '../utils/contentValidation';
import { formatIngredientQuantity } from '../utils/numberFormatting';

const { width } = Dimensions.get('window');

interface RecipeDetail {
  id: number;
  title: string;
  image: string;
  readyInMinutes: number;
  servings: number;
  pricePerServing: number;
  sourceUrl: string;
  summary: string;
  cuisines: string[];
  diets: string[];
  dishTypes: string[];
  extendedIngredients: Array<{
    id: number;
    name: string;
    amount: number;
    unit: string;
    original: string;
  }>;
  analyzedInstructions: Array<{
    name: string;
    steps: Array<{
      number: number;
      step: string;
      ingredients: Array<{ id: number; name: string }>;
      equipment: Array<{ id: number; name: string }>;
    }>;
  }>;
  nutrition?: {
    nutrients: Array<{
      name: string;
      amount: number;
      unit: string;
      percentOfDailyNeeds: number;
    }>;
  };
}

export default function RecipeSpoonacularDetail() {
  const { recipeId } = useLocalSearchParams();
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'ingredients' | 'instructions' | 'nutrition'>('ingredients');
  const [availableIngredients, setAvailableIngredients] = useState<Set<number>>(new Set());
  const [missingIngredients, setMissingIngredients] = useState<Set<number>>(new Set());
  const [pantryItems, setPantryItems] = useState<any[]>([]);
  const [isSaved, setIsSaved] = useState(false);
  const [rating, setRating] = useState<'thumbs_up' | 'thumbs_down' | 'neutral'>('neutral');
  const [isSaving, setIsSaving] = useState(false);
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    fetchRecipeDetails();
    fetchPantryItems();
  }, [recipeId]);

  // Check ingredients when pantryItems change
  useEffect(() => {
    if (recipe && pantryItems.length > 0) {
      checkAvailableIngredients(recipe.extendedIngredients);
    }
  }, [pantryItems, recipe]);

  const fetchRecipeDetails = async () => {
    if (!recipeId) return;

    try {
      setLoading(true);
      const response = await fetch(
        `${Config.API_BASE_URL}/recipes/recipe/${recipeId}?include_nutrition=true`
      );

      if (!response.ok) throw new Error('Failed to fetch recipe details');
      
      const data = await response.json();
      setRecipe(data);
      
      // Check available ingredients after recipe is loaded
      if (data && pantryItems.length > 0) {
        checkAvailableIngredients(data.extendedIngredients);
      }
    } catch (error) {
      console.error('Error fetching recipe details:', error);
      Alert.alert('Error', 'Failed to load recipe details. Please try again.');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const fetchPantryItems = async () => {
    try {
      const response = await fetch(`${Config.API_BASE_URL}/pantry/user/111/items`);
      if (!response.ok) throw new Error('Failed to fetch pantry items');
      
      const items = await response.json();
      setPantryItems(items);
      
      // Check available ingredients if recipe is already loaded
      if (recipe) {
        checkAvailableIngredients(recipe.extendedIngredients);
      }
    } catch (error) {
      console.error('Error fetching pantry items:', error);
    }
  };

  const cleanInstructionText = (text: string): string => {
    // First check if the content is inappropriate
    if (isInappropriateContent(text)) {
      return '';
    }
    
    // Fix common text corruption patterns
    let cleaned = text;
    
    // Fix "FILESTORAGE" -> "STORAGE"
    cleaned = cleaned.replace(/FILESTORAGE/gi, 'STORAGE');
    
    // Fix "COOK'S FILE" -> "COOK'S TIP" or "COOK'S NOTE"
    cleaned = cleaned.replace(/COOK'S FILE/gi, "COOK'S NOTE");
    
    // Add spaces before capital letters that follow lowercase letters without space
    cleaned = cleaned.replace(/([a-z])([A-Z])/g, '$1. $2');
    
    // Fix multiple periods
    cleaned = cleaned.replace(/\.{2,}/g, '.');
    
    // Add space after periods if missing
    cleaned = cleaned.replace(/\.([A-Z])/g, '. $1');
    
    // Remove any file system or technical terms that shouldn't be in recipes
    const technicalTerms = [
      'FILE', 'FILESYSTEM', 'DATABASE', 'CACHE', 'BUFFER', 'MEMORY'
    ];
    
    technicalTerms.forEach(term => {
      // Only remove if it's a standalone word (not part of a larger word)
      const regex = new RegExp(`\\b${term}\\b`, 'gi');
      cleaned = cleaned.replace(regex, '');
    });
    
    // Clean up extra spaces
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    
    // Fix spacing around punctuation
    cleaned = cleaned.replace(/\s+([.,!?])/g, '$1');
    cleaned = cleaned.replace(/([.,!?])([A-Za-z])/g, '$1 $2');
    
    // Final check after cleaning
    if (isInappropriateContent(cleaned)) {
      return '';
    }
    
    return cleaned;
  };

  const filterValidIngredients = (ingredients: RecipeDetail['extendedIngredients']) => {
    return ingredients
      .filter((ingredient) => {
        const lowerName = ingredient.name.toLowerCase();
        const lowerOriginal = ingredient.original.toLowerCase();
        
        // Filter out items that are clearly not ingredients
        const nonIngredientPatterns = [
          'preparation time',
          'cooking time',
          'total time',
          'servings',
          'yield',
          'ready in',
          'prep time',
          'cook time'
        ];
        
        const isNonIngredient = nonIngredientPatterns.some(pattern => 
          lowerName.includes(pattern) || lowerOriginal.includes(pattern)
        );
        
        return !isNonIngredient;
      })
      // Remove duplicates based on ingredient name
      .filter((ingredient, index, self) => 
        index === self.findIndex(i => i.name === ingredient.name)
      );
  };

  const checkAvailableIngredients = (recipeIngredients: RecipeDetail['extendedIngredients']) => {
    // Filter out non-ingredients first
    const validIngredients = filterValidIngredients(recipeIngredients);
    
    const result = calculateIngredientAvailability(validIngredients, pantryItems);
    
    // Validate that counts add up correctly
    if (!validateIngredientCounts(result)) {
      console.warn('Ingredient count validation failed:', result);
    }
    
    setAvailableIngredients(result.availableIngredients);
    setMissingIngredients(result.missingIngredients);
  };

  const handleAddToShoppingList = async () => {
    if (!recipe) {
      Alert.alert('Error', 'Recipe data not loaded');
      return;
    }
    
    // When all ingredients are missing, use all ingredients
    const validIngredients = filterValidIngredients(recipe.extendedIngredients);
    const ingredientsToAdd = missingIngredients.size > 0 
      ? validIngredients.filter(ing => missingIngredients.has(ing.id))
      : (availableIngredients.size === 0 ? validIngredients : []);
    
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

      // Convert ingredients to shopping list items
      const newItems = ingredientsToAdd.map((ingredient, index) => {
        // For Spoonacular, we have both original string and parsed name
        const cleanedOriginal = ingredient.original.trim();
        const fallbackName = ingredient.name.trim();
        
        // Try to parse the original ingredient string
        const parsed = parseIngredientsList([cleanedOriginal])[0];
        
        // Use a cleaner approach for the shopping list
        let displayName = '';
        let displayQuantity = '';
        
        if (parsed && parsed.name && parsed.name.trim()) {
          // If we successfully parsed the ingredient
          displayName = parsed.name;
          if (parsed.quantity && parsed.unit) {
            // Use proper fraction formatting
            const formattedQuantity = formatIngredientQuantity(parsed.quantity, parsed.unit);
            displayQuantity = formattedQuantity ? `${formattedQuantity} ${parsed.unit}` : `${parsed.quantity} ${parsed.unit}`;
          } else if (parsed.quantity) {
            // Use proper fraction formatting for quantity only
            displayQuantity = formatIngredientQuantity(parsed.quantity, '') || `${parsed.quantity}`;
          }
        } else {
          // If parsing failed, use the ingredient name from Spoonacular and original amount
          displayName = fallbackName;
          // Use Spoonacular's formatted amount and unit which should already be properly formatted
          if (ingredient.amount && ingredient.unit) {
            const formattedQuantity = formatIngredientQuantity(ingredient.amount, ingredient.unit);
            displayQuantity = formattedQuantity ? `${formattedQuantity} ${ingredient.unit}` : `${ingredient.amount} ${ingredient.unit}`;
          } else if (ingredient.amount) {
            displayQuantity = formatIngredientQuantity(ingredient.amount, '') || `${ingredient.amount}`;
          }
        }
        
        return {
          id: `${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`,
          name: displayName,
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

  const handleStartCooking = () => {
    if (!recipe) return;
    
    if (missingIngredients.size > 0) {
      Alert.alert(
        'Missing Ingredients',
        `You are missing ${missingIngredients.size} ingredient${missingIngredients.size > 1 ? 's' : ''}. Do you want to continue anyway?`,
        [
          {
            text: 'Cancel',
            style: 'cancel'
          },
          {
            text: 'Add to Shopping List',
            onPress: () => {
              const missingIngredientsList = recipe.extendedIngredients
                .filter(ing => missingIngredients.has(ing.id))
                .map(ing => ing.original);
              
              router.push({
                pathname: '/select-ingredients',
                params: { 
                  ingredients: JSON.stringify(missingIngredientsList),
                  recipeName: recipe.title
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
    if (!recipe) return;
    
    // Convert Spoonacular recipe to our Recipe format for cooking mode
    const recipeForCooking = {
      name: recipe.title,
      ingredients: recipe.extendedIngredients.map(ing => ing.original),
      instructions: recipe.analyzedInstructions[0]?.steps
        .map(step => cleanInstructionText(step.step))
        .filter(text => text.length > 0) || getDefaultInstructions(recipe.title),
      nutrition: {
        calories: recipe.nutrition?.nutrients.find(n => n.name === 'Calories')?.amount || 0,
        protein: recipe.nutrition?.nutrients.find(n => n.name === 'Protein')?.amount || 0,
      },
      time: recipe.readyInMinutes,
      available_ingredients: [],
      missing_ingredients: [],
      missing_count: 0,
      available_count: 0,
      match_score: 0,
      expected_joy: 0,
    };
    
    router.push({
      pathname: '/cooking-mode',
      params: {
        recipe: JSON.stringify(recipeForCooking)
      }
    });
  };

  const handleQuickComplete = async () => {
    if (!recipe) return;
    
    Alert.alert(
      'Complete Recipe',
      'This will subtract the available ingredients from your pantry. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Complete',
          onPress: async () => {
            try {
              // Convert ingredients for completion
              const ingredientsToUse = recipe.extendedIngredients
                .filter(ing => availableIngredients.has(ing.id))
                .map(ing => ({
                  ingredient_name: ing.name,
                  quantity: ing.amount,
                  unit: ing.unit,
                }));

              const result = await completeRecipe({
                user_id: 111,
                recipe_name: recipe.title,
                ingredients: ingredientsToUse,
              });

              Alert.alert(
                'Recipe Completed! ✅',
                result.summary || 'Ingredients have been subtracted from your pantry.',
                [{ text: 'OK' }]
              );
            } catch (error) {
              console.error('Error completing recipe:', error);
              Alert.alert('Error', 'Failed to update pantry. Please try again.');
            }
          }
        }
      ]
    );
  };

  const cleanHtml = (html: string) => {
    return html
      .replace(/<[^>]*>?/gm, '')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"');
  };

  const handleSaveRecipe = async () => {
    if (!recipe) return;
    
    try {
      setIsSaving(true);
      
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
          rating: rating,
          is_favorite: !isSaved, // Toggle favorite
        }),
      });

      if (response.ok) {
        setIsSaved(!isSaved);
      } else {
        const error = await response.json();
        if (error.detail?.includes('already saved')) {
          // Recipe already saved, toggle favorite
          const toggleResponse = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipe.id}/favorite`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
          });
          if (toggleResponse.ok) {
            setIsSaved(!isSaved);
          } else {
            throw new Error('Failed to update favorite status');
          }
        } else {
          Alert.alert('Error', 'Failed to save recipe. Please try again.');
        }
      }
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRating = async (newRating: 'thumbs_up' | 'thumbs_down') => {
    if (!recipe) return;
    
    try {
      setIsSaving(true);
      
      // Toggle rating - if same rating clicked, set to neutral
      const finalRating = rating === newRating ? 'neutral' : newRating;

      // First ensure recipe is saved
      const saveResponse = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
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
          rating: finalRating,
          is_favorite: isSaved,
        }),
      });

      if (!saveResponse.ok) {
        const error = await saveResponse.json();
        if (error.detail?.includes('already saved')) {
          // Recipe already saved, update rating
          const updateResponse = await fetch(`${Config.API_BASE_URL}/user-recipes/${recipe.id}/rating`, {
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

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
        <Text style={styles.loadingText}>Loading recipe details...</Text>
      </View>
    );
  }

  if (!recipe) {
    return null;
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={{ height: insets.top }} />
      
      <View style={styles.imageContainer}>
        <Image source={{ uri: recipe.image }} style={styles.recipeImage} />
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.6)']}
          style={styles.gradient}
        />
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={[styles.ratingButton, rating === 'thumbs_up' && styles.ratingButtonActive]}
            onPress={() => handleRating('thumbs_up')}
            disabled={isSaving}
          >
            <Ionicons 
              name="thumbs-up" 
              size={20} 
              color={rating === 'thumbs_up' ? "#297A56" : "#fff"} 
            />
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.ratingButton, rating === 'thumbs_down' && styles.ratingButtonActive]}
            onPress={() => handleRating('thumbs_down')}
            disabled={isSaving}
          >
            <Ionicons 
              name="thumbs-down" 
              size={20} 
              color={rating === 'thumbs_down' ? "#DC2626" : "#fff"} 
            />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.bookmarkButton}
            onPress={handleSaveRecipe}
            disabled={isSaving}
          >
            <Ionicons 
              name={isSaved ? "bookmark" : "bookmark-outline"} 
              size={22} 
              color={isSaved ? "#297A56" : "#fff"} 
            />
          </TouchableOpacity>
        </View>
        <View style={styles.recipeHeader}>
          <Text style={styles.recipeTitle}>{recipe.title}</Text>
          <View style={styles.recipeMetrics}>
            <View style={styles.metric}>
              <Ionicons name="time-outline" size={20} color="#fff" />
              <Text style={styles.metricText}>{recipe.readyInMinutes} min</Text>
            </View>
            <View style={styles.metric}>
              <Ionicons name="people-outline" size={20} color="#fff" />
              <Text style={styles.metricText}>{recipe.servings} servings</Text>
            </View>
            {recipe.pricePerServing && (
              <View style={styles.metric}>
                <MaterialCommunityIcons name="currency-usd" size={20} color="#fff" />
                <Text style={styles.metricText}>
                  ${(recipe.pricePerServing / 100).toFixed(2)}/serving
                </Text>
              </View>
            )}
          </View>
        </View>
      </View>

      {recipe.cuisines.length > 0 || recipe.diets.length > 0 ? (
        <View style={styles.tagsContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {recipe.cuisines.map((cuisine) => (
              <View key={cuisine} style={[styles.tag, styles.cuisineTag]}>
                <Text style={styles.tagText}>{cuisine}</Text>
              </View>
            ))}
            {recipe.diets.map((diet) => (
              <View key={diet} style={[styles.tag, styles.dietTag]}>
                <Text style={styles.tagText}>{diet}</Text>
              </View>
            ))}
          </ScrollView>
        </View>
      ) : null}

      {recipe.summary && (
        <View style={styles.summaryContainer}>
          <Text style={styles.summaryText}>
            {cleanHtml(recipe.summary)}
          </Text>
        </View>
      )}

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'ingredients' && styles.activeTab]}
          onPress={() => setActiveTab('ingredients')}
        >
          <Text style={[styles.tabText, activeTab === 'ingredients' && styles.activeTabText]}>
            Ingredients
          </Text>
          {missingIngredients.size > 0 && (
            <View style={styles.missingBadge}>
              <Text style={styles.missingBadgeText}>{missingIngredients.size}</Text>
            </View>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'instructions' && styles.activeTab]}
          onPress={() => setActiveTab('instructions')}
        >
          <Text style={[styles.tabText, activeTab === 'instructions' && styles.activeTabText]}>
            Instructions
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'nutrition' && styles.activeTab]}
          onPress={() => setActiveTab('nutrition')}
        >
          <Text style={[styles.tabText, activeTab === 'nutrition' && styles.activeTabText]}>
            Nutrition
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.contentContainer}>
        {activeTab === 'ingredients' && (
          <View style={styles.ingredientsContainer}>
            {missingIngredients.size > 0 && (
              <TouchableOpacity 
                style={styles.addToShoppingListButton}
                onPress={() => {
                  const missingIngredientsList = filterValidIngredients(recipe.extendedIngredients)
                    .filter(ing => missingIngredients.has(ing.id))
                    .map(ing => ing.original);
                  
                  router.push({
                    pathname: '/select-ingredients',
                    params: { 
                      ingredients: JSON.stringify(missingIngredientsList),
                      recipeName: recipe.title
                    }
                  });
                }}
              >
                <Ionicons name="cart-outline" size={20} color="#fff" />
                <Text style={styles.addToShoppingListText}>
                  Add {missingIngredients.size} missing item{missingIngredients.size > 1 ? 's' : ''} to shopping list
                </Text>
              </TouchableOpacity>
            )}
            {filterValidIngredients(recipe.extendedIngredients).map((ingredient, index) => {
                const isAvailable = availableIngredients.has(ingredient.id);
                return (
                  <View key={`ingredient-${ingredient.id}-${index}`} style={styles.ingredientItem}>
                    {isAvailable ? (
                      <Ionicons name="checkmark-circle" size={20} color="#297A56" />
                    ) : (
                      <Ionicons name="close-circle" size={20} color="#EF4444" />
                    )}
                    <Text style={[styles.ingredientText, !isAvailable && styles.missingIngredientText]}>
                      {ingredient.original}
                    </Text>
                    {isAvailable && (
                      <Text style={styles.availableText}>In pantry</Text>
                    )}
                  </View>
                );
              })}
          </View>
        )}

        {activeTab === 'instructions' && (
          <View style={styles.instructionsContainer}>
            {recipe.analyzedInstructions.length > 0 && recipe.analyzedInstructions[0].steps.length > 0 ? (
              recipe.analyzedInstructions[0].steps
                .map((step, index) => {
                  const cleanedText = cleanInstructionText(step.step);
                  return cleanedText ? (
                    <View key={`step-${step.number}-${index}`} style={styles.instructionStep}>
                      <View style={styles.stepNumber}>
                        <Text style={styles.stepNumberText}>{step.number}</Text>
                      </View>
                      <Text style={styles.stepText}>{cleanedText}</Text>
                    </View>
                  ) : null;
                })
                .filter(Boolean)
            ) : (
              getDefaultInstructions(recipe.title).map((instruction, index) => (
                <View key={`default-step-${index}`} style={styles.instructionStep}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.stepText}>{instruction}</Text>
                </View>
              ))
            )}
          </View>
        )}

        {activeTab === 'nutrition' && recipe.nutrition && (
          <View style={styles.nutritionContainer}>
            {recipe.nutrition.nutrients.slice(0, 10).map((nutrient, index) => (
              <View key={`nutrient-${nutrient.name}-${index}`} style={styles.nutrientItem}>
                <Text style={styles.nutrientName}>{nutrient.name}</Text>
                <View style={styles.nutrientValue}>
                  <Text style={styles.nutrientAmount}>
                    {nutrient.amount.toFixed(1)} {nutrient.unit}
                  </Text>
                  <Text style={styles.nutrientPercent}>
                    {nutrient.percentOfDailyNeeds.toFixed(0)}% DV
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Action Buttons */}
      {availableIngredients.size > 0 ? (
        <>
          <View style={styles.actionButtonsContainer}>
            <TouchableOpacity 
              style={[
                styles.startCookingButton,
                missingIngredients.size > 0 && styles.startCookingButtonDisabled
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

          {missingIngredients.size > 0 && (
            <TouchableOpacity 
              style={styles.addToListButton}
              onPress={() => {
                const missingList = recipe.extendedIngredients
                  .filter(ing => missingIngredients.has(ing.id))
                  .map(ing => ing.original);
                router.push({
                  pathname: '/select-ingredients',
                  params: { 
                    ingredients: JSON.stringify(missingList),
                    recipeName: recipe.title
                  }
                });
              }}
            >
              <Ionicons name="cart" size={20} color="#297A56" />
              <Text style={styles.addToListText}>
                Add {missingIngredients.size} to Shopping List
              </Text>
            </TouchableOpacity>
          )}
        </>
      ) : (
        /* All ingredients are missing */
        <View style={styles.allMissingContainer}>
          <Ionicons name="alert-circle" size={48} color="#297A56" style={styles.allMissingIcon} />
          <Text style={styles.allMissingTitle}>No ingredients available</Text>
          <Text style={styles.allMissingSubtitle}>
            You'll need to shop for all {missingIngredients.size} ingredients first
          </Text>
          <TouchableOpacity 
            style={styles.addAllToListButton}
            onPress={() => {
              const allIngredients = recipe.extendedIngredients.map(ing => ing.original);
              router.push({
                pathname: '/select-ingredients',
                params: { 
                  ingredients: JSON.stringify(allIngredients),
                  recipeName: recipe.title
                }
              });
            }}
          >
            <Ionicons name="cart" size={20} color="#fff" />
            <Text style={styles.addAllToListText}>
              Add to Shopping List
            </Text>
          </TouchableOpacity>
        </View>
      )}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
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
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  imageContainer: {
    height: 300,
    position: 'relative',
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
    height: 150,
  },
  backButton: {
    position: 'absolute',
    top: 10,
    left: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerActions: {
    position: 'absolute',
    top: 10,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ratingButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  ratingButtonActive: {
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  bookmarkButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 4,
  },
  recipeHeader: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
  },
  recipeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  recipeMetrics: {
    flexDirection: 'row',
    gap: 16,
  },
  metric: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricText: {
    color: '#fff',
    fontSize: 14,
  },
  tagsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  tag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  cuisineTag: {
    backgroundColor: '#E3F2FD',
  },
  dietTag: {
    backgroundColor: '#F3E5F5',
  },
  tagText: {
    fontSize: 12,
    fontWeight: '500',
  },
  summaryContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  summaryText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
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
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#297A56',
    fontWeight: '600',
  },
  contentContainer: {
    padding: 16,
    backgroundColor: '#fff',
    minHeight: 200,
  },
  ingredientsContainer: {
    gap: 12,
  },
  ingredientItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  ingredientText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    lineHeight: 20,
  },
  instructionsContainer: {
    gap: 16,
  },
  instructionStep: {
    flexDirection: 'row',
    gap: 12,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#297A56',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepNumberText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  stepText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
  },
  noInstructions: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 20,
  },
  nutritionContainer: {
    gap: 8,
  },
  nutrientItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  nutrientName: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  nutrientValue: {
    alignItems: 'flex-end',
  },
  nutrientAmount: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  nutrientPercent: {
    fontSize: 12,
    color: '#666',
  },
  bottomSpacer: {
    height: 50,
  },
  actionButtonsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 10,
    backgroundColor: '#fff',
    gap: 12,
  },
  startCookingButton: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  startCookingButtonDisabled: {
    backgroundColor: '#A0A0A0',
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
    paddingHorizontal: 20,
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
    paddingHorizontal: 20,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#297A56',
    marginHorizontal: 16,
    marginBottom: 20,
    gap: 8,
  },
  addToListText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
  },
  allMissingContainer: {
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 40,
    backgroundColor: '#f0f7f4',
    marginHorizontal: 16,
    marginTop: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#297A56',
  },
  allMissingIcon: {
    marginBottom: 16,
  },
  allMissingTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
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
  missingBadge: {
    backgroundColor: '#EF4444',
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 4,
  },
  missingBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  addToShoppingListButton: {
    backgroundColor: '#297A56',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  addToShoppingListText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  missingIngredientText: {
    color: '#666',
  },
  availableText: {
    fontSize: 12,
    color: '#297A56',
    fontWeight: '500',
  },
});