// COMPLETE BACKUP of EnhancedAnimatedIntroScreenV2.tsx - Created 2025-07-29
// This is the WORKING VERSION with all features:
// ✅ Breathing "Click Here to Begin" button with fade/scale animation
// ✅ Organized fruit dropping animation in neat grid pattern  
// ✅ Magical tunnel transition with teal circles and glow
// ✅ Idle logo reanimation - characters bounce every 12 seconds
// ✅ Fruit gathering/fade-out animation after 6 seconds
// ✅ Gentle welcome screen with Lily and smooth fade transitions
// ✅ Fixed banana positioning to stay on screen
// ✅ All vegetables: carrot, broccoli, tomato, onion, lettuce, banana

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
import Svg, { Path, G, LinearGradient, Defs, Stop, Rect } from 'react-native-svg';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// Current working SVG vegetable icons - replace with premium when available
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
      <Path 
        d="M 25 25 C 20 20 20 30 25 35 C 30 40 40 40 45 35 C 50 40 60 40 65 35 C 70 30 70 20 65 25 C 60 20 50 20 45 25 C 40 20 30 20 25 25 Z" 
        fill="#228b22" 
      />
      <Path 
        d="M 40 35 C 40 45 42 55 45 65 C 48 55 50 45 50 35" 
        fill="#8b4513" 
        strokeWidth="3"
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

const BananaIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      {/* Main banana body */}
      <Path 
        d="M 30 20 C 35 15 40 15 45 18 C 50 22 55 28 60 35 C 65 42 68 50 70 58 C 72 66 70 72 65 75 C 60 78 55 76 50 72 C 45 68 40 62 35 55 C 30 48 28 40 26 32 C 25 25 27 22 30 20 Z" 
        fill="#fdd835" 
      />
      {/* Banana peel tip */}
      <Path 
        d="M 30 20 C 32 18 35 18 37 20 C 39 22 40 25 38 27 C 36 28 34 27 32 25 C 30 23 29 21 30 20 Z" 
        fill="#8bc34a" 
      />
      {/* Banana ridges */}
      <Path 
        d="M 35 25 C 40 30 45 38 50 46 C 55 54 58 62 60 68 C 58 70 56 69 54 67 C 50 60 45 52 40 44 C 37 38 35 32 35 25 M 42 28 C 46 34 50 42 54 50 C 57 58 59 65 61 70 C 59 71 58 70 57 68 C 54 61 50 53 46 45 C 44 39 42 33 42 28" 
        fill="#ffb300" 
        opacity="0.7"
      />
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

    // Idle reanimation for individual characters
    const startIdleAnimation = () => {
      const idleDelay = 6000 + index * 100; // Stagger idle animations
      setTimeout(() => {
        const idleAnimation = () => {
          translateY.value = withSequence(
            withSpring(-15, { damping: 8, stiffness: 100 }),
            withSpring(0, { damping: 10, stiffness: 120 })
          );
          scale.value = withSequence(
            withSpring(1.1, { damping: 8, stiffness: 100 }),
            withSpring(1, { damping: 10, stiffness: 120 })
          );
        };
        
        idleAnimation();
        // Repeat every 12 seconds with character-specific offset
        const interval = setInterval(idleAnimation, 12000 + index * 500);
        return () => clearInterval(interval);
      }, idleDelay);
    };

    startIdleAnimation();
  }, [index, isPaused]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
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
    
    // Organized landing positions at the bottom in a neat grid
    const totalVegetables = 6;
    const spacing = screenWidth * 0.7 / (totalVegetables - 1); // Even spacing across 70% of screen (tighter)
    const startX = screenWidth * 0.15; // Start at 15% from left (more padding)
    const endX = startX + index * spacing; // Evenly spaced positions
    const endY = screenHeight * 0.72 + (index % 2) * 25; // Slight alternating height for visual interest

    // Fall from top of screen
    translateY.value = withDelay(
      delay,
      withSpring(endY, { damping: 6, stiffness: 40 })
    );

    translateX.value = withDelay(
      delay + 200,
      withSpring(endX - screenWidth / 2, { damping: 8, stiffness: 60 }) // Center-relative positioning
    );

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
    
    // After landing, wait 6 seconds then gather them aesthetically by fading them out
    setTimeout(() => {
      // Gentle fade out with slight upward drift (like they're being collected)
      opacity.value = withSpring(0, { damping: 12, stiffness: 40 });
      translateY.value = withSpring(translateY.value - 30, { damping: 10, stiffness: 30 });
      scale.value = withSpring(0.8, { damping: 10, stiffness: 40 });
    }, delay + 6000);
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
      <Component size={80} />
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
        <Pressable style={styles.button} onPress={handleGetStarted}>
          <Text style={styles.buttonText}>Get Started</Text>
        </Pressable>
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