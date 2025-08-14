import React, { useEffect } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

interface AnimatedFilterButtonProps {
  label: string;
  icon: string;
  isActive: boolean;
  onPress: () => void;
  testID?: string;
  index?: number;
}

const AnimatedFilterButton: React.FC<AnimatedFilterButtonProps> = ({
  label,
  icon,
  isActive,
  onPress,
  testID,
  index = 0,
}) => {
  const scale = useSharedValue(1);
  const iconScale = useSharedValue(1);
  const activeProgress = useSharedValue(isActive ? 1 : 0);
  const enterProgress = useSharedValue(0);

  // Staggered entrance animation
  useEffect(() => {
    const delay = index * 50; // 50ms stagger between items
    setTimeout(() => {
      enterProgress.value = withSpring(1, {
        damping: 15,
        stiffness: 200,
      });
    }, delay);
  }, [index]);

  // Active state animation
  useEffect(() => {
    activeProgress.value = withSpring(isActive ? 1 : 0, {
      damping: 12,
      stiffness: 300,
    });
    
    if (isActive) {
      // Icon bounce when becoming active
      iconScale.value = withSpring(1.2, {
        damping: 8,
        stiffness: 400,
      }, () => {
        iconScale.value = withSpring(1, {
          damping: 10,
          stiffness: 300,
        });
      });
    }
  }, [isActive]);

  const animatedContainerStyle = useAnimatedStyle(() => {
    const backgroundColor = interpolate(
      activeProgress.value,
      [0, 1],
      [0, 1]
    );
    
    return {
      backgroundColor: backgroundColor === 1 ? '#E6F7F0' : '#F3F4F6',
      borderColor: backgroundColor === 1 ? '#297A56' : 'transparent',
      borderWidth: backgroundColor === 1 ? 1.5 : 0,
      transform: [
        { scale: scale.value * enterProgress.value },
        { 
          translateY: interpolate(
            enterProgress.value,
            [0, 1],
            [20, 0]
          )
        }
      ],
      opacity: enterProgress.value,
    };
  });

  const animatedIconStyle = useAnimatedStyle(() => ({
    transform: [{ scale: iconScale.value }],
  }));

  const animatedTextStyle = useAnimatedStyle(() => {
    const color = interpolate(
      activeProgress.value,
      [0, 1],
      [0, 1]
    );
    
    return {
      color: color === 1 ? '#297A56' : '#666',
    };
  });

  const handlePressIn = () => {
    scale.value = withSpring(0.95, {
      damping: 15,
      stiffness: 400,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 400,
    });
  };

  const handlePress = () => {
    // Haptic feedback
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    onPress();
  };

  return (
    <TouchableOpacity
      testID={testID}
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={[styles.filterButton, animatedContainerStyle]}>
        <Animated.Text style={[styles.filterIcon, animatedIconStyle]}>
          {icon}
        </Animated.Text>
        <Animated.Text style={[styles.filterText, animatedTextStyle]}>
          {label}
        </Animated.Text>
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 24,
    marginRight: 8,
    minWidth: 90,
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
  },
});

export default AnimatedFilterButton;