/**
 * Improved Recipes Screen with Enhanced Connectivity and Error Handling
 * 
 * This is an enhanced version of the recipes screen that demonstrates:
 * - Better error handling and loading states
 * - Offline support and retry mechanisms
 * - Connectivity monitoring
 * - User-friendly error messages
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { ErrorBoundary, NetworkError, LoadingError, EmptyState } from '../ErrorBoundary';
import { useRecipeSearch, usePantryData } from '../../hooks/useApiCall';
import { connectivityMonitor, ConnectivityResult } from '../../utils/connectivityValidator';

export default function ImprovedRecipesScreen() {
  const [activeTab, setActiveTab] = useState<'pantry' | 'discover' | 'my-recipes'>('pantry');
  const [searchQuery, setSearchQuery] = useState('');
  const [connectivityStatus, setConnectivityStatus] = useState<ConnectivityResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const insets = useSafeAreaInsets();
  const recipeSearch = useRecipeSearch();
  const pantryData = usePantryData();

  // Monitor connectivity
  useEffect(() => {
    const unsubscribe = connectivityMonitor.addListener(setConnectivityStatus);
    connectivityMonitor.start();

    return () => {
      unsubscribe();
      connectivityMonitor.stop();
    };
  }, []);

  // Load initial data based on active tab
  useEffect(() => {
    loadTabData();
  }, [activeTab]);

  const loadTabData = useCallback(async () => {
    try {
      switch (activeTab) {
        case 'pantry':
          await recipeSearch.pantrySearch.execute({
            user_id: 111,
            max_missing_ingredients: 5,
            use_expiring_first: true,
          });
          break;
        case 'discover':
          if (searchQuery) {
            await recipeSearch.complexSearch.execute(searchQuery);
          } else {
            await recipeSearch.randomRecipes.execute();
          }
          break;
        case 'my-recipes':
          // Load saved recipes
          break;
      }
    } catch (error) {
      console.error('Error loading tab data:', error);
    }
  }, [activeTab, searchQuery, recipeSearch]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    
    // Clear caches
    pantryData.clearCache();
    
    // Reload data
    await loadTabData();
    
    setRefreshing(false);
  }, [loadTabData, pantryData]);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    
    await recipeSearch.complexSearch.execute(searchQuery);
  }, [searchQuery, recipeSearch]);

  const renderConnectivityBanner = () => {
    if (!connectivityStatus || connectivityStatus.isHealthy) return null;

    return (
      <View style={styles.connectivityBanner}>
        <MaterialCommunityIcons name="wifi-off" size={16} color="#ff9800" />
        <Text style={styles.connectivityText}>
          Limited connectivity - some features may not work
        </Text>
      </View>
    );
  };

  const renderTabContent = () => {
    const isLoading = recipeSearch.pantrySearch.loading || 
                     recipeSearch.complexSearch.loading || 
                     recipeSearch.randomRecipes.loading;

    const hasError = recipeSearch.pantrySearch.error || 
                    recipeSearch.complexSearch.error || 
                    recipeSearch.randomRecipes.error;

    if (isLoading && !refreshing) {
      return (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#297A56" />
          <Text style={styles.loadingText}>
            {activeTab === 'pantry' ? 'Finding recipes from your pantry...' : 
             activeTab === 'discover' ? 'Searching for recipes...' : 
             'Loading your recipes...'}
          </Text>
        </View>
      );
    }

    if (hasError) {
      const error = recipeSearch.pantrySearch.error || 
                   recipeSearch.complexSearch.error || 
                   recipeSearch.randomRecipes.error;

      // Show specific error types
      if (error?.includes('network') || error?.includes('timeout') || error?.includes('fetch')) {
        return (
          <NetworkError 
            onRetry={loadTabData}
            message={`Unable to load ${activeTab} recipes. Please check your connection.`}
          />
        );
      }

      return (
        <LoadingError 
          onRetry={loadTabData}
          title={`Failed to Load ${activeTab === 'pantry' ? 'Pantry' : activeTab === 'discover' ? 'Discovery' : 'My'} Recipes`}
          message={error || 'Something went wrong while loading recipes.'}
        />
      );
    }

    // Get current data based on active tab
    let recipes: any[] = [];
    switch (activeTab) {
      case 'pantry':
        recipes = recipeSearch.pantrySearch.data?.recipes || [];
        break;
      case 'discover':
        recipes = recipeSearch.complexSearch.data?.results || recipeSearch.randomRecipes.data?.recipes || [];
        break;
      case 'my-recipes':
        recipes = []; // TODO: Implement saved recipes
        break;
    }

    if (recipes.length === 0) {
      return (
        <EmptyState
          icon={activeTab === 'pantry' ? 'food-off' : activeTab === 'discover' ? 'compass-off' : 'bookmark-off'}
          title={`No ${activeTab === 'pantry' ? 'Pantry' : activeTab === 'discover' ? 'Discovery' : 'Saved'} Recipes Found`}
          message={
            activeTab === 'pantry' 
              ? 'No recipes found with your current pantry items. Try adding more ingredients to your pantry.'
              : activeTab === 'discover'
              ? searchQuery 
                ? `No recipes found for "${searchQuery}". Try a different search term.`
                : 'Pull to refresh for new recipe suggestions.'
              : 'You haven\'t saved any recipes yet. Browse and save recipes you want to try!'
          }
          actionText={activeTab === 'pantry' ? 'Add Pantry Items' : activeTab === 'discover' ? 'Clear Search' : 'Discover Recipes'}
          onAction={() => {
            if (activeTab === 'discover' && searchQuery) {
              setSearchQuery('');
            }
            // TODO: Add navigation actions
          }}
        />
      );
    }

    return (
      <ScrollView
        style={styles.recipesList}
        contentContainerStyle={styles.recipesContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={['#297A56']}
            tintColor="#297A56"
          />
        }
      >
        {recipes.map((recipe, index) => (
          <View key={recipe.id || index} style={styles.recipeCard}>
            <Text style={styles.recipeTitle}>{recipe.title}</Text>
            <Text style={styles.recipeStats}>
              {recipe.usedIngredientCount || 0} have • {recipe.missedIngredientCount || 0} missing
            </Text>
          </View>
        ))}
      </ScrollView>
    );
  };

  return (
    <ErrorBoundary>
      <View style={[styles.container, { paddingTop: insets.top }]}>
        {renderConnectivityBanner()}
        
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Recipes</Text>
          <TouchableOpacity 
            style={styles.debugButton}
            onPress={() => {
              Alert.alert(
                'Debug Info',
                `API Status: ${connectivityStatus?.isHealthy ? 'Healthy' : 'Issues'}\n` +
                `Pantry Items: ${pantryData.data?.length || 0}\n` +
                `Cache Age: ${pantryData.cacheAge ? Math.round(pantryData.cacheAge / 1000) + 's' : 'N/A'}`
              );
            }}
          >
            <MaterialCommunityIcons name="information" size={24} color="#297A56" />
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <View style={styles.searchBar}>
            <MaterialCommunityIcons name="magnify" size={20} color="#666" />
            <TextInput
              style={styles.searchInput}
              placeholder={`Search ${activeTab} recipes...`}
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <MaterialCommunityIcons name="close-circle" size={20} color="#666" />
              </TouchableOpacity>
            )}
          </View>
          {activeTab === 'discover' && searchQuery.length > 0 && (
            <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
              <Text style={styles.searchButtonText}>Search</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Tabs */}
        <View style={styles.tabContainer}>
          {(['pantry', 'discover', 'my-recipes'] as const).map((tab) => (
            <TouchableOpacity
              key={tab}
              style={[styles.tab, activeTab === tab && styles.activeTab]}
              onPress={() => setActiveTab(tab)}
            >
              <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
                {tab === 'pantry' ? 'From Pantry' : 
                 tab === 'discover' ? 'Discover' : 'My Recipes'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Content */}
        {renderTabContent()}
      </View>
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  connectivityBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff3cd',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#ffeaa7',
  },
  connectivityText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#856404',
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
  debugButton: {
    padding: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
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
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#297A56',
    fontWeight: '600',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  recipesList: {
    flex: 1,
  },
  recipesContent: {
    padding: 16,
  },
  recipeCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  recipeTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  recipeStats: {
    fontSize: 14,
    color: '#666',
  },
});