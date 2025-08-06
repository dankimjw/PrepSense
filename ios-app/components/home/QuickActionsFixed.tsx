import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Pressable } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withDelay,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';

export interface QuickAction {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  color: string;
  route?: string;
  onPress?: () => void;
}

interface QuickActionsProps {
  actions?: QuickAction[];
}

const defaultActions: QuickAction[] = [
  { 
    id: 'scan-items', 
    icon: 'basket',
    title: 'Scan Items',
    color: '#297A56',
    route: '/scan-items'
  },
  { 
    id: 'scan', 
    icon: 'receipt',
    title: 'Scan Receipt',
    color: '#4F46E5',
    route: '/receipt-scanner'
  },
  { 
    id: 'recipe', 
    icon: 'restaurant',
    title: 'Recipes',
    color: '#DB2777',
    route: '/recipes'
  },
  { 
    id: 'shopping', 
    icon: 'cart',
    title: 'Shopping List',
    color: '#7C3AED',
    route: '/shopping-list'
  },
];

// Helper function to render multi-line text for specific buttons
const renderButtonText = (action: QuickAction) => {
  if (action.id === 'scan') {
    // "Scan Receipt" -> "Scan" on first line, "Receipt" on second line
    return (
      <View style={styles.textContainer}>
        <Text style={styles.actionText}>Scan</Text>
        <Text style={styles.actionText}>Receipt</Text>
      </View>
    );
  } else if (action.id === 'shopping') {
    // "Shopping List" -> "Shopping" on first line, "List" on second line
    return (
      <View style={styles.textContainer}>
        <Text style={styles.actionText}>Shopping</Text>
        <Text style={styles.actionText}>List</Text>
      </View>
    );
  } else {
    // Default single line text for other buttons - use same container for consistency
    return (
      <View style={styles.textContainer}>
        <Text style={styles.actionText} numberOfLines={1} ellipsizeMode="tail">
          {action.title}
        </Text>
      </View>
    );
  }
};

// Fixed Quick Action Card Component using Pressable
const QuickActionCard = ({ 
  action, 
  index, 
  onPress 
}: { 
  action: QuickAction; 
  index: number; 
  onPress: () => void;
}) => {
  const router = useRouter();
  const translateY = useSharedValue(50);
  const opacity = useSharedValue(0);
  const scale = useSharedValue(0.8);
  const iconScale = useSharedValue(1);
  
  // Long press state for recipes button only
  const [isLongPressing, setIsLongPressing] = useState(false);
  const longPressProgress = useSharedValue(0);
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const delay = index * 150; // Stagger animations

    // Entrance animation
    translateY.value = withDelay(delay, withSpring(0, { damping: 8, stiffness: 100 }));
    opacity.value = withDelay(delay, withSpring(1, { damping: 8 }));
    scale.value = withDelay(delay, withSpring(1, { damping: 8, stiffness: 100 }));

    // Cleanup function
    return () => {
      if (longPressTimer.current) {
        clearTimeout(longPressTimer.current);
        longPressTimer.current = null;
      }
    };
  }, [index]);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
      { scale: scale.value }
    ],
    opacity: opacity.value,
  }));

  const iconAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: iconScale.value }],
  }));

  const longPressRingStyle = useAnimatedStyle(() => ({
    opacity: isLongPressing ? 1 : 0,
    borderWidth: longPressProgress.value * 3,
    borderColor: `rgba(245, 158, 11, ${longPressProgress.value})`,
  }));

  const cancelLongPress = () => {
    console.log('Long press cancelled for recipe button');
    setIsLongPressing(false);
    
    // Clear timer
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    
    // Reset animation
    longPressProgress.value = withTiming(0, { duration: 200 });
  };

  const completeLongPress = () => {
    console.log('Long press completed for recipe button - navigating to recipe completion');
    setIsLongPressing(false);
    
    // Clear timer
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    
    // Success haptic
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    
    // Reset animation
    longPressProgress.value = withTiming(0, { duration: 200 });
    
    // Navigate to recipe completion modal directly
    setTimeout(() => {
      router.push('/test-recipe-completion');
    }, 100);
  };

  return (
    <Animated.View style={[styles.actionCardContainer, animatedContainerStyle]}>
      {/* Progress ring for long press (recipes button only) */}
      {action.id === 'recipe' && (
        <Animated.View style={[styles.longPressRing, longPressRingStyle]} />
      )}
      
      <TouchableOpacity
        style={[
          styles.actionCard, 
          { backgroundColor: action.color + '15' }
        ]}
        onPress={() => {
          // Only call onPress if it's not a long press for recipes
          if (action.id === 'recipe' && isLongPressing) {
            console.log('Blocking normal press because long press is in progress');
            return;
          }
          onPress();
        }}
        onPressIn={() => {
          console.log('Press in on action:', action.id);
          iconScale.value = withSpring(0.9, { damping: 6 });
          scale.value = withSpring(0.95, { damping: 6 });

          // Start long press only for recipes button
          if (action.id === 'recipe') {
            console.log('Starting long press for recipe button');
            setIsLongPressing(true);
            
            // Animate progress ring
            longPressProgress.value = withTiming(1, { duration: 5000 });
            
            // Initial haptic feedback
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            
            // Set up completion timer (5 seconds)
            longPressTimer.current = setTimeout(() => {
              completeLongPress();
            }, 5000);
          }
        }}
        onPressOut={() => {
          console.log('Press out on action:', action.id, 'isLongPressing:', isLongPressing);
          iconScale.value = withSpring(1, { damping: 6 });
          scale.value = withSpring(1, { damping: 6 });

          // Cancel long press if in progress
          if (action.id === 'recipe' && isLongPressing) {
            cancelLongPress();
          }
        }}
        delayLongPress={5000}
        onLongPress={() => {
          console.log('Native long press triggered for action:', action.id);
          if (action.id === 'recipe') {
            completeLongPress();
          }
        }}
        activeOpacity={0.8}
      >
        <Animated.View style={[styles.actionIcon, { backgroundColor: action.color }, iconAnimatedStyle]}>
          <Ionicons name={action.icon} size={24} color="white" />
        </Animated.View>
        {renderButtonText(action)}
      </TouchableOpacity>
      
      {/* Long press hint for recipes button */}
      {action.id === 'recipe' && isLongPressing && (
        <View style={styles.longPressHint}>
          <Text style={styles.longPressHintText}>Quick Recipe Test</Text>
        </View>
      )}
    </Animated.View>
  );
};

export const QuickActionsFixed: React.FC<QuickActionsProps> = ({ actions = defaultActions }) => {
  const router = useRouter();
  const titleOpacity = useSharedValue(0);
  const titleTranslateY = useSharedValue(-20);

  useEffect(() => {
    // Animate title first
    titleOpacity.value = withSpring(1, { damping: 8 });
    titleTranslateY.value = withSpring(0, { damping: 8, stiffness: 100 });
  }, []);

  const titleAnimatedStyle = useAnimatedStyle(() => ({
    opacity: titleOpacity.value,
    transform: [{ translateY: titleTranslateY.value }],
  }));

  const handleActionPress = (action: QuickAction) => {
    if (action.onPress) {
      action.onPress();
    } else if (action.route) {
      router.push(action.route as any);
    }
  };

  return (
    <>
      <Animated.Text style={[styles.sectionTitle, titleAnimatedStyle]}>
        Quick Actions
      </Animated.Text>
      <View style={styles.quickActions}>
        {actions.map((action, index) => (
          <QuickActionCard
            key={action.id}
            action={action}
            index={index}
            onPress={() => handleActionPress(action)}
          />
        ))}
      </View>
    </>
  );
};

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  actionCardContainer: {
    flex: 1,
    marginHorizontal: 4,
  },
  actionCard: {
    height: 110, // Fixed height instead of minHeight
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  textContainer: {
    height: 28, // Fixed height for text area
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  actionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'center',
    lineHeight: 14,
  },
  smallActionText: {
    fontSize: 10,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'center',
    lineHeight: 12,
  },
  multiLineTextContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  longPressRing: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    borderColor: '#F59E0B',
    zIndex: 1,
    top: '50%',
    left: '50%',
    marginTop: -40,
    marginLeft: -40,
  },
  longPressHint: {
    position: 'absolute',
    top: -30,
    left: '50%',
    marginLeft: -50,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    zIndex: 10,
    width: 100,
  },
  longPressHintText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '500',
    textAlign: 'center',
  },
});

// Export as default for drop-in replacement
export default QuickActionsFixed;