// app/components/CustomHeader.tsx - Part of the PrepSense mobile app
import { View, Text, StyleSheet, Pressable, Alert, ActivityIndicator, Image } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { usePathname, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState } from 'react';
import { API_BASE_URL } from '../../constants/Config';
import GradientText from './GradientText';

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
  const [showAdminMenu, setShowAdminMenu] = useState(false);
  const [isCleaningUp, setIsCleaningUp] = useState(false);
  
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
  
  // Show buttons based on props and current route
  const shouldShowChat = isMainTab && showChatButton !== false;
  const shouldShowAdmin = isMainTab && showAdminButton !== false;
  const shouldShowDb = isMainTab && showDbButton !== false;
  
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
        <View style={styles.titleContainer}>
          <Text style={styles.title}>{headerTitle}</Text>
        </View>
        
        <View style={styles.rightButtons}>
          {shouldShowDb && (
            <Pressable 
              hitSlop={12} 
              onPress={() => router.push('/bigquery-tester')}
              style={styles.iconButton}
            >
              <Ionicons name="server-outline" size={24} color="#1b6b45" />
            </Pressable>
          )}
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
            <View>
              <Pressable 
                hitSlop={12} 
                onPress={() => setShowAdminMenu(!showAdminMenu)}
                style={styles.iconButton}
              >
                <Ionicons name="shield-outline" size={24} color="#1b6b45" />
              </Pressable>
              
              {/* Popup admin menu */}
              {showAdminMenu && (
                <View style={styles.adminMenuContainer}>
                  {/* Admin Settings option */}
                  <Pressable 
                    style={styles.adminMenuItem}
                    onPress={() => {
                      setShowAdminMenu(false);
                      router.push('/(tabs)/admin');
                    }}
                  >
                    <View style={styles.adminMenuIcon}>
                      <Ionicons name="settings-outline" size={16} color="#FFFFFF" />
                    </View>
                    <Text style={styles.adminMenuText}>Admin Panel</Text>
                  </Pressable>
                  

                </View>
              )}
            </View>
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
    width: 80,
    alignItems: 'flex-start',
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
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
    fontSize: 20,
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
    width: 80,
    justifyContent: 'flex-end',
  },
  iconButton: {
    paddingHorizontal: 8,
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
