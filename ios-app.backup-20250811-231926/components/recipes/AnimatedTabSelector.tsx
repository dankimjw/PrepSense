import React, { useEffect, useMemo } from 'react';
import { TouchableOpacity, View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

interface Tab {
  key: string;
  label: string;
}

interface AnimatedTabSelectorProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabKey: string) => void;
  testID?: string;
}

interface AnimatedTabProps {
  tab: Tab;
  index: number;
  isActive: boolean;
  tabScale: Animated.SharedValue<number>;
  onPress: () => void;
}

// Separate component for individual tabs to avoid calling hooks inside map callbacks
const AnimatedTab: React.FC<AnimatedTabProps> = ({ tab, index, isActive, tabScale, onPress }) => {
  const animatedTabStyle = useAnimatedStyle(() => ({
    transform: [{ scale: tabScale.value }],
  }));

  const animatedTextStyle = useAnimatedStyle(() => ({
    color: isActive ? '#297A56' : '#666',
    fontWeight: isActive ? '600' : '500',
  }));

  return (
    <TouchableOpacity
      testID={`tab-${tab.key}`}
      style={styles.tab}
      onPress={onPress}
      activeOpacity={1}
    >
      <Animated.View style={[styles.tabContent, animatedTabStyle]}>
        <Animated.Text style={[styles.tabText, animatedTextStyle]}>
          {tab.label}
        </Animated.Text>
      </Animated.View>
    </TouchableOpacity>
  );
};

const AnimatedTabSelector: React.FC<AnimatedTabSelectorProps> = ({
  tabs,
  activeTab,
  onTabChange,
  testID,
}) => {
  const activeIndex = tabs.findIndex(tab => tab.key === activeTab);
  const indicatorPosition = useSharedValue(activeIndex);
  
  // Create individual shared values for each tab - can't use hooks inside callbacks
  const tabScale0 = useSharedValue(1);
  const tabScale1 = useSharedValue(1);
  const tabScale2 = useSharedValue(1);
  const tabScale3 = useSharedValue(1);
  const tabScale4 = useSharedValue(1);
  
  // Create array of scales based on number of tabs (fallback to individual scales)
  const tabScales = useMemo(() => {
    const scales = [tabScale0, tabScale1, tabScale2, tabScale3, tabScale4];
    return scales.slice(0, tabs.length);
  }, [tabs.length, tabScale0, tabScale1, tabScale2, tabScale3, tabScale4]);

  useEffect(() => {
    const newIndex = tabs.findIndex(tab => tab.key === activeTab);
    indicatorPosition.value = withSpring(newIndex, {
      damping: 15,
      stiffness: 300,
    });
  }, [activeTab, tabs, indicatorPosition]);

  const indicatorStyle = useAnimatedStyle(() => {
    const tabWidth = 100 / tabs.length;
    const translateXPercent = indicatorPosition.value * tabWidth;
    
    return {
      transform: [
        {
          translateX: `${translateXPercent}%`
        }
      ],
      width: `${100 / tabs.length}%`,
    };
  });

  const handleTabPress = (tabKey: string, index: number) => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    
    // Animate pressed tab
    tabScales[index].value = withSpring(0.95, {
      damping: 15,
      stiffness: 400,
    }, () => {
      tabScales[index].value = withSpring(1, {
        damping: 15,
        stiffness: 400,
      });
    });

    onTabChange(tabKey);
  };

  return (
    <View style={styles.tabContainer} testID={testID}>
      {/* Active Tab Indicator */}
      <Animated.View 
        style={[
          styles.activeIndicator, 
          indicatorStyle
        ]} 
      />
      
      {/* Tab Buttons */}
      {tabs.map((tab, index) => (
        <AnimatedTab
          key={tab.key}
          tab={tab}
          index={index}
          isActive={tab.key === activeTab}
          tabScale={tabScales[index]}
          onPress={() => handleTabPress(tab.key, index)}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    position: 'relative',
  },
  activeIndicator: {
    position: 'absolute',
    bottom: 0,
    left: 16,
    right: 16,
    height: 3,
    backgroundColor: '#297A56',
    borderRadius: 1.5,
    zIndex: 1,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 16,
  },
  tabContent: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabText: {
    fontSize: 15,
  },
});

export default AnimatedTabSelector;