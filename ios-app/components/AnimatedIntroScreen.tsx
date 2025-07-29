import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSequence,
  withDelay,
  withSpring,
  interpolate,
  Easing,
  FadeIn,
  FadeOut,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface AnimatedIntroScreenProps {
  onFinished: () => void;
}

const BRAND_GREEN = '#5BA041';
const BRAND_AVOCADO = '#7FB96E';
const BRAND_BLUE = '#113c70';

// Individual animated character component
const AnimatedCharacter = ({ char, index, totalChars }: { char: string; index: number; totalChars: number }) => {
  const translateY = useSharedValue(screenHeight);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(0.5);
  const opacity = useSharedValue(0);

  useEffect(() => {
    const delay = index * 100; // Stagger the animations
    
    // Jump in animation
    translateY.value = withDelay(
      delay,
      withSequence(
        withSpring(-100, {
          damping: 8,
          stiffness: 100,
          mass: 1,
          velocity: -10,
        }),
        withSpring(0, {
          damping: 10,
          stiffness: 150,
        })
      )
    );

    // Rotation while jumping
    rotation.value = withDelay(
      delay,
      withSequence(
        withTiming(360, { duration: 600, easing: Easing.out(Easing.cubic) }),
        withTiming(0, { duration: 0 })
      )
    );

    // Scale animation
    scale.value = withDelay(
      delay,
      withSequence(
        withSpring(1.2, { damping: 5, stiffness: 200 }),
        withSpring(1, { damping: 8, stiffness: 150 })
      )
    );

    // Fade in
    opacity.value = withDelay(
      delay,
      withTiming(1, { duration: 300 })
    );

    // Small bounce effect after landing
    setTimeout(() => {
      translateY.value = withSequence(
        withSpring(-20, { damping: 5, stiffness: 200 }),
        withSpring(0, { damping: 8, stiffness: 150 })
      );
    }, delay + 800);
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { translateY: translateY.value },
        { rotate: `${rotation.value}deg` },
        { scale: scale.value },
      ],
      opacity: opacity.value,
    };
  });

  return (
    <Animated.Text style={[styles.logoChar, animatedStyle]}>
      {char}
    </Animated.Text>
  );
};

// Animated vegetable icons
const VegetableIcon = ({ type, delay }: { type: 'carrot' | 'broccoli' | 'tomato'; delay: number }) => {
  const translateY = useSharedValue(-100);
  const translateX = useSharedValue(0);
  const rotation = useSharedValue(0);
  const opacity = useSharedValue(0);
  const scale = useSharedValue(0);

  const getIcon = () => {
    switch (type) {
      case 'carrot':
        return '🥕';
      case 'broccoli':
        return '🥦';
      case 'tomato':
        return '🍅';
    }
  };

  useEffect(() => {
    // Random starting position
    const startX = (Math.random() - 0.5) * screenWidth;
    translateX.value = startX;

    // Animate falling and bouncing
    opacity.value = withDelay(delay, withTiming(1, { duration: 300 }));
    
    translateY.value = withDelay(
      delay,
      withSequence(
        withSpring(screenHeight * 0.7, {
          damping: 6,
          stiffness: 50,
          mass: 1,
          velocity: 5,
        }),
        // Bounce
        withSpring(screenHeight * 0.6, {
          damping: 5,
          stiffness: 200,
        }),
        withSpring(screenHeight * 0.7, {
          damping: 8,
          stiffness: 150,
        })
      )
    );

    // Spin while falling
    rotation.value = withDelay(
      delay,
      withTiming(720, { duration: 2000, easing: Easing.linear })
    );

    // Scale animation
    scale.value = withDelay(
      delay,
      withSpring(1, { damping: 8, stiffness: 150 })
    );

    // Gentle sway after landing
    setTimeout(() => {
      translateX.value = withSequence(
        withTiming(startX + 20, { duration: 2000, easing: Easing.inOut(Easing.ease) }),
        withTiming(startX - 20, { duration: 2000, easing: Easing.inOut(Easing.ease) }),
        withTiming(startX, { duration: 2000, easing: Easing.inOut(Easing.ease) })
      );
    }, delay + 2000);
  }, []);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { translateY: translateY.value },
        { translateX: translateX.value },
        { rotate: `${rotation.value}deg` },
        { scale: scale.value },
      ],
      opacity: opacity.value,
    };
  });

  return (
    <Animated.Text style={[styles.vegetableIcon, animatedStyle]}>
      {getIcon()}
    </Animated.Text>
  );
};

const AnimatedIntroScreen: React.FC<AnimatedIntroScreenProps> = ({ onFinished }) => {
  const taglineOpacity = useSharedValue(0);
  const taglineScale = useSharedValue(0.8);
  const buttonOpacity = useSharedValue(0);
  const buttonScale = useSharedValue(0.9);
  const backgroundOpacity = useSharedValue(0);

  useEffect(() => {
    // Background fade in
    backgroundOpacity.value = withTiming(1, { duration: 500 });

    // Tagline animation (after logo completes)
    setTimeout(() => {
      taglineOpacity.value = withSpring(1, { damping: 10, stiffness: 100 });
      taglineScale.value = withSpring(1, { damping: 10, stiffness: 100 });
    }, 1500);

    // Button animation
    setTimeout(() => {
      buttonOpacity.value = withTiming(1, { duration: 500 });
      buttonScale.value = withSequence(
        withSpring(1.1, { damping: 5, stiffness: 200 }),
        withSpring(1, { damping: 8, stiffness: 150 })
      );
    }, 2500);

    // Pulse button
    setTimeout(() => {
      const pulse = () => {
        buttonScale.value = withSequence(
          withTiming(1.05, { duration: 800, easing: Easing.inOut(Easing.ease) }),
          withTiming(0.95, { duration: 800, easing: Easing.inOut(Easing.ease) })
        );
      };
      pulse();
      setInterval(pulse, 1600);
    }, 3500);
  }, []);

  const taglineStyle = useAnimatedStyle(() => ({
    opacity: taglineOpacity.value,
    transform: [{ scale: taglineScale.value }],
  }));

  const buttonStyle = useAnimatedStyle(() => ({
    opacity: buttonOpacity.value,
    transform: [{ scale: buttonScale.value }],
  }));

  const backgroundStyle = useAnimatedStyle(() => ({
    opacity: backgroundOpacity.value,
  }));

  const logoText = 'PrepSense';
  
  return (
    <View style={styles.container}>
      <StatusBar hidden />
      <Animated.View style={[StyleSheet.absoluteFillObject, backgroundStyle]}>
        <LinearGradient
          colors={['#0a0a0a', '#1a1a1a', '#0a0a0a']}
          style={styles.background}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
      </Animated.View>

      {/* Falling vegetables in background */}
      <View style={styles.vegetablesContainer}>
        <VegetableIcon type="carrot" delay={1800} />
        <VegetableIcon type="broccoli" delay={2000} />
        <VegetableIcon type="tomato" delay={2200} />
      </View>

      <View style={styles.content}>
        {/* Logo with jumping characters */}
        <View style={styles.logoContainer}>
          <View style={styles.logoTextContainer}>
            {logoText.split('').map((char, index) => (
              <AnimatedCharacter
                key={index}
                char={char}
                index={index}
                totalChars={logoText.length}
              />
            ))}
          </View>
        </View>

        {/* Tagline */}
        <Animated.View style={[styles.taglineContainer, taglineStyle]}>
          <Text style={styles.tagline}>Smart Pantry, Zero Waste</Text>
          <Text style={styles.subTagline}>Let's make every ingredient count</Text>
        </Animated.View>

        {/* Call to Action */}
        <TouchableOpacity onPress={onFinished} activeOpacity={0.8}>
          <Animated.View style={[styles.button, buttonStyle]}>
            <Text style={styles.buttonText}>Get Started</Text>
          </Animated.View>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  background: {
    flex: 1,
  },
  vegetablesContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1,
  },
  vegetableIcon: {
    position: 'absolute',
    fontSize: 40,
    zIndex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
    paddingHorizontal: 40,
  },
  logoContainer: {
    marginBottom: 60,
  },
  logoTextContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoChar: {
    fontSize: 56,
    fontWeight: 'bold',
    color: BRAND_GREEN,
    marginHorizontal: 2,
    textShadowColor: BRAND_AVOCADO,
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 10,
  },
  taglineContainer: {
    alignItems: 'center',
    marginBottom: 80,
  },
  tagline: {
    fontSize: 24,
    color: 'white',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  subTagline: {
    fontSize: 18,
    color: '#cccccc',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  button: {
    backgroundColor: BRAND_GREEN,
    paddingHorizontal: 50,
    paddingVertical: 18,
    borderRadius: 30,
    shadowColor: BRAND_GREEN,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 8,
  },
  buttonText: {
    fontSize: 20,
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default AnimatedIntroScreen;