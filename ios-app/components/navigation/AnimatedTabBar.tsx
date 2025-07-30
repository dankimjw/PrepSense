import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { usePathname } from 'expo-router';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface TabConfig {
  name: string;
  icon: string;
  label: string;
  route: string;
}

const tabs: TabConfig[] = [
  { name: 'home', icon: 'home-outline', label: 'Pantry', route: '/(tabs)' },
  { name: 'recipes', icon: 'restaurant-outline', label: 'Recipes', route: '/(tabs)/recipes' },
  { name: 'chat', icon: 'chatbubble-outline', label: 'Chat', route: '/(tabs)/chat' },
  { name: 'stats', icon: 'bar-chart-outline', label: 'Stats', route: '/(tabs)/stats' },
  { name: 'profile', icon: 'person-outline', label: 'Profile', route: '/(tabs)/profile' },
];

const TAB_WIDTH = SCREEN_WIDTH / tabs.length;

interface AnimatedTabBarProps {
  onTabPress: (route: string) => void;
}

export const AnimatedTabBar: React.FC<AnimatedTabBarProps> = ({ onTabPress }) => {
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const indicatorPosition = useSharedValue(0);
  
  // Find current tab index
  const currentTabIndex = tabs.findIndex(tab => pathname.startsWith(tab.route));
  
  useEffect(() => {
    if (currentTabIndex !== -1) {
      indicatorPosition.value = withSpring(currentTabIndex * TAB_WIDTH, {
        damping: 15,
        stiffness: 150,
        mass: 1,
      });
    }
  }, [currentTabIndex]);

  const indicatorStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: indicatorPosition.value }],
  }));

  const handleTabPress = (index: number, route: string) => {
    'worklet';
    indicatorPosition.value = withSpring(index * TAB_WIDTH, {
      damping: 15,
      stiffness: 150,
      mass: 1,
    });
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    runOnJS(onTabPress)(route);
  };

  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      {/* Animated indicator */}
      <Animated.View style={[styles.indicator, indicatorStyle]} />
      
      {/* Tab items */}
      <View style={styles.tabsContainer}>
        {tabs.map((tab, index) => (
          <TabItem
            key={tab.name}
            tab={tab}
            index={index}
            isActive={currentTabIndex === index}
            onPress={() => handleTabPress(index, tab.route)}
          />
        ))}
      </View>
    </View>
  );
};

interface TabItemProps {
  tab: TabConfig;
  index: number;
  isActive: boolean;
  onPress: () => void;
}

const TabItem: React.FC<TabItemProps> = ({ tab, index, isActive, onPress }) => {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(isActive ? 1 : 0.6);
  const translateY = useSharedValue(0);

  useEffect(() => {
    opacity.value = withTiming(isActive ? 1 : 0.6, { duration: 200 });
    translateY.value = withSpring(isActive ? -2 : 0, {
      damping: 15,
      stiffness: 150,
    });
  }, [isActive]);

  const animatedIconStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { translateY: translateY.value },
    ],
    opacity: opacity.value,
  }));

  const animatedTextStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ scale: interpolate(opacity.value, [0.6, 1], [0.9, 1]) }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9, {
      damping: 15,
      stiffness: 200,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 200,
    });
  };

  return (
    <TouchableOpacity
      style={styles.tab}
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Animated.View style={animatedIconStyle}>
        <Ionicons
          name={isActive ? tab.icon.replace('-outline', '') : tab.icon}
          size={24}
          color={isActive ? '#297A56' : '#666'}
        />
      </Animated.View>
      <Animated.Text style={[styles.tabLabel, animatedTextStyle, isActive && styles.activeLabel]}>
        {tab.label}
      </Animated.Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    position: 'relative',
  },
  tabsContainer: {
    flexDirection: 'row',
    height: 60,
  },
  indicator: {
    position: 'absolute',
    top: 0,
    width: TAB_WIDTH,
    height: 3,
    backgroundColor: '#297A56',
    borderRadius: 1.5,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 8,
  },
  tabLabel: {
    fontSize: 11,
    marginTop: 4,
    color: '#666',
  },
  activeLabel: {
    color: '#297A56',
    fontWeight: '600',
  },
});