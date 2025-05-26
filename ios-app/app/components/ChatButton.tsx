// app/components/ChatButton.tsx - Part of the PrepSense mobile app
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { useAuth } from '../../context/AuthContext';

// Get screen width to calculate tab positions
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 64; // From tab bar styles
const TAB_COUNT = 5; // Number of tabs (including the empty add button)
const TAB_WIDTH = SCREEN_WIDTH / TAB_COUNT;

const FAB_SIZE = 48;
const FAB_MARGIN = 16;

export function ChatButton() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuth();
  
  const isAdmin = user?.is_admin;

  // Don't render the chat button if we're on the chat screen
  if (pathname === '/chat' || pathname === '/(tabs)/admin') {
    return null;
  }

  return (
    <View style={styles.fabContainer}>
      {isAdmin && (
        <Pressable
          onPress={() => router.push('/(tabs)/admin')}
          style={[styles.fab, styles.adminFab]}>
          <MaterialIcons name="admin-panel-settings" size={24} color="#fff" />
        </Pressable>
      )}
      <Pressable
        onPress={() => router.push('/chat')}
        style={[styles.fab, styles.chatFab]}>
        <Ionicons name="chatbubble-ellipses" size={20} color="#fff" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  fabContainer: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + 16,
    right: TAB_WIDTH / 2 - FAB_SIZE / 2,
    alignItems: 'center',
  },
  fab: {
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10, // Make sure it's above the tab bar
  },
  chatFab: {
    backgroundColor: 'rgba(41, 122, 86, 0.9)', // 90% opacity of the original green
  },
  adminFab: {
    backgroundColor: 'rgba(74, 109, 167, 0.9)', // Blue color for admin
    marginBottom: FAB_MARGIN,
  },
});
