import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
  Animated,
  ActivityIndicator,
  Modal,
  Platform,
  Alert
} from 'react-native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Recipe } from '../../services/recipeService';
import { pantryService } from '../../services/pantryService';
import { recipeService } from '../../services/recipeService';
import { shoppingListService } from '../../services/shoppingListService';
import { QuickCompleteModal } from '../modals/QuickCompleteModal';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const HERO_IMAGE_HEIGHT = SCREEN_WIDTH * 0.6; // 16:10 aspect ratio

interface RecipeDetailCardV2Props {
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

export default function RecipeDetailCardV2({ 
  recipe, 
  onBack,
  onRatingSubmitted 
}: RecipeDetailCardV2Props) {
  const router = useRouter();
  const [isBookmarked, setIsBookmarked] = useState(recipe.is_favorite || false);
  const [showAllIngredients, setShowAllIngredients] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasCookedRecipe, setHasCookedRecipe] = useState(false);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [showNutritionModal, setShowNutritionModal] = useState(false);
  const [showQuickCompleteModal, setShowQuickCompleteModal] = useState(false);
  
  const bookmarkAnimation = useRef(new Animated.Value(1)).current;

  // Process ingredients with availability status
  const processedIngredients: IngredientWithStatus[] = recipe.extendedIngredients?.map((ing: any) => ({
    original: ing.original || ing.name || '',
    name: ing.name || ing.original || '',
    amount: ing.amount,
    unit: ing.unit,
    isAvailable: recipe.available_ingredients?.includes(ing.original) || false,
    pantryItemId: recipe.pantry_item_matches?.[ing.original]?.[0]?.pantry_item_id
  })) || [];

  const availableIngredients = processedIngredients.filter(ing => ing.isAvailable);
  const missingIngredients = processedIngredients.filter(ing => !ing.isAvailable);
  
  // For progressive disclosure - only for ingredients
  const INITIAL_INGREDIENTS_SHOWN = 5;
  
  const displayedIngredients = showAllIngredients 
    ? processedIngredients 
    : processedIngredients.slice(0, INITIAL_INGREDIENTS_SHOWN);
    
  const instructions = recipe.analyzedInstructions?.[0]?.steps || [];
  // Always show all steps - no truncation
  const displayedSteps = instructions;

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
        await recipeService.saveRecipe(recipe, 111); // Demo user
      } else {
        // Remove from saved recipes
        // await recipeService.removeRecipe(recipe.id, 111);
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
      setIsBookmarked(isBookmarked); // Revert on error
    }
  };

  const handleCookNow = () => {
    // Navigate to cooking mode or start cooking flow
    router.push({
      pathname: '/cooking-mode',
      params: { 
        recipeId: recipe.id,
        recipeData: JSON.stringify(recipe)
      }
    });
  };

  const handleQuickComplete = () => {
    setShowQuickCompleteModal(true);
  };

  const handleQuickCompleteSuccess = () => {
    // Close modal and navigate back
    setShowQuickCompleteModal(false);
    Alert.alert(
      'Recipe Completed!',
      'Your pantry has been updated.',
      [
        {
          text: 'OK',
          onPress: () => {
            if (onBack) {
              onBack();
            } else {
              router.back();
            }
          },
        },
      ]
    );
  };

  const handleFinishCooking = () => {
    setHasCookedRecipe(true);
    setShowRatingModal(true);
  };

  const handleRating = async (rating: 'thumbs_up' | 'thumbs_down') => {
    setShowRatingModal(false);
    
    try {
      // Save rating to backend
      await recipeService.rateRecipe(recipe.id, 111, rating); // Demo user
      
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
    const percentage = total > 0 ? Math.round((available / total) * 100) : 0;
    
    // Debug logging to help identify data issues
    console.log('Match calculation:', { 
      total, 
      available, 
      percentage,
      hasExtendedIngredients: !!recipe.extendedIngredients,
      hasAvailableIngredients: !!recipe.available_ingredients,
      extendedIngredientsLength: recipe.extendedIngredients?.length || 0,
      availableIngredientsLength: recipe.available_ingredients?.length || 0
    });
    
    return percentage;
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Simplified Top App Bar */}
      <View style={styles.appBar}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={onBack || (() => router.back())}
        >
          <Ionicons name="arrow-back" size={24} color="#333" />
          <Text style={styles.backText}>Recipe Details</Text>
        </TouchableOpacity>
      </View>

      {/* Hero Image with Bookmark Overlay */}
      <View style={styles.heroContainer}>
        <Image 
          source={{ uri: recipe.image || 'https://via.placeholder.com/400' }}
          style={styles.heroImage}
          resizeMode="cover"
        />
        <TouchableOpacity
          style={styles.bookmarkOverlay}
          onPress={handleBookmark}
          activeOpacity={0.8}
        >
          <Animated.View style={{ transform: [{ scale: bookmarkAnimation }] }}>
            <Ionicons 
              name={isBookmarked ? "bookmark" : "bookmark-outline"} 
              size={28} 
              color={isBookmarked ? "#FF6B6B" : "#FFF"} 
            />
          </Animated.View>
        </TouchableOpacity>
      </View>

      {/* Primary CTAs */}
      <View style={styles.ctaContainer}>
        <TouchableOpacity 
          style={styles.primaryCTA}
          onPress={hasCookedRecipe ? handleFinishCooking : handleCookNow}
          activeOpacity={0.9}
        >
          <Text style={styles.primaryCTAText}>
            {hasCookedRecipe ? 'Finish Cooking' : 'Cook Now'}
          </Text>
        </TouchableOpacity>
        
        {!hasCookedRecipe && (
          <TouchableOpacity 
            style={styles.quickCompleteCTA}
            onPress={handleQuickComplete}
            activeOpacity={0.9}
          >
            <Ionicons name="flash" size={20} color="#6366F1" />
            <Text style={styles.quickCompleteCTAText}>Quick Complete</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Title */}
      <Text style={styles.title}>{recipe.title}</Text>

      {/* Stat Bar */}
      <View style={styles.statBar}>
        <View style={styles.statChip}>
          <Ionicons name="time-outline" size={16} color="#666" />
          <Text style={styles.statText}>{formatCookingTime(recipe.readyInMinutes || 30)}</Text>
        </View>
        
        <View style={styles.statDivider} />
        
        <TouchableOpacity 
          style={styles.statChip}
          onPress={() => setShowNutritionModal(true)}
        >
          <Text style={styles.statText}>{recipe.nutrition?.calories || 0} kcal</Text>
        </TouchableOpacity>
        
        <View style={styles.statDivider} />
        
        <View style={styles.statChip}>
          <Text style={styles.statText}>{recipe.nutrition?.protein || 0}g protein</Text>
        </View>
        
        <View style={styles.statDivider} />
        
        <View style={styles.statChip}>
          <View style={styles.matchBar}>
            <View style={[styles.matchFill, { width: `${getMatchPercentage()}%` }]} />
          </View>
          <Text style={styles.statText}>{getMatchPercentage()}% match</Text>
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
              ✓ = In your pantry
            </Text>
          )}
        </View>

        <View style={styles.ingredientList}>
          {displayedIngredients.map((ingredient, index) => (
            <View key={index} style={styles.ingredientRow}>
              <View style={styles.ingredientIcon}>
                {ingredient.isAvailable ? (
                  <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />
                ) : (
                  <Ionicons name="add-circle-outline" size={20} color="#FF9800" />
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

        {/* Shopping list moved to RecipeCompletionModal for better UX */}
      </View>

      {/* Instructions Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          Steps ({instructions.length})
        </Text>

        <View style={styles.stepList}>
          {displayedSteps.map((step: any, index: number) => (
            <View key={index} style={styles.stepRow}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>{step.number}</Text>
              </View>
              <Text style={styles.stepText}>{step.step}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Bottom Actions (only shown after cooking) */}
      {hasCookedRecipe && (
        <View style={styles.bottomActions}>
          <TouchableOpacity
            style={[styles.ratingButton, styles.positiveButton]}
            onPress={() => handleRating('thumbs_up')}
          >
            <Ionicons name="thumbs-up" size={24} color="#4CAF50" />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.ratingButton, styles.negativeButton]}
            onPress={() => handleRating('thumbs_down')}
          >
            <Ionicons name="thumbs-down" size={24} color="#F44336" />
          </TouchableOpacity>
        </View>
      )}

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
                onPress={() => handleRating('thumbs_up')}
              >
                <Ionicons name="thumbs-up" size={32} color="#4CAF50" />
                <Text style={styles.modalButtonText}>Great!</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.modalButton, styles.negativeModalButton]}
                onPress={() => handleRating('thumbs_down')}
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
                <Text style={styles.nutritionValue}>{recipe.nutrition?.calories || 0}</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Protein</Text>
                <Text style={styles.nutritionValue}>{recipe.nutrition?.protein || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Carbs</Text>
                <Text style={styles.nutritionValue}>{recipe.nutrition?.carbs || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Fat</Text>
                <Text style={styles.nutritionValue}>{recipe.nutrition?.fat || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Fiber</Text>
                <Text style={styles.nutritionValue}>{recipe.nutrition?.fiber || 0}g</Text>
              </View>
              
              <View style={styles.nutritionItem}>
                <Text style={styles.nutritionLabel}>Sugar</Text>
                <Text style={styles.nutritionValue}>{recipe.nutrition?.sugar || 0}g</Text>
              </View>
            </View>
            
            <Text style={styles.nutritionDisclaimer}>
              * Nutritional values are estimates and may vary based on specific ingredients used.
            </Text>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  
  // App Bar
  appBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    paddingBottom: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingRight: 16,
  },
  backText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 8,
  },
  
  // Hero Image
  heroContainer: {
    position: 'relative',
  },
  heroImage: {
    width: SCREEN_WIDTH,
    height: HERO_IMAGE_HEIGHT,
    backgroundColor: '#E0E0E0',
  },
  bookmarkOverlay: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  // Primary CTA
  ctaContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: -28,
    gap: 12,
  },
  primaryCTA: {
    backgroundColor: '#FF6B6B',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 28,
    shadowColor: '#FF6B6B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  quickCompleteCTA: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 28,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  quickCompleteCTAText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6366F1',
  },
  primaryCTAText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF',
  },
  
  // Title
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginHorizontal: 16,
    marginBottom: 12,
    lineHeight: 32,
  },
  
  // Stat Bar
  statBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 24,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#FFF',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statChip: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 14,
    color: '#666',
  },
  statDivider: {
    width: 1,
    height: 16,
    backgroundColor: '#E0E0E0',
    marginHorizontal: 8,
  },
  matchBar: {
    width: 40,
    height: 4,
    backgroundColor: '#E0E0E0',
    borderRadius: 2,
    overflow: 'hidden',
    marginRight: 4,
  },
  matchFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  
  // Sections
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
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
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  ingredientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  ingredientIcon: {
    marginRight: 12,
  },
  ingredientText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
  },
  
  // Steps
  stepList: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  stepRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#FF6B6B',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFF',
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  
  // Show More Button
  showMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 8,
    gap: 4,
  },
  showMoreText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  
  // Bottom Actions
  bottomActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 24,
    gap: 32,
  },
  ratingButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  positiveButton: {
    backgroundColor: '#E8F5E9',
  },
  negativeButton: {
    backgroundColor: '#FFEBEE',
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
});