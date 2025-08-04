// Test setup for React Native Paper components
import 'react-native-gesture-handler/jestSetup';

// Mock Appearance
jest.mock('react-native/Libraries/Utilities/Appearance', () => ({
  getColorScheme: () => 'light',
  addChangeListener: () => {},
  removeChangeListener: () => {},
}));

// Mock useColorScheme
jest.mock('react-native/Libraries/Utilities/useColorScheme', () => ({
  __esModule: true,
  default: jest.fn(() => 'light'),
}));

// Platform is already mocked in jest.setup.js

// Global test environment setup
beforeEach(() => {
  jest.clearAllMocks();
});