import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';
import { useFocusEffect } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';

interface TabScreenTransitionProps {
  children: React.ReactNode;
  routeName: string;
  transitionStyle?: 'slide' | 'fade' | 'scale' | 'slideUp';
}

export const TabScreenTransition: React.FC<TabScreenTransitionProps> = ({
  children,
  routeName,
  transitionStyle = 'slideUp',
}) => {
  const animation = useSharedValue(0);
  const isFirstMount = useSharedValue(true);

  useFocusEffect(
    React.useCallback(() => {
      // Skip animation on first mount for faster initial load
      if (isFirstMount.value) {
        animation.value = 1;
        isFirstMount.value = false;
        return;
      }

      // Reset animation
      animation.value = 0;
      
      // Trigger haptic feedback
      runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
      
      // Animate in
      animation.value = withSpring(1, {
        damping: 20,
        stiffness: 180,
        overshootClamping: false,
      });

      return () => {
        // Optional: animate out when leaving
        // animation.value = withTiming(0, { duration: 200 });
      };
    }, [])
  );

  const getAnimatedStyle = () => {
    switch (transitionStyle) {
      case 'slide':
        return useAnimatedStyle(() => ({
          transform: [
            {
              translateX: interpolate(
                animation.value,
                [0, 1],
                [100, 0],
                Extrapolate.CLAMP
              ),
            },
          ],
          opacity: interpolate(
            animation.value,
            [0, 0.5, 1],
            [0, 0.5, 1],
            Extrapolate.CLAMP
          ),
        }));

      case 'fade':
        return useAnimatedStyle(() => ({
          opacity: animation.value,
        }));

      case 'scale':
        return useAnimatedStyle(() => ({
          opacity: animation.value,
          transform: [
            {
              scale: interpolate(
                animation.value,
                [0, 1],
                [0.9, 1],
                Extrapolate.CLAMP
              ),
            },
          ],
        }));

      case 'slideUp':
      default:
        return useAnimatedStyle(() => ({
          opacity: interpolate(
            animation.value,
            [0, 0.5, 1],
            [0, 0.8, 1],
            Extrapolate.CLAMP
          ),
          transform: [
            {
              translateY: interpolate(
                animation.value,
                [0, 1],
                [30, 0],
                Extrapolate.CLAMP
              ),
            },
            {
              scale: interpolate(
                animation.value,
                [0, 0.5, 1],
                [0.95, 0.97, 1],
                Extrapolate.CLAMP
              ),
            },
          ],
        }));
    }
  };

  const animatedStyle = getAnimatedStyle();

  return (
    <Animated.View style={[styles.container, animatedStyle]}>
      {children}
    </Animated.View>
  );
};

// Higher-order component for easy wrapping
export const withTabTransition = (
  Component: React.ComponentType<any>,
  transitionStyle?: 'slide' | 'fade' | 'scale' | 'slideUp'
) => {
  return (props: any) => (
    <TabScreenTransition routeName={props.route?.name || ''} transitionStyle={transitionStyle}>
      <Component {...props} />
    </TabScreenTransition>
  );
};

// Custom hook for tab transition animations
export const useTabTransition = () => {
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const animateIn = () => {
    translateX.value = withSpring(0, { damping: 20, stiffness: 150 });
    translateY.value = withSpring(0, { damping: 20, stiffness: 150 });
    scale.value = withSpring(1, { damping: 15, stiffness: 150 });
    opacity.value = withTiming(1, { duration: 300 });
  };

  const animateOut = () => {
    opacity.value = withTiming(0, { duration: 200 });
    scale.value = withSpring(0.95, { damping: 20, stiffness: 200 });
  };

  return {
    translateX,
    translateY,
    scale,
    opacity,
    animateIn,
    animateOut,
  };
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});