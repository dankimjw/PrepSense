import { Stack } from 'expo-router';
import { ThemeProvider, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { useColorScheme } from 'react-native';

export default function RootLayout() {
  const scheme = useColorScheme();

  return (
    <ThemeProvider value={scheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        {/* Screen entry for your Tabs layout */}
        <Stack.Screen
          name="(tabs)"
          options={{
            headerShown: false,
          }}
        />
        {/* Screen entry for your confirm screen */}
        <Stack.Screen
          name="confirm"
          options={{
            title: 'Confirm Items', // Set a title for the header
            headerBackTitle: 'Back', // Replace (tabs) with Back
          }}
        />
      </Stack>
    </ThemeProvider>
  );
}