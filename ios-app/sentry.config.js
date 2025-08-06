/**
 * Enhanced Sentry configuration for PrepSense React Native app
 * This file replaces the basic sentry.config.js with comprehensive error monitoring
 */
import { initializeSentry } from './config/sentryConfig';

// Initialize Sentry with enhanced configuration
initializeSentry();

console.log('📊 Sentry configuration loaded');

// Export for backward compatibility
export { default, sentryLogger } from './config/sentryConfig';