import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Image,
  RefreshControl,
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Config } from '../../config';
import { useItems } from '../../context/ItemsContext';

const { width } = Dimensions.get('window');

interface Recipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
  usedIngredientCount: number;
  missedIngredientCount: number;
  missedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  usedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  likes: number;
}

export default function RecipesScreen() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'pantry' | 'search' | 'random'>('pantry');
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { items } = useItems();

  const fetchRecipesFromPantry = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111, // Default demo user
          max_missing_ingredients: 5,
          use_expiring_first: true,
        }),
      });

      if (!response.ok) throw new Error('Failed to fetch recipes');
      
      const data = await response.json();
      setRecipes(data.recipes || []);
    } catch (error) {
      console.error('Error fetching recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const searchRecipes = async () => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          number: 20,
        }),
      });

      if (!response.ok) throw new Error('Failed to search recipes');
      
      const data = await response.json();
      setRecipes(data.results || []);
    } catch (error) {
      console.error('Error searching recipes:', error);
      Alert.alert('Error', 'Failed to search recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRandomRecipes = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${Config.API_BASE_URL}/recipes/random?number=20`);

      if (!response.ok) throw new Error('Failed to fetch random recipes');
      
      const data = await response.json();
      setRecipes(data.recipes || []);
    } catch (error) {
      console.error('Error fetching random recipes:', error);
      Alert.alert('Error', 'Failed to load recipes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'pantry') {
      fetchRecipesFromPantry();
    } else if (activeTab === 'random') {
      fetchRandomRecipes();
    }
  }, [activeTab, fetchRecipesFromPantry]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeTab === 'pantry') {
      await fetchRecipesFromPantry();
    } else if (activeTab === 'random') {
      await fetchRandomRecipes();
    } else if (activeTab === 'search' && searchQuery) {
      await searchRecipes();
    }
    setRefreshing(false);
  }, [activeTab, searchQuery, fetchRecipesFromPantry]);

  const navigateToRecipeDetail = (recipe: Recipe) => {
    router.push({
      pathname: '/recipe-spoonacular-detail',
      params: { recipeId: recipe.id.toString() },
    });
  };

  const renderRecipeCard = (recipe: Recipe) => (
    <TouchableOpacity
      key={recipe.id}
      style={styles.recipeCard}
      onPress={() => navigateToRecipeDetail(recipe)}
    >
      <Image source={{ uri: recipe.image }} style={styles.recipeImage} />
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradient}
      />
      <View style={styles.recipeInfo}>
        <Text style={styles.recipeTitle} numberOfLines={2}>
          {recipe.title}
        </Text>
        <View style={styles.recipeStats}>
          <View style={styles.stat}>
            <MaterialCommunityIcons name="check-circle" size={16} color="#4CAF50" />
            <Text style={styles.statText}>{recipe.usedIngredientCount || 0} have</Text>
          </View>
          <View style={styles.stat}>
            <MaterialCommunityIcons name="close-circle" size={16} color="#F44336" />
            <Text style={styles.statText}>{recipe.missedIngredientCount || 0} missing</Text>
          </View>
          {recipe.likes && (
            <View style={styles.stat}>
              <MaterialCommunityIcons name="heart" size={16} color="#E91E63" />
              <Text style={styles.statText}>{recipe.likes}</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recipes</Text>
        <TouchableOpacity onPress={() => router.push('/chat')}>
          <MaterialCommunityIcons name="chef-hat" size={24} color="#297A56" />
        </TouchableOpacity>
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'pantry' && styles.activeTab]}
          onPress={() => setActiveTab('pantry')}
        >
          <Text style={[styles.tabText, activeTab === 'pantry' && styles.activeTabText]}>
            From Pantry
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'search' && styles.activeTab]}
          onPress={() => setActiveTab('search')}
        >
          <Text style={[styles.tabText, activeTab === 'search' && styles.activeTabText]}>
            Search
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'random' && styles.activeTab]}
          onPress={() => setActiveTab('random')}
        >
          <Text style={[styles.tabText, activeTab === 'random' && styles.activeTabText]}>
            Discover
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'search' && (
        <View style={styles.searchContainer}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#666" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search recipes..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={searchRecipes}
              returnKeyType="search"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={20} color="#666" />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity style={styles.searchButton} onPress={searchRecipes}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>
      )}

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#297A56" />
          <Text style={styles.loadingText}>Finding delicious recipes...</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={['#297A56']}
              tintColor="#297A56"
            />
          }
          showsVerticalScrollIndicator={false}
        >
          {recipes.length === 0 ? (
            <View style={styles.emptyContainer}>
              <MaterialCommunityIcons name="food-off" size={64} color="#ccc" />
              <Text style={styles.emptyText}>
                {activeTab === 'pantry'
                  ? 'No recipes found with your pantry items'
                  : activeTab === 'search'
                  ? 'Search for recipes by name or ingredient'
                  : 'Pull to refresh for new recipes'}
              </Text>
            </View>
          ) : (
            <View style={styles.recipesGrid}>
              {recipes.map(renderRecipeCard)}
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#297A56',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
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
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 10,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 40,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  searchButton: {
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 8,
    paddingTop: 16,
  },
  recipeCard: {
    width: (width - 32) / 2,
    height: 220,
    margin: 8,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
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
    height: 100,
  },
  recipeInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  recipeStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#fff',
  },
});