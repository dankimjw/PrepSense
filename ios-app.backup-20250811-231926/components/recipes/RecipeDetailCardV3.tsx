import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
  Animated,
  Modal,
  Platform,
  SafeAreaView
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Recipe } from '../../services/recipeService';
import { recipeService } from '../../services/recipeService';
import { QuickCompleteModal } from '../modals/QuickCompleteModal';
import { getIngredientIcon, capitalizeIngredientName } from '../../utils/ingredientIcons';
import { Config } from '../../config';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const HERO_IMAGE_HEIGHT = SCREEN_HEIGHT * 0.25; // 25% of screen height for smaller hero
const STICKY_HEADER_HEIGHT = 60; // Height of sticky header when collapsed
const SCROLL_THRESHOLD = HERO_IMAGE_HEIGHT - STICKY_HEADER_HEIGHT; // When to start sticking

interface RecipeDetailCardV3Props {
  recipe: Recipe;
  onBack?: () => void;
  onRatingSubmitted?: (rating: 'thumbs_up' | 'thumbs_down') => void;
}

interface IngredientWithStatus {
  original: string;
  name: string;
  amount?: number;
  unit?: string;
  isAvailable: boolean;
  pantryItemId?: number;
}

// Helper function to normalize recipe data structures
const normalizeRecipeData = (recipe: Recipe) => {
  // Handle chat-generated recipes that might have different data structure
  const normalizedRecipe = { ...recipe };
  
  // Normalize ingredients - handle both Spoonacular and chat-generated formats
  if (!normalizedRecipe.extendedIngredients && recipe.ingredients) {
    // Convert chat-generated ingredients array to extendedIngredients format
    if (Array.isArray(recipe.ingredients)) {
      normalizedRecipe.extendedIngredients = recipe.ingredients.map((ingredient, index) => {
        if (typeof ingredient === 'string') {
          // Simple string format
          return {
            id: index + 1,
            name: ingredient,
            original: ingredient,
            amount: undefined,
            unit: undefined
          };
        } else if (typeof ingredient === 'object') {
          // Object format with structured data
          return {
            id: ingredient.id || index + 1,
            name: ingredient.name || ingredient.ingredient_name || '',
            original: ingredient.original || ingredient.name || ingredient.ingredient_name || '',
            amount: ingredient.amount || ingredient.quantity,
            unit: ingredient.unit || ''
          };
        }
        return {
          id: index + 1,
          name: String(ingredient),
          original: String(ingredient),
          amount: undefined,
          unit: undefined
        };
      });
    }
  }
  
  // Normalize instructions - handle both Spoonacular and chat-generated formats
  if (!normalizedRecipe.analyzedInstructions && recipe.instructions) {
    if (Array.isArray(recipe.instructions)) {
      // Array of strings format (chat-generated)
      normalizedRecipe.analyzedInstructions = [{
        name: '',
        steps: recipe.instructions.map((instruction, index) => ({
          number: index + 1,
          step: typeof instruction === 'string' ? instruction : instruction.step || String(instruction),
          ingredients: [],
          equipment: []
        }))
      }];
    } else if (typeof recipe.instructions === 'string') {
      // Single string format - split by common delimiters
      const steps = recipe.instructions
        .split(/\d+\.\s*/)
        .filter(step => step.trim().length > 0)
        .map((step, index) => ({
          number: index + 1,
          step: step.trim(),
          ingredients: [],
          equipment: []
        }));
      
      normalizedRecipe.analyzedInstructions = [{
        name: '',
        steps: steps.length > 0 ? steps : [{
          number: 1,
          step: recipe.instructions,
          ingredients: [],
          equipment: []
        }]
      }];
    }
  }
  
  // Ensure analyzedInstructions exists with at least empty structure
  if (!normalizedRecipe.analyzedInstructions) {
    normalizedRecipe.analyzedInstructions = [{
      name: '',
      steps: []
    }];
  }
  
  // Normalize nutrition data
  if (!normalizedRecipe.nutrition && recipe.nutrition) {
    normalizedRecipe.nutrition = {
      calories: recipe.nutrition.calories || 0,
      protein: recipe.nutrition.protein || 0,
      carbs: recipe.nutrition.carbs || recipe.nutrition.carbohydrates || 0,
      fat: recipe.nutrition.fat || 0,
      fiber: recipe.nutrition.fiber || 0,
      sugar: recipe.nutrition.sugar || 0,
      ...recipe.nutrition
    };
  }
  
  // Set default values for missing properties
  normalizedRecipe.readyInMinutes = normalizedRecipe.readyInMinutes || normalizedRecipe.time || 30;
  normalizedRecipe.servings = normalizedRecipe.servings || 4;
  normalizedRecipe.image = normalizedRecipe.image || 'https://via.placeholder.com/400x300?text=Recipe+Image';
  
  return normalizedRecipe;
};

export default function RecipeDetailCardV3({ 
  recipe, 
  onBack,
  onRatingSubmitted 
}: RecipeDetailCardV3Props) {
  const router = useRouter();
  const [isBookmarked, setIsBookmarked] = useState(recipe.is_favorite || false);
  const [showAllIngredients, setShowAllIngredients] = useState(false);
  const [hasCookedRecipe, setHasCookedRecipe] = useState(false);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [showNutritionModal, setShowNutritionModal] = useState(false);
  const [showQuickCompleteModal, setShowQuickCompleteModal] = useState(false);
  const [userRating, setUserRating] = useState<'thumbs_up' | 'thumbs_down' | null>(null);
  
  const bookmarkAnimation = useRef(new Animated.Value(1)).current;
  const scrollY = useRef(new Animated.Value(0)).current;
  const scrollViewRef = useRef<ScrollView>(null);

  // Normalize the recipe data to handle different formats
  const normalizedRecipe = normalizeRecipeData(recipe);

  // Animated values for sticky header
  const headerOpacity = scrollY.interpolate({
    inputRange: [0, SCROLL_THRESHOLD],
    outputRange: [0, 1],
    extrapolate: 'clamp',
  });

  const heroImageTranslateY = scrollY.interpolate({
    inputRange: [0, SCROLL_THRESHOLD],
    outputRange: [0, -SCROLL_THRESHOLD],
    extrapolate: 'clamp',
  });

  const overlayButtonsTranslateY = scrollY.interpolate({
    inputRange: [0, SCROLL_THRESHOLD],
    outputRange: [0, -SCROLL_THRESHOLD],
    extrapolate: 'clamp',
  });

  // Process ingredients with availability status using normalized data
  const processedIngredients: IngredientWithStatus[] = normalizedRecipe.extendedIngredients?.map(ing => ({
    original: ing.original || ing.name || '',
    name: capitalizeIngredientName(ing.name || ing.original || ''),
    amount: ing.amount,
    unit: ing.unit,
    isAvailable: normalizedRecipe.available_ingredients?.includes(ing.original) || false,
    pantryItemId: normalizedRecipe.pantry_item_matches?.[ing.original]?.[0]?.pantry_item_id
  })) || [];

  const availableIngredients = processedIngredients.filter(ing => ing.isAvailable);
  const missingIngredients = processedIngredients.filter(ing => !ing.isAvailable);
  
  const INITIAL_INGREDIENTS_SHOWN = 5;
  const displayedIngredients = showAllIngredients 
    ? processedIngredients 
    : processedIngredients.slice(0, INITIAL_INGREDIENTS_SHOWN);
    
  const instructions = normalizedRecipe.analyzedInstructions?.[0]?.steps || [];

  const handleBookmark = async () => {
    Animated.sequence([
      Animated.timing(bookmarkAnimation, {
        toValue: 1.3,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(bookmarkAnimation, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();

    setIsBookmarked(!isBookmarked);
    
    try {
      if (!isBookmarked) {
        await recipeService.saveRecipe(normalizedRecipe, 111); // Demo user
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
      setIsBookmarked(isBookmarked); // Revert on error
    }
  };

  const handleCookNow = () => {
    setShowRatingModal(false);
    setShowNutritionModal(false);
    setShowQuickCompleteModal(false);
    
    router.push({
      pathname: '/cooking-mode',
      params: { 
        recipeId: normalizedRecipe.id,
        recipeData: JSON.stringify(normalizedRecipe)
      }
    });
  };

  const handleQuickComplete = () => {
    setShowQuickCompleteModal(true);
  };

  const handleQuickCompleteConfirm = async () => {
    setShowQuickCompleteModal(false);
    
    if (normalizedRecipe.id) {
      try {
        const response = await fetch(`${Config.API_BASE_URL}/user-recipes/${normalizedRecipe.id}/mark-cooked`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          console.log('Recipe marked as cooked after QuickComplete');
        }
      } catch (error) {
        console.error('Error marking recipe as cooked:', error);
      }
    }
    
    setHasCookedRecipe(true);
    setShowRatingModal(true);
  };

  const handleRating = async (rating: 'thumbs_up' | 'thumbs_down') => {
    setUserRating(rating);
    
    try {
      await recipeService.rateRecipe(normalizedRecipe.id, 111, rating); // Demo user
      
      if (onRatingSubmitted) {
        onRatingSubmitted(rating);
      }
    } catch (error) {
      console.error('Error submitting rating:', error);
    }
  };

  const formatCookingTime = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const getMatchPercentage = () => {
    const total = processedIngredients.length;
    const available = availableIngredients.length;
    return total > 0 ? Math.round((available / total) * 100) : 0;
  };

  const navigateToRecipes = () => {
    router.push('/(tabs)/recipes');
  };

  return (
    <View style={styles.container}>
      {/* Sticky Header (appears when scrolled) */}
      <Animated.View 
        style={[
          styles.stickyHeader,
          {
            opacity: headerOpacity,
          }
        ]}
      >
        <SafeAreaView style={styles.stickyHeaderContent}>
          <TouchableOpacity
            style={styles.stickyButton}
            onPress={navigateToRecipes}
            activeOpacity={0.8}
          >
            <Ionicons name="close" size={20} color="#333" />
          </TouchableOpacity>
          
          <Text style={styles.stickyTitle} numberOfLines={1}>
            {normalizedRecipe.title}
          </Text>
          
          <View style={styles.stickyRightButtons}>
            {userRating && (
              <View style={[styles.stickyButton, styles.ratingStickyIndicator]}>
                <Ionicons 
                  name={userRating === 'thumbs_up' ? "thumbs-up" : "thumbs-down"} 
                  size={16} 
                  color={userRating === 'thumbs_up' ? "#4CAF50" : "#F44336"} 
                />
              </View>
            )}
            
            <TouchableOpacity
              style={styles.stickyButton}
              onPress={handleBookmark}
              activeOpacity={0.8}
            >
              <Animated.View style={{ transform: [{ scale: bookmarkAnimation }] }}>
                <Ionicons 
                  name={isBookmarked ? "bookmark" : "bookmark-outline"} 
                  size={18} 
                  color={isBookmarked ? "#FF6B6B" : "#333"} 
                />
              </Animated.View>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Animated.View>

      {/* Main ScrollView with Hero Image */}
      <Animated.ScrollView 
        ref={scrollViewRef}
        style={styles.scrollableContent}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContentContainer}
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { y: scrollY } } }],
          { useNativeDriver: false }
        )}
        scrollEventThrottle={16}
      >
        {/* Hero Image Section */}
        <View style={styles.heroSection}>
          <Image 
            source={{ uri: normalizedRecipe.image || 'https://via.placeholder.com/400' }}
            style={styles.heroImage}
            resizeMode="cover"
          />
          
          {/* Floating Overlay Buttons */}
          <View style={styles.overlayButtons}>
            <TouchableOpacity
              style={styles.overlayButton}
              onPress={navigateToRecipes}
              activeOpacity={0.8}
            >
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
            
            <View style={styles.rightButtons}>
              {userRating && (
                <View style={[styles.overlayButton, styles.ratingIndicator]}>
                  <Ionicons 
                    name={userRating === 'thumbs_up' ? "thumbs-up" : "thumbs-down"} 
                    size={20} 
                    color={userRating === 'thumbs_up' ? "#4CAF50" : "#F44336"} 
                  />
                </View>
              )}
              
              <TouchableOpacity
                style={styles.overlayButton}
                onPress={handleBookmark}
                activeOpacity={0.8}
              >
                <Animated.View style={{ transform: [{ scale: bookmarkAnimation }] }}>
                  <Ionicons 
                    name={isBookmarked ? "bookmark" : "bookmark-outline"} 
                    size={22} 
                    color={isBookmarked ? "#FF6B6B" : "#333"} 
                  />
                </Animated.View>
              </TouchableOpacity>
            </View>
          </View>
        </View>
        {/* Title and Info Card */}
        <View style={styles.infoCard}>
          <Text style={styles.title}>{normalizedRecipe.title}</Text>
          
          {/* Stat Bar */}
          <View style={styles.statBar}>
            <View style={styles.statItem}>
              <Ionicons name="time-outline" size={16} color="#666" />
              <Text style={styles.statText}>{formatCookingTime(normalizedRecipe.readyInMinutes || 30)}</Text>
            </View>
            
            <TouchableOpacity 
              style={styles.statItem}
              onPress={() => setShowNutritionModal(true)}
            >
              <Text style={styles.statText}>{normalizedRecipe.nutrition?.calories || 0} kcal</Text>
              <Ionicons name="chevron-forward" size={12} color="#666" />
            </TouchableOpacity>
            
            <View style={styles.statItem}>
              <View style={styles.matchBar}>
                <View style={[styles.matchFill, { width: `${getMatchPercentage()}%` }]} />
              </View>
              <Text style={styles.statText}>{getMatchPercentage()}% match</Text>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtonsContainer}>
            <TouchableOpacity 
              style={[styles.actionButton, styles.cookNowButton]}
              onPress={handleCookNow}
              activeOpacity={0.9}
            >
              <Text style={styles.cookNowButtonText}>Cook Now</Text>
            </TouchableOpacity>

            {normalizedRecipe.available_ingredients && normalizedRecipe.available_ingredients.length > 0 && (
              <TouchableOpacity 
                style={[styles.actionButton, styles.quickCompleteButton]}
                onPress={handleQuickComplete}
                activeOpacity={0.9}
              >
                <Ionicons name="flash" size={18} color="#6366F1" />
                <Text style={styles.quickCompleteButtonText}>Quick</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Ingredients Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              Ingredients ({processedIngredients.length})
            </Text>
            {availableIngredients.length > 0 && (
              <Text style={styles.legendText}>
                ✓ = In pantry
              </Text>
            )}
          </View>

          <View style={styles.ingredientList}>
            {displayedIngredients.map((ingredient, index) => (
              <View key={index} style={styles.ingredientRow}>
                <View style={styles.ingredientIcon}>
                  <View style={styles.foodIconContainer}>
                    <Text style={styles.foodIcon}>{getIngredientIcon(ingredient.name)}</Text>
                  </View>
                  {ingredient.isAvailable && (
                    <Ionicons 
                      name="checkmark-circle" 
                      size={14} 
                      color="#4CAF50" 
                      style={styles.statusIcon}
                    />
                  )}
                </View>
                <Text style={styles.ingredientText}>
                  {ingredient.original}
                </Text>
              </View>
            ))}
          </View>

          {processedIngredients.length > INITIAL_INGREDIENTS_SHOWN && (
            <TouchableOpacity
              style={styles.showMoreButton}
              onPress={() => setShowAllIngredients(!showAllIngredients)}
            >
              <Text style={styles.showMoreText}>
                {showAllIngredients 
                  ? 'Show less' 
                  : `Show all ${processedIngredients.length} ingredients`}
              </Text>
              <Ionicons 
                name={showAllIngredients ? "chevron-up" : "chevron-down"} 
                size={16} 
                color="#007AFF" 
              />
            </TouchableOpacity>
          )}
        </View>

        {/* Instructions Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Instructions ({instructions.length})
          </Text>

          <View style={styles.stepList}>
            {instructions.length > 0 ? (
              instructions.map((step, index) => (
                <View key={index} style={styles.stepRow}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{step.number}</Text>
                  </View>
                  <Text style={styles.stepText}>{step.step}</Text>
                </View>
              ))
            ) : (
              <View style={styles.noInstructionsContainer}>
                <Ionicons name="information-circle-outline" size={24} color="#666" />
                <Text style={styles.noInstructionsText}>
                  No detailed instructions available for this recipe.
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Debug Recipe ID */}
        {normalizedRecipe.id && (
          <View style={styles.debugIdContainer}>
            <Text style={styles.debugIdText}>Recipe ID: {normalizedRecipe.id}</Text>
          </View>
        )}

        {/* Extra padding at bottom */}
        <View style={{ height: 40 }} />
      </Animated.ScrollView>

      {/* Rating Modal */}
      <Modal
        visible={showRatingModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRatingModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>How did it turn out?</Text>
            <Text style={styles.modalSubtitle}>Your feedback helps us improve recommendations</Text>
            
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.positiveModalButton]}
                onPress={() => {
                  handleRating('thumbs_up');
                  setShowRatingModal(false);
                }}
              >
                <Ionicons name="thumbs-up" size={32} color="#4CAF50" />
                <Text style={styles.modalButtonText}>Great!</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.modalButton, styles.negativeModalButton]}
                onPress={() => {
                  handleRating('thumbs_down');
                  setShowRatingModal(false);
                }}
              >
                <Ionicons name="thumbs-down" size={32} color="#F44336" />
                <Text style={styles.modalButtonText}>Not so good</Text>
              </TouchableOpacity>
            </View>
            
            <TouchableOpacity
              style={styles.modalSkip}
              onPress={() => setShowRatingModal(false)}
            >
              <Text style={styles.modalSkipText}>Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Nutrition Modal */}
      <Modal
        visible={showNutritionModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowNutritionModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, styles.nutritionModal]}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Nutrition Facts</Text>
              <TouchableOpacity onPress={() => setShowNutritionModal(false)}>
                <Ionicons name="close" size={24} color="#333" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.nutritionGrid}>
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Calories</Text>
                <Text style={styles.nutritionValue}>{normalizedRecipe.nutrition?.calories || 0}</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Protein</Text>
                <Text style={styles.nutritionValue}>{normalizedRecipe.nutrition?.protein || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Carbs</Text>
                <Text style={styles.nutritionValue}>{normalizedRecipe.nutrition?.carbs || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Fat</Text>
                <Text style={styles.nutritionValue}>{normalizedRecipe.nutrition?.fat || 0}g</Text>
              </View>
            </View>
            
            <Text style={styles.nutritionDisclaimer}>
              * Nutritional values are estimates
            </Text>
          </View>
        </View>
      </Modal>

      {/* Quick Complete Modal */}
      <QuickCompleteModal
        visible={showQuickCompleteModal}
        onClose={() => setShowQuickCompleteModal(false)}
        onConfirm={handleQuickCompleteConfirm}
        recipeId={normalizedRecipe.id}
        recipeName={normalizedRecipe.title}
        userId={111}
        servings={normalizedRecipe.servings}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  
  // Hero Section
  heroSection: {
    height: HERO_IMAGE_HEIGHT,
    position: 'relative',
  },
  heroImage: {
    width: SCREEN_WIDTH,
    height: HERO_IMAGE_HEIGHT,
    backgroundColor: '#E0E0E0',
  },

  // Sticky Header
  stickyHeader: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: STICKY_HEADER_HEIGHT + (Platform.OS === 'ios' ? 44 : 24),
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    zIndex: 100,
  },
  stickyHeaderContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 10 : 0,
  },
  stickyButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stickyTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A1A',
    marginHorizontal: 16,
    textAlign: 'center',
  },
  stickyRightButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  ratingStickyIndicator: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
  },
  
  // Overlay Buttons
  overlayButtons: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 54 : 34,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    zIndex: 10,
  },
  rightButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  overlayButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  ratingIndicator: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
  },
  
  // Scrollable Content
  scrollableContent: {
    flex: 1,
  },
  scrollContentContainer: {
    paddingBottom: 20,
  },
  
  // Info Card
  infoCard: {
    backgroundColor: '#FFF',
    marginTop: -20,
    marginHorizontal: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
    zIndex: 5,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 16,
    lineHeight: 28,
  },
  
  // Stat Bar
  statBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statText: {
    fontSize: 14,
    color: '#666',
  },
  matchBar: {
    width: 50,
    height: 4,
    backgroundColor: '#E0E0E0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  matchFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  
  // Action Buttons
  actionButtonsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cookNowButton: {
    backgroundColor: '#FF6B6B',
  },
  cookNowButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
  quickCompleteButton: {
    backgroundColor: '#F3F4F6',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 0,
    paddingHorizontal: 20,
  },
  quickCompleteButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366F1',
  },
  
  // Sections
  section: {
    marginTop: 20,
    marginHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  legendText: {
    fontSize: 12,
    color: '#666',
  },
  
  // Ingredients
  ingredientList: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  ingredientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  ingredientIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
    position: 'relative',
  },
  foodIconContainer: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
    alignItems: 'center',
  },
  foodIcon: {
    fontSize: 14,
  },
  statusIcon: {
    position: 'absolute',
    right: -4,
    bottom: -2,
    backgroundColor: 'white',
    borderRadius: 7,
  },
  ingredientText: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    lineHeight: 20,
  },
  
  // Steps
  stepList: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  stepRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  stepNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FF6B6B',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFF',
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  noInstructionsContainer: {
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  noInstructionsText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  
  // Show More
  showMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 8,
    gap: 4,
  },
  showMoreText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  
  // Modals
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 24,
    width: '85%',
    maxWidth: 320,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1A1A1A',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  modalButton: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    width: 120,
  },
  positiveModalButton: {
    backgroundColor: '#E8F5E9',
  },
  negativeModalButton: {
    backgroundColor: '#FFEBEE',
  },
  modalButtonText: {
    marginTop: 8,
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  modalSkip: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  modalSkipText: {
    fontSize: 16,
    color: '#666',
  },
  
  // Nutrition Modal
  nutritionModal: {
    width: '90%',
    maxWidth: 400,
  },
  nutritionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 16,
    marginBottom: 24,
  },
  nutritionItem: {
    width: '50%',
    paddingVertical: 12,
  },
  nutritionLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  nutritionValue: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  nutritionDisclaimer: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Debug Recipe ID
  debugIdContainer: {
    alignItems: 'center',
    paddingVertical: 8,
    marginTop: 16,
    marginHorizontal: 16,
  },
  debugIdText: {
    fontSize: 11,
    color: '#999',
    fontStyle: 'italic',
    opacity: 0.7,
  },
});