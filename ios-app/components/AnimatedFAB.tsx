import React, { useEffect } from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withSequence,
  withDelay,
} from 'react-native-reanimated';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface AnimatedFABProps {
  onPress: () => void;
}

const AnimatedFAB: React.FC<AnimatedFABProps> = ({ onPress }) => {
  const scale = useSharedValue(1);
  const rotation = useSharedValue(0);
  const pulseScale = useSharedValue(1);

  useEffect(() => {
    // Subtle pulse animation
    pulseScale.value = withRepeat(
      withSequence(
        withDelay(2000, withSpring(1.05, { damping: 10, stiffness: 100 })),
        withSpring(1, { damping: 10, stiffness: 100 })
      ),
      -1,
      false
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value * pulseScale.value },
      { rotate: `${rotation.value}deg` },
    ],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9, {
      damping: 10,
      stiffness: 200,
    });
    rotation.value = withSpring(-10, {
      damping: 10,
      stiffness: 200,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 10,
      stiffness: 200,
    });
    rotation.value = withSpring(0, {
      damping: 10,
      stiffness: 200,
    });
  };

  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onPress();
  };

  return (
    <TouchableOpacity
      style={styles.fabContainer}
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={[styles.fab, animatedStyle]}>
        <MaterialCommunityIcons name="chef-hat" size={28} color="#fff" />
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  fabContainer: {
    position: 'relative',
    top: -24,
    zIndex: 10,
    alignItems: 'center',
    justifyContent: 'center',
    width: 64,
    paddingHorizontal: 0,
  },
  fab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#297A56',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
});

export default AnimatedFAB;