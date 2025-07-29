// app/_layout.tsx - Part of the PrepSense mobile app
import { Stack, useRouter, useSegments, usePathname } from 'expo-router';
import { ThemeProvider, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { useColorScheme, View, StyleSheet, ActivityIndicator, LogBox } from 'react-native';
import { CustomHeader } from './components/CustomHeader';
import { useEffect, useState } from 'react';
import { ItemsProvider } from '../context/ItemsContext';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { UserPreferencesProvider } from '../context/UserPreferencesContext';
import { TabDataProvider } from '../context/TabDataProvider';
import { envValidator, EnvironmentStatus } from '../utils/environmentValidator';
import ConfigurationError from './components/ConfigurationError';
import { ToastProvider } from '../hooks/useToast';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { PreloadDebugOverlay } from '../components/PreloadDebugOverlay';
import { initPreloadDebug } from '../utils/debugPreload';
import AnimatedIntroScreen from '../components/AnimatedIntroScreen';
import EnhancedAnimatedIntroScreenV2 from '../components/EnhancedAnimatedIntroScreenV2';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Initialize debug commands in development
if (__DEV__) {
  initPreloadDebug();
}

// Configure warning/error suppression
if (process.env.EXPO_PUBLIC_SUPPRESS_WARNINGS === 'true') {
  // Suppress ALL logs (warnings and errors) in the app
  LogBox.ignoreAllLogs(true);
} else {
  // Selectively ignore specific warnings
  LogBox.ignoreLogs([
    // React Native warnings
    'Warning: componentWillReceiveProps',
    'Warning: componentWillMount',
    'Non-serializable values were found',
    'VirtualizedLists should never be nested',
    // Expo warnings
    'Constants.platform.ios.model',
    'Constants.deviceId',
    // AsyncStorage warnings
    'AsyncStorage has been extracted',
    // Add more specific warnings to ignore here
  ]);
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

// This component will protect routes that require auth
function AppContent() {
  const colorScheme = useColorScheme();
  const { isLoading, isAuthenticated, signIn } = useAuth();
  const segments = useSegments();
  const pathname = usePathname();
  const router = useRouter();
  const [envStatus, setEnvStatus] = useState<EnvironmentStatus | null>(null);
  const [isValidatingEnv, setIsValidatingEnv] = useState(true);
  const [showIntro, setShowIntro] = useState(false);
  const [isCheckingIntro, setIsCheckingIntro] = useState(true);

  // Check if the current route is in the auth group
  const isAuthRoute = segments[0] === '(auth)';

  // Check if intro has been shown before
  useEffect(() => {
    const checkIntroShown = async () => {
      try {
        const hasShownIntro = await AsyncStorage.getItem('hasShownIntro');
        // Don't show intro automatically, wait for keyboard trigger
        setShowIntro(false);
      } catch (error) {
        console.error('Error checking intro status:', error);
        setShowIntro(false);
      } finally {
        setIsCheckingIntro(false);
      }
    };

    checkIntroShown();
  }, []);

  // Expose intro trigger globally for demo
  useEffect(() => {
    if (__DEV__) {
      // @ts-ignore
      global.showIntroAnimation = () => {
        console.log('🎬 Triggering intro animation...');
        setShowIntro(true);
      };
      console.log('💡 To show intro: global.showIntroAnimation() or triple-tap PrepSense logo');
    }
  }, []);

  // Validate environment on app start
  useEffect(() => {
    const validateEnv = async () => {
      try {
        const status = await envValidator.validateEnvironment();
        setEnvStatus(status);
      } catch (error) {
        console.error('Environment validation error:', error);
      } finally {
        setIsValidatingEnv(false);
      }
    };

    validateEnv();
  }, []);

  // Log screen changes
  useEffect(() => {
    if (pathname) {
      envValidator.displayScreenLoad(pathname);
    }
  }, [pathname]);

  // Auto sign in with default credentials on initial load
  useEffect(() => {
    const autoSignIn = async () => {
      if (!isAuthenticated && !isLoading) {
        try {
          // Use default credentials to sign in automatically
          await signIn('samantha.smith@example.com', 'password');
        } catch (error) {
          console.log('Auto sign-in failed, showing sign-in screen');
        }
      }
    };

    autoSignIn();
  }, [isAuthenticated, isLoading]);

  // Handle navigation based on auth state
  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated && isAuthRoute) {
        // If user is signed in and the current route is in the auth group, redirect to home
        router.replace('/(tabs)');
      } else if (!isAuthenticated && !isAuthRoute) {
        // If user is not signed in and the current route is not in the auth group, redirect to sign-in
        router.replace('/(auth)/sign-in');
      }
    }
  }, [isLoading, isAuthenticated, isAuthRoute, pathname]);

  // Handle intro screen completion
  const handleIntroFinished = async () => {
    try {
      await AsyncStorage.setItem('hasShownIntro', 'true');
      setShowIntro(false);
    } catch (error) {
      console.error('Error saving intro status:', error);
    }
  };

  // Show intro screen if needed
  if (showIntro && !isCheckingIntro) {
    return <EnhancedAnimatedIntroScreenV2 onFinished={handleIntroFinished} />;
  }

  // Show a loading indicator while checking environment or auth state
  if (isValidatingEnv || isLoading || isCheckingIntro) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
      </View>
    );
  }

  // Show configuration error screen if there are critical errors
  if (envStatus && !envStatus.allValid) {
    const hasErrors = Object.values(envStatus.checks).some(check => check.status === 'ERROR');
    if (hasErrors) {
      return (
        <ConfigurationError 
          status={envStatus} 
          onRetry={async () => {
            setIsValidatingEnv(true);
            const newStatus = await envValidator.validateEnvironment();
            setEnvStatus(newStatus);
            setIsValidatingEnv(false);
          }}
        />
      );
    }
  }

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <ToastProvider>
        <UserPreferencesProvider>
          <ItemsProvider>
            <TabDataProvider>
              <View style={styles.container}>
                <Stack>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen 
              name="(auth)" 
              options={{ 
                headerShown: false,
                animation: 'fade',
              }} 
            />
            <Stack.Screen 
              name="edit-item" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Edit Item" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                ),
                presentation: 'modal',
                animation: 'slide_from_bottom',
              }} 
            />
<Stack.Screen 
              name="confirm" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Confirm Items" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                )
              }} 
            />
            <Stack.Screen 
              name="upload-photo" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Upload Photo" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                )
              }} 
            />
            <Stack.Screen 
              name="settings" 
              options={{ headerShown: false }} 
            />
            <Stack.Screen 
              name="confirm-photo" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Confirm Photo" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                )
              }} 
            />
            <Stack.Screen 
              name="items-detected" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Items Detected" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                )
              }} 
            />
            <Stack.Screen 
              name="select-unit" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Select Unit" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                ),
                presentation: 'modal',
              }} 
            />
            <Stack.Screen 
              name="add-item" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Add Item" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                ),
                presentation: 'modal',
                animation: 'slide_from_bottom',
              }} 
            />
            <Stack.Screen 
              name="chat-modal" 
              options={{ 
                headerShown: false,
                presentation: 'modal',
                animation: 'slide_from_bottom',
              }} 
            />
            <Stack.Screen 
              name="recipe-spoonacular-detail" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Recipe Details" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                ),
                animation: 'slide_from_right',
              }} 
            />
                </Stack>
              </View>
              {/* {__DEV__ && <PreloadDebugOverlay />} */}
            </TabDataProvider>
          </ItemsProvider>
        </UserPreferencesProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </GestureHandlerRootView>
  );
}