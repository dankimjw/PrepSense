// app/_layout.tsx - Part of the PrepSense mobile app
import { Stack, useRouter, useSegments, usePathname } from 'expo-router';
import { ThemeProvider, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { useColorScheme, View, StyleSheet, ActivityIndicator } from 'react-native';
import { ChatButton } from './components/ChatButton';
import { CustomHeader } from './components/CustomHeader';
import { useEffect } from 'react';
import { ItemsProvider } from '../context/ItemsContext';
import { AuthProvider, useAuth } from '../context/AuthContext';

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

  // Check if the current route is in the auth group
  const isAuthRoute = segments[0] === '(auth)';

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

  // Show a loading indicator while checking auth state
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
      </View>
    );
  }

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <ItemsProvider>
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
              name="chat" 
              options={{ 
                header: ({ navigation }) => (
                  <CustomHeader 
                    title="Chat with AI" 
                    showBackButton={true}
                    onBackPress={() => navigation.goBack()}
                  />
                ),
                presentation: 'modal',
                animation: 'slide_from_right',
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
          </Stack>
          <ChatButton />
        </View>
      </ItemsProvider>
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}