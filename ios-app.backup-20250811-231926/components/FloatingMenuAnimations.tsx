// Showcase of different floating menu animation styles
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withDelay,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';

// Animation Style 1: Elastic Pop with Overshoot
export const ElasticPopAnimation = {
  animateIn: (scale: any, index: number) => {
    scale.value = withDelay(
      index * 50,
      withSpring(1, {
        damping: 8, // Lower damping = more bounce
        stiffness: 150,
        overshootClamping: false, // Allow overshoot for elastic effect
      })
    );
  },
  animateOut: (scale: any) => {
    scale.value = withSpring(0, {
      damping: 20,
      stiffness: 300,
    });
  },
};

// Animation Style 2: Spiral Appearance
export const SpiralAnimation = {
  getAnimatedStyle: (index: number, animation: any) => {
    return useAnimatedStyle(() => {
      const angle = (index * 360) / 6; // Distribute items in a circle
      const radius = interpolate(
        animation.value,
        [0, 1],
        [0, 80],
        Extrapolate.CLAMP
      );
      const rotation = interpolate(
        animation.value,
        [0, 1],
        [0, 360],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          {
            translateX: radius * Math.cos((angle + rotation) * Math.PI / 180),
          },
          {
            translateY: radius * Math.sin((angle + rotation) * Math.PI / 180),
          },
          {
            scale: animation.value,
          },
          {
            rotate: `${rotation}deg`,
          },
        ],
        opacity: animation.value,
      };
    });
  },
};

// Animation Style 3: Wave Effect
export const WaveAnimation = {
  getAnimatedStyle: (index: number, animation: any, totalItems: number) => {
    return useAnimatedStyle(() => {
      const progress = animation.value;
      const delay = index / totalItems;
      const waveProgress = Math.max(0, Math.min(1, (progress - delay) * 2));
      
      const translateY = interpolate(
        waveProgress,
        [0, 0.5, 1],
        [50, -10, 0],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        waveProgress,
        [0, 0.5, 1],
        [0, 1.2, 1],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { translateY },
          { scale },
        ],
        opacity: waveProgress,
      };
    });
  },
};

// Animation Style 4: Flip Cards
export const FlipCardAnimation = {
  getAnimatedStyle: (index: number, animation: any) => {
    return useAnimatedStyle(() => {
      const rotateY = interpolate(
        animation.value,
        [0, 1],
        [-90, 0],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        animation.value,
        [0, 0.5, 1],
        [0.8, 1.1, 1],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { perspective: 1000 },
          { rotateY: `${rotateY}deg` },
          { scale },
        ],
        opacity: interpolate(
          animation.value,
          [0, 0.3, 1],
          [0, 0.5, 1],
          Extrapolate.CLAMP
        ),
      };
    });
  },
};

// Animation Style 5: Morphing Blob
export const MorphAnimation = {
  getContainerStyle: (animation: any) => {
    return useAnimatedStyle(() => {
      const width = interpolate(
        animation.value,
        [0, 1],
        [56, 280],
        Extrapolate.CLAMP
      );
      
      const height = interpolate(
        animation.value,
        [0, 1],
        [56, 200],
        Extrapolate.CLAMP
      );
      
      const borderRadius = interpolate(
        animation.value,
        [0, 0.5, 1],
        [28, 40, 20],
        Extrapolate.CLAMP
      );
      
      return {
        width,
        height,
        borderRadius,
        transform: [
          {
            scale: interpolate(
              animation.value,
              [0, 0.5, 1],
              [1, 0.95, 1],
              Extrapolate.CLAMP
            ),
          },
        ],
      };
    });
  },
};

// Animation Style 6: Particle Explosion
export const ParticleAnimation = {
  getAnimatedStyle: (index: number, animation: any, totalItems: number) => {
    return useAnimatedStyle(() => {
      const angle = (index * 360) / totalItems;
      const randomOffset = Math.sin(index * 123.456) * 20; // Pseudo-random offset
      
      const distance = interpolate(
        animation.value,
        [0, 0.6, 1],
        [0, 100 + randomOffset, 80],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        animation.value,
        [0, 0.3, 0.6, 1],
        [0, 1.5, 0.8, 1],
        Extrapolate.CLAMP
      );
      
      const rotation = interpolate(
        animation.value,
        [0, 1],
        [0, 180 + randomOffset * 5],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          {
            translateX: distance * Math.cos(angle * Math.PI / 180),
          },
          {
            translateY: distance * Math.sin(angle * Math.PI / 180),
          },
          {
            scale,
          },
          {
            rotate: `${rotation}deg`,
          },
        ],
        opacity: interpolate(
          animation.value,
          [0, 0.2, 1],
          [0, 1, 1],
          Extrapolate.CLAMP
        ),
      };
    });
  },
};

// Chat Suggestion Specific Animations
export const ChatBubbleAnimations = {
  // Typewriter effect
  typewriterStyle: (index: number, animation: any) => {
    return useAnimatedStyle(() => {
      const progress = animation.value;
      const itemDelay = index * 0.1;
      const itemProgress = Math.max(0, Math.min(1, (progress - itemDelay) / 0.3));
      
      const width = interpolate(
        itemProgress,
        [0, 1],
        [0, 100],
        Extrapolate.CLAMP
      );
      
      return {
        width: `${width}%`,
        opacity: itemProgress,
        overflow: 'hidden',
      };
    });
  },
  
  // Ripple effect from button
  rippleStyle: (index: number, animation: any, totalItems: number) => {
    return useAnimatedStyle(() => {
      const delay = index / totalItems * 0.3;
      const progress = Math.max(0, animation.value - delay);
      
      const scale = interpolate(
        progress,
        [0, 0.5, 1],
        [0.3, 1.1, 1],
        Extrapolate.CLAMP
      );
      
      const translateX = interpolate(
        progress,
        [0, 1],
        [50, 0],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { scale },
          { translateX },
        ],
        opacity: progress,
      };
    });
  },
  
  // Bubble up effect
  bubbleUpStyle: (index: number, animation: any) => {
    return useAnimatedStyle(() => {
      const translateY = interpolate(
        animation.value,
        [0, 0.5, 1],
        [30, -5, 0],
        Extrapolate.CLAMP
      );
      
      const scale = interpolate(
        animation.value,
        [0, 0.6, 1],
        [0.7, 1.05, 1],
        Extrapolate.CLAMP
      );
      
      return {
        transform: [
          { translateY },
          { scale },
        ],
        opacity: animation.value,
      };
    });
  },
};

export default {
  ElasticPopAnimation,
  SpiralAnimation,
  WaveAnimation,
  FlipCardAnimation,
  MorphAnimation,
  ParticleAnimation,
  ChatBubbleAnimations,
};