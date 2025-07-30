import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import AnimatedFilterButton from './AnimatedFilterButton';

interface FilterItem {
  id: string;
  label: string;
  icon: string;
}

interface AccordionFilterSectionProps {
  title: string;
  filters: FilterItem[];
  selectedFilters: string[];
  onToggleFilter: (filterId: string) => void;
  isExpanded?: boolean;
  onToggle?: () => void;
  testID?: string;
}

const AccordionFilterSection: React.FC<AccordionFilterSectionProps> = ({
  title,
  filters,
  selectedFilters,
  onToggleFilter,
  isExpanded = false,
  onToggle,
  testID,
}) => {
  const heightProgress = useSharedValue(isExpanded ? 1 : 0);
  const rotationProgress = useSharedValue(isExpanded ? 1 : 0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(true);
    
    heightProgress.value = withSpring(isExpanded ? 1 : 0, {
      damping: 15,
      stiffness: 300,
    }, () => {
      runOnJS(setIsAnimating)(false);
    });
    
    rotationProgress.value = withTiming(isExpanded ? 1 : 0, {
      duration: 300,
    });
  }, [isExpanded]);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    height: interpolate(
      heightProgress.value,
      [0, 1],
      [0, 70] // Collapsed: 0px, Expanded: ~70px for one row of filters
    ),
    opacity: interpolate(
      heightProgress.value,
      [0, 0.3, 1],
      [0, 0.3, 1]
    ),
  }));

  const animatedIconStyle = useAnimatedStyle(() => ({
    transform: [{
      rotate: `${interpolate(rotationProgress.value, [0, 1], [0, 180])}deg`
    }],
  }));

  const handleToggle = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    onToggle?.();
  };

  const activeFiltersCount = selectedFilters.filter(id => 
    filters.some(filter => filter.id === id)
  ).length;

  return (
    <View style={styles.container} testID={testID}>
      {/* Header Row */}
      <TouchableOpacity
        style={styles.header}
        onPress={handleToggle}
        activeOpacity={0.7}
      >
        <View style={styles.headerContent}>
          <Text style={styles.title}>{title}</Text>
          {activeFiltersCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{activeFiltersCount}</Text>
            </View>
          )}
        </View>
        <Animated.View style={animatedIconStyle}>
          <Ionicons 
            name="chevron-down" 
            size={20} 
            color="#666" 
          />
        </Animated.View>
      </TouchableOpacity>

      {/* Expandable Content */}
      <Animated.View style={[styles.content, animatedContainerStyle]}>
        <ScrollView 
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterRow}
          style={styles.scrollView}
        >
          {filters.map((filter, index) => (
            <AnimatedFilterButton
              key={filter.id}
              testID={`${testID}-filter-${filter.id}`}
              label={filter.label}
              icon={filter.icon}
              isActive={selectedFilters.includes(filter.id)}
              onPress={() => onToggleFilter(filter.id)}
              index={index}
            />
          ))}
        </ScrollView>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 48,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginRight: 8,
  },
  badge: {
    backgroundColor: '#297A56',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    minWidth: 20,
    alignItems: 'center',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  content: {
    overflow: 'hidden',
  },
  scrollView: {
    flexGrow: 0,
  },
  filterRow: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
});

export default AccordionFilterSection;