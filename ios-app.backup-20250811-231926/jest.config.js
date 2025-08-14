module.exports = {
  preset: 'jest-expo',
  setupFiles: [
    '<rootDir>/jest.setup.js'
  ],
  setupFilesAfterEnv: [
    '<rootDir>/__tests__/setup/testSetup.ts'
  ],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|react-native-paper|react-native-vector-icons|@react-native-async-storage|react-native-safe-area-context|react-native-gesture-handler)'
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1'
  },
  testEnvironment: 'node',
  testPathIgnorePatterns: [
    '/node_modules/',
    '/__tests__/helpers/'
  ],
  globals: {
    __DEV__: true
  },
  
  // Enhanced coverage configuration
  collectCoverage: false, // Set to true in CI
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'services/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'context/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/__tests__/**',
    '!**/__mocks__/**',
    '!**/node_modules/**',
    '!**/*.config.{js,ts}',
    '!**/coverage/**',
    '!babel.config.js',
    '!metro.config.js',
  ],
  
  // Coverage thresholds for enterprise standards
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
    // Component-specific thresholds
    './components/**/*.{js,jsx,ts,tsx}': {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75,
    },
    './services/**/*.{js,jsx,ts,tsx}': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
  ],
  
  // Test result processors
  testResultsProcessor: 'jest-sonar-reporter',
  
  // Verbose output for better debugging
  verbose: true,
  
  // Test timeout
  testTimeout: 10000,
  
  // Additional test patterns
  testMatch: [
    '**/__tests__/**/*.(test|spec).(js|jsx|ts|tsx)',
    '**/?(*.)(test|spec).(js|jsx|ts|tsx)',
  ],
  
  // Performance tests configuration
  projects: [
    {
      displayName: 'unit-tests',
      testMatch: ['**/__tests__/**/*.test.(js|jsx|ts|tsx)'],
      testEnvironment: 'jsdom',
    },
    {
      displayName: 'integration-tests', 
      testMatch: ['**/__tests__/**/*.integration.test.(js|jsx|ts|tsx)'],
      testEnvironment: 'node',
    },
    {
      displayName: 'performance-tests',
      testMatch: ['**/__tests__/**/*.performance.test.(js|jsx|ts|tsx)'],
      testEnvironment: 'node',
      testTimeout: 30000,
    },
  ],
  
  // Mock configuration
  clearMocks: true,
  restoreMocks: true,
  
  // Error handling
  errorOnDeprecated: true,
  
  // Watch plugins for better development experience
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],
};