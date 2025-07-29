import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface AnimatedTabNavigatorProps {
  children: React.ReactNode;
  currentIndex: number;
}

export const AnimatedTabNavigator: React.FC<AnimatedTabNavigatorProps> = ({
  children,
  currentIndex,
}) => {
  const slideAnimation = useSharedValue(0);
  const previousIndex = useRef(0);

  useEffect(() => {
    const direction = currentIndex > previousIndex.current ? 1 : -1;
    
    // Trigger haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Animate to new position
    slideAnimation.value = withSpring(currentIndex, {
      damping: 20,
      stiffness: 150,
      overshootClamping: true,
    });
    
    previousIndex.current = currentIndex;
  }, [currentIndex]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      {
        translateX: interpolate(
          slideAnimation.value,
          [0, 1, 2, 3, 4],
          [0, -SCREEN_WIDTH, -SCREEN_WIDTH * 2, -SCREEN_WIDTH * 3, -SCREEN_WIDTH * 4],
          Extrapolate.CLAMP
        ),
      },
    ],
  }));

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.screensContainer, animatedStyle]}>
        {React.Children.map(children, (child, index) => (
          <View key={index} style={styles.screen}>
            {child}
          </View>
        ))}
      </Animated.View>
    </View>
  );
};

// Alternative transition styles
export const TransitionStyles = {
  // Slide transition (default)
  slide: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => ({
      transform: [
        {
          translateX: interpolate(
            animation.value,
            [index - 1, index, index + 1],
            [SCREEN_WIDTH, 0, -SCREEN_WIDTH],
            Extrapolate.CLAMP
          ),
        },
      ],
    }));
  },

  // Fade transition
  fade: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => ({
      opacity: interpolate(
        animation.value,
        [index - 0.5, index, index + 0.5],
        [0, 1, 0],
        Extrapolate.CLAMP
      ),
    }));
  },

  // Scale and fade
  scaleAndFade: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => {
      const isActive = Math.abs(animation.value - index) < 0.5;
      
      return {
        opacity: interpolate(
          animation.value,
          [index - 1, index - 0.5, index, index + 0.5, index + 1],
          [0, 0, 1, 0, 0],
          Extrapolate.CLAMP
        ),
        transform: [
          {
            scale: interpolate(
              animation.value,
              [index - 1, index, index + 1],
              [0.85, 1, 0.85],
              Extrapolate.CLAMP
            ),
          },
        ],
      };
    });
  },

  // 3D flip
  flip3D: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => {
      const rotateY = interpolate(
        animation.value,
        [index - 1, index, index + 1],
        [-90, 0, 90],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { perspective: 1000 },
          { rotateY: `${rotateY}deg` },
        ],
        opacity: interpolate(
          Math.abs(rotateY),
          [0, 90],
          [1, 0],
          Extrapolate.CLAMP
        ),
      };
    });
  },

  // Carousel
  carousel: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => {
      const translateX = interpolate(
        animation.value,
        [index - 1, index, index + 1],
        [-SCREEN_WIDTH * 0.8, 0, SCREEN_WIDTH * 0.8],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        animation.value,
        [index - 1, index - 0.5, index, index + 0.5, index + 1],
        [0.8, 0.85, 1, 0.85, 0.8],
        Extrapolate.CLAMP
      );
      
      const opacity = interpolate(
        animation.value,
        [index - 1, index - 0.5, index, index + 0.5, index + 1],
        [0.5, 0.7, 1, 0.7, 0.5],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { translateX },
          { scale },
        ],
        opacity,
      };
    });
  },

  // Stack
  stack: (index: number, targetIndex: number, animation: any) => {
    return useAnimatedStyle(() => {
      const translateX = interpolate(
        animation.value,
        [index - 1, index, index + 1],
        [0, 0, SCREEN_WIDTH],
        Extrapolate.CLAMP
      );
      
      const translateY = interpolate(
        animation.value,
        [index - 1, index, index + 1],
        [0, 0, 50],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        animation.value,
        [index - 1, index, index + 1],
        [1, 1, 0.9],
        Extrapolate.CLAMP
      );
      
      const opacity = interpolate(
        animation.value,
        [index - 1, index, index + 0.5, index + 1],
        [1, 1, 0.5, 0],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { translateX },
          { translateY },
          { scale },
        ],
        opacity,
      };
    });
  },
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  screensContainer: {
    flex: 1,
    flexDirection: 'row',
  },
  screen: {
    width: SCREEN_WIDTH,
    flex: 1,
  },
});