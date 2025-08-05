import * as Sentry from '@sentry/react-native';

// Initialize Sentry
Sentry.init({
  dsn: 'YOUR_SENTRY_DSN_HERE', // Replace with your actual Sentry DSN
  debug: __DEV__, // Enable debug in development
  environment: __DEV__ ? 'development' : 'production',
  beforeSend(event) {
    // Filter out development errors if needed
    if (__DEV__) {
      console.log('Sentry Event:', event);
    }
    return event;
  },
});

export default Sentry;