import { View, Text, StyleSheet, Pressable, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { usePathname, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type CustomHeaderProps = {
  title?: string;
  showBackButton?: boolean;
  onBackPress?: () => void;
};

export function CustomHeader({ title = 'PrepSense', showBackButton = false, onBackPress }: CustomHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();

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
        
        {/* Title */}
        <Text style={styles.title}>{title}</Text>
        
        {/* Menu Button (always shown) */}
        <Pressable 
          hitSlop={12} 
          onPress={toggleMenu} 
          style={styles.menuButton}
        >
          <Ionicons name="menu" size={24} color="#1b6b45" />
        </Pressable>
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
  },
  menuButton: {
    marginLeft: 'auto', // Push to the right
  },
  leftButton: {
    marginRight: 'auto', // Push to the left
  },
});
