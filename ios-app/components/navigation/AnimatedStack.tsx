import React from 'react';
import { Stack } from 'expo-router';
import { Platform } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';
import { screenAnimations, iosSpring, timingConfig } from '../../utils/navigationAnimations';

interface AnimatedStackScreenProps {
  name: string;
  options?: any;
  animationType?: 'push' | 'modal' | 'fade' | 'scale';
}

export const AnimatedStackScreen: React.FC<AnimatedStackScreenProps> = ({
  name,
  options = {},
  animationType = 'push',
}) => {
  // Select animation based on type
  const getAnimation = () => {
    switch (animationType) {
      case 'modal':
        return {
          presentation: 'modal',
          animation: 'slide_from_bottom',
          gestureEnabled: true,
          gestureDirection: 'vertical',
          cardOverlayEnabled: true,
          cardShadowEnabled: true,
          cardStyle: { backgroundColor: 'transparent' },
          ...screenAnimations.modalSlideFromBottom,
        };
      case 'fade':
        return {
          animation: 'fade',
          ...screenAnimations.fadeIn,
        };
      case 'scale':
        return {
          animation: 'fade',
          ...screenAnimations.scaleFromCenter,
        };
      case 'push':
      default:
        return {
          animation: 'slide_from_right',
          gestureEnabled: true,
          gestureDirection: 'horizontal',
          cardShadowEnabled: true,
          ...screenAnimations.pushFromRight,
        };
    }
  };

  return (
    <Stack.Screen
      name={name}
      options={{
        ...options,
        ...getAnimation(),
        // iOS-specific options
        ...(Platform.OS === 'ios' && {
          headerTransparent: false,
          headerBlurEffect: 'regular',
          contentStyle: {
            backgroundColor: 'transparent',
          },
        }),
      }}
    />
  );
};

// Custom hook for screen transition callbacks
export const useScreenTransition = (onTransitionStart?: () => void, onTransitionEnd?: () => void) => {
  React.useEffect(() => {
    onTransitionStart?.();
    return () => {
      onTransitionEnd?.();
    };
  }, []);
};

// Animated container for smooth screen transitions
export const AnimatedScreenContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const animatedStyle = useAnimatedStyle(() => ({
    opacity: withTiming(1, { duration: 300 }),
    transform: [
      {
        scale: withSpring(1, {
          damping: 20,
          stiffness: 90,
          mass: 1,
        }),
      },
    ],
  }));

  return (
    <Animated.View style={[{ flex: 1 }, animatedStyle]}>
      {children}
    </Animated.View>
  );
};