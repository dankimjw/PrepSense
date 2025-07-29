import { useEffect } from 'react';
import {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  interpolate,
} from 'react-native-reanimated';

export const useScreenAnimation = (delay = 0) => {
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.value = withTiming(1, {
      duration: 600,
      delay,
    });
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [
      {
        translateY: interpolate(progress.value, [0, 1], [30, 0]),
      },
    ],
  }));

  return animatedStyle;
};

export const useSpringAnimation = () => {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const onPressIn = () => {
    scale.value = withSpring(0.95, {
      damping: 10,
      stiffness: 100,
    });
  };

  const onPressOut = () => {
    scale.value = withSpring(1, {
      damping: 10,
      stiffness: 100,
    });
  };

  return { animatedStyle, onPressIn, onPressOut };
};