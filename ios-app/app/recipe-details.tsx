// app/recipe-details.tsx - Recipe detail screen for PrepSense
import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Image, 
  TouchableOpacity,
  ActivityIndicator
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { Recipe, generateRecipeImage } from '../services/api';

export default function RecipeDetailsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [imageLoading, setImageLoading] = useState(true);
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [useGenerated, setUseGenerated] = useState(true); // Default to AI generated images

  useEffect(() => {
    if (params.recipe) {
      try {
        const recipeData = JSON.parse(params.recipe as string);
        setRecipe(recipeData);
        
        // Generate image for the recipe
        generateImageForRecipe(recipeData.name, useGenerated);
      } catch (error) {
        console.error('Error parsing recipe data:', error);
      }
    }
  }, [params.recipe, useGenerated]);

  const generateImageForRecipe = async (recipeName: string, useAI: boolean = false) => {
    try {
      setImageLoading(true);
      setImageError(null);
      
      const imageResponse = await generateRecipeImage(
        recipeName, 
        "professional food photography, beautifully plated, appetizing",
        useAI
      );
      setGeneratedImageUrl(imageResponse.image_url);
    } catch (error) {
      console.error('Error generating recipe image:', error);
      setImageError('Failed to generate recipe image');
    } finally {
      setImageLoading(false);
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


  // Get instructions from recipe data or generate basic ones
  const getInstructions = (recipe: Recipe) => {
    // Use recipe instructions if available
    if (recipe.instructions && recipe.instructions.length > 0) {
      return recipe.instructions;
    }
    
    // Otherwise generate basic instructions based on recipe name
    const recipeName = recipe.name.toLowerCase();
    
    if (recipeName.includes('smoothie')) {
      return [
        "Add all ingredients to a blender",
        "Blend on high speed for 60-90 seconds",
        "Check consistency and blend more if needed",
        "Pour into glasses and serve immediately",
        "Garnish with fresh fruit if desired"
      ];
    } else if (recipeName.includes('soup')) {
      return [
        "Heat oil in a large pot over medium heat",
        "Add aromatics and cook until fragrant",
        "Add main ingredients and cook for 5 minutes",
        "Pour in liquid and bring to a boil",
        "Reduce heat and simmer for 20-25 minutes",
        "Season with salt and pepper to taste",
        "Serve hot with desired garnishes"
      ];
    } else if (recipeName.includes('grilled') || recipeName.includes('chicken')) {
      return [
        "Preheat grill or grill pan to medium-high heat",
        "Season the protein with salt and pepper",
        "Oil the grill grates to prevent sticking",
        "Cook for 6-8 minutes on the first side",
        "Flip and cook for another 6-8 minutes",
        "Check internal temperature reaches safe levels",
        "Let rest for 5 minutes before serving"
      ];
    } else if (recipeName.includes('stir-fry') || recipeName.includes('stir fry')) {
      return [
        "Heat oil in a large wok or skillet over high heat",
        "Add protein and cook until almost done",
        "Remove protein and set aside",
        "Add vegetables in order of cooking time needed",
        "Return protein to the pan",
        "Add sauce and toss everything together",
        "Serve immediately over rice or noodles"
      ];
    } else {
      // Generic cooking instructions
      return [
        "Gather and prepare all ingredients",
        "Preheat cooking equipment as needed",
        "Follow proper food safety guidelines",
        "Cook ingredients according to recipe requirements",
        "Season and adjust flavors to taste",
        "Plate attractively and serve"
      ];
    }
  };

  const instructions = getInstructions(recipe);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Recipe Details</Text>
        <TouchableOpacity style={styles.favoriteButton}>
          <Ionicons name="heart-outline" size={24} color="#333" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Recipe Image */}
        <View style={styles.imageContainer}>
          {generatedImageUrl && !imageError ? (
            <Image
              source={{ uri: generatedImageUrl }}
              style={styles.recipeImage}
              onError={() => setImageError('Failed to load generated image')}
            />
          ) : (
            <View style={styles.imagePlaceholder}>
              {imageLoading ? (
                <>
                  <ActivityIndicator size="large" color="#297A56" />
                  <Text style={styles.imageLoadingText}>Generating recipe image...</Text>
                </>
              ) : imageError ? (
                <>
                  <Ionicons name="image-outline" size={64} color="#ccc" />
                  <Text style={styles.imageErrorText}>Image generation failed</Text>
                  <TouchableOpacity 
                    style={styles.retryButton}
                    onPress={() => generateImageForRecipe(recipe.name, useGenerated)}
                  >
                    <Text style={styles.retryButtonText}>Retry</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <Ionicons name="image-outline" size={64} color="#ccc" />
                  <Text style={styles.imageErrorText}>No image available</Text>
                </>
              )}
            </View>
          )}
        </View>

        {/* Recipe Info Card */}
        <View style={styles.recipeCard}>
          <Text style={styles.recipeTitle}>{recipe.name}</Text>
          
          <View style={styles.recipeMetrics}>
            <View style={styles.metricItem}>
              <Ionicons name="time" size={20} color="#666" />
              <Text style={styles.metricText}>{recipe.time} min</Text>
            </View>
            <View style={styles.metricItem}>
              <Ionicons name="fitness" size={20} color="#666" />
              <Text style={styles.metricText}>{recipe.nutrition.calories} cal</Text>
            </View>
            <View style={styles.metricItem}>
              <MaterialIcons name="fitness-center" size={20} color="#666" />
              <Text style={styles.metricText}>{recipe.nutrition.protein}g protein</Text>
            </View>
            <View style={styles.metricItem}>
              <Ionicons name="checkmark-circle" size={20} color="#297A56" />
              <Text style={styles.metricText}>{Math.round(recipe.match_score * 100)}% match</Text>
            </View>
            <View style={styles.metricItem}>
              <Ionicons name="star" size={20} color="#F59E0B" />
              <Text style={styles.metricText}>{recipe.expected_joy || 75}% joy</Text>
            </View>
          </View>

          {/* Ingredients Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Ingredients</Text>
            
            {/* Complete ingredients list */}
            <View style={styles.ingredientGroup}>
              <Text style={styles.ingredientGroupTitle}>📝 Complete ingredient list:</Text>
              {recipe.ingredients.map((ingredient, index) => {
                const isAvailable = recipe.available_ingredients.includes(ingredient);
                return (
                  <View key={index} style={styles.ingredientItem}>
                    <Ionicons 
                      name={isAvailable ? "checkmark-circle" : "add-circle-outline"} 
                      size={16} 
                      color={isAvailable ? "#297A56" : "#DC2626"} 
                    />
                    <Text style={isAvailable ? styles.availableIngredient : styles.missingIngredient}>
                      {ingredient}
                    </Text>
                  </View>
                );
              })}
            </View>
            
            {/* Summary of what's missing */}
            {recipe.missing_ingredients.length > 0 && (
              <View style={[styles.ingredientGroup, styles.missingSummary]}>
                <Text style={styles.ingredientGroupTitle}>
                  🛒 Shopping list ({recipe.missing_ingredients.length} items):
                </Text>
                {recipe.missing_ingredients.map((ingredient, index) => (
                  <View key={index} style={styles.ingredientItem}>
                    <Text style={styles.missingIngredient}>• {ingredient}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          {/* Instructions Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Instructions</Text>
            {instructions.map((instruction, index) => (
              <View key={index} style={styles.instructionItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>{index + 1}</Text>
                </View>
                <Text style={styles.instructionText}>{instruction}</Text>
              </View>
            ))}
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.startCookingButton}>
              <Ionicons name="play" size={20} color="#fff" />
              <Text style={styles.startCookingText}>Start Cooking</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.addToListButton}>
              <Text style={styles.addToListText}>+ Shopping List</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
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
  },
  favoriteButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
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
  addToListButton: {
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
  addToListText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
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