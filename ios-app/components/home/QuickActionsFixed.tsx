import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Pressable } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withDelay,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

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
  const translateY = useSharedValue(50);
  const opacity = useSharedValue(0);
  const scale = useSharedValue(0.8);
  const iconScale = useSharedValue(1);

  useEffect(() => {
    const delay = index * 150; // Stagger animations

    // Entrance animation
    translateY.value = withDelay(delay, withSpring(0, { damping: 8, stiffness: 100 }));
    opacity.value = withDelay(delay, withSpring(1, { damping: 8 }));
    scale.value = withDelay(delay, withSpring(1, { damping: 8, stiffness: 100 }));
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

  return (
    <Animated.View style={[styles.actionCardContainer, animatedContainerStyle]}>
      <Pressable
        style={({ pressed }) => [
          styles.actionCard, 
          { backgroundColor: action.color + '15' },
          pressed && styles.actionCardPressed
        ]}
        onPress={onPress}
        onPressIn={() => {
          iconScale.value = withSpring(0.9, { damping: 6 });
          scale.value = withSpring(0.95, { damping: 6 });
        }}
        onPressOut={() => {
          iconScale.value = withSpring(1, { damping: 6 });
          scale.value = withSpring(1, { damping: 6 });
        }}
      >
        <Animated.View style={[styles.actionIcon, { backgroundColor: action.color }, iconAnimatedStyle]}>
          <Ionicons name={action.icon} size={24} color="white" />
        </Animated.View>
        <Text style={styles.actionText} numberOfLines={1} ellipsizeMode="tail">{action.title}</Text>
      </Pressable>
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
    minHeight: 110,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionCardPressed: {
    opacity: 0.8,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'center',
    lineHeight: 14,
  },
});

// Export as default for drop-in replacement
export default QuickActionsFixed;