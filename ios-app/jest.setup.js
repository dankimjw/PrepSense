// Jest setup file
// Note: @testing-library/react-native v12.4+ includes matchers by default

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Mock SafeAreaProvider
jest.mock('react-native-safe-area-context', () => {
  const inset = { top: 0, right: 0, bottom: 0, left: 0 };
  return {
    SafeAreaProvider: ({ children }) => children,
    SafeAreaConsumer: ({ children }) => children(inset),
    SafeAreaView: ({ children }) => children,
    useSafeAreaInsets: () => inset,
    useSafeAreaFrame: () => ({ x: 0, y: 0, width: 390, height: 844 }),
  };
});

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock Animated to silence warnings
global.AnimatedValue = jest.fn();
global.AnimatedValueXY = jest.fn();

// Mock expo-router
jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
  useSearchParams: jest.fn(() => ({})),
  Link: ({ children }) => children,
  Stack: {
    Screen: () => null,
  },
}));

// Mock expo-linear-gradient
jest.mock('expo-linear-gradient', () => ({
  LinearGradient: ({ children }) => children,
}));

// Mock expo-haptics
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
  selectionAsync: jest.fn(),
  ImpactFeedbackStyle: {
    Light: 'Light',
    Medium: 'Medium',
    Heavy: 'Heavy',
  },
}));

// Mock @expo/vector-icons
jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
  MaterialCommunityIcons: 'MaterialCommunityIcons',
}));

// Mock Config
jest.mock('./config', () => ({
  Config: {
    API_BASE_URL: 'http://localhost:8000/api/v1',
  },
}));

// Mock contexts
jest.mock('./context/ItemsContext', () => ({
  useItems: jest.fn(() => ({ items: [] })),
}));

jest.mock('./context/AuthContext', () => ({
  useAuth: jest.fn(() => ({ user: null, token: null, isAuthenticated: false })),
}));

// Mock utils
jest.mock('./utils/ingredientMatcher', () => ({
  calculateIngredientAvailability: jest.fn(() => ({
    availableCount: 2,
    usedIngredientCount: 2,
    missedIngredientCount: 1,
  })),
  validateIngredientCounts: jest.fn(() => true),
}));

jest.mock('./utils/contentValidation', () => ({
  isValidRecipe: jest.fn((recipe) => Boolean(recipe && recipe.id && recipe.title)),
}));

// Dimensions mock will be handled by jest-expo

// Global test utilities
global.fetch = jest.fn();