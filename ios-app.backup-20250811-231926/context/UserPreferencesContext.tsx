import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface UserPreferences {
  allergens: string[];
  dietaryPreferences: string[];
  cuisines: string[];
}

interface UserPreferencesContextType {
  preferences: UserPreferences;
  updatePreferences: (newPreferences: UserPreferences) => Promise<void>;
  addAllergen: (allergen: string) => Promise<void>;
  removeAllergen: (allergen: string) => Promise<void>;
  addDietaryPreference: (preference: string) => Promise<void>;
  removeDietaryPreference: (preference: string) => Promise<void>;
  addCuisine: (cuisine: string) => Promise<void>;
  removeCuisine: (cuisine: string) => Promise<void>;
  clearAllPreferences: () => Promise<void>;
  isLoading: boolean;
}

const defaultPreferences: UserPreferences = {
  allergens: [],
  dietaryPreferences: [],
  cuisines: []
};

const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined);

const STORAGE_KEY = 'prepsense_user_preferences';

export function UserPreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [isLoading, setIsLoading] = useState(true);

  // Load preferences from storage on app start
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setIsLoading(true);
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsedPreferences = JSON.parse(stored) as UserPreferences;
        // Ensure all arrays are properly initialized
        const safePreferences = {
          allergens: parsedPreferences.allergens || [],
          dietaryPreferences: parsedPreferences.dietaryPreferences || [],
          cuisines: parsedPreferences.cuisines || []
        };
        setPreferences(safePreferences);
      } else {
        // No stored preferences, use defaults
        setPreferences(defaultPreferences);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
      // Use default preferences if loading fails
      setPreferences(defaultPreferences);
    } finally {
      setIsLoading(false);
    }
  };

  const savePreferences = async (newPreferences: UserPreferences) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(newPreferences));
      setPreferences(newPreferences);
    } catch (error) {
      console.error('Error saving user preferences:', error);
      throw error;
    }
  };

  const updatePreferences = async (newPreferences: UserPreferences) => {
    await savePreferences(newPreferences);
  };

  const addAllergen = async (allergen: string) => {
    const currentAllergens = preferences.allergens || [];
    const newPreferences = {
      ...preferences,
      allergens: [...currentAllergens.filter(a => a !== allergen), allergen]
    };
    await savePreferences(newPreferences);
  };

  const removeAllergen = async (allergen: string) => {
    const currentAllergens = preferences.allergens || [];
    const newPreferences = {
      ...preferences,
      allergens: currentAllergens.filter(a => a !== allergen)
    };
    await savePreferences(newPreferences);
  };

  const addDietaryPreference = async (preference: string) => {
    const currentPreferences = preferences.dietaryPreferences || [];
    const newPreferences = {
      ...preferences,
      dietaryPreferences: [...currentPreferences.filter(p => p !== preference), preference]
    };
    await savePreferences(newPreferences);
  };

  const removeDietaryPreference = async (preference: string) => {
    const currentPreferences = preferences.dietaryPreferences || [];
    const newPreferences = {
      ...preferences,
      dietaryPreferences: currentPreferences.filter(p => p !== preference)
    };
    await savePreferences(newPreferences);
  };

  const addCuisine = async (cuisine: string) => {
    const currentCuisines = preferences.cuisines || [];
    const newPreferences = {
      ...preferences,
      cuisines: [...currentCuisines.filter(c => c !== cuisine), cuisine]
    };
    await savePreferences(newPreferences);
  };

  const removeCuisine = async (cuisine: string) => {
    const currentCuisines = preferences.cuisines || [];
    const newPreferences = {
      ...preferences,
      cuisines: currentCuisines.filter(c => c !== cuisine)
    };
    await savePreferences(newPreferences);
  };

  const clearAllPreferences = async () => {
    await savePreferences(defaultPreferences);
  };

  const contextValue: UserPreferencesContextType = {
    preferences,
    updatePreferences,
    addAllergen,
    removeAllergen,
    addDietaryPreference,
    removeDietaryPreference,
    addCuisine,
    removeCuisine,
    clearAllPreferences,
    isLoading
  };

  return (
    <UserPreferencesContext.Provider value={contextValue}>
      {children}
    </UserPreferencesContext.Provider>
  );
}

export function useUserPreferences(): UserPreferencesContextType {
  const context = useContext(UserPreferencesContext);
  if (!context) {
    throw new Error('useUserPreferences must be used within a UserPreferencesProvider');
  }
  return context;
}