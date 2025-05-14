import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabsLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index" // Refers to app/(tabs)/index.tsx
        options={{
          tabBarLabel: 'Home', // Custom label for the tab
          title: 'Confirm Photo', // Custom title for the screen
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}