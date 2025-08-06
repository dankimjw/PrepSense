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

// Fallback image URL for recipes with missing or invalid images
const FALLBACK_RECIPE_IMAGE = 'https://img.spoonacular.com/recipes/default-312x231.jpg';

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
    
    console.log('🖼️ AnimatedRecipeCard - Processing image URL:', {
      recipe_id: recipe.id,
      image: recipe.image,
      initial_url: imageUrl
    });
    
    // Return fallback image if the URL is empty or invalid
    if (!imageUrl || imageUrl.trim() === '') {
      console.log('🖼️ AnimatedRecipeCard - Using fallback image for recipe:', recipe.title);
      return FALLBACK_RECIPE_IMAGE;
    }
    
    return imageUrl;
  };

  // Image load animation
  const handleImageLoad = () => {
    setImageLoaded(true);
    imageOpacity.value = withTiming(1, { duration: 300 });
    runOnJS(setImageLoaded)(true);
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

  const availabilityPercentage = recipe.usedIngredientCount && recipe.missedIngredientCount 
    ? (recipe.usedIngredientCount / (recipe.usedIngredientCount + recipe.missedIngredientCount)) * 100
    : 0;

  return (
    <TouchableOpacity
      testID={testID}
      onPress={handleCardPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={[styles.recipeCard, animatedCardStyle]}>
        {/* Shimmer loading effect */}
        {!imageLoaded && (
          <Animated.View style={[styles.shimmerOverlay, shimmerStyle]} />
        )}
        
        {/* Recipe Image */}
        <Animated.View style={animatedImageStyle}>
          <Image 
            source={{ uri: getImageUrl() }} 
            style={styles.recipeImage}
            defaultSource={{ uri: FALLBACK_RECIPE_IMAGE }}
            onLoad={handleImageLoad}
            onError={(error) => {
              console.log('🚨 AnimatedRecipeCard - Failed to load image:', {
                recipe_id: recipe.id,
                attempted_url: getImageUrl(),
                error: error.nativeEvent?.error
              });
            }}
          />
        </Animated.View>

        {/* Gradient Overlay */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />

        {/* Bookmark Button */}
        <TouchableOpacity 
          style={styles.bookmarkButton}
          onPress={handleBookmarkPress}
          activeOpacity={0.8}
        >
          <Animated.View style={bookmarkAnimatedStyle}>
            <Ionicons 
              name={isBookmarked ? "bookmark" : "bookmark-outline"} 
              size={20} 
              color={isBookmarked ? "#FFD700" : "#fff"} 
            />
          </Animated.View>
        </TouchableOpacity>

        {/* Recipe Info */}
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {recipe.title}
          </Text>
          
          {/* Ingredient Availability Bar */}
          {availabilityPercentage > 0 && (
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
    overflow: 'hidden',
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
    fontWeight: '600',
  },
  recipeStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statText: {
    fontSize: 13,
    color: '#fff',
    fontWeight: '600',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
});

export default AnimatedRecipeCard;