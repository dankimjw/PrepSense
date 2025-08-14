import React, { memo, useEffect, useState } from 'react';
import { View, StyleSheet, InteractionManager } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
  cancelAnimation,
} from 'react-native-reanimated';
import { useFocusEffect } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { performanceMonitor } from '../../utils/performanceMonitoring';

interface OptimizedTabScreenTransitionProps {
  children: React.ReactNode;
  routeName: string;
  transitionStyle?: 'slide' | 'fade' | 'scale' | 'slideUp' | 'none';
  enableHaptics?: boolean;
  delayContent?: boolean;
}

export const OptimizedTabScreenTransition = memo<OptimizedTabScreenTransitionProps>(({
  children,
  routeName,
  transitionStyle = 'slideUp',
  enableHaptics = true,
  delayContent = true,
}) => {
  const animation = useSharedValue(0);
  const isFirstMount = useSharedValue(true);
  const [contentReady, setContentReady] = useState(!delayContent);

  useFocusEffect(
    React.useCallback(() => {
      const perfLabel = `tab-transition-${routeName}`;
      performanceMonitor.startMeasure(perfLabel);

      // Skip animation on first mount for faster initial load
      if (isFirstMount.value) {
        animation.value = 1;
        isFirstMount.value = false;
        setContentReady(true);
        performanceMonitor.endMeasure(perfLabel);
        return;
      }

      // Cancel any ongoing animation
      cancelAnimation(animation);

      // No animation mode for maximum performance
      if (transitionStyle === 'none') {
        animation.value = 1;
        setContentReady(true);
        performanceMonitor.endMeasure(perfLabel);
        return;
      }

      // Reset animation
      animation.value = 0;

      // Defer content and animation
      InteractionManager.runAfterInteractions(() => {
        // Trigger haptic feedback if enabled
        if (enableHaptics) {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {
            // Ignore haptic errors
          });
        }

        // Show content
        if (delayContent) {
          setContentReady(true);
        }

        // Simplified animation with reduced complexity
        animation.value = withTiming(1, {
          duration: 200, // Reduced from 600ms
        }, (finished) => {
          if (finished) {
            runOnJS(() => {
              const duration = performanceMonitor.endMeasure(perfLabel);
              if (duration > 300) {
                console.warn(`[Performance] Slow tab transition: ${routeName} (${duration.toFixed(0)}ms)`);
              }
            })();
          }
        });
      });

      return () => {
        // Cleanup: cancel animation on unmount
        cancelAnimation(animation);
      };
    }, [routeName, transitionStyle, enableHaptics, delayContent])
  );

  const animatedStyle = useAnimatedStyle(() => {
    if (transitionStyle === 'none') {
      return {};
    }

    switch (transitionStyle) {
      case 'fade':
        return {
          opacity: animation.value,
        };

      case 'scale':
        return {
          opacity: animation.value,
          transform: [{
            scale: interpolate(
              animation.value,
              [0, 1],
              [0.95, 1],
              Extrapolate.CLAMP
            ),
          }],
        };

      case 'slide':
        return {
          opacity: animation.value,
          transform: [{
            translateX: interpolate(
              animation.value,
              [0, 1],
              [50, 0], // Reduced from 100
              Extrapolate.CLAMP
            ),
          }],
        };

      case 'slideUp':
      default:
        return {
          opacity: animation.value,
          transform: [{
            translateY: interpolate(
              animation.value,
              [0, 1],
              [20, 0], // Reduced from 30
              Extrapolate.CLAMP
            ),
          }],
        };
    }
  }, [transitionStyle]);

  // Show placeholder while content is loading
  if (!contentReady) {
    return <View style={styles.placeholder} />;
  }

  if (transitionStyle === 'none') {
    return <View style={styles.container}>{children}</View>;
  }

  return (
    <Animated.View style={[styles.container, animatedStyle]}>
      {children}
    </Animated.View>
  );
});

OptimizedTabScreenTransition.displayName = 'OptimizedTabScreenTransition';

// Higher-order component for easy migration
export const withOptimizedTabTransition = (
  Component: React.ComponentType<any>,
  transitionStyle?: OptimizedTabScreenTransitionProps['transitionStyle']
) => {
  return memo((props: any) => (
    <OptimizedTabScreenTransition 
      routeName={props.route?.name || ''} 
      transitionStyle={transitionStyle}
    >
      <Component {...props} />
    </OptimizedTabScreenTransition>
  ));
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  placeholder: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});