// Jest setup file
// Note: @testing-library/react-native v12.4+ includes matchers by default

// Mock StyleSheet FIRST with aggressive early mocking
jest.doMock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    StyleSheet: {
      create: jest.fn((styles) => styles),
      flatten: jest.fn((style) => style),
      hairlineWidth: 1,
      absoluteFill: {
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
      },
      absoluteFillObject: {
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
      },
    },
    Platform: {
      OS: 'ios',
      Version: '14.0',
      select: jest.fn((obj) => obj.ios || obj.default),
      isPad: false,
      isTesting: true,
      isTV: false,
    },
    Dimensions: {
      get: jest.fn(() => ({ 
        width: 390, 
        height: 844, 
        scale: 3, 
        fontScale: 1 
      })),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
  };
});

// Mock PixelRatio FIRST - must be before any StyleSheet usage
jest.doMock('react-native/Libraries/Utilities/PixelRatio', () => ({
  get: jest.fn(() => 2),
  getFontScale: jest.fn(() => 1),
  getPixelSizeForLayoutSize: jest.fn((layoutSize) => layoutSize * 2),
  roundToNearestPixel: jest.fn((layoutSize) => Math.round(layoutSize)),
}));

// Mock StyleSheet early - use doMock to ensure it runs before imports
jest.doMock('react-native/Libraries/StyleSheet/StyleSheet', () => ({
  create: jest.fn((styles) => styles),
  flatten: jest.fn((style) => style),
  hairlineWidth: 1,
  absoluteFill: {},
  absoluteFillObject: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
}));

// Mock Platform early for React Native Paper
jest.doMock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'ios',
  Version: '14.0',
  select: jest.fn((obj) => obj.ios || obj.default),
  isPad: false,
  isTesting: true,
  isTV: false,
}));

// Create a comprehensive StyleSheet mock available globally
global.StyleSheet = {
  create: jest.fn((styles) => styles),
  flatten: jest.fn((style) => style),
  hairlineWidth: 1,
  absoluteFill: {},
  absoluteFillObject: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
};

// CRITICAL: Mock react-native-paper BEFORE any imports
jest.mock('react-native-paper', () => {
  const mockTheme = {
    colors: {
      primary: '#6200EE',
      surface: '#FFFFFF',
      background: '#F6F6F6',
      text: '#000000',
      disabled: '#C0C0C0',
      placeholder: '#808080',
      backdrop: 'rgba(0, 0, 0, 0.5)',
      onSurface: '#000000',
      notification: '#FF4444',
      primaryContainer: '#e3f2fa',
      secondary: '#4a5568',
      secondaryContainer: '#e2e8f0',
      tertiary: '#2d3748',
      tertiaryContainer: '#cbd5e0',
      surfaceVariant: '#f7fafc',
      surfaceDisabled: '#e2e8f0',
      error: '#e53e3e',
      errorContainer: '#fed7d7',
      onPrimary: '#ffffff',
      onSecondary: '#ffffff',
      onTertiary: '#ffffff',
      onSurface: '#1a202c',
      onSurfaceVariant: '#4a5568',
      onError: '#ffffff',
      onErrorContainer: '#742a2a',
      onBackground: '#1a202c',
      onPrimaryContainer: '#1a365d',
      onSecondaryContainer: '#2d3748',
      onTertiaryContainer: '#1a202c',
      outline: '#a0aec0',
      outlineVariant: '#e2e8f0',
      inverseSurface: '#2d3748',
      inverseOnSurface: '#f7fafc',
      inversePrimary: '#90cdf4',
      shadow: '#000000',
      scrim: '#000000',
      surfaceTint: '#0066cc',
    },
    fonts: {
      regular: { fontFamily: 'System' },
      medium: { fontFamily: 'System' },
      light: { fontFamily: 'System' },
      thin: { fontFamily: 'System' },
    },
    roundness: 4,
  };

  return {
    // Components
    TextInput: ({ children, ...props }) => children,
    HelperText: ({ children, ...props }) => children,
    Searchbar: ({ children, ...props }) => children,
    IconButton: ({ children, ...props }) => children,
    Portal: ({ children, ...props }) => children,
    Dialog: ({ children, ...props }) => children,
    Button: ({ children, ...props }) => children,
    Divider: ({ children, ...props }) => children,
    Switch: ({ children, ...props }) => children,
    Badge: ({ children, ...props }) => children,
    
    // Providers
    PaperProvider: ({ children, ...props }) => children,
    MD3LightTheme: mockTheme,
    MD3DarkTheme: mockTheme,
    DefaultTheme: mockTheme,
    
    // Theme utilities
    useTheme: jest.fn(() => mockTheme),
    withTheme: jest.fn((Component) => Component),
    
    // Other utilities
    configureFonts: jest.fn(() => mockTheme.fonts),
  };
});

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

// Mock Dimensions
jest.mock('react-native/Libraries/Utilities/Dimensions', () => ({
  get: jest.fn(() => ({ 
    width: 390, 
    height: 844, 
    scale: 3, 
    fontScale: 1 
  })),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

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

// Mock expo-notifications
jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(),
  cancelScheduledNotificationAsync: jest.fn(),
  getAllScheduledNotificationsAsync: jest.fn(),
  setNotificationHandler: jest.fn(),
  addNotificationReceivedListener: jest.fn(),
  addNotificationResponseReceivedListener: jest.fn(),
  removeNotificationSubscription: jest.fn(),
}));

// Mock @expo/vector-icons
jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
  MaterialIcons: 'MaterialIcons',
  MaterialCommunityIcons: 'MaterialCommunityIcons',
  Feather: 'Feather',
  FontAwesome: 'FontAwesome',
  AntDesign: 'AntDesign',
}));

// Mock DebugPanel to avoid StyleSheet issues
jest.mock('./components/debug/DebugPanel', () => ({
  DebugPanel: () => null,
  DebugButton: () => null,
  debugBorder: jest.fn(),
  debugLog: jest.fn(),
  debugHybrid: jest.fn(),
  debugRenderTime: jest.fn(),
}));

// Config is mocked via __mocks__/config.js

// Mock contexts
jest.mock('./context/ItemsContext', () => ({
  useItems: jest.fn(() => ({ items: [] })),
}));

jest.mock('./context/AuthContext', () => ({
  useAuth: jest.fn(() => ({ user: null, token: null, isAuthenticated: false })),
}));

// Remove mock of ingredientMatcher to test actual implementation
// jest.mock('./utils/ingredientMatcher', () => ({
//   calculateIngredientAvailability: jest.fn(() => ({
//     availableCount: 2,
//     usedIngredientCount: 2,
//     missedIngredientCount: 1,
//   })),
//   validateIngredientCounts: jest.fn(() => true),
// }));

jest.mock('./utils/contentValidation', () => ({
  isValidRecipe: jest.fn((recipe) => Boolean(recipe && recipe.id && recipe.title)),
}));

// Dimensions mock will be handled by jest-expo

// Mock AbortController for ApiClient tests
global.AbortController = class AbortController {
  constructor() {
    this.signal = { 
      aborted: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };
  }
  abort() {
    this.signal.aborted = true;
  }
};

// Mock Alert globally 
global.Alert = { alert: jest.fn() };

// Global test utilities
global.fetch = jest.fn();