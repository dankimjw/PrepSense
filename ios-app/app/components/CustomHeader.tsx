import { View, Text, StyleSheet, Pressable, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { usePathname, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type CustomHeaderProps = {
  title?: string;
  showBackButton?: boolean;
  showChatButton?: boolean;
  showAdminButton?: boolean;
  onBackPress?: () => void;
};

export function CustomHeader({ 
  title = 'PrepSense', 
  showBackButton = false, 
  showChatButton = false, 
  showAdminButton = false,
  onBackPress 
}: CustomHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  
  // Always show 'PrepSense' as the title
  const headerTitle = 'PrepSense';
  
  // Determine if we're on a main tab where chat and admin buttons should be visible
  const isMainTab = [
    '/(tabs)/',
    '/(tabs)/index',
    '/(tabs)/stats',
    '/(tabs)/recipes',
    '/(tabs)/profile',
  ].some(path => pathname.startsWith(path));
  
  // Always show chat and admin buttons on main tabs, unless explicitly disabled
  const shouldShowChat = isMainTab && showChatButton !== false;
  const shouldShowAdmin = isMainTab && showAdminButton !== false;

  const toggleMenu = () => {
    // Navigate to settings when menu is pressed
    if (pathname !== '/settings') {
      router.push('/settings');
    }
  };

  const handleBack = () => {
    if (onBackPress) {
      onBackPress();
    } else if (router.canGoBack()) {
      router.back();
    } else {
      router.replace('/(tabs)');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        {/* Back Button (only shown when showBackButton is true) */}
        {showBackButton && (
          <Pressable 
            hitSlop={12} 
            onPress={handleBack} 
            style={styles.leftButton}
          >
            <Ionicons name="arrow-back" size={24} color="#1b6b45" />
          </Pressable>
        )}
        
        {/* Title - Always show 'PrepSense' */}
        <Text style={styles.title}>{headerTitle}</Text>
        
        <View style={styles.rightButtons}>
          {shouldShowChat && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/chat')}
              style={styles.iconButton}
            >
              <Ionicons name="chatbubble-ellipses-outline" size={24} color="#1b6b45" />
            </Pressable>
          )}
          {shouldShowAdmin && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/(tabs)/admin')}
              style={styles.iconButton}
            >
              <Ionicons name="shield-outline" size={24} color="#1b6b45" />
            </Pressable>
          )}
          <Pressable 
            hitSlop={12} 
            onPress={toggleMenu} 
            style={styles.iconButton}
          >
            <Ionicons name="menu" size={24} color="#1b6b45" />
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderBottomWidth: 0.5,
    borderBottomColor: '#e5e5e5',
  },
  header: {
    marginTop: 17, // Matches iOS standard spacing
    marginHorizontal: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: 36, // Standard touch target size
    marginBottom: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1b6b45',
    marginLeft: 0,
  },
  rightButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 'auto',
  },
  iconButton: {
    marginLeft: 16,
  },
  leftButton: {
    marginRight: 'auto',
  },
});
