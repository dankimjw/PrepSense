// Enhanced AddButton with creative animations and long press for recipe completion
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View, Text, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import React, { useState, useRef, useMemo } from 'react';
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
const LONG_PRESS_DURATION = 5000; // 5 seconds for long press

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
  { id: 'rc', icon: 'restaurant', label: 'Complete Recipe', color: '#F97316', route: '/test-recipe-completion' },
];

function EnhancedAddButton() {
  const router = useRouter();
  
  const [modalVisible, setModalVisible] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLongPressing, setIsLongPressing] = useState(false);
  
  // Reanimated values
  const addButtonScale = useSharedValue(1);
  const addButtonRotation = useSharedValue(0);
  const lightbulbScale = useSharedValue(1);
  const lightbulbRotation = useSharedValue(0);
  
  // Long press animation values
  const longPressProgress = useSharedValue(0);
  const longPressScale = useSharedValue(1);
  
  // Animation values for menu items
  const menuItemsAnimation = useSharedValue(0);
  const suggestionsAnimation = useSharedValue(0);
  
  // Individual item animations - use useMemo to prevent recreation
  const itemScales = useMemo(() => addMenuItems.map(() => useSharedValue(0)), []);
  const suggestionScales = useMemo(() => suggestedMessages.map(() => useSharedValue(0)), []);

  // Refs for long press timer
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);
  const hapticTimer = useRef<NodeJS.Timeout | null>(null);

  // Animated styles - always define them at top level
  const addButtonAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: addButtonScale.value * longPressScale.value },
      { rotate: `${addButtonRotation.value}deg` },
    ],
  }));

  const lightbulbAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: lightbulbScale.value },
      { rotate: `${lightbulbRotation.value}deg` },
    ],
  }));

  const progressRingStyle = useAnimatedStyle(() => ({
    opacity: isLongPressing ? 1 : 0,
    borderWidth: interpolate(longPressProgress.value, [0, 1], [0, 3], Extrapolate.CLAMP),
    borderColor: `rgba(245, 158, 11, ${longPressProgress.value})`,
  }));

  const longPressHintStyle = useAnimatedStyle(() => ({
    opacity: withSpring(isLongPressing ? 1 : 0),
  }));

  // For now, always show the component (remove conditional hiding to eliminate hooks violation)
  const shouldHide = false;

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
        case 'rc':
          router.push('/test-recipe-completion');
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

  // Long press handlers
  const startLongPress = () => {
    if (modalVisible || showSuggestions) return;
    
    setIsLongPressing(true);
    
    // Animate progress and scale
    longPressProgress.value = withTiming(1, { duration: LONG_PRESS_DURATION });
    longPressScale.value = withSpring(1.1, { damping: 15, stiffness: 200 });
    
    // Start haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Set up completion timer
    longPressTimer.current = setTimeout(() => {
      completeLongPress();
    }, LONG_PRESS_DURATION);
    
    // Periodic haptic feedback
    let hapticCount = 0;
    hapticTimer.current = setInterval(() => {
      hapticCount++;
      if (hapticCount < 5) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
    }, 1000);
  };

  const cancelLongPress = () => {
    if (!isLongPressing) return;
    
    setIsLongPressing(false);
    
    // Clear timers
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (hapticTimer.current) {
      clearInterval(hapticTimer.current);
      hapticTimer.current = null;
    }
    
    // Reset animations
    longPressProgress.value = withTiming(0, { duration: 200 });
    longPressScale.value = withSpring(1, { damping: 15, stiffness: 200 });
  };

  const completeLongPress = () => {
    setIsLongPressing(false);
    
    // Clear timers
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (hapticTimer.current) {
      clearInterval(hapticTimer.current);
      hapticTimer.current = null;
    }
    
    // Success haptic
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    
    // Reset animations
    longPressProgress.value = withTiming(0, { duration: 200 });
    longPressScale.value = withSpring(1, { damping: 15, stiffness: 200 });
    
    // Navigate to recipe completion
    setTimeout(() => {
      router.push('/test-recipe-completion');
    }, 200);
  };

  // Don't render if we should hide
  if (shouldHide) {
    return null;
  }

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
            {suggestedMessages.map((suggestion, index) => (
              <SuggestionBubble 
                key={index}
                suggestion={suggestion}
                scale={suggestionScales[index]}
                onPress={() => handleSuggestionPress(suggestion)}
              />
            ))}
          </View>
        </>
      )}
      
      {/* Add Button with Long Press Support */}
      <View style={styles.addButtonContainer}>
        {/* Progress Ring for Long Press */}
        <Animated.View style={[styles.progressRing, progressRingStyle]} />
        
        <AnimatedPressable
          onPress={handleAddPress}
          onPressIn={() => {
            addButtonScale.value = withSpring(0.9, { damping: 15, stiffness: 300 });
            startLongPress();
          }}
          onPressOut={() => {
            addButtonScale.value = withSpring(1, { damping: 15, stiffness: 300 });
            cancelLongPress();
          }}
          style={[styles.fab, addButtonAnimatedStyle]}
        >
          <Ionicons name="add" size={28} color="#fff" />
        </AnimatedPressable>
      </View>

      {/* Long Press Hint Text */}
      {isLongPressing && (
        <Animated.View style={[styles.longPressHint, longPressHintStyle]}>
          <Text style={styles.longPressHintText}>Hold for Recipe Completion</Text>
        </Animated.View>
      )}

      {/* Add Menu with Circular Fan-Out Animation */}
      {modalVisible && (
        <>
          <Pressable 
            style={styles.dismissOverlay} 
            onPress={handleAddPress} 
          />
          
          <View style={styles.addMenuContainer}>
            {addMenuItems.map((item, index) => (
              <MenuItemButton 
                key={item.id}
                item={item}
                index={index}
                scale={itemScales[index]}
                menuAnimation={menuItemsAnimation}
                onPress={() => handleMenuItemPress(item)}
              />
            ))}
          </View>
        </>
      )}
    </>
  );
}

// Helper component to avoid hooks in map callbacks
const SuggestionBubble = ({ suggestion, scale, onPress }: {
  suggestion: string;
  scale: any;
  onPress: () => void;
}) => {
  const animatedStyle = useAnimatedStyle(() => {
    const scaleValue = scale.value;
    const translateY = interpolate(scaleValue, [0, 1], [20, 0], Extrapolate.CLAMP);
    const opacity = interpolate(scaleValue, [0, 0.5, 1], [0, 0.5, 1], Extrapolate.CLAMP);
    
    return {
      transform: [{ scale: scaleValue }, { translateY }],
      opacity,
    };
  });

  return (
    <AnimatedTouchableOpacity
      style={[styles.suggestionBubble, animatedStyle]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <Text style={styles.suggestionText}>{suggestion}</Text>
    </AnimatedTouchableOpacity>
  );
};

// Helper component for menu items
const MenuItemButton = ({ item, index, scale, menuAnimation, onPress }: {
  item: typeof addMenuItems[0];
  index: number;
  scale: any;
  menuAnimation: any;
  onPress: () => void;
}) => {
  const animatedStyle = useAnimatedStyle(() => {
    const scaleValue = scale.value;
    
    // Calculate circular positions
    const angle = (index * 30) - 45;
    const distance = 70;
    const translateX = interpolate(
      menuAnimation.value,
      [0, 1],
      [0, -distance * Math.cos(angle * Math.PI / 180)],
      Extrapolate.CLAMP
    );
    const translateY = interpolate(
      menuAnimation.value,
      [0, 1],
      [0, -distance * Math.sin(angle * Math.PI / 180)],
      Extrapolate.CLAMP
    );
    
    const opacity = interpolate(scaleValue, [0, 0.5, 1], [0, 0.5, 1], Extrapolate.CLAMP);
    
    return {
      transform: [{ translateX }, { translateY }, { scale: scaleValue }],
      opacity,
    };
  });

  return (
    <AnimatedTouchableOpacity
      style={[
        styles.menuItem,
        { backgroundColor: item.color },
        animatedStyle
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <Ionicons name={item.icon as any} size={20} color="#fff" />
      <Text style={styles.menuItemLabel}>{item.label}</Text>
    </AnimatedTouchableOpacity>
  );
};

export default EnhancedAddButton;

const styles = StyleSheet.create({
  fab: {
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
    zIndex: 12,
  },
  addButtonContainer: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_MARGIN,
    width: FAB_SIZE + 8,
    height: FAB_SIZE + 8,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  progressRing: {
    position: 'absolute',
    width: FAB_SIZE + 6,
    height: FAB_SIZE + 6,
    borderRadius: (FAB_SIZE + 6) / 2,
    borderColor: '#F59E0B',
    zIndex: 11,
  },
  longPressHint: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN + FAB_SIZE + 16,
    right: FAB_MARGIN - 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    zIndex: 15,
  },
  longPressHintText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
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
    flexWrap: 'wrap',
    textAlign: 'center',
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
    minWidth: 120,
    maxWidth: 140,
  },
  menuItemLabel: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    flexWrap: 'wrap',
    flexShrink: 1,
    textAlign: 'left',
    numberOfLines: 2,
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