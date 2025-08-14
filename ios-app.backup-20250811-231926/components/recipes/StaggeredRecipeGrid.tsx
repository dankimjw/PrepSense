import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withDelay,
  runOnJS,
} from 'react-native-reanimated';
import AnimatedRecipeCard from './AnimatedRecipeCard';
import AnimatedSavedRecipeCard from './AnimatedSavedRecipeCard';

interface Recipe {
  id: number;
  title: string;
  image: string;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
}

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

interface StaggeredRecipeGridProps {
  recipes: Recipe[];
  savedRecipes?: SavedRecipe[];
  onRecipePress: (recipe: Recipe | SavedRecipe) => void;
  onRecipeSave?: (recipe: Recipe) => void;
  onSavedRecipeRating?: (recipeId: string, rating: 'thumbs_up' | 'thumbs_down' | 'neutral') => void;
  onSavedRecipeFavorite?: (recipeId: string, isFavorite: boolean) => void;
  onSavedRecipeDelete?: (recipeId: string) => void;
  isMyRecipes?: boolean;
  testID?: string;
}

const StaggeredRecipeGrid: React.FC<StaggeredRecipeGridProps> = ({
  recipes,
  savedRecipes,
  onRecipePress,
  onRecipeSave,
  onSavedRecipeRating,
  onSavedRecipeFavorite,
  onSavedRecipeDelete,
  isMyRecipes = false,
  testID,
}) => {
  const containerOpacity = useSharedValue(0);

  useEffect(() => {
    // Animate container entrance
    containerOpacity.value = withDelay(
      100,
      withSpring(1, {
        damping: 15,
        stiffness: 200,
      })
    );
  }, [recipes.length, savedRecipes?.length]);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    opacity: containerOpacity.value,
  }));

  const recipesToRender = isMyRecipes ? savedRecipes || [] : recipes;

  return (
    <Animated.View 
      style={[styles.recipesGrid, animatedContainerStyle]} 
      testID={testID}
    >
      {recipesToRender.map((recipe, index) => (
        <View key={recipe.id} style={styles.recipeCardWrapper}>
          {isMyRecipes ? (
            <AnimatedSavedRecipeCard
              recipe={recipe as SavedRecipe}
              onPress={() => onRecipePress(recipe)}
              onRating={(rating) => onSavedRecipeRating?.((recipe as SavedRecipe).id, rating)}
              onFavorite={(isFavorite) => onSavedRecipeFavorite?.((recipe as SavedRecipe).id, isFavorite)}
              onDelete={() => onSavedRecipeDelete?.((recipe as SavedRecipe).id)}
              index={index}
              testID={`saved-recipe-card-${recipe.id}`}
            />
          ) : (
            <AnimatedRecipeCard
              recipe={recipe as Recipe}
              onPress={() => onRecipePress(recipe)}
              onSave={() => onRecipeSave?.(recipe as Recipe)}
              index={index}
              testID={`recipe-card-${recipe.id}`}
            />
          )}
        </View>
      ))}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 20,
  },
  recipeCardWrapper: {
    width: '50%',
    paddingHorizontal: 6,
    marginBottom: 20,
  },
});

export default StaggeredRecipeGrid;