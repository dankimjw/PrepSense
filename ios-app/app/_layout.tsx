import { Stack, useRouter, useSegments, usePathname } from 'expo-router';
import { ThemeProvider, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { useColorScheme, View, StyleSheet, Text, ActivityIndicator } from 'react-native';
import { ChatButton } from './components/ChatButton';
import { CustomHeader } from './components/CustomHeader';
import { useEffect, useState } from 'react';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
});

// This is a simple auth context for demo purposes
// In a real app, you'd want to use a proper auth provider like Auth0, Firebase, etc.
function useAuth() {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      // Simulate checking auth state
      await new Promise(resolve => setTimeout(resolve, 1000));
      // For demo, we'll consider user as logged in if they're not on auth screens
      const isAuthRoute = ['/(auth)'].some(route => router.canGoBack());
      setUser(isAuthRoute ? null : 'demo@example.com');
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  return {
    isLoading,
    user,
    signIn: (email: string) => {
      setUser(email);
      return Promise.resolve();
    },
    signOut: () => {
      setUser(null);
      return Promise.resolve();
    },
  };
}

// This component will protect routes that require authentication
function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isLoading, user } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!user && !inAuthGroup) {
      // Redirect to sign-in if not authenticated and not in auth group
      router.replace('/(auth)/sign-in');
    } else if (user && inAuthGroup) {
      // Redirect to home if authenticated and in auth group
      router.replace('/(tabs)');
    }
  }, [user, isLoading, segments]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#297A56" />
      </View>
    );
  }

  return <>{children}</>;
}

export default function RootLayout() {
  const scheme = useColorScheme();

  return (
    <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <View style={styles.container}>
          <Stack>
            <Stack.Screen
              name="(tabs)"
              options={{
                headerShown: true,
                title: 'PrepSense',
                header: () => (
                  <CustomHeader 
                    title="PrepSense"
                    showBackButton={false}
                  />
                ),
              }}
            />
            <Stack.Screen
              name="(auth)"
              options={{
                headerShown: false,
              }}
            />
            <Stack.Screen
              name="confirm"
              options={{
                title: 'Confirm Items',
                header: () => (
                  <CustomHeader 
                    title="Confirm Items"
                    showBackButton={true}
                  />
                ),
              }}
            />
            <Stack.Screen
              name="chat"
              options={{
                headerShown: true,
                title: 'Pantry Assistant',
                header: ({ options }) => (
                  <CustomHeader 
                    title={options.title}
                    showBackButton={true}
                  />
                ),
              }}
            />
            <Stack.Screen
              name="upload-photo"
              options={{
                headerShown: true,
                title: 'Upload Photo',
                header: ({ options }) => (
                  <CustomHeader 
                    title={options.title}
                    showBackButton={true}
                  />
                ),
              }}
            />
            <Stack.Screen
              name="settings"
              options={{
                headerShown: false,
              }}
            />
          </Stack>
          <ChatButton />
        </View>
      </AuthProvider>
    </ThemeProvider>
  );
}