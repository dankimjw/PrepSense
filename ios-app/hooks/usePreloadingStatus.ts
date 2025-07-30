// usePreloadingStatus.ts - Hook to track and persist preloading status
import { useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTabData } from '../context/TabDataProvider';

const PRELOAD_STATUS_KEY = 'prepsense_preload_status';

interface PreloadStatus {
  lastPreloadTime: string;
  loadDuration: number;
  recipesCount: number;
  statsLoaded: boolean;
  chatQuestionsCount: number;
  errors: string[];
}

export const usePreloadingStatus = () => {
  const startTimeRef = useRef<number>(Date.now());
  const { 
    recipesData, 
    statsData, 
    chatData, 
    isPreloadComplete,
    recipesError,
    statsError,
    chatError
  } = useTabData();
  
  // Save preload status when complete
  useEffect(() => {
    if (isPreloadComplete) {
      const status: PreloadStatus = {
        lastPreloadTime: new Date().toISOString(),
        loadDuration: Date.now() - startTimeRef.current,
        recipesCount: recipesData?.pantryRecipes?.length || 0,
        statsLoaded: !!statsData,
        chatQuestionsCount: chatData?.suggestedQuestions?.length || 0,
        errors: [
          recipesError && `Recipes: ${recipesError}`,
          statsError && `Stats: ${statsError}`,
          chatError && `Chat: ${chatError}`
        ].filter(Boolean) as string[]
      };
      
      // Log to console
      console.log('📊 Preload Status Report:');
      console.log(`  - Time: ${status.loadDuration}ms`);
      console.log(`  - Recipes: ${status.recipesCount} loaded`);
      console.log(`  - Stats: ${status.statsLoaded ? 'Success' : 'Failed'}`);
      console.log(`  - Chat: ${status.chatQuestionsCount} questions`);
      if (status.errors.length > 0) {
        console.log('  - Errors:', status.errors);
      }
      
      // Save to AsyncStorage for debugging
      AsyncStorage.setItem(PRELOAD_STATUS_KEY, JSON.stringify(status))
        .catch(err => console.error('Failed to save preload status:', err));
    }
  }, [isPreloadComplete, recipesData, statsData, chatData, recipesError, statsError, chatError]);
  
  // Function to get last preload status
  const getLastPreloadStatus = async (): Promise<PreloadStatus | null> => {
    try {
      const saved = await AsyncStorage.getItem(PRELOAD_STATUS_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('Failed to get preload status:', error);
      return null;
    }
  };
  
  // Function to clear preload status (for debugging)
  const clearPreloadStatus = async () => {
    try {
      await AsyncStorage.removeItem(PRELOAD_STATUS_KEY);
      console.log('Preload status cleared');
    } catch (error) {
      console.error('Failed to clear preload status:', error);
    }
  };
  
  return {
    getLastPreloadStatus,
    clearPreloadStatus,
    currentStatus: {
      isComplete: isPreloadComplete,
      hasErrors: !!(recipesError || statsError || chatError),
      recipesLoaded: !!recipesData,
      statsLoaded: !!statsData,
      chatLoaded: !!chatData
    }
  };
};