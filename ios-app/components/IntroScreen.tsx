import React, { useEffect, useRef } from 'react';
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
  runOnJS,
  interpolate,
  Extrapolate,
  Easing,
} from 'react-native-reanimated';
import Svg, { Path, G } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface IntroScreenProps {
  onFinished: () => void;
}

const BRAND_GREEN = '#5BA041';
const BRAND_AVOCADO = '#7FB96E';
const BRAND_BLUE = '#113c70';

const IntroScreen: React.FC<IntroScreenProps> = ({ onFinished }) => {
  // Animation values
  const fadeIn = useSharedValue(0);
  const logoDrawProgress = useSharedValue(0);
  const logoFillProgress = useSharedValue(0);
  const taglineY = useSharedValue(50);
  const taglineOpacity = useSharedValue(0);
  const questionScale = useSharedValue(0.8);
  const questionOpacity = useSharedValue(0);
  const factOpacity = useSharedValue(0);
  const counterValue = useSharedValue(0);
  const trashIconRotation = useSharedValue(0);
  const sweepX = useSharedValue(-screenWidth);
  const sweepOpacity = useSharedValue(0);
  const impactOpacity = useSharedValue(0);
  const callToActionScale = useSharedValue(0.9);
  const callToActionOpacity = useSharedValue(0);

  useEffect(() => {
    // 0-0.5s: Fade in from black
    fadeIn.value = withTiming(1, { duration: 500 });

    // 0.5-1.5s: Logo outline draw → fill
    logoDrawProgress.value = withDelay(
      500,
      withTiming(1, { duration: 800, easing: Easing.out(Easing.quad) })
    );
    logoFillProgress.value = withDelay(
      1000,
      withTiming(1, { duration: 500, easing: Easing.out(Easing.quad) })
    );

    // 1.5-3s: Tagline slides up
    taglineY.value = withDelay(1500, withTiming(0, { duration: 800 }));
    taglineOpacity.value = withDelay(1500, withTiming(1, { duration: 800 }));

    // 3-4.5s: Question zoom-in with typewriter
    questionScale.value = withDelay(3000, withTiming(1, { duration: 1000 }));
    questionOpacity.value = withDelay(3000, withTiming(1, { duration: 1000 }));

    // 4.5-6s: Fact counter animation
    factOpacity.value = withDelay(4500, withTiming(1, { duration: 300 }));
    counterValue.value = withDelay(4800, withTiming(40, { duration: 1200 }));
    trashIconRotation.value = withDelay(4500, withTiming(15, { duration: 300 }));

    // 6-7.5s: Impact sweep
    sweepOpacity.value = withDelay(6000, withTiming(1, { duration: 200 }));
    sweepX.value = withDelay(6000, withTiming(screenWidth, { duration: 1500 }));
    impactOpacity.value = withDelay(6200, withTiming(1, { duration: 800 }));

    // 7.5-8s: Call to action pulse (loops)
    callToActionOpacity.value = withDelay(7500, withTiming(1, { duration: 500 }));
    
    const startPulse = () => {
      callToActionScale.value = withSequence(
        withTiming(1.05, { duration: 800 }),
        withTiming(0.95, { duration: 800 }),
        withTiming(1, { duration: 800, easing: Easing.out(Easing.quad) })
      );
      // Loop the pulse animation
      setTimeout(startPulse, 2400);
    };
    
    setTimeout(startPulse, 7500);
  }, []);

  // Animated styles
  const fadeInStyle = useAnimatedStyle(() => ({
    opacity: fadeIn.value,
  }));

  const logoStyle = useAnimatedStyle(() => ({
    opacity: logoFillProgress.value,
    transform: [{ scale: interpolate(logoDrawProgress.value, [0, 1], [0.8, 1]) }],
  }));

  const taglineStyle = useAnimatedStyle(() => ({
    opacity: taglineOpacity.value,
    transform: [{ translateY: taglineY.value }],
  }));

  const questionStyle = useAnimatedStyle(() => ({
    opacity: questionOpacity.value,
    transform: [{ scale: questionScale.value }],
  }));

  const factStyle = useAnimatedStyle(() => ({
    opacity: factOpacity.value,
  }));

  const counterStyle = useAnimatedStyle(() => ({
    opacity: factOpacity.value,
  }));

  const trashStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${trashIconRotation.value}deg` }],
  }));

  const sweepStyle = useAnimatedStyle(() => ({
    opacity: sweepOpacity.value,
    transform: [{ translateX: sweepX.value }],
  }));

  const impactStyle = useAnimatedStyle(() => ({
    opacity: impactOpacity.value,
  }));

  const callToActionStyle = useAnimatedStyle(() => ({
    opacity: callToActionOpacity.value,
    transform: [{ scale: callToActionScale.value }],
  }));

  const handlePress = () => {
    onFinished();
  };

  // Simplified vegetable icons as SVG paths
  const CarrotIcon = () => (
    <Svg width="40" height="40" viewBox="0 0 100 100">
      <Path
        d="M50 10C45 10 40 15 35 25L25 50C20 70 30 85 50 90C70 85 80 70 75 50L65 25C60 15 55 10 50 10Z"
        fill={BRAND_GREEN}
      />
    </Svg>
  );

  const BroccoliIcon = () => (
    <Svg width="40" height="40" viewBox="0 0 100 100">
      <G>
        <Path
          d="M30 60C25 55 25 45 30 40C35 35 45 35 50 40C55 35 65 35 70 40C75 45 75 55 70 60C65 65 55 65 50 60C45 65 35 65 30 60Z"
          fill={BRAND_GREEN}
        />
        <Path
          d="M45 60L45 85C45 87 47 90 50 90C53 90 55 87 55 85L55 60"
          fill={BRAND_GREEN}
        />
      </G>
    </Svg>
  );

  const TomatoIcon = () => (
    <Svg width="40" height="40" viewBox="0 0 100 100">
      <Path
        d="M50 20C65 20 75 30 75 45C75 65 65 85 50 85C35 85 25 65 25 45C25 30 35 20 50 20Z"
        fill={BRAND_GREEN}
      />
    </Svg>
  );

  const TrashIcon = () => (
    <Svg width="60" height="60" viewBox="0 0 100 100">
      <Path
        d="M20 30L80 30L80 85C80 90 75 95 70 95L30 95C25 95 20 90 20 85L20 30Z M35 20L65 20L65 30L35 30L35 20Z"
        fill={BRAND_BLUE}
      />
    </Svg>
  );

  return (
    <View style={styles.container}>
      <StatusBar hidden />
      <LinearGradient
        colors={['#000000', '#0a0a0a']}
        style={styles.background}
      />
      
      <Animated.View style={[styles.content, fadeInStyle]}>
        {/* Logo Section */}
        <Animated.View style={[styles.logoSection, logoStyle]}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoText}>PrepSense</Text>
            <View style={styles.iconsContainer}>
              <View style={styles.iconWrapper}>
                <CarrotIcon />
              </View>
              <View style={styles.iconWrapper}>
                <BroccoliIcon />
              </View>
              <View style={styles.iconWrapper}>
                <TomatoIcon />
              </View>
            </View>
          </View>
        </Animated.View>

        {/* Tagline */}
        <Animated.View style={[styles.taglineContainer, taglineStyle]}>
          <Text style={styles.tagline}>Let's make every ingredient count</Text>
        </Animated.View>

        {/* Question */}
        <Animated.View style={[styles.questionContainer, questionStyle]}>
          <Text style={styles.question}>
            What if you could see your pantry,{'\n'}
            reduce waste, and plan better meals?
          </Text>
        </Animated.View>

        {/* Fact Section */}
        <Animated.View style={[styles.factContainer, factStyle]}>
          <Animated.View style={[styles.trashIconContainer, trashStyle]}>
            <TrashIcon />
          </Animated.View>
          <Animated.Text style={[styles.factPercentage, counterStyle]}>
            {Math.round(counterValue.value)}%
          </Animated.Text>
          <Text style={styles.factText}>of all food in the U.S. goes uneaten</Text>
        </Animated.View>

        {/* Sweep Effect */}
        <Animated.View style={[styles.sweepContainer, sweepStyle]}>
          <View style={styles.leafParticle} />
          <View style={[styles.leafParticle, { marginLeft: 20 }]} />
          <View style={[styles.leafParticle, { marginLeft: 40 }]} />
        </Animated.View>

        {/* Impact Message */}
        <Animated.View style={[styles.impactContainer, impactStyle]}>
          <Text style={styles.impactText}>
            PrepSense turns waste into savings,{'\n'}
            better food & climate impact.
          </Text>
        </Animated.View>

        {/* Call to Action */}
        <Animated.View style={styles.callToActionContainer}>
          <TouchableOpacity onPress={handlePress}>
            <Animated.View style={[styles.callToActionButton, callToActionStyle]}>
              <Text style={styles.callToActionText}>Press ⌘ ↵ to start</Text>
            </Animated.View>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  background: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoContainer: {
    alignItems: 'center',
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: BRAND_GREEN,
    textAlign: 'center',
    marginBottom: 20,
  },
  iconsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconWrapper: {
    marginHorizontal: 10,
  },
  taglineContainer: {
    marginBottom: 60,
  },
  tagline: {
    fontSize: 24,
    color: 'white',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  questionContainer: {
    marginBottom: 60,
  },
  question: {
    fontSize: 22,
    color: 'white',
    textAlign: 'center',
    lineHeight: 32,
  },
  factContainer: {
    alignItems: 'center',
    marginBottom: 60,
  },
  trashIconContainer: {
    marginBottom: 20,
  },
  factPercentage: {
    fontSize: 72,
    fontWeight: 'bold',
    color: BRAND_GREEN,
    marginBottom: 10,
  },
  factText: {
    fontSize: 18,
    color: 'white',
    textAlign: 'center',
  },
  sweepContainer: {
    position: 'absolute',
    top: '50%',
    left: -100,
    flexDirection: 'row',
    alignItems: 'center',
  },
  leafParticle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: BRAND_AVOCADO,
  },
  impactContainer: {
    marginBottom: 60,
  },
  impactText: {
    fontSize: 20,
    color: 'white',
    textAlign: 'center',
    lineHeight: 28,
  },
  callToActionContainer: {
    position: 'absolute',
    bottom: 80,
  },
  callToActionButton: {
    paddingHorizontal: 40,
    paddingVertical: 15,
    backgroundColor: BRAND_AVOCADO,
    borderRadius: 25,
  },
  callToActionText: {
    fontSize: 18,
    color: 'white',
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default IntroScreen;