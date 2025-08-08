import React, { useEffect, useState } from 'react';
import { TouchableOpacity, Text, Image, View, StyleSheet, Alert } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withSequence,
  withDelay,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';

// Working fallback image URL for recipes with missing or invalid images
const FALLBACK_RECIPE_IMAGE = 'https://via.placeholder.com/312x231/E5E5E5/666666?text=Recipe+Image';

interface Recipe {
  id: number;
  title: string;
  image: string;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
}

interface AnimatedRecipeCardProps {
  recipe: Recipe;
  onPress: () => void;
  onSave?: () => void;
  index?: number;
  testID?: string;
}

const AnimatedRecipeCard: React.FC<AnimatedRecipeCardProps> = ({
  recipe,
  onPress,
  onSave,
  index = 0,
  testID,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  
  // Animation values
  const scale = useSharedValue(1);
  const enterProgress = useSharedValue(0);
  const imageOpacity = useSharedValue(0);
  const bookmarkScale = useSharedValue(1);
  const shimmerProgress = useSharedValue(0);

  // Staggered entrance animation
  useEffect(() => {
    const delay = index * 100; // 100ms stagger
    setTimeout(() => {
      enterProgress.value = withSpring(1, {
        damping: 15,
        stiffness: 200,
      });
    }, delay);
  }, [index]);

  // Shimmer animation for loading state
  useEffect(() => {
    if (!imageLoaded) {
      shimmerProgress.value = withSequence(
        withTiming(1, { duration: 1000 }),
        withTiming(0, { duration: 1000 })
      );
    }
  }, [imageLoaded]);

  // Enhanced recipe ID resolution
  const getRecipeId = (): number | null => {
    const id = recipe.id;
    if (id && (typeof id === 'number' || typeof id === 'string')) {
      const numericId = typeof id === 'string' ? parseInt(id, 10) : id;
      if (!isNaN(numericId) && numericId > 0) {
        console.log('🔍 AnimatedRecipeCard - Found recipe ID:', {
          recipe_id: numericId,
          original_type: typeof id
        });
        return numericId;
      }
    }
    
    console.error('❌ AnimatedRecipeCard - No valid recipe ID found:', {
      id: recipe.id,
      id_type: typeof recipe.id,
      recipe_keys: Object.keys(recipe)
    });
    return null;
  };

  // Enhanced image URL handling with proper fallback
  const getImageUrl = (): string => {
    let imageUrl = recipe.image || '';
    const recipeId = recipe.id;
    
    console.log('🖼️ AnimatedRecipeCard - Processing image URL:', {
      recipe_id: recipe.id,
      image: recipe.image,
      initial_url: imageUrl
    });
    
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
    if (!imageUrl || 
        imageUrl === 'https://img.spoonacular.com/recipes/default-312x231.jpg' ||
        !imageUrl.startsWith('http')) {
      imageUrl = FALLBACK_RECIPE_IMAGE;
      console.log('🖼️ Using working fallback image for recipe:', recipe.title);
    }
    
    return imageUrl;
  };

  // Image load animation
  const handleImageLoad = () => {
    setImageLoaded(true);
    imageOpacity.value = withTiming(1, { duration: 300 });
    
    const imageUrl = getImageUrl();
    console.log(`✅ AnimatedRecipeCard - Image loaded successfully:`, {
      url: imageUrl,
      recipe_id: recipe.id,
      recipe_title: recipe.title
    });
  };

  // Image load error handling
  const handleImageError = (error: any) => {
    const imageUrl = getImageUrl();
    console.log(`🚨 AnimatedRecipeCard - Failed to load recipe image:`, {
      attempted_url: imageUrl,
      recipe_id: recipe.id,
      error: error?.nativeEvent?.error || 'Failed to load image'
    });
    
    // Still show the image component with fallback - React Native will handle retries
    setImageLoaded(true);
    imageOpacity.value = withTiming(1, { duration: 300 });
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

  const shimmerStyle = useAnimatedStyle(() => ({
    opacity: imageLoaded ? 0 : interpolate(shimmerProgress.value, [0, 1], [0.3, 0.7]),
    transform: [
      {
        translateX: interpolate(shimmerProgress.value, [0, 1], [-100, 100])
      }
    ]
  }));

  const bookmarkAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: bookmarkScale.value }],
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

  const handleBookmarkPress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Medium);
    
    // Bookmark animation
    bookmarkScale.value = withSequence(
      withSpring(1.3, { damping: 8, stiffness: 400 }),
      withSpring(1, { damping: 10, stiffness: 300 })
    );
    
    setIsBookmarked(!isBookmarked);
    onSave?.();
  };

  const handleCardPress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    
    // Enhanced navigation logic with proper ID resolution
    const recipeId = getRecipeId();
    if (recipeId) {
      console.log('📱 AnimatedRecipeCard - Navigating to recipe details:', {
        recipe_id: recipeId,
        title: recipe.title,
        source: 'animated_card'
      });
      
      router.push({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: recipeId.toString() },
      });
    } else {
      console.error('❌ AnimatedRecipeCard - Unable to navigate, no valid recipe ID found');
      Alert.alert(
        'Error', 
        'Unable to open recipe details. This recipe may be corrupted or have missing information.',
        [
          { text: 'OK', style: 'default' }
        ]
      );
    }
  };

  // Calculate availability percentage for progress bar
  const totalIngredients = (recipe.usedIngredientCount || 0) + (recipe.missedIngredientCount || 0);
  const availabilityPercentage = totalIngredients > 0 
    ? Math.round(((recipe.usedIngredientCount || 0) / totalIngredients) * 100)
    : 0;

  const imageUrl = getImageUrl();

  return (
    <TouchableOpacity
      testID={testID}
      onPress={handleCardPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={0.9}
    >
      <Animated.View style={[styles.recipeCard, animatedCardStyle]}>
        <View style={styles.imageContainer}>
          <Animated.View style={[StyleSheet.absoluteFill, animatedImageStyle]}>
            <Image 
              source={{ uri: imageUrl }}
              style={styles.recipeImage}
              resizeMode="cover"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </Animated.View>
          
          {/* Shimmer loading overlay */}
          <Animated.View style={[styles.shimmerOverlay, shimmerStyle]} />
          
          {/* Gradient overlay */}
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.7)']}
            style={styles.gradient}
          />
          
          {/* Bookmark button */}
          <Animated.View style={[styles.bookmarkButton, bookmarkAnimatedStyle]}>
            <TouchableOpacity onPress={handleBookmarkPress}>
              <Ionicons 
                name={isBookmarked ? "bookmark" : "bookmark-outline"} 
                size={24} 
                color="white" 
              />
            </TouchableOpacity>
          </Animated.View>
        </View>

        {/* Recipe info overlay */}
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {recipe.title}
          </Text>

          {/* Ingredient availability bar */}
          {totalIngredients > 0 && (
            <View style={styles.availabilityContainer}>
              <View style={styles.availabilityBar}>
                <View 
                  style={[
                    styles.availabilityFill, 
                    { width: `${availabilityPercentage}%` }
                  ]} 
                />
              </View>
              <Text style={styles.availabilityText}>
                {Math.round(availabilityPercentage)}% available
              </Text>
            </View>
          )}

          {/* Recipe Stats */}
          <View style={styles.recipeStats}>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="check-circle" 
                size={16} 
                color="#4CAF50" 
              />
              <Text style={styles.statText}>
                {recipe.usedIngredientCount || 0} have
              </Text>
            </View>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="close-circle" 
                size={16} 
                color="#F44336" 
              />
              <Text style={styles.statText}>
                {recipe.missedIngredientCount || 0} missing
              </Text>
            </View>
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
  imageContainer: {
    flex: 1,
    position: 'relative',
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  shimmerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#E1E5E9',
    zIndex: 1,
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 120,
  },
  bookmarkButton: {
    position: 'absolute',
    top: 12,
    right: 12,
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
  availabilityContainer: {
    marginBottom: 8,
  },
  availabilityBar: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
    marginBottom: 4,
  },
  availabilityFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 2,
  },
  availabilityText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.9)',
    fontWeight: '500',
  },
  recipeStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
});

export default AnimatedRecipeCard;