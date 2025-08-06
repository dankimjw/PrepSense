// TabDataProvider.tsx - Preloads data for all tabs to ensure smooth transitions
import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { fetchPantryItems, searchRecipesFromPantry } from '../services/api';
import { Config } from '../config';
import { useItems } from './ItemsContext';
import { useUserPreferences } from './UserPreferencesContext';

interface RecipeData {
  pantryRecipes: any[];
  myRecipes: any[];
  randomRecipes: any[];
  lastFetched: Date;
}

interface StatsData {
  pantryItems: any[];
  comprehensiveStats: any;
  cookingTrends: any;
  lastFetched: Date;
}

interface ChatData {
  userPreferences: any;
  suggestedQuestions: string[];
  lastFetched: Date;
}

interface TabDataContextType {
  // Data states
  recipesData: RecipeData | null;
  statsData: StatsData | null;
  chatData: ChatData | null;
  
  // Loading states
  isLoadingRecipes: boolean;
  isLoadingStats: boolean;
  isLoadingChat: boolean;
  
  // Error states
  recipesError: string | null;
  statsError: string | null;
  chatError: string | null;
  
  // Refresh functions
  refreshRecipesData: () => Promise<void>;
  refreshStatsData: () => Promise<void>;
  refreshChatData: () => Promise<void>;
  refreshAllData: () => Promise<void>;
  
  // Preload status
  isPreloadComplete: boolean;
}

const TabDataContext = createContext<TabDataContextType | undefined>(undefined);

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes cache

export const TabDataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { items, isInitialized: itemsInitialized } = useItems();
  const { preferences } = useUserPreferences();
  
  // Data states
  const [recipesData, setRecipesData] = useState<RecipeData | null>(null);
  const [statsData, setStatsData] = useState<StatsData | null>(null);
  const [chatData, setChatData] = useState<ChatData | null>(null);
  
  // Loading states
  const [isLoadingRecipes, setIsLoadingRecipes] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  
  // Error states
  const [recipesError, setRecipesError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  
  // Preload status
  const [isPreloadComplete, setIsPreloadComplete] = useState(false);
  
  // Helper function to check if data needs refresh
  const needsRefresh = (lastFetched?: Date) => {
    if (!lastFetched) return true;
    return Date.now() - lastFetched.getTime() > CACHE_DURATION;
  };
  
  // Fetch recipes data
  const fetchRecipesData = useCallback(async () => {
    if (!needsRefresh(recipesData?.lastFetched) || isLoadingRecipes) {
      return;
    }
    
    setIsLoadingRecipes(true);
    setRecipesError(null);
    
    console.log('🍳 Fetching recipes data...');
    console.log('🍳 Using API Base URL:', Config.API_BASE_URL);
    
    try {
      // Get pantry items for recipe matching
      const pantryItemNames = items.map(item => item.item_name);
      
      // Fetch all recipe data in parallel
      const [pantryRecipesResult, myRecipesResult] = await Promise.allSettled([
        searchRecipesFromPantry(111), // Use the pantry-based search
        // Fetch saved recipes using the API directly
        fetch(`${Config.API_BASE_URL}/user-recipes`, {
          headers: {
            'Content-Type': 'application/json',
          },
        }).then(res => {
          if (!res.ok) {
            console.error('Failed to fetch saved recipes:', res.status, res.statusText);
            return Promise.reject(`HTTP ${res.status}: ${res.statusText}`);
          }
          return res.json();
        })
      ]);
      
      const newRecipesData: RecipeData = {
        pantryRecipes: pantryRecipesResult.status === 'fulfilled' ? 
          (pantryRecipesResult.value?.recipes || pantryRecipesResult.value || []) : [],
        myRecipes: myRecipesResult.status === 'fulfilled' ? myRecipesResult.value : [],
        randomRecipes: [], // We'll fetch random recipes separately when needed
        lastFetched: new Date()
      };
      
      setRecipesData(newRecipesData);
      console.log(`  → Recipes loaded: ${newRecipesData.pantryRecipes.length} pantry, ${newRecipesData.myRecipes.length} saved`);
      
      // Log any failures with more detail
      if (pantryRecipesResult.status === 'rejected') {
        console.error('Failed to fetch pantry recipes:', pantryRecipesResult.reason);
        setRecipesError(`Failed to load pantry recipes: ${pantryRecipesResult.reason}`);
      }
      if (myRecipesResult.status === 'rejected') {
        console.error('Failed to fetch my recipes:', myRecipesResult.reason);
        // Don't set error for my recipes failure if pantry recipes succeeded
        if (pantryRecipesResult.status === 'rejected') {
          setRecipesError(`Failed to load recipes: ${myRecipesResult.reason}`);
        }
      }
      
    } catch (error) {
      console.error('Error fetching recipes data:', error);
      setRecipesError('Failed to load recipes data');
    } finally {
      setIsLoadingRecipes(false);
    }
  }, [items, preferences, recipesData?.lastFetched, isLoadingRecipes]);
  
  // Fetch stats data
  const fetchStatsData = useCallback(async () => {
    if (!needsRefresh(statsData?.lastFetched) || isLoadingStats) {
      return;
    }
    
    setIsLoadingStats(true);
    setStatsError(null);
    
    console.log('📊 Fetching stats data...');
    console.log('📊 Using API Base URL:', Config.API_BASE_URL);
    
    try {
      // Use the standardized API base URL from Config
      const baseUrl = Config.API_BASE_URL;
      
      // Fetch all stats data in parallel
      const [comprehensiveStatsResponse, cookingTrendsResponse] = await Promise.allSettled([
        fetch(`${baseUrl}/stats/comprehensive?user_id=111`),
        fetch(`${baseUrl}/cooking-history/trends?user_id=111`)
      ]);
      
      let comprehensiveStats = null;
      let cookingTrends = null;
      
      if (comprehensiveStatsResponse.status === 'fulfilled' && comprehensiveStatsResponse.value.ok) {
        comprehensiveStats = await comprehensiveStatsResponse.value.json();
      } else if (comprehensiveStatsResponse.status === 'rejected') {
        console.warn('Failed to fetch comprehensive stats:', comprehensiveStatsResponse.reason);
      }
      
      if (cookingTrendsResponse.status === 'fulfilled' && cookingTrendsResponse.value.ok) {
        cookingTrends = await cookingTrendsResponse.value.json();
      } else if (cookingTrendsResponse.status === 'rejected') {
        console.warn('Failed to fetch cooking trends:', cookingTrendsResponse.reason);
      }
      
      const newStatsData: StatsData = {
        pantryItems: items,
        comprehensiveStats,
        cookingTrends,
        lastFetched: new Date()
      };
      
      setStatsData(newStatsData);
      console.log(`  → Stats loaded: ${newStatsData.pantryItems.length} items, comprehensive: ${!!comprehensiveStats}`);
      
    } catch (error) {
      console.error('Error fetching stats data:', error);
      setStatsError('Failed to load statistics');
    } finally {
      setIsLoadingStats(false);
    }
  }, [items, statsData?.lastFetched, isLoadingStats]);
  
  // Fetch chat data (user preferences and suggested questions)
  const fetchChatData = useCallback(async () => {
    if (!needsRefresh(chatData?.lastFetched) || isLoadingChat) {
      return;
    }
    
    setIsLoadingChat(true);
    setChatError(null);
    
    console.log('💬 Preparing chat suggestions...');
    
    try {
      // Generate dynamic suggested questions based on:
      // 1. Current pantry items
      // 2. Time of day
      // 3. User preferences
      // 4. Items expiring soon
      
      const currentHour = new Date().getHours();
      const timeBasedQuestions = [];
      
      // Time-based suggestions
      if (currentHour >= 5 && currentHour < 11) {
        timeBasedQuestions.push("What's good for breakfast?", "Quick breakfast ideas?");
      } else if (currentHour >= 11 && currentHour < 14) {
        timeBasedQuestions.push("What can I make for lunch?", "Light lunch recipes?");
      } else if (currentHour >= 17 && currentHour < 21) {
        timeBasedQuestions.push("What can I make for dinner?", "What should I cook tonight?");
      }
      
      // Pantry-based suggestions
      const pantryQuestions = [];
      if (items.length > 0) {
        const expiringItems = items.filter(item => {
          const daysUntilExpiry = Math.ceil((new Date(item.expected_expiration).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
          return daysUntilExpiry <= 3 && daysUntilExpiry > 0;
        });
        
        if (expiringItems.length > 0) {
          const itemNames = expiringItems.slice(0, 2).map(i => i.item_name).join(' and ');
          pantryQuestions.push(`How can I use up my ${itemNames}?`);
        }
        
        // Random pantry item suggestions
        if (items.length > 3) {
          const randomItem = items[Math.floor(Math.random() * items.length)];
          pantryQuestions.push(`What can I make with ${randomItem.item_name}?`);
        }
      }
      
      // Preference-based suggestions
      const preferenceQuestions = [];
      if (preferences?.dietaryPreferences?.length > 0) {
        const diet = preferences.dietaryPreferences[0];
        preferenceQuestions.push(`Show me ${diet} recipes`);
      }
      if (preferences?.cuisines?.length > 0) {
        const cuisine = preferences.cuisines[0];
        preferenceQuestions.push(`${cuisine} recipes from my pantry?`);
      }
      
      // Combine all suggestions
      const allQuestions = [
        "What can I make with only ingredients I have?",
        ...timeBasedQuestions,
        ...pantryQuestions,
        ...preferenceQuestions,
        "Quick meals under 20 minutes",
        "Show me healthy recipes",
        "Low-effort recipes for today"
      ];
      
      // Remove duplicates and limit to 6
      const uniqueQuestions = Array.from(new Set(allQuestions)).slice(0, 6);
      
      const newChatData: ChatData = {
        userPreferences: preferences,
        suggestedQuestions: uniqueQuestions,
        lastFetched: new Date()
      };
      
      setChatData(newChatData);
      console.log(`  → Chat suggestions ready: ${uniqueQuestions.length} questions`);
      console.log(`    Questions:`, uniqueQuestions);
      
    } catch (error) {
      console.error('Error preparing chat data:', error);
      setChatError('Failed to load chat suggestions');
    } finally {
      setIsLoadingChat(false);
    }
  }, [items, preferences, chatData?.lastFetched, isLoadingChat]);
  
  // Refresh functions
  const refreshRecipesData = useCallback(async () => {
    setRecipesData(null); // Force refresh
    await fetchRecipesData();
  }, [fetchRecipesData]);
  
  const refreshStatsData = useCallback(async () => {
    setStatsData(null); // Force refresh
    await fetchStatsData();
  }, [fetchStatsData]);
  
  const refreshChatData = useCallback(async () => {
    setChatData(null); // Force refresh
    await fetchChatData();
  }, [fetchChatData]);
  
  const refreshAllData = useCallback(async () => {
    await Promise.all([
      refreshRecipesData(),
      refreshStatsData(),
      refreshChatData()
    ]);
  }, [refreshRecipesData, refreshStatsData, refreshChatData]);
  
  // Initial preload when items are ready
  useEffect(() => {
    if (itemsInitialized && items.length > 0 && !isPreloadComplete) {
      console.log('📱 TabDataProvider: Starting preload...');
      console.log(`  - Pantry items available: ${items.length}`);
      console.log(`  - User preferences loaded: ${preferences ? 'Yes' : 'No'}`);
      console.log(`  - API Base URL: ${Config.API_BASE_URL}`);
      
      const startTime = Date.now();
      
      // Preload in parallel
      Promise.all([
        fetchRecipesData().then(() => console.log('  ✅ Recipes data loaded')),
        fetchStatsData().then(() => console.log('  ✅ Stats data loaded')),
        fetchChatData().then(() => console.log('  ✅ Chat suggestions loaded'))
      ]).then(() => {
        const loadTime = Date.now() - startTime;
        console.log(`📱 TabDataProvider: Preload complete in ${loadTime}ms`);
        setIsPreloadComplete(true);
      }).catch(error => {
        console.error('Error during preload:', error);
        setIsPreloadComplete(true); // Mark as complete even on error
      });
    }
  }, [itemsInitialized, items.length, isPreloadComplete, fetchRecipesData, fetchStatsData, fetchChatData]);
  
  // Refresh recipes when pantry items change significantly
  useEffect(() => {
    if (isPreloadComplete && items.length > 0) {
      // Debounce to avoid too many refreshes
      const timer = setTimeout(() => {
        if (needsRefresh(recipesData?.lastFetched)) {
          fetchRecipesData();
        }
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [items, isPreloadComplete, recipesData?.lastFetched, fetchRecipesData]);
  
  // Refresh when user preferences change
  useEffect(() => {
    if (isPreloadComplete && preferences) {
      refreshRecipesData();
      refreshChatData();
    }
  }, [preferences?.allergens, preferences?.dietaryPreferences, preferences?.cuisines, isPreloadComplete]);
  
  const contextValue: TabDataContextType = {
    recipesData,
    statsData,
    chatData,
    isLoadingRecipes,
    isLoadingStats,
    isLoadingChat,
    recipesError,
    statsError,
    chatError,
    refreshRecipesData,
    refreshStatsData,
    refreshChatData,
    refreshAllData,
    isPreloadComplete
  };
  
  return (
    <TabDataContext.Provider value={contextValue}>
      {children}
    </TabDataContext.Provider>
  );
};

export const useTabData = (): TabDataContextType => {
  const context = useContext(TabDataContext);
  if (!context) {
    throw new Error('useTabData must be used within a TabDataProvider');
  }
  return context;
};