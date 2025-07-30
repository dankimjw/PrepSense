import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import Animated from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import AnimatedFilterButton from './AnimatedFilterButton';

const AnimatedPressable = Animated.createAnimatedComponent(TouchableOpacity);

interface FilterItem {
  id: string;
  label: string;
  icon: string;
}

interface AccordionSection {
  id: string;
  title: string;
  filters: FilterItem[];
  color: string;
}

interface FlexGrowAccordionProps {
  sections: AccordionSection[];
  selectedFilters: string[];
  onToggleFilter: (filterId: string) => void;
  testID?: string;
}

const FlexGrowAccordion: React.FC<FlexGrowAccordionProps> = ({
  sections,
  selectedFilters,
  onToggleFilter,
  testID,
}) => {
  const [expandedId, setExpandedId] = useState(0);

  const handleSectionPress = (index: number) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setExpandedId(index);
  };

  const getActiveFiltersCount = (filters: FilterItem[]) => {
    return selectedFilters.filter(id => 
      filters.some(filter => filter.id === id)
    ).length;
  };

  return (
    <View style={styles.container} testID={testID}>
      {sections.map((section, index) => {
        const isExpanded = index === expandedId;
        const activeCount = getActiveFiltersCount(section.filters);

        return (
          <AnimatedPressable
            key={section.id}
            onPress={() => handleSectionPress(index)}
            style={[
              styles.section,
              {
                backgroundColor: section.color,
                flexGrow: isExpanded ? 3 : 1,
                // @ts-ignore - React Native Reanimated CSS transition
                transitionProperty: 'flexGrow',
                transitionDuration: 250,
              },
            ]}
          >
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.headerContent}>
                <Text style={styles.title}>{section.title}</Text>
                {activeCount > 0 && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{activeCount}</Text>
                  </View>
                )}
              </View>
              <Ionicons 
                name={isExpanded ? "chevron-up" : "chevron-down"} 
                size={20} 
                color="#fff" 
              />
            </View>

            {/* Expanded Content */}
            {isExpanded && (
              <View style={styles.expandedContent}>
                <ScrollView 
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.filtersContainer}
                >
                  {section.filters.map((filter, filterIndex) => (
                    <View key={filter.id} style={styles.filterWrapper}>
                      <AnimatedFilterButton
                        testID={`${testID}-${section.id}-filter-${filter.id}`}
                        label={filter.label}
                        icon={filter.icon}
                        isActive={selectedFilters.includes(filter.id)}
                        onPress={() => onToggleFilter(filter.id)}
                        index={filterIndex}
                      />
                    </View>
                  ))}
                </ScrollView>
              </View>
            )}
          </AnimatedPressable>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    height: 70,
    marginHorizontal: 16,
    marginVertical: 6,
    gap: 6,
  },
  section: {
    borderRadius: 12,
    overflow: 'hidden',
    justifyContent: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 10,
    minHeight: 44,
  },
  headerContent: {
    flexDirection: 'column',
    alignItems: 'flex-start',
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
    textShadowColor: 'rgba(0,0,0,0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 1,
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    minWidth: 20,
    alignItems: 'center',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  expandedContent: {
    flex: 1,
    paddingHorizontal: 8,
    paddingBottom: 16,
  },
  filtersContainer: {
    paddingHorizontal: 8,
  },
  filterWrapper: {
    marginRight: 8,
  },
});

export default FlexGrowAccordion;