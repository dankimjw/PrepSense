// src/config.ts (or your preferred location)

// --- Environment Detection ---
// __DEV__ is a global variable set by React Native/Expo.
// It's true during development (Metro bundler) and false in production builds.
const IS_DEVELOPMENT = __DEV__;

// --- API Configuration ---
// Allow overriding the API URL via an environment variable exposed by Expo.
const ENV_API_URL = process.env.EXPO_PUBLIC_API_BASE_URL;

// Development API (your local machine running the backend)
// `run_ios.py` attempts to detect your computer's IP and sets
// EXPO_PUBLIC_API_BASE_URL automatically. If that fails,
// replace '127.0.0.1' with your actual IP address.
// '127.0.0.1' works if the app is running in a web browser on the SAME machine as the backend.
const DEV_API_CONFIG = {
  baseURL: ENV_API_URL || 'http://127.0.0.1:8001/api/v1', // Using port 8001 for the backend service
  timeout: 15000, // API request timeout in milliseconds (e.g., 15 seconds)
};

// Production API (your deployed backend)
// IMPORTANT: Replace with your actual deployed backend URL.
const PROD_API_CONFIG = {
  baseURL: 'https://api.yourprepsenseapp.com/v1', // Example production URL
  timeout: 30000, // API request timeout in milliseconds (e.g., 30 seconds)
};

// Select API config based on environment
const API_CONFIG = IS_DEVELOPMENT ? DEV_API_CONFIG : PROD_API_CONFIG;

// --- Feature Flags ---
// Use these to easily enable/disable features during development or for A/B testing.
const FEATURE_FLAGS = {
  enableAdvancedAnalytics: !IS_DEVELOPMENT, // Example: Only enable in production
  enableExperimentalImageProcessing: false, // Example: A feature currently off for everyone
  showDebugInfo: IS_DEVELOPMENT, // Example: Show extra debug info only in development
};

// --- Logging Configuration ---
const LOG_LEVEL = IS_DEVELOPMENT ? 'debug' : 'warn'; // 'debug', 'info', 'warn', 'error'

// --- App Settings ---
const APP_SETTINGS = {
  appName: 'PrepSense',
  version: '1.0.0', // Your app version
  defaultDebounceTime: 300, // Default debounce time in ms for inputs
  maxImageUploadSizeMB: 10, // Max image size in MB
};

// --- Third-Party Service Keys (Example) ---
// Be cautious about storing sensitive keys directly in client-side code.
// For truly sensitive keys, consider using a backend proxy or build-time variables.
const THIRD_PARTY_KEYS = {
  // exampleAnalyticsKey: IS_DEVELOPMENT ? 'DEV_ANALYTICS_KEY' : 'PROD_ANALYTICS_KEY',
  // exampleErrorReportingKey: 'YOUR_ERROR_REPORTING_KEY',
};

// --- Export all configurations ---
export const Config = {
  IS_DEVELOPMENT,
  API_BASE_URL: API_CONFIG.baseURL,
  API_TIMEOUT: API_CONFIG.timeout,
  FEATURE_FLAGS,
  LOG_LEVEL,
  APP_SETTINGS,
  THIRD_PARTY_KEYS,
  // You can also export the full API_CONFIG if you need more than just baseURL and timeout
  // API_CONFIG,
};

// Default export for convenience if you primarily use API_BASE_URL
export default Config.API_BASE_URL;

// How to use in your app:
// import { Config } from './config'; // Or the correct path
// console.log(Config.API_BASE_URL);
// console.log(Config.FEATURE_FLAGS.showDebugInfo);

// Or for just the API base URL (if you keep the default export):
// import API_BASE_URL from './config';
// console.log(API_BASE_URL);
