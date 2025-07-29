import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
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

// Individual vegetable SVG components extracted from the main logo
const CarrotIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 25 75 C 30 80 35 85 45 85 C 55 85 60 80 65 75 C 70 70 75 60 75 50 C 75 40 70 30 60 25 C 50 20 40 20 30 25 C 20 30 15 40 15 50 C 15 60 20 70 25 75 Z" 
        fill="#ff8c00" 
      />
      <Path 
        d="M 40 15 C 40 20 42 25 45 30 C 48 25 50 20 50 15 C 50 10 45 10 40 15 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const BroccoliIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 30 30 C 25 25 25 35 30 40 C 35 45 45 45 50 40 C 55 45 65 45 70 40 C 75 35 75 25 70 30 C 65 25 55 25 50 30 C 45 25 35 25 30 30 Z" 
        fill="#228b22" 
      />
      <Path 
        d="M 45 40 C 45 50 47 60 50 70 C 53 60 55 50 55 40" 
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
        d="M 20 40 C 20 60 35 80 50 80 C 65 80 80 60 80 40 C 80 25 65 20 50 20 C 35 20 20 25 20 40 Z" 
        fill="#ff6347" 
      />
      <Path 
        d="M 40 15 C 38 20 42 25 45 20 C 48 25 52 20 50 15 C 55 20 58 15 60 15 C 58 10 52 10 50 15 C 48 10 42 10 40 15 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const OnionIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 30 35 C 25 40 25 50 25 60 C 25 70 35 80 50 80 C 65 80 75 70 75 60 C 75 50 75 40 70 35 C 65 30 55 25 50 25 C 45 25 35 30 30 35 Z" 
        fill="#dda0dd" 
      />
      <Path 
        d="M 40 20 C 42 25 45 30 50 30 C 55 30 58 25 60 20 C 58 15 52 15 50 20 C 48 15 42 15 40 20 Z" 
        fill="#228b22" 
      />
    </Svg>
  </Animated.View>
);

const LettuceIcon = ({ size = 50, style = {} }: { size?: number; style?: any }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path 
        d="M 25 30 C 20 35 20 45 25 50 C 20 55 25 65 30 70 C 35 75 45 75 50 70 C 55 75 65 75 70 70 C 75 65 80 55 75 50 C 80 45 80 35 75 30 C 70 25 60 25 55 30 C 50 25 40 25 35 30 C 30 25 25 25 25 30 Z" 
        fill="#90ee90" 
      />
    </Svg>
  </Animated.View>
);

interface AnimatedCharacterProps {
  char: string;
  index: number;
  totalChars: number;
}

const AnimatedCharacter = ({ char, index, totalChars }: AnimatedCharacterProps) => {
  const translateY = useSharedValue(screenHeight);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(0.5);
  const opacity = useSharedValue(0);

  useEffect(() => {
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
  }, [index]);

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
}

const VegetableIcon = ({ Component, index }: VegetableIconProps) => {
  const translateY = useSharedValue(-screenHeight);
  const translateX = useSharedValue(0);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(0.8);
  const opacity = useSharedValue(0);

  useEffect(() => {
    const delay = 1500 + index * 200; // Start after text animation
    const endY = screenHeight * 0.6 + Math.random() * 200; // Random end position
    const endX = (Math.random() - 0.5) * screenWidth * 0.8; // Random horizontal drift

    translateY.value = withDelay(
      delay,
      withSpring(endY, { damping: 6, stiffness: 40 })
    );

    translateX.value = withDelay(
      delay + 200,
      withSpring(endX, { damping: 8, stiffness: 60 })
    );

    rotation.value = withDelay(
      delay,
      withSpring(Math.random() * 720 - 360, { damping: 6 }) // Random spin
    );

    scale.value = withDelay(
      delay,
      withSpring(1 + Math.random() * 0.3, { damping: 8 })
    );

    opacity.value = withDelay(delay, withSpring(1));

    // Fade out after some time
    opacity.value = withDelay(
      delay + 3000,
      withSpring(0, { damping: 8 })
    );
  }, [index]);

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
      <Component size={40} />
    </Animated.View>
  );
};

interface EnhancedAnimatedIntroScreenProps {
  onFinished: () => void;
}

const EnhancedAnimatedIntroScreen = ({ onFinished }: EnhancedAnimatedIntroScreenProps) => {
  const taglineOpacity = useSharedValue(0);
  const taglineScale = useSharedValue(0.8);
  const buttonOpacity = useSharedValue(0);
  const buttonScale = useSharedValue(0.8);

  const text = 'PrepSense';
  const vegetables = [CarrotIcon, BroccoliIcon, TomatoIcon, OnionIcon, LettuceIcon];

  useEffect(() => {
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

    // Auto-finish after 5 seconds
    const timer = setTimeout(() => {
      runOnJS(onFinished)();
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  const taglineAnimatedStyle = useAnimatedStyle(() => ({
    opacity: taglineOpacity.value,
    transform: [{ scale: taglineScale.value }],
  }));

  const buttonAnimatedStyle = useAnimatedStyle(() => ({
    opacity: buttonOpacity.value,
    transform: [{ scale: buttonScale.value }],
  }));

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
      
      {/* Main text animation */}
      <View style={styles.textContainer}>
        {text.split('').map((char, index) => (
          <AnimatedCharacter
            key={index}
            char={char}
            index={index}
            totalChars={text.length}
          />
        ))}
      </View>

      {/* Tagline */}
      <Animated.View style={[styles.taglineContainer, taglineAnimatedStyle]}>
        <Text style={styles.tagline}>Smart Pantry Management</Text>
      </Animated.View>

      {/* Get Started Button */}
      <Animated.View style={[styles.buttonContainer, buttonAnimatedStyle]}>
        <View style={styles.button}>
          <Text style={styles.buttonText}>Get Started</Text>
        </View>
      </Animated.View>

      {/* Falling vegetables */}
      {vegetables.map((VegComponent, index) => (
        <VegetableIcon
          key={index}
          Component={VegComponent}
          index={index}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
    justifyContent: 'center',
    alignItems: 'center',
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
});

export default EnhancedAnimatedIntroScreen;