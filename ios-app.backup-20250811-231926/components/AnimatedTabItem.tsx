import React, { useEffect } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface AnimatedTabItemProps {
  route: any;
  isFocused: boolean;
  onPress: () => void;
  iconName: keyof typeof Ionicons.glyphMap;
  label: string;
}

const AnimatedTabItem: React.FC<AnimatedTabItemProps> = ({
  route,
  isFocused,
  onPress,
  iconName,
  label,
}) => {
  const scale = useSharedValue(1);
  const iconScale = useSharedValue(isFocused ? 1.1 : 1);
  const opacity = useSharedValue(isFocused ? 1 : 0.6);

  useEffect(() => {
    iconScale.value = withSpring(isFocused ? 1.1 : 1, {
      damping: 15,
      stiffness: 200,
    });
    opacity.value = withTiming(isFocused ? 1 : 0.6, {
      duration: 200,
    });
  }, [isFocused]);

  const animatedIconStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value * iconScale.value },
    ],
    opacity: opacity.value,
  }));

  const animatedLabelStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [
      { scale: interpolate(opacity.value, [0.6, 1], [0.9, 1]) },
    ],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9, {
      damping: 15,
      stiffness: 300,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 300,
    });
  };

  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onPress();
  };

  return (
    <TouchableOpacity
      key={route.key}
      accessibilityRole="button"
      accessibilityState={isFocused ? { selected: true } : {}}
      style={styles.tab}
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={animatedIconStyle}>
        <Ionicons 
          name={iconName} 
          size={24} 
          color={isFocused ? '#297A56' : '#888'} 
        />
      </Animated.View>
      <Animated.Text style={[styles.label, animatedLabelStyle, isFocused && styles.activeLabel]}>
        {label}
      </Animated.Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    paddingBottom: 8,
    maxWidth: 80,
    overflow: 'hidden',
  },
  label: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  activeLabel: {
    color: '#297A56',
    fontWeight: '600',
  },
});

export default AnimatedTabItem;