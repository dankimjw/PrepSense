import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions } from 'react-native';
import { useRouter, usePathname } from 'expo-router';

// Get screen width to calculate tab positions
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 64; // From tab bar styles
const TAB_COUNT = 5; // Number of tabs (including the empty add button)
const TAB_WIDTH = SCREEN_WIDTH / TAB_COUNT;

export function ChatButton() {
  const router = useRouter();
  const pathname = usePathname();

  // Don't render the chat button if we're on the chat screen
  if (pathname === '/chat') {
    return null;
  }

  return (
    <Pressable
      onPress={() => router.push('/chat')}
      style={styles.fab}>
      <Ionicons name="chatbubble-ellipses" size={20} color="#fff" />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + 16, // Position above the tab bar with more space
    right: TAB_WIDTH / 2 - 24, // Center above the last tab (profile)
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(41, 122, 86, 0.85)', // 85% opacity of the original green
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10, // Make sure it's above the tab bar
  },
});
