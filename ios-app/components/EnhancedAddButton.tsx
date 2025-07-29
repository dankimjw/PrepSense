// Enhanced AddButton with creative animations
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View, Text, TouchableOpacity } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { useState, useRef } from 'react';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withDelay,
  interpolate,
  Extrapolate,
  runOnJS,
  withSequence,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 72;
const FAB_SIZE = 48;
const FAB_MARGIN = 16;

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);
const AnimatedTouchableOpacity = Animated.createAnimatedComponent(TouchableOpacity);

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

const addMenuItems = [
  { id: 'image', icon: 'image', label: 'Add Image', color: '#10B981' },
  { id: 'food', icon: 'fast-food', label: 'Add Food Item', color: '#3B82F6' },
  { id: 'receipt', icon: 'receipt', label: 'Scan Receipt', color: '#8B5CF6' },
];

function EnhancedAddButton() {
  const router = useRouter();
  let pathname = '';
  
  try {
    pathname = usePathname() || '';
  } catch (error) {
    console.warn('Error getting pathname:', error);
  }
  
  const [modalVisible, setModalVisible] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Reanimated values
  const addButtonScale = useSharedValue(1);
  const addButtonRotation = useSharedValue(0);
  const lightbulbScale = useSharedValue(1);
  const lightbulbRotation = useSharedValue(0);
  
  // Animation values for menu items
  const menuItemsAnimation = useSharedValue(0);
  const suggestionsAnimation = useSharedValue(0);
  
  // Individual item animations
  const itemScales = addMenuItems.map(() => useSharedValue(0));
  const suggestionScales = suggestedMessages.map(() => useSharedValue(0));

  if (pathname && (pathname === '/add-item' || pathname === '/upload-photo' || pathname === '/(tabs)/admin' || pathname === '/chat-modal' || pathname === '/receipt-scanner')) {
    return null;
  }

  const handleAddPress = () => {
    const newState = !modalVisible;
    setModalVisible(newState);
    
    // Close suggestions if open
    if (newState && showSuggestions) {
      setShowSuggestions(false);
      suggestionsAnimation.value = withTiming(0, { duration: 200 });
    }
    
    // Animate button rotation
    addButtonRotation.value = withSpring(newState ? 45 : 0, {
      damping: 15,
      stiffness: 200,
    });
    
    // Animate menu
    menuItemsAnimation.value = withSpring(newState ? 1 : 0, {
      damping: 20,
      stiffness: 180,
    });
    
    // Stagger individual items with elastic effect
    itemScales.forEach((scale, index) => {
      if (newState) {
        scale.value = withDelay(
          index * 50,
          withSpring(1, {
            damping: 10,
            stiffness: 200,
            overshootClamping: false,
          })
        );
      } else {
        scale.value = withDelay(
          (itemScales.length - index - 1) * 30,
          withSpring(0, { damping: 15, stiffness: 300 })
        );
      }
    });
    
    if (newState) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handleSuggestionsPress = () => {
    const newState = !showSuggestions;
    setShowSuggestions(newState);
    
    // Close add menu if open
    if (newState && modalVisible) {
      setModalVisible(false);
      menuItemsAnimation.value = withTiming(0, { duration: 200 });
      addButtonRotation.value = withSpring(0);
    }
    
    // Animate lightbulb wiggle
    if (newState) {
      lightbulbRotation.value = withSequence(
        withTiming(-10, { duration: 50 }),
        withTiming(10, { duration: 100 }),
        withTiming(-10, { duration: 100 }),
        withTiming(10, { duration: 100 }),
        withTiming(0, { duration: 50 })
      );
    }
    
    // Animate suggestions
    suggestionsAnimation.value = withSpring(newState ? 1 : 0, {
      damping: 20,
      stiffness: 150,
    });
    
    // Stagger individual suggestions with wave effect
    suggestionScales.forEach((scale, index) => {
      if (newState) {
        scale.value = withDelay(
          index * 40,
          withSpring(1, {
            damping: 12,
            stiffness: 180,
            overshootClamping: false,
          })
        );
      } else {
        scale.value = withTiming(0, { duration: 200 });
      }
    });
    
    if (newState) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handleMenuItemPress = (item: typeof addMenuItems[0]) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    handleAddPress(); // Close menu
    
    setTimeout(() => {
      switch (item.id) {
        case 'image':
          router.push('/upload-photo');
          break;
        case 'food':
          router.push('/add-item');
          break;
        case 'receipt':
          router.push('/receipt-scanner');
          break;
      }
    }, 300);
  };

  const handleSuggestionPress = (suggestion: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    handleSuggestionsPress(); // Close suggestions
    
    setTimeout(() => {
      if (suggestion === "Go to chat") {
        router.push('/chat-modal');
      } else {
        router.push({
          pathname: '/chat-modal',
          params: { suggestion }
        });
      }
    }, 300);
  };

  // Animated styles for buttons
  const addButtonAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: addButtonScale.value },
      { rotate: `${addButtonRotation.value}deg` },
    ],
  }));

  const lightbulbAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: lightbulbScale.value },
      { rotate: `${lightbulbRotation.value}deg` },
    ],
  }));

  return (
    <>
      {/* Lightbulb Button */}
      <AnimatedTouchableOpacity
        style={[styles.lightbulbFab, lightbulbAnimatedStyle]}
        onPress={handleSuggestionsPress}
        onPressIn={() => {
          lightbulbScale.value = withSpring(0.9, { damping: 15, stiffness: 300 });
        }}
        onPressOut={() => {
          lightbulbScale.value = withSpring(1, { damping: 15, stiffness: 300 });
        }}
        activeOpacity={1}
      >
        <Ionicons 
          name={showSuggestions ? "bulb" : "bulb-outline"} 
          size={24} 
          color="#fff" 
        />
      </AnimatedTouchableOpacity>
      
      {/* Chat Suggestions with Wave Animation */}
      {showSuggestions && (
        <>
          <Pressable 
            style={styles.dismissOverlay} 
            onPress={handleSuggestionsPress} 
          />
          
          <View style={styles.suggestionsContainer}>
            {suggestedMessages.map((suggestion, index) => {
              const animatedStyle = useAnimatedStyle(() => {
                const scale = suggestionScales[index].value;
                const translateY = interpolate(
                  suggestionScales[index].value,
                  [0, 1],
                  [20, 0],
                  Extrapolate.CLAMP
                );
                const opacity = interpolate(
                  suggestionScales[index].value,
                  [0, 0.5, 1],
                  [0, 0.5, 1],
                  Extrapolate.CLAMP
                );
                
                return {
                  transform: [
                    { scale },
                    { translateY },
                  ],
                  opacity,
                };
              });

              return (
                <AnimatedTouchableOpacity
                  key={index}
                  style={[styles.suggestionBubble, animatedStyle]}
                  onPress={() => handleSuggestionPress(suggestion)}
                  activeOpacity={0.8}
                >
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </AnimatedTouchableOpacity>
              );
            })}
          </View>
        </>
      )}
      
      {/* Add Button */}
      <AnimatedPressable
        onPress={handleAddPress}
        onPressIn={() => {
          addButtonScale.value = withSpring(0.9, { damping: 15, stiffness: 300 });
        }}
        onPressOut={() => {
          addButtonScale.value = withSpring(1, { damping: 15, stiffness: 300 });
        }}
        style={[styles.fab, addButtonAnimatedStyle]}
      >
        <Ionicons name="add" size={28} color="#fff" />
      </AnimatedPressable>

      {/* Add Menu with Circular Fan-Out Animation */}
      {modalVisible && (
        <>
          <Pressable 
            style={styles.dismissOverlay} 
            onPress={handleAddPress} 
          />
          
          <View style={styles.addMenuContainer}>
            {addMenuItems.map((item, index) => {
              const animatedStyle = useAnimatedStyle(() => {
                const scale = itemScales[index].value;
                
                // Calculate circular positions
                const angle = (index * 30) - 30; // -30°, 0°, 30°
                const distance = 70;
                const translateX = interpolate(
                  menuItemsAnimation.value,
                  [0, 1],
                  [0, -distance * Math.cos(angle * Math.PI / 180)],
                  Extrapolate.CLAMP
                );
                const translateY = interpolate(
                  menuItemsAnimation.value,
                  [0, 1],
                  [0, -distance * Math.sin(angle * Math.PI / 180)],
                  Extrapolate.CLAMP
                );
                
                const opacity = interpolate(
                  scale,
                  [0, 0.5, 1],
                  [0, 0.5, 1],
                  Extrapolate.CLAMP
                );
                
                return {
                  transform: [
                    { translateX },
                    { translateY },
                    { scale },
                  ],
                  opacity,
                };
              });

              return (
                <AnimatedTouchableOpacity
                  key={item.id}
                  style={[
                    styles.menuItem,
                    { backgroundColor: item.color },
                    animatedStyle
                  ]}
                  onPress={() => handleMenuItemPress(item)}
                  activeOpacity={0.8}
                >
                  <Ionicons name={item.icon as any} size={20} color="#fff" />
                  <Text style={styles.menuItemLabel}>{item.label}</Text>
                </AnimatedTouchableOpacity>
              );
            })}
          </View>
        </>
      )}
    </>
  );
}

export default EnhancedAddButton;

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
    gap: 6,
  },
  suggestionBubble: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#F59E0B',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  suggestionText: {
    fontSize: 13,
    color: '#F59E0B',
    fontWeight: '500',
  },
  addMenuContainer: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_MARGIN,
    zIndex: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItem: {
    position: 'absolute',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 25,
    gap: 8,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  menuItemLabel: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
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