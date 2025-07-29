import React, { useEffect, useState } from 'react';
import { TouchableOpacity, Text, Image, View, StyleSheet } from 'react-native';
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

  // Fix image URL if it's a relative path
  let imageUrl = recipe.recipe_image;
  if (imageUrl && !imageUrl.startsWith('http')) {
    const baseUrl = Config.API_BASE_URL.replace('/api/v1', '');
    imageUrl = `${baseUrl}${imageUrl.startsWith('/') ? '' : '/'}${imageUrl}`;
  }

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
    onPress();
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
            source={{ uri: imageUrl }} 
            style={styles.recipeImage}
            onLoad={handleImageLoad}
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