import React, { memo, useEffect, useState } from 'react';
import { View, StyleSheet, InteractionManager } from 'react-native';
import Animated, { 
  FadeIn, 
  FadeOut,
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import { useComponentPerformance } from '../utils/performanceMonitoring';

interface OptimizedScreenWrapperProps {
  children: React.ReactNode;
  style?: any;
  enableAnimation?: boolean;
  placeholderComponent?: React.ReactNode;
  onAnimationComplete?: () => void;
}

const ScreenPlaceholder = () => (
  <View style={styles.placeholder} />
);

export const OptimizedScreenWrapper = memo<OptimizedScreenWrapperProps>(({ 
  children, 
  style,
  enableAnimation = true,
  placeholderComponent,
  onAnimationComplete,
}) => {
  const [isReady, setIsReady] = useState(false);
  const opacity = useSharedValue(enableAnimation ? 0 : 1);
  
  // Use performance monitoring
  useComponentPerformance('OptimizedScreenWrapper');

  useEffect(() => {
    // Defer heavy content rendering until after navigation animation
    const interaction = InteractionManager.runAfterInteractions(() => {
      setIsReady(true);
      
      if (enableAnimation) {
        opacity.value = withTiming(1, { 
          duration: 200,
          // Use native driver for better performance
        }, (finished) => {
          if (finished && onAnimationComplete) {
            runOnJS(onAnimationComplete)();
          }
        });
      } else if (onAnimationComplete) {
        onAnimationComplete();
      }
    });

    return () => {
      interaction.cancel();
    };
  }, [enableAnimation, onAnimationComplete]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  // Show placeholder during navigation for smoother transition
  if (!isReady) {
    return placeholderComponent || <ScreenPlaceholder />;
  }

  if (enableAnimation) {
    return (
      <Animated.View 
        style={[styles.container, animatedStyle, style]}
        entering={FadeIn.duration(200).withCallback((finished) => {
          'worklet';
          if (finished && onAnimationComplete) {
            runOnJS(onAnimationComplete)();
          }
        })}
        exiting={FadeOut.duration(150)}
      >
        {children}
      </Animated.View>
    );
  }

  // Skip animation for faster navigation when needed
  return (
    <View style={[styles.container, style]}>
      {children}
    </View>
  );
});

OptimizedScreenWrapper.displayName = 'OptimizedScreenWrapper';

// HOC for easy migration from existing ScreenWrapper
export const withOptimizedScreenWrapper = <P extends object>(
  Component: React.ComponentType<P>,
  options?: Partial<OptimizedScreenWrapperProps>
) => {
  return memo((props: P) => (
    <OptimizedScreenWrapper {...options}>
      <Component {...props} />
    </OptimizedScreenWrapper>
  ));
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  placeholder: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});