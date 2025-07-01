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
  
  const insets = useSafeAreaInsets();
  const router = useRouter();

  useEffect(() => {
    fetchRecipeDetails();
  }, [recipeId]);

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
    } catch (error) {
      console.error('Error fetching recipe details:', error);
      Alert.alert('Error', 'Failed to load recipe details. Please try again.');
      router.back();
    } finally {
      setLoading(false);
    }
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
            {recipe.extendedIngredients.map((ingredient) => (
              <View key={ingredient.id} style={styles.ingredientItem}>
                <MaterialCommunityIcons name="checkbox-blank-circle-outline" size={20} color="#297A56" />
                <Text style={styles.ingredientText}>{ingredient.original}</Text>
              </View>
            ))}
          </View>
        )}

        {activeTab === 'instructions' && (
          <View style={styles.instructionsContainer}>
            {recipe.analyzedInstructions.length > 0 ? (
              recipe.analyzedInstructions[0].steps.map((step) => (
                <View key={step.number} style={styles.instructionStep}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{step.number}</Text>
                  </View>
                  <Text style={styles.stepText}>{step.step}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.noInstructions}>
                No detailed instructions available. Please check the original recipe source.
              </Text>
            )}
          </View>
        )}

        {activeTab === 'nutrition' && recipe.nutrition && (
          <View style={styles.nutritionContainer}>
            {recipe.nutrition.nutrients.slice(0, 10).map((nutrient) => (
              <View key={nutrient.name} style={styles.nutrientItem}>
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
});