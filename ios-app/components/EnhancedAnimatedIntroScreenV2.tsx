import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Dimensions, Pressable } from 'react-native';
import Animated, {
  useSharedValue,
  withSpring,
  withSequence,  
  withDelay,
  useAnimatedStyle,
  runOnJS,
  interpolate,
} from 'react-native-reanimated';
import Svg, { Path, G, LinearGradient, Defs, Stop, Rect, Circle } from 'react-native-svg';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Simple, visible vegetable icons
const CarrotIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 20 75 C 25 80 30 85 40 85 C 50 85 55 80 60 75 C 65 70 70 60 70 50 C 70 40 65 30 55 25 C 45 20 35 20 25 25 C 15 30 10 40 10 50 C 10 60 15 70 20 75 Z" 
        fill="#ff8c00" 
      />
      <Path 
        d="M 35 10 C 35 15 37 20 40 25 C 43 20 45 15 45 10 C 45 5 40 5 35 10 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const BroccoliIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      {/* Multiple fluffy clusters for afro-like appearance */}
      <Circle cx="35" cy="25" r="8" fill="#228b22" />
      <Circle cx="50" cy="20" r="9" fill="#228b22" />
      <Circle cx="65" cy="25" r="8" fill="#228b22" />
      <Circle cx="30" cy="35" r="7" fill="#228b22" />
      <Circle cx="45" cy="30" r="8" fill="#228b22" />
      <Circle cx="60" cy="32" r="7" fill="#228b22" />
      <Circle cx="70" cy="35" r="6" fill="#228b22" />
      <Circle cx="40" cy="38" r="6" fill="#228b22" />
      <Circle cx="55" cy="40" r="6" fill="#228b22" />
      {/* Thick uniform stem */}
      <Path 
        d="M 35 35 L 35 75 L 55 75 L 55 35 Z" 
        fill="#90EE90"
      />
    </Svg>
  </Animated.View>
);

const TomatoIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 15 35 C 15 55 30 75 45 75 C 60 75 75 55 75 35 C 75 20 60 15 45 15 C 30 15 15 20 15 35 Z" 
        fill="#ff6347" 
      />
      <Path 
        d="M 35 10 C 33 15 37 20 40 15 C 43 20 47 15 45 10 C 50 15 53 10 55 10 C 53 5 47 5 45 10 C 43 5 37 5 35 10 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const OnionIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 25 30 C 20 35 20 45 20 55 C 20 65 30 75 45 75 C 60 75 70 65 70 55 C 70 45 70 35 65 30 C 60 25 50 20 45 20 C 40 20 30 25 25 30 Z" 
        fill="#dda0dd" 
      />
      <Path 
        d="M 35 15 C 37 20 40 25 45 25 C 50 25 53 20 55 15 C 53 10 47 10 45 15 C 43 10 37 10 35 15 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const LettuceIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 20 25 C 15 30 15 40 20 45 C 15 50 20 60 25 65 C 30 70 40 70 45 65 C 50 70 60 70 65 65 C 70 60 75 50 70 45 C 75 40 75 30 70 25 C 65 20 55 20 50 25 C 45 20 35 20 30 25 C 25 20 20 20 20 25 Z" 
        fill="#90ee90" 
      />
    </Svg>
  </Animated.View>
);

const BananaIcon = ({ size = 95, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      {/* Main banana body - C-shaped crescent curve, slightly thicker */}
      <Path 
        d="M 35 15 C 25 15 12 25 12 35 C 12 45 18 55 23 65 C 28 75 33 85 43 90 C 50 93 58 91 58 85 C 58 79 52 74 47 69 C 42 64 37 54 32 44 C 27 34 27 24 35 15 Z" 
        fill="#fdd835" 
      />
      {/* Rectangular brown tip at the stem end */}
      <Path 
        d="M 33 13 L 37 13 L 37 17 L 33 17 Z" 
        fill="#8b4513" 
      />
      {/* Gradual brown spots - overripe but still edible */}
      <Path 
        d="M 28 28 C 27 27 26 28 27 29 C 28 30 29 29 28 28 Z" 
        fill="#d2691e" 
        opacity="0.4"
      />
      <Path 
        d="M 23 38 C 21 36 19 38 21 40 C 23 42 25 40 23 38 Z" 
        fill="#cd853f" 
        opacity="0.5"
      />
      <Path 
        d="M 27 52 C 25 50 23 52 25 54 C 27 56 29 54 27 52 Z" 
        fill="#a0522d" 
        opacity="0.6"
      />
      <Path 
        d="M 25 42 C 24 41 23 42 24 43 C 25 44 26 43 25 42 Z" 
        fill="#daa520" 
        opacity="0.3"
      />
      <Path 
        d="M 33 68 C 31 66 29 68 31 70 C 33 72 35 70 33 68 Z" 
        fill="#8b4513" 
        opacity="0.7"
      />
      <Path 
        d="M 39 80 C 37 78 35 80 37 82 C 39 84 41 82 39 80 Z" 
        fill="#a0522d" 
        opacity="0.6"
      />
      <Path 
        d="M 30 60 C 29 59 28 60 29 61 C 30 62 31 61 30 60 Z" 
        fill="#cd853f" 
        opacity="0.4"
      />
      {/* Banana ridges following the C curve */}
      <Path 
        d="M 32 20 C 27 25 22 35 22 45 C 22 55 27 65 32 75 C 37 80 42 85 47 87 C 45 85 40 80 35 75 C 30 65 27 55 27 45 C 27 35 30 25 32 20 M 30 22 C 25 27 20 37 20 47 C 20 57 25 67 30 77 C 35 82 40 87 45 89 C 43 87 38 82 33 77 C 28 67 25 57 25 47 C 25 37 28 27 30 22" 
        fill="#ffb300" 
        opacity="0.7"
      />
    </Svg>
  </Animated.View>
);

// Premium Avocado Icon - Inspired by the complex curved shapes in original SVG
const AvocadoIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <G>
        {/* Main avocado body */}
        <Path
          d="M50 15C35 15 25 25 22 40C20 55 25 70 35 80C40 85 45 88 50 88C55 88 60 85 65 80C75 70 80 55 78 40C75 25 65 15 50 15Z"
          fill="#5BA041"
        />
        {/* Highlight */}
        <Path
          d="M45 25C40 25 35 30 35 35C35 40 40 45 45 45C50 45 55 40 55 35C55 30 50 25 45 25Z"
          fill="#7FB96E"
        />
        {/* Pit */}
        <Path
          d="M50 45C45 45 42 48 42 52C42 58 45 62 50 62C55 62 58 58 58 52C58 48 55 45 50 45Z"
          fill="#8b4513"
        />
      </G>
    </Svg>
  </Animated.View>
);

// Premium Corn Icon - Inspired by the grain patterns in original SVG
const CornIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <G>
        {/* Corn husk */}
        <Path
          d="M35 15L35 25C35 30 32 35 28 38L25 85C25 90 28 92 32 92L68 92C72 92 75 90 75 85L72 38C68 35 65 30 65 25L65 15C60 12 55 10 50 10C45 10 40 12 35 15Z"
          fill="#7FB96E"
        />
        {/* Corn kernels pattern */}
        <Path
          d="M40 25C40 23 42 22 44 22C46 22 48 23 48 25L48 75C48 77 46 78 44 78C42 78 40 77 40 75L40 25Z M52 25C52 23 54 22 56 22C58 22 60 23 60 25L60 75C60 77 58 78 56 78C54 78 52 77 52 75L52 25Z"
          fill="#FFD700"
        />
        {/* Top leaves */}
        <Path
          d="M45 10C42 8 40 12 42 15L48 20L52 15C54 12 52 8 49 10C48 8 46 8 45 10Z"
          fill="#228b22"
        />
      </G>
    </Svg>
  </Animated.View>
);

// Premium Bell Pepper Icon - Inspired by the vegetable complexity in original SVG
const BellPepperIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <G>
        {/* Pepper body */}
        <Path
          d="M50 20C60 20 70 25 75 35C80 45 78 55 75 65C70 75 65 82 55 85C50 87 45 87 40 85C30 82 25 75 20 65C17 55 15 45 20 35C25 25 35 20 50 20Z"
          fill="#FF6B6B"
        />
        {/* Highlight/shine */}
        <Path
          d="M45 30C40 30 38 35 40 38C42 40 45 42 48 40C50 38 52 35 50 32C48 30 46 30 45 30Z"
          fill="#FF9999"
        />
        {/* Stem */}
        <Path
          d="M48 15C46 12 44 10 42 12C40 14 42 16 44 18L46 20L50 18L54 20L56 18C58 16 60 14 58 12C56 10 54 12 52 15C51 13 49 13 48 15Z"
          fill="#228b22"
        />
      </G>
    </Svg>
  </Animated.View>
);

interface AnimatedCharacterProps {
  char: string;
  index: number;
  totalChars: number;
  isPaused: boolean;
}

const AnimatedCharacter = ({ char, index, totalChars, isPaused }: AnimatedCharacterProps) => {
  const translateY = useSharedValue(screenHeight);
  const translateX = useSharedValue(0);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(0.5);
  const opacity = useSharedValue(0);

  useEffect(() => {
    if (isPaused) return;

    const delay = index * 150; // Stagger the animations
    
    // Start the animation sequence
    translateY.value = withDelay(
      delay,
      withSequence(
        withSpring(-100, { damping: 8, stiffness: 100 }), // Bounce high
        withSpring(0, { damping: 12, stiffness: 150 }) // Settle to position
      )
    );

    rotation.value = withDelay(
      delay,
      withSequence(
        withSpring(20, { damping: 8 }), // Rotate right
        withSpring(-10, { damping: 8 }), // Rotate left
        withSpring(0, { damping: 12 }) // Back to center
      )
    );

    scale.value = withDelay(
      delay,
      withSpring(1, { damping: 10, stiffness: 150 })
    );

    opacity.value = withDelay(delay, withSpring(1));

    // Idle reanimation for individual characters - subtle sway with shorter intervals
    const startIdleAnimation = () => {
      const idleDelay = Math.random() * 10000 + 15000; // Random delay between 15-25 seconds
      
      setTimeout(() => {
        const idleAnimation = () => {
          // Very subtle left-to-right sway - barely noticeable
          translateX.value = withSequence(
            withSpring(2, { damping: 25, stiffness: 30 }), 
            withSpring(-2, { damping: 25, stiffness: 30 }),
            withSpring(0, { damping: 30, stiffness: 50 })
          );

          // Very subtle scale breathing
          scale.value = withSequence(
            withSpring(1.005, { damping: 25, stiffness: 60 }),
            withSpring(1, { damping: 30, stiffness: 80 })
          );
        };
        
        idleAnimation();
        // Repeat every 20-35 seconds - more frequent but still subtle
        const repeatInterval = Math.random() * 15000 + 20000;
        const interval = setInterval(idleAnimation, repeatInterval);
        return () => clearInterval(interval);
      }, idleDelay);
    };

    startIdleAnimation();
  }, [index, isPaused]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
      { translateX: translateX.value },
      { rotate: `${rotation.value}deg` },
      { scale: scale.value },
    ],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[styles.character, animatedStyle]}>
      <Text style={styles.characterText}>{char}</Text>
    </Animated.View>
  );
};

interface VegetableIconProps {
  Component: React.ComponentType<{ size?: number; style?: any }>;
  index: number;
  isPaused: boolean;
}

const VegetableIcon = ({ Component, index, isPaused }: VegetableIconProps) => {
  const translateY = useSharedValue(-screenHeight);
  const translateX = useSharedValue(0);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(0.8);
  const opacity = useSharedValue(0);

  useEffect(() => {
    if (isPaused) return;

    const delay = 1500 + index * 200; // Start after text animation
    
    // Organized landing positions - shift first 5 vegetables left, give banana (index 5) more room
    const totalVegetables = 6;
    let endX, endY;
    
    if (index < 5) {
      // First 5 vegetables - shifted left with tighter spacing
      const spacing = screenWidth * 0.55 / 4; // 5 vegetables in 55% of screen width
      const startX = screenWidth * 0.08; // Start at 8% from left
      endX = startX + index * spacing;
      endY = screenHeight * 0.72 + (index % 2) * 25;
    } else {
      // Banana (index 5) - more room on the right with better spacing
      endX = screenWidth * 0.80; // Position banana at 80% from left for more even spacing
      endY = screenHeight * 0.70; // Slightly higher for prominence
    }

    // Fall from top of screen
    translateY.value = withDelay(
      delay,
      withSpring(endY, { damping: 6, stiffness: 40 })
    );

    translateX.value = withDelay(
      delay + 200,
      withSpring(endX - screenWidth / 2, { damping: 8, stiffness: 60 }) // Center-relative positioning
    );
    
    // Add subtle alive bounce animation after landing
    setTimeout(() => {
      const aliveAnimation = () => {
        translateY.value = withSequence(
          withSpring(endY - 8, { damping: 12, stiffness: 80 }),
          withSpring(endY, { damping: 15, stiffness: 100 })
        );
        scale.value = withSequence(
          withSpring((0.95 + (index % 3) * 0.05) * 1.02, { damping: 12, stiffness: 80 }),
          withSpring(0.95 + (index % 3) * 0.05, { damping: 15, stiffness: 100 })
        );
      };
      
      // Start alive animation after landing
      setTimeout(aliveAnimation, 1000);
      
      // Repeat alive bounce every 8-15 seconds with random intervals
      const aliveInterval = Math.random() * 7000 + 8000;
      setInterval(aliveAnimation, aliveInterval);
    }, delay + 2000);

    // Moderate spin for falling effect
    rotation.value = withDelay(
      delay,
      withSpring((index % 2 === 0 ? 180 : -180) + index * 30, { damping: 6 }) // Alternating spin direction
    );

    // Slight size variation for organic feel
    scale.value = withDelay(
      delay,
      withSpring(0.95 + (index % 3) * 0.05, { damping: 8 })
    );

    opacity.value = withDelay(delay, withSpring(1));
    
    // Keep vegetables on screen permanently - no fade out
  }, [index, isPaused]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
      { translateX: translateX.value },
      { rotate: `${rotation.value}deg` },
      { scale: scale.value },
    ],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[styles.vegetableIcon, animatedStyle]}>
      <Component size={index === 5 ? 95 : 85} />
    </Animated.View>
  );
};

interface EnhancedAnimatedIntroScreenV2Props {
  onFinished: () => void;
}

const EnhancedAnimatedIntroScreenV2 = ({ onFinished }: EnhancedAnimatedIntroScreenV2Props) => {
  const [hasStarted, setHasStarted] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);
  const [showTunnel, setShowTunnel] = useState(false);
  
  const taglineOpacity = useSharedValue(0);
  const taglineScale = useSharedValue(0.8);
  const buttonOpacity = useSharedValue(0);
  const buttonScale = useSharedValue(0.8);
  const getStartedBreathingScale = useSharedValue(1);
  const getStartedBreathingOpacity = useSharedValue(1);
  
  // Breathing animation for the start button
  const breathingScale = useSharedValue(1);
  const breathingOpacity = useSharedValue(1);
  
  // Tunnel animation values
  const tunnelScale = useSharedValue(0);
  const tunnelOpacity = useSharedValue(0);
  const lightOpacity = useSharedValue(0);
  const welcomeOpacity = useSharedValue(0);
  const welcomeScale = useSharedValue(0.8);

  const text = 'PrepSense';
  const vegetables = [CarrotIcon, BroccoliIcon, TomatoIcon, OnionIcon, LettuceIcon, BananaIcon];

  // Start breathing animation immediately
  useEffect(() => {
    const breathingAnimation = () => {
      breathingScale.value = withSequence(
        withSpring(1.05, { damping: 8, stiffness: 40 }),
        withSpring(0.98, { damping: 8, stiffness: 40 }),
        withSpring(1.0, { damping: 8, stiffness: 40 })
      );
      
      breathingOpacity.value = withSequence(
        withSpring(0.8, { damping: 8, stiffness: 40 }),
        withSpring(0.6, { damping: 8, stiffness: 40 }),
        withSpring(1.0, { damping: 8, stiffness: 40 })
      );
    };
    
    // Start breathing and repeat every 3.5 seconds
    breathingAnimation();
    const interval = setInterval(breathingAnimation, 3500);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!hasStarted) return;

    // Animate tagline after text animation
    taglineOpacity.value = withDelay(
      2000,
      withSpring(1, { damping: 8 })
    );
    taglineScale.value = withDelay(
      2000,
      withSpring(1, { damping: 8 })
    );

    // Animate button after tagline
    buttonOpacity.value = withDelay(
      2500,
      withSpring(1, { damping: 8 })
    );
    buttonScale.value = withDelay(
      2500,
      withSpring(1, { damping: 8 })
    );
    
    // Start gentle breathing animation for Get Started button
    setTimeout(() => {
      const breathingAnimation = () => {
        getStartedBreathingScale.value = withSequence(
          withSpring(1.05, { damping: 8, stiffness: 40 }),
          withSpring(0.98, { damping: 8, stiffness: 40 }),
          withSpring(1.0, { damping: 8, stiffness: 40 })
        );
        
        getStartedBreathingOpacity.value = withSequence(
          withSpring(0.8, { damping: 8, stiffness: 40 }),
          withSpring(0.6, { damping: 8, stiffness: 40 }),
          withSpring(1.0, { damping: 8, stiffness: 40 })
        );
      };
      
      // Start breathing animation
      breathingAnimation();
      
      // Repeat breathing every 4-6 seconds
      const breathingInterval = setInterval(() => {
        breathingAnimation();
      }, Math.random() * 2000 + 4000);
      
      return () => clearInterval(breathingInterval);
    }, 3500);

    // Set up idle reanimation after everything settles
    const idleReanimation = () => {
      // Gentle bounce for all characters
      setTimeout(() => {
        taglineScale.value = withSequence(
          withSpring(1.05, { damping: 6 }),
          withSpring(1, { damping: 8 })
        );
      }, 8000); // Start idle animation after 8 seconds
    };

    idleReanimation();
    // Repeat idle animation every 15 seconds
    const interval = setInterval(idleReanimation, 15000);
    
    return () => clearInterval(interval);
  }, [hasStarted]);

  const handleScreenPress = () => {
    if (!hasStarted) {
      setHasStarted(true);
    }
  };

  const handleGetStarted = () => {
    setShowTunnel(true);
    
    // Magical formation - start very small and gently grow
    tunnelScale.value = withSequence(
      // Start tiny and gradually form
      withSpring(0.1, { damping: 15, stiffness: 200 }),
      withSpring(0.3, { damping: 12, stiffness: 120 }),
      withSpring(0.8, { damping: 10, stiffness: 100 }),
      // Then gently expand to envelop
      withSpring(3, { damping: 8, stiffness: 60 })
    );
    
    // Gentle magical fade-in and out
    tunnelOpacity.value = withSequence(
      withSpring(0.3, { damping: 12, stiffness: 80 }), // Subtle start
      withSpring(0.7, { damping: 10, stiffness: 70 }), // Build up
      withDelay(800, withSpring(0, { damping: 8, stiffness: 50 })) // Gentle fade
    );
    
    // Soft, warm light effect
    lightOpacity.value = withSequence(
      withDelay(600, withSpring(0.4, { damping: 10, stiffness: 60 })), // Gentle glow
      withDelay(1000, withSpring(0.8, { damping: 8, stiffness: 50 })), // Bright moment
      withDelay(1400, withSpring(0, { damping: 10, stiffness: 40 })) // Soft fade
    );
    
    // Show welcome after tunnel
    setTimeout(() => {
      setShowWelcome(true);
      // Very gentle fade-in for welcome message
      welcomeOpacity.value = withSpring(1, { damping: 12, stiffness: 50 });
      welcomeScale.value = withSpring(1, { damping: 12, stiffness: 50 });
    }, 2000);
    
    // Gentle fade out and finish after welcome
    setTimeout(() => {
      // Gentle fade out
      welcomeOpacity.value = withSpring(0, { damping: 10, stiffness: 40 });
      welcomeScale.value = withSpring(0.95, { damping: 10, stiffness: 40 });
      
      // Finish after fade out completes
      setTimeout(() => {
        onFinished();
      }, 1500);
    }, 5500);
  };

  const taglineAnimatedStyle = useAnimatedStyle(() => ({
    opacity: taglineOpacity.value,
    transform: [{ scale: taglineScale.value }],
  }));

  const buttonAnimatedStyle = useAnimatedStyle(() => ({
    opacity: buttonOpacity.value,
    transform: [{ scale: buttonScale.value }],
  }));
  
  const getStartedBreathingStyle = useAnimatedStyle(() => ({
    transform: [{ scale: getStartedBreathingScale.value }],
    opacity: getStartedBreathingOpacity.value,
  }));

  const tunnelAnimatedStyle = useAnimatedStyle(() => ({
    opacity: tunnelOpacity.value,
    transform: [{ scale: tunnelScale.value }],
  }));

  const lightAnimatedStyle = useAnimatedStyle(() => ({
    opacity: lightOpacity.value,
  }));

  const welcomeAnimatedStyle = useAnimatedStyle(() => ({
    opacity: welcomeOpacity.value,
    transform: [{ scale: welcomeScale.value }],
  }));

  const breathingAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: breathingScale.value }],
    opacity: breathingOpacity.value,
  }));

  // Blank screen - wait for tap
  if (!hasStarted) {
    return (
      <View style={styles.blankScreen}>
        {/* Bright gradient background */}
        <Svg 
          style={StyleSheet.absoluteFillObject} 
          width={screenWidth} 
          height={screenHeight}
          viewBox={`0 0 ${screenWidth} ${screenHeight}`}
        >
          <Defs>
            <LinearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#f0f9ff" stopOpacity="1" />
              <Stop offset="30%" stopColor="#e0f2fe" stopOpacity="1" />
              <Stop offset="70%" stopColor="#f0fdf4" stopOpacity="1" />
              <Stop offset="100%" stopColor="#ecfdf5" stopOpacity="1" />
            </LinearGradient>
          </Defs>
          <Rect width={screenWidth} height={screenHeight} fill="url(#backgroundGradient)" />
        </Svg>
        
        <Animated.View style={[styles.breathingButtonContainer, breathingAnimatedStyle]}>
          <Pressable style={styles.breathingButton} onPress={handleScreenPress}>
            <Text style={styles.breathingButtonText}>Click Here to Begin</Text>
          </Pressable>
        </Animated.View>
      </View>
    );
  }

  // Tunnel transition screen
  if (showTunnel && !showWelcome) {
    return (
      <View style={styles.container}>
        {/* Circular tunnel effect */}
        <Animated.View style={[styles.tunnelContainer, tunnelAnimatedStyle]}>
          <View style={styles.tunnelCircle} />
          <View style={[styles.tunnelCircle, styles.tunnelCircleMid]} />
          <View style={[styles.tunnelCircle, styles.tunnelCircleOuter]} />
        </Animated.View>
        
        {/* Bright light at the end */}
        <Animated.View style={[styles.lightContainer, lightAnimatedStyle]}>
          <View style={styles.brightLight} />
        </Animated.View>
      </View>
    );
  }

  // Welcome screen
  if (showWelcome) {
    return (
      <View style={styles.container}>
        {/* Bright gradient background */}
        <Svg 
          style={StyleSheet.absoluteFillObject} 
          width={screenWidth} 
          height={screenHeight}
          viewBox={`0 0 ${screenWidth} ${screenHeight}`}
        >
          <Defs>
            <LinearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#f0f9ff" stopOpacity="1" />
              <Stop offset="30%" stopColor="#e0f2fe" stopOpacity="1" />
              <Stop offset="70%" stopColor="#f0fdf4" stopOpacity="1" />
              <Stop offset="100%" stopColor="#ecfdf5" stopOpacity="1" />
            </LinearGradient>
          </Defs>
          <Rect width={screenWidth} height={screenHeight} fill="url(#backgroundGradient)" />
        </Svg>
        
        <Animated.View style={[styles.welcomeContainer, welcomeAnimatedStyle]}>
          <Text style={styles.welcomeTitle}>Welcome Back, Lily! 👋</Text>
          <Text style={styles.welcomeSubtitle}>Ready to make cooking effortless?</Text>
        </Animated.View>
      </View>
    );
  }

  // Main animation screen
  return (
    <Pressable style={styles.container} onPress={handleScreenPress}>
      {/* Bright gradient background */}
      <Svg 
        style={StyleSheet.absoluteFillObject} 
        width={screenWidth} 
        height={screenHeight}
        viewBox={`0 0 ${screenWidth} ${screenHeight}`}
      >
        <Defs>
          <LinearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="#f0f9ff" stopOpacity="1" />
            <Stop offset="30%" stopColor="#e0f2fe" stopOpacity="1" />
            <Stop offset="70%" stopColor="#f0fdf4" stopOpacity="1" />
            <Stop offset="100%" stopColor="#ecfdf5" stopOpacity="1" />
          </LinearGradient>
        </Defs>
        <Rect width={screenWidth} height={screenHeight} fill="url(#backgroundGradient)" />
      </Svg>

      {/* Main text animation */}
      <View style={styles.textContainer}>
        {text.split('').map((char, index) => (
          <AnimatedCharacter
            key={index}
            char={char}
            index={index}
            totalChars={text.length}
            isPaused={false}
          />
        ))}
      </View>

      {/* Tagline */}
      <Animated.View style={[styles.taglineContainer, taglineAnimatedStyle]}>
        <Text style={styles.tagline}>Smart Pantry Management</Text>
      </Animated.View>

      {/* Get Started Button */}
      <Animated.View style={[styles.buttonContainer, buttonAnimatedStyle]}>
        <Animated.View style={[getStartedBreathingStyle]}>
          <Pressable style={styles.button} onPress={handleGetStarted}>
            <Text style={styles.buttonText}>Get Started</Text>
          </Pressable>
        </Animated.View>
      </Animated.View>

      {/* Falling vegetables - make them bigger and closer */}
      {vegetables.map((VegComponent, index) => (
        <VegetableIcon
          key={index}
          Component={VegComponent}
          index={index}
          isPaused={false}
        />
      ))}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pauseButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  pauseButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1b6b45',
  },
  textContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
  },
  character: {
    marginHorizontal: 2,
  },
  characterText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#1b6b45',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  taglineContainer: {
    marginBottom: 60,
  },
  tagline: {
    fontSize: 18,
    color: '#4a5568',
    fontWeight: '500',
    textAlign: 'center',
  },
  buttonContainer: {
    paddingHorizontal: 40,
  },
  button: {
    backgroundColor: '#1b6b45',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    overflow: 'hidden',
    position: 'relative',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  vegetableIcon: {
    position: 'absolute',
    top: 0,
    left: screenWidth / 2 - 20,
  },
  welcomeContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1b6b45',
    textAlign: 'center',
    marginBottom: 16,
  },
  welcomeSubtitle: {
    fontSize: 18,
    color: '#4a5568',
    textAlign: 'center',
    fontWeight: '500',
  },
  blankScreen: {
    flex: 1,
    backgroundColor: '#f0f9ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  breathingButtonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  breathingButton: {
    backgroundColor: '#1b6b45',
    paddingHorizontal: 40,
    paddingVertical: 16,
    borderRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  breathingButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  tunnelContainer: {
    position: 'absolute',
    top: screenHeight / 2 - screenWidth,
    left: screenWidth / 2 - screenWidth,
    width: screenWidth * 2,
    height: screenWidth * 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tunnelCircle: {
    position: 'absolute',
    width: screenWidth * 0.6,
    height: screenWidth * 0.6,
    borderRadius: screenWidth * 0.3,
    backgroundColor: '#2dd4bf', // Magical teal-green
    opacity: 0.4,
    shadowColor: '#2dd4bf',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 10,
  },
  tunnelCircleMid: {
    width: screenWidth * 1.0,
    height: screenWidth * 1.0,
    borderRadius: screenWidth * 0.5,
    backgroundColor: '#34d399', // Brighter magical green
    opacity: 0.3,
    shadowColor: '#34d399',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 30,
    elevation: 8,
  },
  tunnelCircleOuter: {
    width: screenWidth * 1.6,
    height: screenWidth * 1.6,
    borderRadius: screenWidth * 0.8,
    backgroundColor: '#6ee7b7', // Soft magical mint
    opacity: 0.2,
    shadowColor: '#6ee7b7',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 40,
    elevation: 6,
  },
  lightContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  brightLight: {
    width: screenWidth * 1.5,
    height: screenHeight * 1.5,
    borderRadius: screenWidth * 0.75,
    backgroundColor: '#ffffff',
    shadowColor: '#ffffff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 50,
    elevation: 20,
  },
});

export default EnhancedAnimatedIntroScreenV2;