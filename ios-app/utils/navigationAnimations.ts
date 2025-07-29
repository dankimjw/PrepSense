import { withSpring, withTiming, SharedValue, Easing } from 'react-native-reanimated';

// iOS-style spring configuration
export const iosSpring = {
  damping: 500,
  stiffness: 1000,
  mass: 3,
  overshootClamping: true,
  restDisplacementThreshold: 0.01,
  restSpeedThreshold: 0.01,
};

// Navigation timing configurations
export const timingConfig = {
  duration: 350,
  easing: Easing.bezier(0.25, 0.1, 0.25, 1), // iOS easing curve
};

// Screen transition animations
export const screenAnimations = {
  // iOS-style push animation
  pushFromRight: {
    cardStyleInterpolator: ({ current, next, layouts }: any) => {
      const translateX = current.progress.interpolate({
        inputRange: [0, 1],
        outputRange: [layouts.screen.width, 0],
      });

      const opacity = current.progress.interpolate({
        inputRange: [0, 0.5, 1],
        outputRange: [0, 0.1, 1],
      });

      const scale = next
        ? next.progress.interpolate({
            inputRange: [0, 1],
            outputRange: [1, 0.95],
          })
        : 1;

      return {
        cardStyle: {
          transform: [{ translateX }, { scale }],
          opacity,
        },
        overlayStyle: {
          opacity: current.progress.interpolate({
            inputRange: [0, 1],
            outputRange: [0, 0.3],
          }),
        },
      };
    },
  },

  // iOS-style modal presentation
  modalSlideFromBottom: {
    cardStyleInterpolator: ({ current, layouts }: any) => {
      const translateY = current.progress.interpolate({
        inputRange: [0, 1],
        outputRange: [layouts.screen.height, 0],
      });

      return {
        cardStyle: {
          transform: [{ translateY }],
        },
        overlayStyle: {
          opacity: current.progress.interpolate({
            inputRange: [0, 1],
            outputRange: [0, 0.5],
          }),
        },
      };
    },
  },

  // Fade transition for auth screens
  fadeIn: {
    cardStyleInterpolator: ({ current }: any) => ({
      cardStyle: {
        opacity: current.progress,
      },
    }),
  },

  // Scale + fade for special screens
  scaleFromCenter: {
    cardStyleInterpolator: ({ current }: any) => {
      const opacity = current.progress;
      const scale = current.progress.interpolate({
        inputRange: [0, 1],
        outputRange: [0.85, 1],
      });

      return {
        cardStyle: {
          opacity,
          transform: [{ scale }],
        },
      };
    },
  },
};

// Shared element transition helpers
export const sharedElementTransition = {
  duration: 400,
  easing: Easing.bezier(0.33, 0.01, 0, 1),
};

// Tab bar animation configuration
export const tabBarAnimation = {
  duration: 250,
  easing: Easing.out(Easing.cubic),
};