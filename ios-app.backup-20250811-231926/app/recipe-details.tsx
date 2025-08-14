import React, { useState, useEffect } from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import RecipeDetailCardV3 from '../components/recipes/RecipeDetailCardV3';
import { Recipe } from '../services/recipeService';

export default function RecipeDetailsScreen() {
  const params = useLocalSearchParams();
  const [recipe, setRecipe] = useState<Recipe | null>(null);

  useEffect(() => {
    // Support both 'recipe' and 'recipeData' parameters for compatibility
    const recipeParam = params.recipeData || params.recipe;
    if (recipeParam) {
      try {
        const recipeData = JSON.parse(recipeParam as string);
        setRecipe(recipeData);
      } catch (error) {
        console.error('Error parsing recipe data:', error);
      }
    }
  }, [params.recipeData, params.recipe]);

  if (!recipe) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
        <Text style={styles.loadingText}>Loading recipe...</Text>
      </View>
    );
  }

  const handleRatingSubmitted = (rating: 'thumbs_up' | 'thumbs_down') => {
    console.log('Rating submitted:', rating);
  };

  return (
    <RecipeDetailCardV3
      recipe={recipe}
      onRatingSubmitted={handleRatingSubmitted}
    />
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
});