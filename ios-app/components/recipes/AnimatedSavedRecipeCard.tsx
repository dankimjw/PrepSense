import React, { useEffect, useState } from 'react';
import { TouchableOpacity, Text, Image, View, StyleSheet, Alert } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withSequence,
  withDelay,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Config } from '../../config';
import { router } from 'expo-router';

// Fallback image URL for recipes with missing or invalid images
const FALLBACK_RECIPE_IMAGE = 'https://img.spoonacular.com/recipes/default-312x231.jpg';

interface SavedRecipe {
  id: string;
  recipe_id: number;
  recipe_title: string;
  recipe_image: string;
  recipe_data: any;
  rating: 'thumbs_up' | 'thumbs_down' | 'neutral';
  is_favorite?: boolean;
  source: string;
  status?: 'saved' | 'cooked';
  cooked_at?: string | null;
  created_at: string;
  updated_at: string;
}

interface AnimatedSavedRecipeCardProps {
  recipe: SavedRecipe;
  onPress: () => void;
  onRating?: (rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => void;
  onFavorite?: (isFavorite: boolean) => void;
  onDelete?: () => void;
  index?: number;
  testID?: string;
}

const AnimatedSavedRecipeCard: React.FC<AnimatedSavedRecipeCardProps> = ({
  recipe,
  onPress,
  onRating,
  onFavorite,
  onDelete,
  index = 0,
  testID,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  
  // Animation values
  const scale = useSharedValue(1);
  const enterProgress = useSharedValue(0);
  const imageOpacity = useSharedValue(0);
  const ratingScale = useSharedValue(1);
  const favoriteScale = useSharedValue(1);

  // Staggered entrance animation
  useEffect(() => {
    const delay = index * 100;
    setTimeout(() => {
      enterProgress.value = withSpring(1, {
        damping: 15,
        stiffness: 200,
      });
    }, delay);
  }, [index]);

  // Image load animation
  const handleImageLoad = () => {
    setImageLoaded(true);
    imageOpacity.value = withSpring(1, { damping: 15 });
  };

  // Enhanced recipe ID resolution with comprehensive fallback logic
  const getRecipeId = (): number | null => {
    const possibleIds = [
      recipe.recipe_id,
      recipe.recipe_data?.external_recipe_id,
      recipe.recipe_data?.id,
      recipe.recipe_data?.spoonacular_id,
      parseInt(recipe.id, 10) // Convert string ID to number as last resort
    ];
    
    for (const id of possibleIds) {
      if (id && (typeof id === 'number' || typeof id === 'string')) {
        const numericId = typeof id === 'string' ? parseInt(id, 10) : id;
        if (!isNaN(numericId) && numericId > 0) {
          console.log('🔍 AnimatedSavedRecipeCard - Found recipe ID:', {
            recipe_id: recipe.id,
            source_field: possibleIds.indexOf(id) === 0 ? 'recipe_id' : 
                         possibleIds.indexOf(id) === 1 ? 'external_recipe_id' :
                         possibleIds.indexOf(id) === 2 ? 'recipe_data.id' :
                         possibleIds.indexOf(id) === 3 ? 'spoonacular_id' : 'fallback_id',
            found_id: numericId
          });
          return numericId;
        }
      }
    }
    
    console.error('❌ AnimatedSavedRecipeCard - No valid recipe ID found:', {
      recipe_id: recipe.id,
      recipe_id_field: recipe.recipe_id,
      recipe_data_keys: recipe.recipe_data ? Object.keys(recipe.recipe_data) : 'no recipe_data'
    });
    return null;
  };

  // Enhanced image URL handling with proper fallback
  const getImageUrl = (): string => {
    let imageUrl = recipe.recipe_image || recipe.recipe_data?.image || recipe.recipe_data?.image_url || '';
    
    console.log('🖼️ AnimatedSavedRecipeCard - Processing image URL:', {
      recipe_id: recipe.id,
      recipe_image: recipe.recipe_image,
      recipe_data_image: recipe.recipe_data?.image,
      recipe_data_image_url: recipe.recipe_data?.image_url,
      initial_url: imageUrl
    });
    
    // Fix relative URLs for backend-served images
    if (imageUrl && !imageUrl.startsWith('http')) {
      const baseUrl = Config.API_BASE_URL.replace('/api/v1', '');
      imageUrl = `${baseUrl}${imageUrl.startsWith('/') ? '' : '/'}${imageUrl}`;
      console.log('🔧 AnimatedSavedRecipeCard - Fixed relative image URL:', {
        original: recipe.recipe_image,
        fixed: imageUrl
      });
    }
    
    // Return fallback image if the URL is empty or invalid
    if (!imageUrl || imageUrl.trim() === '') {
      console.log('🖼️ AnimatedSavedRecipeCard - Using fallback image for recipe:', recipe.recipe_title);
      return FALLBACK_RECIPE_IMAGE;
    }
    
    return imageUrl;
  };

  const animatedCardStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value * enterProgress.value },
      { 
        translateY: interpolate(
          enterProgress.value,
          [0, 1],
          [30, 0]
        )
      }
    ],
    opacity: enterProgress.value,
  }));

  const animatedImageStyle = useAnimatedStyle(() => ({
    opacity: imageOpacity.value,
  }));

  const ratingAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: ratingScale.value }],
  }));

  const favoriteAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: favoriteScale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95, {
      damping: 15,
      stiffness: 400,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 400,
    });
  };

  const handleRatingPress = (rating: 'thumbs_up' | 'thumbs_down') => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Medium);
    
    ratingScale.value = withSequence(
      withSpring(1.3, { damping: 8, stiffness: 400 }),
      withSpring(1, { damping: 10, stiffness: 300 })
    );
    
    const newRating = recipe.rating === rating ? 'neutral' : rating;
    onRating?.(newRating);
  };

  const handleFavoritePress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Medium);
    
    favoriteScale.value = withSequence(
      withSpring(1.3, { damping: 8, stiffness: 400 }),
      withSpring(1, { damping: 10, stiffness: 300 })
    );
    
    onFavorite?.(!recipe.is_favorite);
  };

  const handleCardPress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    
    // Enhanced navigation logic with proper ID resolution
    if (recipe.source === 'chat' || recipe.source === 'openai') {
      // Chat/AI-generated recipes should go to recipe-details
      router.push({
        pathname: '/recipe-details',
        params: { recipe: JSON.stringify(recipe.recipe_data) },
      });
    } else {
      // Spoonacular saved recipes go to recipe-spoonacular-detail
      const recipeId = getRecipeId();
      if (recipeId) {
        router.push({
          pathname: '/recipe-spoonacular-detail',
          params: { recipeId: recipeId.toString() },
        });
      } else {
        console.error('❌ AnimatedSavedRecipeCard - Unable to navigate, no valid recipe ID found');
        Alert.alert(
          'Error', 
          'Unable to open recipe details. This recipe may be corrupted or have missing information.',
          [
            { text: 'OK', style: 'default' }
          ]
        );
      }
    }
  };

  return (
    <TouchableOpacity
      testID={testID}
      onPress={handleCardPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={[styles.recipeCard, animatedCardStyle]}>
        {/* Recipe Image */}
        <Animated.View style={animatedImageStyle}>
          <Image 
            source={{ uri: getImageUrl() }} 
            style={styles.recipeImage}
            defaultSource={{ uri: FALLBACK_RECIPE_IMAGE }}
            onLoad={handleImageLoad}
            onError={(error) => {
              console.log('🚨 AnimatedSavedRecipeCard - Failed to load image:', {
                recipe_id: recipe.id,
                attempted_url: getImageUrl(),
                error: error.nativeEvent?.error
              });
            }}
          />
        </Animated.View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity 
            style={styles.favoriteButton}
            onPress={handleFavoritePress}
            activeOpacity={0.8}
          >
            <Animated.View style={favoriteAnimatedStyle}>
              <Ionicons 
                name={recipe.is_favorite ? "heart" : "heart-outline"} 
                size={20} 
                color={recipe.is_favorite ? "#FF4444" : "#fff"} 
              />
            </Animated.View>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.deleteButton}
            onPress={onDelete}
            activeOpacity={0.8}
          >
            <Ionicons name="trash-outline" size={18} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Gradient Overlay */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />

        {/* Recipe Info */}
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {recipe.recipe_title}
          </Text>
          
          {/* Status Badge */}
          {recipe.status === 'cooked' && (
            <View style={styles.statusBadge}>
              <Ionicons name="checkmark-circle" size={14} color="#4CAF50" />
              <Text style={styles.statusText}>Cooked</Text>
            </View>
          )}
          
          {/* Rating Buttons */}
          <View style={styles.ratingButtons}>
            <TouchableOpacity 
              style={[
                styles.ratingButton,
                recipe.rating === 'thumbs_up' && styles.ratingButtonActive
              ]}
              onPress={() => handleRatingPress('thumbs_up')}
              activeOpacity={0.8}
            >
              <Animated.View style={ratingAnimatedStyle}>
                <Ionicons 
                  name="thumbs-up" 
                  size={16} 
                  color={recipe.rating === 'thumbs_up' ? '#4CAF50' : '#fff'} 
                />
              </Animated.View>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[
                styles.ratingButton,
                recipe.rating === 'thumbs_down' && styles.ratingButtonActive
              ]}
              onPress={() => handleRatingPress('thumbs_down')}
              activeOpacity={0.8}
            >
              <Animated.View style={ratingAnimatedStyle}>
                <Ionicons 
                  name="thumbs-down" 
                  size={16} 
                  color={recipe.rating === 'thumbs_down' ? '#F44336' : '#fff'} 
                />
              </Animated.View>
            </TouchableOpacity>
          </View>
        </View>
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  recipeCard: {
    width: '100%',
    height: 320,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  actionButtons: {
    position: 'absolute',
    top: 16,
    right: 16,
    flexDirection: 'row',
    gap: 10,
  },
  favoriteButton: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 20,
    padding: 8,
    backdropFilter: 'blur(10px)',
  },
  deleteButton: {
    backgroundColor: 'rgba(0,0,0,0.6)',
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
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 8,
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  ratingButtons: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
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
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 120,
  },
});

export default AnimatedSavedRecipeCard;