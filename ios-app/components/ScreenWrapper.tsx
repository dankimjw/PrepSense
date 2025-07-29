import React, { memo, useEffect, useState } from 'react';
import { View, StyleSheet, InteractionManager } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import { useScreenAnimation } from '../hooks/useScreenAnimation';
import { useComponentPerformance } from '../utils/performanceMonitoring';

interface ScreenWrapperProps {
  children: React.ReactNode;
  style?: any;
  enableAnimation?: boolean;
  deferContent?: boolean;
}

const ScreenWrapper: React.FC<ScreenWrapperProps> = memo(({
  children,
  style,
  enableAnimation = true,
  deferContent = false,
}) => {
  const [contentReady, setContentReady] = useState(!deferContent);
  const animatedStyle = useScreenAnimation();
  
  // Track component performance
  useComponentPerformance('ScreenWrapper');

  useEffect(() => {
    if (deferContent && !contentReady) {
      const handle = InteractionManager.runAfterInteractions(() => {
        setContentReady(true);
      });
      
      return () => handle.cancel();
    }
  }, [deferContent, contentReady]);

  if (!contentReady) {
    return <View style={[styles.container, style]} />;
  }

  if (!enableAnimation) {
    return (
      <View style={[styles.container, style]}>
        {children}
      </View>
    );
  }

  return (
    <Animated.View 
      style={[styles.container, animatedStyle, style]}
      entering={FadeIn.duration(200)}
      exiting={FadeOut.duration(150)}
    >
      {children}
    </Animated.View>
  );
});

ScreenWrapper.displayName = 'ScreenWrapper';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});

export default ScreenWrapper;