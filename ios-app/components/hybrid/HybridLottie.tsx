// Hybrid Lottie component with React Native Paper theming and NativeWind styling
import React, { useRef, useImperativeHandle, forwardRef } from 'react';
import { View, ViewStyle } from 'react-native';
import LottieView from 'lottie-react-native';
import { useTheme } from 'react-native-paper';
import { StyleDebugger } from '../../config/hybridProvider';
import { twMerge } from 'tailwind-merge';

interface HybridLottieProps {
  // Lottie source
  source: any;
  
  // NativeWind styling
  className?: string;
  containerClassName?: string;
  
  // Size
  size?: number;
  width?: number;
  height?: number;
  
  // Animation controls
  autoPlay?: boolean;
  loop?: boolean;
  speed?: number;
  
  // Callbacks
  onAnimationFinish?: () => void;
  onAnimationFailure?: (error: string) => void;
  onAnimationLoop?: () => void;
  
  // Theming
  useThemeColors?: boolean;
  colorFilters?: Array<{
    keypath: string;
    color: string;
  }>;
  
  // Style
  style?: ViewStyle;
  
  // Debug
  debugName?: string;
}

export interface HybridLottieRef {
  play: () => void;
  pause: () => void;
  reset: () => void;
}

// Helper function to enhance animations with smooth fades
const AnimationWrapper: React.FC<{ children: React.ReactNode; fadeIn?: boolean; fadeOut?: boolean; className?: string }> = ({ 
  children, 
  fadeIn = false, 
  fadeOut = false,
  className 
}) => {
  const fadeInClass = fadeIn ? 'animate-fade-in' : '';
  const fadeOutClass = fadeOut ? 'animate-fade-out' : '';
  
  return (
    <View className={twMerge(fadeInClass, fadeOutClass, className)}>
      {children}
    </View>
  );
};

export const HybridLottie = forwardRef<HybridLottieRef, HybridLottieProps>(({
  source,
  className,
  containerClassName,
  size = 200,
  width,
  height,
  autoPlay = true,
  loop = false,
  speed = 1,
  onAnimationFinish,
  onAnimationFailure,
  onAnimationLoop,
  useThemeColors = true,
  colorFilters,
  style,
  debugName = 'HybridLottie',
}, ref) => {
  const theme = useTheme();
  const lottieRef = useRef<LottieView>(null);
  
  // Debug performance
  const renderStart = __DEV__ ? StyleDebugger.performance.start(`${debugName}-render`) : 0;
  
  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    play: () => lottieRef.current?.play(),
    pause: () => lottieRef.current?.pause(),
    reset: () => lottieRef.current?.reset(),
  }));
  
  // Apply theme colors if enabled
  const themedColorFilters = useThemeColors && !colorFilters ? [
    {
      keypath: "**",
      color: theme.colors.primary,
    }
  ] : colorFilters;
  
  // Calculate dimensions
  const finalWidth = width || size;
  const finalHeight = height || size;
  
  if (__DEV__) {
    StyleDebugger.log(debugName, `size: ${finalWidth}x${finalHeight}, autoPlay: ${autoPlay}, loop: ${loop}`);
  }
  
  const renderContent = () => (
    <View className={twMerge('items-center justify-center', containerClassName)}>
      <LottieView
        ref={lottieRef}
        source={source}
        autoPlay={autoPlay}
        loop={loop}
        speed={speed}
        style={[
          {
            width: finalWidth,
            height: finalHeight,
          },
          style,
        ]}
        className={className}
        colorFilters={themedColorFilters}
        onAnimationFinish={onAnimationFinish}
        onAnimationFailure={onAnimationFailure}
        onAnimationLoop={onAnimationLoop}
        renderMode="SOFTWARE"
        cacheComposition={true}
        resizeMode="contain"
      />
    </View>
  );
  
  const content = renderContent();
  
  if (__DEV__) {
    StyleDebugger.performance.end(`${debugName}-render`, renderStart);
  }
  
  return content;
});

HybridLottie.displayName = 'HybridLottie';

// Preset animations with optimal settings
export const SuccessAnimation = forwardRef<HybridLottieRef, Omit<HybridLottieProps, 'source'>>((props, ref) => (
  <AnimationWrapper fadeIn className="shadow-lg">
    <HybridLottie
      ref={ref}
      source={require('../../assets/lottie/success-check.json')}
      size={120}
      loop={false}
      speed={1.2}
      debugName="SuccessAnimation"
      {...props}
    />
  </AnimationWrapper>
));

export const LoadingAnimation = forwardRef<HybridLottieRef, Omit<HybridLottieProps, 'source'>>((props, ref) => (
  <HybridLottie
    ref={ref}
    source={require('../../assets/lottie/loading-dots.json')}
    size={80}
    loop={true}
    speed={1.5}
    debugName="LoadingAnimation"
    {...props}
  />
));

export const EmptyStateAnimation = forwardRef<HybridLottieRef, Omit<HybridLottieProps, 'source'>>((props, ref) => (
  <AnimationWrapper fadeIn>
    <HybridLottie
      ref={ref}
      source={require('../../assets/lottie/empty-box.json')}
      size={160}
      loop={true}
      speed={0.8}
      debugName="EmptyStateAnimation"
      {...props}
    />
  </AnimationWrapper>
));

export const ErrorAnimation = forwardRef<HybridLottieRef, Omit<HybridLottieProps, 'source'>>((props, ref) => (
  <AnimationWrapper fadeIn className="shadow-lg">
    <HybridLottie
      ref={ref}
      source={require('../../assets/lottie/error-x.json')}
      size={120}
      loop={false}
      speed={1.3}
      debugName="ErrorAnimation"
      {...props}
    />
  </AnimationWrapper>
));

export const ScanningAnimation = forwardRef<HybridLottieRef, Omit<HybridLottieProps, 'source'>>((props, ref) => (
  <HybridLottie
    ref={ref}
    source={require('../../assets/lottie/scanning.json')}
    size={200}
    loop={true}
    speed={1.2}
    debugName="ScanningAnimation"
    {...props}
  />
));

// Hook for animation state management
export const useLottieAnimation = (autoReset = true, resetDelay = 3000) => {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const animationRef = useRef<HybridLottieRef>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  const play = React.useCallback(() => {
    setIsPlaying(true);
    animationRef.current?.play();
  }, []);
  
  const reset = React.useCallback(() => {
    setIsPlaying(false);
    animationRef.current?.reset();
  }, []);
  
  const handleFinish = React.useCallback(() => {
    if (autoReset) {
      timeoutRef.current = setTimeout(() => {
        reset();
      }, resetDelay);
    }
  }, [autoReset, resetDelay, reset]);
  
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
  return {
    ref: animationRef,
    isPlaying,
    play,
    reset,
    onAnimationFinish: handleFinish,
  };
};