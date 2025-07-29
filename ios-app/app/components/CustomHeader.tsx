// app/components/CustomHeader.tsx - Part of the PrepSense mobile app
import { View, Text, StyleSheet, Pressable, Alert, ActivityIndicator, Image } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { usePathname, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState, useRef } from 'react';
import { Config } from '../../config';
import GradientText from './GradientText';
import { useAuth } from '../../context/AuthContext';
import UserPreferencesModal from './UserPreferencesModal';

type CustomHeaderProps = {
  title?: string;
  showBackButton?: boolean;
  showChatButton?: boolean;
  showAdminButton?: boolean;
  showDbButton?: boolean;
  onBackPress?: () => void;
  onRefresh?: () => void;
};

export function CustomHeader({ 
  title = 'PrepSense', 
  showBackButton = false, 
  showChatButton = false, 
  showAdminButton = false,
  showDbButton = false,
  onBackPress,
  onRefresh
}: CustomHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const [preferencesVisible, setPreferencesVisible] = useState(false);
  const tapCountRef = useRef(0);
  const tapTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  const isAdmin = user?.is_admin;
  
  // Always show 'PrepSense' as the title
  const headerTitle = 'PrepSense';
  
  // Determine if we're on a main tab where chat and admin buttons should be visible
  const isMainTab = [
    '/(tabs)/',
    '/(tabs)/index',
    '/(tabs)/stats',
    '/(tabs)/recipes',
    '/(tabs)/shopping-list',
    '/(tabs)/profile',
  ].some(path => pathname.startsWith(path));
  
  // Show buttons based on props and current route
  const shouldShowChat = showChatButton !== false;
  const shouldShowAdmin = showAdminButton !== false && isAdmin; // Re-added admin check
  const shouldShowDb = showDbButton !== false;
  
  // Cleanup functionality has been moved to the Admin screen

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

  const handleTitlePress = () => {
    // Single tap - do nothing
  };

  const handleTitleLongPress = () => {
    if (__DEV__) {
      // @ts-ignore
      if (global.showIntroAnimation) {
        // @ts-ignore
        global.showIntroAnimation();
      }
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        {/* Left side - Back button or spacer */}
        <View style={styles.leftContainer}>
          {showBackButton && (
            <Pressable 
              hitSlop={12} 
              onPress={handleBack} 
              style={styles.leftButton}
            >
              <Ionicons name="arrow-back" size={24} color="#1b6b45" />
            </Pressable>
          )}
        </View>
        
        {/* Title - Always centered */}
        <Pressable 
          onPress={handleTitlePress}
          onLongPress={handleTitleLongPress}
          delayLongPress={600}
          style={styles.titleContainer}
        >
          <Text style={styles.title}>{headerTitle}</Text>
        </Pressable>
        
        <View style={styles.rightButtons}>
          {shouldShowDb && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/bigquery-tester')}
              style={styles.iconButton}
            >
              <Ionicons name="server-outline" size={22} color="#1b6b45" />
            </Pressable>
          )}
          {shouldShowChat && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/chat-modal')}
              style={styles.iconButton}
            >
              <Ionicons name="chatbubble-ellipses-outline" size={22} color="#1b6b45" />
            </Pressable>
          )}
          <Pressable 
            hitSlop={12} 
            onPress={() => setPreferencesVisible(true)}
            style={styles.iconButton}
          >
            <Ionicons name="person-circle-outline" size={22} color="#1b6b45" />
          </Pressable>
          {shouldShowAdmin && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/(tabs)/admin')}
              style={styles.iconButton}
            >
              <Ionicons name="shield-outline" size={22} color="#1b6b45" />
            </Pressable>
          )}
          <Pressable 
            hitSlop={12} 
            onPress={toggleMenu} 
            style={styles.iconButton}
          >
            <Ionicons name="menu" size={22} color="#1b6b45" />
          </Pressable>
        </View>
      </View>
      
      {/* User Preferences Modal */}
      <UserPreferencesModal
        visible={preferencesVisible}
        onClose={() => setPreferencesVisible(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderBottomWidth: 0.5,
    borderBottomColor: '#e4e4e7',
    zIndex: 10, // Increased to ensure admin menu shows above everything
    elevation: 10,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  leftContainer: {
    width: 120,
    alignItems: 'flex-start',
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  logo: {
    width: 28,
    height: 28,
    marginRight: 8,
  },
  logoIcon: {
    marginRight: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1b6b45',
  },
  leftButton: {
    width: 40,
    alignItems: 'flex-start',
  },
  rightButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 6,
    width: 120,
  },
  iconButton: {
    paddingHorizontal: 4,
  },
  adminMenuContainer: {
    position: 'absolute',
    right: 0,
    top: 40,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 8,
    width: 200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    zIndex: 20,
  },
  adminMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 4,
  },
  adminMenuItemDisabled: {
    opacity: 0.6,
  },
  adminMenuIcon: {
    backgroundColor: '#1b6b45',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  adminMenuText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937',
  },
});

export default CustomHeader;
