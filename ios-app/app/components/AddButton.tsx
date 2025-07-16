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
  "Go to chat",
  "What can I make for dinner?",
  "What can I make with only ingredients I have?",
  "What's good for breakfast?",
  "Show me healthy recipes",
  "Quick meals under 20 minutes",
  "What's expiring soon?",
  "Low calorie recipes",
  "High protein meals",
];

function AddButton() {
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
  const modalFadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnims = useRef(
    suggestedMessages.map(() => new Animated.Value(-50))
  ).current;
  
  // Ensure animations are initialized
  if (!fadeAnim || !slideAnims || slideAnims.length === 0) {
    return null;
  }

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
    
    // Close lightbulb suggestions if open
    if (newState && showSuggestions) {
      setShowSuggestions(false);
      fadeAnim.setValue(0);
      slideAnims.forEach(anim => {
        if (anim) anim.setValue(-50);
      });
    }
    
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
  
  const toggleSuggestions = () => {
    const newState = !showSuggestions;
    setShowSuggestions(newState);
    
    if (!fadeAnim || !slideAnims) return;
    
    // Close add modal if open
    if (newState && modalVisible) {
      setModalVisible(false);
      modalFadeAnim.setValue(0);
    }
    
    if (newState) {
      // Reset slide animations to starting position
      slideAnims.forEach(anim => {
        if (anim) anim.setValue(-50);
      });
      
      // Animate in
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        ...slideAnims.map((anim, index) =>
          anim ? Animated.timing(anim, {
            toValue: 0,
            duration: 300,
            delay: index * 30, // Reduced delay for more items
            useNativeDriver: true,
          }) : null
        ).filter(Boolean),
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
          anim ? Animated.timing(anim, {
            toValue: -50,
            duration: 200,
            useNativeDriver: true,
          }) : null
        ).filter(Boolean),
      ]).start(() => {
        // Reset animations after closing
        fadeAnim.setValue(0);
        slideAnims.forEach(anim => {
          if (anim) anim.setValue(-50);
        });
      });
    }
  };
  
  const handleSuggestionPress = (suggestion: string) => {
    setShowSuggestions(false);
    
    if (suggestion === "Go to chat") {
      // Navigate to chat modal without a suggestion
      router.push('/chat-modal');
    } else {
      // Navigate to chat modal with the suggestion
      router.push({
        pathname: '/chat-modal',
        params: { suggestion }
      });
    }
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
        <>
          {/* Invisible overlay to detect outside clicks */}
          <Pressable 
            style={styles.dismissOverlay} 
            onPress={() => setShowSuggestions(false)} 
          />
          
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
                {/* Individual background swatch */}
                <View style={styles.suggestionSwatch} />
                
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
        </>
      )}
      
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
              <View style={styles.suggestionSwatch} />
              <TouchableOpacity
                style={styles.suggestionBubble}
                onPress={handleAddImage}
                activeOpacity={0.8}
              >
                <View style={styles.addOptionContent}>
                  <Ionicons name="image" size={18} color="#297A56" />
                  <Text style={styles.suggestionText}>Add Image</Text>
                </View>
              </TouchableOpacity>
            </View>
            
            {/* Add Food Item Option */}
            <View style={styles.addOptionWrapper}>
              <View style={styles.suggestionSwatch} />
              <TouchableOpacity
                style={styles.suggestionBubble}
                onPress={handleAddFoodItem}
                activeOpacity={0.8}
              >
                <View style={styles.addOptionContent}>
                  <Ionicons name="fast-food" size={18} color="#297A56" />
                  <Text style={styles.suggestionText}>Add Food Item</Text>
                </View>
              </TouchableOpacity>
            </View>
          </Animated.View>
        </>
      )}
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
  lightbulbFab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_SIZE + FAB_MARGIN * 2 + 8,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: 'rgba(245, 158, 11, 0.85)',
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
    position: 'relative',
  },
  suggestionSwatch: {
    position: 'absolute',
    top: -5,
    left: -5,
    right: -5,
    bottom: -5,
    borderRadius: 23,
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
  },
  suggestionBubble: {
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
  suggestionText: {
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