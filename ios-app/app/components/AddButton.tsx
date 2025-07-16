// app/components/AddButton.tsx - Part of the PrepSense mobile app
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View, Modal, Text, TouchableOpacity, Animated } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { useState, useRef } from 'react';
import UserPreferencesModal from './UserPreferencesModal';

// Get screen width to calculate tab positions
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 72; // From tab bar styles
const FAB_SIZE = 48; // Reduced from 56
const FAB_MARGIN = 16;

function AddButton() {
  const router = useRouter();
  let pathname = '';
  
  try {
    pathname = usePathname() || '';
  } catch (error) {
    console.warn('Error getting pathname:', error);
  }
  
  const [modalVisible, setModalVisible] = useState(false);
  const [preferencesVisible, setPreferencesVisible] = useState(false);
  
  // Animation values
  const modalFadeAnim = useRef(new Animated.Value(0)).current;

  // Don't render the buttons on certain screens
  if (pathname && (pathname === '/add-item' || pathname === '/upload-photo' || pathname === '/(tabs)/admin' || pathname === '/chat-modal')) {
    return null;
  }

  const handleAddImage = () => {
    toggleModal();
    setTimeout(() => router.push('/upload-photo'), 200);
  };

  const handleAddFoodItem = () => {
    toggleModal();
    setTimeout(() => router.push('/add-item'), 200);
  };
  
  const toggleModal = () => {
    const newState = !modalVisible;
    
    if (newState) {
      setModalVisible(true);
      Animated.timing(modalFadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(modalFadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start(() => {
        setModalVisible(false);
        modalFadeAnim.setValue(0);
      });
    }
  };

  const openPreferences = () => {
    setPreferencesVisible(true);
  };

  return (
    <>
      {/* Preferences Button - Always visible */}
      <TouchableOpacity
        style={styles.preferencesFab}
        onPress={openPreferences}
        activeOpacity={0.8}
      >
        <Ionicons 
          name="settings" 
          size={24} 
          color="#fff" 
        />
      </TouchableOpacity>
      
      {/* Add Button */}
      <Pressable
        onPress={toggleModal}
        style={styles.fab}>
        <Ionicons name="add" size={28} color="#fff" />
      </Pressable>

      {/* Add Button Modal */}
      {modalVisible && (
        <>
          {/* Invisible overlay to detect outside clicks */}
          <Pressable 
            style={styles.dismissOverlay} 
            onPress={() => setModalVisible(false)} 
          />
          
          <Animated.View 
            style={[
              styles.addOptionsContainer,
              { 
                opacity: modalFadeAnim,
                transform: [{ scale: modalFadeAnim }]
              }
            ]}
          >
            {/* Add Image Option */}
            <View style={styles.addOptionWrapper}>
              <View style={styles.optionSwatch} />
              <TouchableOpacity
                style={styles.optionBubble}
                onPress={handleAddImage}
                activeOpacity={0.8}
              >
                <View style={styles.addOptionContent}>
                  <Ionicons name="image" size={18} color="#297A56" />
                  <Text style={styles.optionText}>Add Image</Text>
                </View>
              </TouchableOpacity>
            </View>
            
            {/* Add Food Item Option */}
            <View style={styles.addOptionWrapper}>
              <View style={styles.optionSwatch} />
              <TouchableOpacity
                style={styles.optionBubble}
                onPress={handleAddFoodItem}
                activeOpacity={0.8}
              >
                <View style={styles.addOptionContent}>
                  <Ionicons name="fast-food" size={18} color="#297A56" />
                  <Text style={styles.optionText}>Add Food Item</Text>
                </View>
              </TouchableOpacity>
            </View>
          </Animated.View>
        </>
      )}

      {/* User Preferences Modal */}
      <UserPreferencesModal
        visible={preferencesVisible}
        onClose={() => setPreferencesVisible(false)}
      />
    </>
  );
}

export default AddButton;

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: 'rgba(41, 122, 86, 0.85)',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#297A56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10,
  },
  addOptionsContainer: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_SIZE + FAB_MARGIN + 8,
    zIndex: 9,
    alignItems: 'flex-end',
  },
  addOptionWrapper: {
    marginBottom: 8,
    position: 'relative',
  },
  addOptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  preferencesFab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_SIZE + FAB_MARGIN * 2 + 8,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: 'rgba(107, 114, 128, 0.85)',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#6B7280',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10,
  },
  optionSwatch: {
    position: 'absolute',
    top: -5,
    left: -5,
    right: -5,
    bottom: -5,
    borderRadius: 23,
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
  },
  optionBubble: {
    backgroundColor: '#fff',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#297A56',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 5,
  },
  optionText: {
    fontSize: 13,
    color: '#297A56',
    fontWeight: '500',
  },
  dismissOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 8,
  },
});