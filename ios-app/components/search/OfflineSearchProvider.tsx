// components/search/OfflineSearchProvider.tsx - Enhanced search with offline capabilities
/**
 * Search provider that seamlessly integrates online and offline recipe search.
 * Provides offline-first search with fallback to online sources.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { recipeBundleService, SearchResult, OfflineRecipe } from '../../services/recipeBundleService';
import { recipeService, Recipe } from '../../services/recipeService';
import NetInfo from '@react-native-community/netinfo';

export interface SearchOptions {
  query: string;
  limit?: number;
  includeOffline?: boolean;
  includeOnline?: boolean;
  sortBy?: 'relevance' | 'popularity' | 'recent';
}

export interface EnhancedSearchResult {
  recipe: Recipe | OfflineRecipe;
  source: 'online' | 'offline';
  relevance_score: number;
  match_type?: string;
  is_available_offline?: boolean;
}

interface SearchContextType {
  searchResults: EnhancedSearchResult[];
  isSearching: boolean;
  isOfflineMode: boolean;
  searchHistory: string[];
  performSearch: (options: SearchOptions) => Promise<void>;
  clearSearch: () => void;
  addToHistory: (query: string) => void;
  clearHistory: () => void;
  getSimilarRecipes: (recipeId: number) => Promise<OfflineRecipe[]>;
}

const SearchContext = createContext<SearchContextType | null>(null);

export const useOfflineSearch = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useOfflineSearch must be used within OfflineSearchProvider');
  }
  return context;
};

interface OfflineSearchProviderProps {
  children: React.ReactNode;
}

export const OfflineSearchProvider: React.FC<OfflineSearchProviderProps> = ({ children }) => {
  const [searchResults, setSearchResults] = useState<EnhancedSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  useEffect(() => {
    // Monitor network connectivity
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOfflineMode(!state.isConnected);
    });

    // Load search history
    loadSearchHistory();

    // Initialize database
    recipeBundleService.initializeDatabase().catch(console.error);

    return unsubscribe;
  }, []);

  const loadSearchHistory = async () => {
    try {
      // Load from AsyncStorage if needed
      // For now, using empty array
      setSearchHistory([]);
    } catch (error) {
      console.error('Failed to load search history:', error);
    }
  };

  const performSearch = async (options: SearchOptions): Promise<void> => {
    const { query, limit = 20, includeOffline = true, includeOnline = true, sortBy = 'relevance' } = options;
    
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    
    try {
      const results: EnhancedSearchResult[] = [];

      // Search offline recipes first (faster)
      if (includeOffline) {
        try {
          const offlineResults = await recipeBundleService.searchRecipes(query, limit);
          
          const enhancedOfflineResults: EnhancedSearchResult[] = offlineResults.map(result => ({
            recipe: result.recipe,
            source: 'offline' as const,
            relevance_score: result.relevance_score,
            match_type: result.match_type,
            is_available_offline: true
          }));
          
          results.push(...enhancedOfflineResults);
        } catch (error) {
          console.error('Offline search failed:', error);
        }
      }

      // Search online recipes if connected and enabled
      if (includeOnline && !isOfflineMode) {
        try {
          const onlineRecipes = await recipeService.searchRecipes(query, limit);
          
          // Check which online recipes are available offline
          const enhancedOnlineResults: EnhancedSearchResult[] = [];
          
          for (const recipe of onlineRecipes) {
            const isAvailableOffline = await recipeBundleService.isRecipeAvailableOffline(recipe.id);
            
            // Only add if not already in offline results
            const alreadyExists = results.some(r => 
              r.source === 'offline' && (r.recipe as OfflineRecipe).id === recipe.id
            );
            
            if (!alreadyExists) {
              enhancedOnlineResults.push({
                recipe,
                source: 'online' as const,
                relevance_score: recipe.spoonacularScore || 0,
                is_available_offline: isAvailableOffline
              });
            }
          }
          
          results.push(...enhancedOnlineResults);
        } catch (error) {
          console.error('Online search failed:', error);
        }
      }

      // Sort results based on criteria
      const sortedResults = sortResults(results, sortBy);
      
      setSearchResults(sortedResults.slice(0, limit));
      
      // Add to search history
      if (query.trim()) {
        addToHistory(query.trim());
      }
      
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const sortResults = (results: EnhancedSearchResult[], sortBy: string): EnhancedSearchResult[] => {
    return results.sort((a, b) => {
      switch (sortBy) {
        case 'popularity':
          return b.relevance_score - a.relevance_score;
        case 'recent':
          // Prioritize offline recipes as they're more recently downloaded
          if (a.source === 'offline' && b.source === 'online') return -1;
          if (a.source === 'online' && b.source === 'offline') return 1;
          return b.relevance_score - a.relevance_score;
        case 'relevance':
        default:
          // Boost offline results slightly for better user experience
          const aScore = a.relevance_score + (a.source === 'offline' ? 10 : 0);
          const bScore = b.relevance_score + (b.source === 'offline' ? 10 : 0);
          return bScore - aScore;
      }
    });
  };

  const clearSearch = () => {
    setSearchResults([]);
  };

  const addToHistory = (query: string) => {
    setSearchHistory(prev => {
      const filtered = prev.filter(item => item !== query);
      const updated = [query, ...filtered].slice(0, 10); // Keep last 10 searches
      // TODO: Persist to AsyncStorage
      return updated;
    });
  };

  const clearHistory = () => {
    setSearchHistory([]);
    // TODO: Clear from AsyncStorage
  };

  const getSimilarRecipes = async (recipeId: number): Promise<OfflineRecipe[]> => {
    try {
      return await recipeBundleService.getSimilarRecipes(recipeId);
    } catch (error) {
      console.error('Failed to get similar recipes:', error);
      return [];
    }
  };

  const contextValue: SearchContextType = {
    searchResults,
    isSearching,
    isOfflineMode,
    searchHistory,
    performSearch,
    clearSearch,
    addToHistory,
    clearHistory,
    getSimilarRecipes
  };

  return (
    <SearchContext.Provider value={contextValue}>
      {children}
    </SearchContext.Provider>
  );
};

// Utility hook for offline status
export const useOfflineStatus = () => {
  const { isOfflineMode } = useOfflineSearch();
  return isOfflineMode;
};

// Utility hook for checking if a recipe is available offline
export const useRecipeOfflineStatus = (recipeId: number) => {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAvailability = async () => {
      try {
        const available = await recipeBundleService.isRecipeAvailableOffline(recipeId);
        setIsAvailable(available);
      } catch (error) {
        console.error('Failed to check offline availability:', error);
        setIsAvailable(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkAvailability();
  }, [recipeId]);

  return { isAvailable, isChecking };
};