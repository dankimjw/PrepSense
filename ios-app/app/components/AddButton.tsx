// app/components/AddButton.tsx - Part of the PrepSense mobile app
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View, Modal, Text, TouchableOpacity, Animated } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { useState, useRef } from 'react';

// Get screen width to calculate tab positions
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 72; // From tab bar styles
const FAB_SIZE = 48; // Reduced from 56
const FAB_MARGIN = 16;

const suggestedMessages = [
  "What can I make for dinner?",
  "What can I make with only ingredients I have?",
  "What's good for breakfast?",
  "Show me healthy recipes",
  "Quick meals under 20 minutes",
  "What's expiring soon?",
  "Low calorie recipes",
  "High protein meals",
];

export function AddButton() {
  const router = useRouter();
  let pathname = '';
  
  try {
    pathname = usePathname() || '';
  } catch (error) {
    console.warn('Error getting pathname:', error);
  }
  
  const [modalVisible, setModalVisible] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnims = useRef(
    suggestedMessages.map(() => new Animated.Value(-50))
  ).current;

  // Don't render the buttons on certain screens
  if (pathname && (pathname === '/add-item' || pathname === '/upload-photo' || pathname === '/(tabs)/admin')) {
    return null;
  }

  const handleAddImage = () => {
    setModalVisible(false);
    router.push('/upload-photo');
  };

  const handleAddFoodItem = () => {
    setModalVisible(false);
    router.push('/add-item');
  };
  
  const toggleSuggestions = () => {
    const newState = !showSuggestions;
    setShowSuggestions(newState);
    
    if (newState) {
      // Animate in
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        ...slideAnims.map((anim, index) =>
          Animated.timing(anim, {
            toValue: 0,
            duration: 300,
            delay: index * 30, // Reduced delay for more items
            useNativeDriver: true,
          })
        ),
      ]).start();
    } else {
      // Animate out
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        ...slideAnims.map((anim) =>
          Animated.timing(anim, {
            toValue: -50,
            duration: 200,
            useNativeDriver: true,
          })
        ),
      ]).start();
    }
  };
  
  const handleSuggestionPress = (suggestion: string) => {
    setShowSuggestions(false);
    // Navigate to chat with the suggestion
    router.push({
      pathname: '/(tabs)/chat',
      params: { suggestion }
    });
  };

  return (
    <>
      {/* Lightbulb Button - Always visible */}
      <TouchableOpacity
        style={styles.lightbulbFab}
        onPress={toggleSuggestions}
        activeOpacity={0.8}
      >
        <Ionicons 
          name={showSuggestions ? "bulb" : "bulb-outline"} 
          size={24} 
          color="#fff" 
        />
      </TouchableOpacity>
      
      {/* Floating Suggestions */}
      {showSuggestions && (
        <Animated.View 
          style={[
            styles.suggestionsContainer,
            { opacity: fadeAnim }
          ]}
        >
          {suggestedMessages.map((suggestion, index) => (
            <Animated.View
              key={index}
              style={[
                styles.suggestionWrapper,
                {
                  transform: [{ translateX: slideAnims[index] }]
                }
              ]}
            >
              <TouchableOpacity
                style={styles.suggestionBubble}
                onPress={() => handleSuggestionPress(suggestion)}
                activeOpacity={0.8}
              >
                <Text style={styles.suggestionText}>{suggestion}</Text>
              </TouchableOpacity>
            </Animated.View>
          ))}
        </Animated.View>
      )}
      
      {/* Add Button */}
      <Pressable
        onPress={() => setModalVisible(true)}
        style={styles.fab}>
        <Ionicons name="add" size={28} color="#fff" />
      </Pressable>

      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setModalVisible(false)}>
          <View style={styles.modalContent}>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddImage}>
              <Ionicons name="image" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Image</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddFoodItem}>
              <Ionicons name="fast-food" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Food Item</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#297A56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: TAB_BAR_HEIGHT + FAB_SIZE + FAB_MARGIN * 2,
    marginRight: FAB_MARGIN,
    width: 200,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 12,
  },
  modalBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  modalBtnText: {
    fontSize: 16,
    color: '#297A56',
    marginLeft: 12,
    fontWeight: '600',
  },
  lightbulbFab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_SIZE + FAB_MARGIN * 2 + 8,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: '#F59E0B',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#F59E0B',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10,
  },
  suggestionsContainer: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_SIZE + FAB_MARGIN + 8,
    zIndex: 9,
    width: 240,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
  },
  suggestionWrapper: {
    marginBottom: 6,
    marginRight: 6,
  },
  suggestionBubble: {
    backgroundColor: '#fff',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#297A56',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: -1, height: 1 },
    elevation: 3,
  },
  suggestionText: {
    fontSize: 13,
    color: '#297A56',
    fontWeight: '500',
  },
});