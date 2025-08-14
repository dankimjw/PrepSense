import { useEffect, useRef } from 'react';
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';
import { useIsFocused } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';

interface NavigationAnimationOptions {
  type?: 'fade' | 'slide' | 'scale' | 'parallax';
  duration?: number;
  delay?: number;
  haptic?: boolean;
}

export const useNavigationAnimation = (options: NavigationAnimationOptions = {}) => {
  const {
    type = 'fade',
    duration = 350,
    delay = 0,
    haptic = false,
  } = options;

  const isFocused = useIsFocused();
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(20);
  const translateX = useSharedValue(0);
  const scale = useSharedValue(0.95);

  useEffect(() => {
    if (isFocused) {
      if (haptic) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }

      // Animate in
      opacity.value = withTiming(1, { duration }, () => {
        if (haptic) {
          runOnJS(Haptics.notificationAsync)(Haptics.NotificationFeedbackType.Success);
        }
      });

      switch (type) {
        case 'slide':
          translateY.value = withSpring(0, {
            damping: 20,
            stiffness: 90,
            mass: 1,
          });
          break;
        case 'scale':
          scale.value = withSpring(1, {
            damping: 15,
            stiffness: 150,
            mass: 1,
          });
          break;
        case 'parallax':
          translateX.value = withSpring(0, {
            damping: 20,
            stiffness: 100,
            mass: 1.2,
          });
          break;
      }
    } else {
      // Reset values when unfocused
      opacity.value = 0;
      translateY.value = 20;
      translateX.value = -50;
      scale.value = 0.95;
    }
  }, [isFocused, type, duration, haptic]);

  const animatedStyle = useAnimatedStyle(() => {
    switch (type) {
      case 'slide':
        return {
          opacity: opacity.value,
          transform: [{ translateY: translateY.value }],
        };
      case 'scale':
        return {
          opacity: opacity.value,
          transform: [{ scale: scale.value }],
        };
      case 'parallax':
        return {
          opacity: opacity.value,
          transform: [{ translateX: translateX.value }],
        };
      case 'fade':
      default:
        return {
          opacity: opacity.value,
        };
    }
  });

  // Stagger animation for list items
  const getStaggeredStyle = (index: number, totalItems: number) => {
    const staggerDelay = index * 50; // 50ms between each item
    const maxDelay = 500; // Cap the total delay
    const actualDelay = Math.min(staggerDelay, maxDelay);

    return useAnimatedStyle(() => {
      const progress = interpolate(
        opacity.value,
        [0, 1],
        [0, 1],
        Extrapolate.CLAMP
      );

      const itemOpacity = withTiming(progress, {
        duration: 300,
        delay: actualDelay,
      });

      const itemTranslateY = withSpring(
        interpolate(progress, [0, 1], [30, 0]),
        {
          damping: 15,
          stiffness: 100,
          mass: 1,
          delay: actualDelay,
        }
      );

      return {
        opacity: itemOpacity,
        transform: [{ translateY: itemTranslateY }],
      };
    });
  };

  return {
    animatedStyle,
    getStaggeredStyle,
    isAnimating: opacity.value < 1,
  };
};

// Hook for hero animations (shared element transitions)
export const useHeroAnimation = (heroId: string) => {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const animateHero = (toScale: number = 1.05) => {
    'worklet';
    scale.value = withSpring(toScale, {
      damping: 15,
      stiffness: 150,
    });
  };

  const heroStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return {
    heroStyle,
    animateHero,
    resetHero: () => {
      scale.value = withSpring(1);
      opacity.value = withTiming(1);
    },
  };
};