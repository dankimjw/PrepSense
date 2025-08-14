import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

type ActiveTab = 'pantry' | 'discover' | 'my-recipes';
type MyRecipesFilter = 'all' | 'thumbs_up' | 'thumbs_down' | 'favorites';
type MyRecipesTab = 'saved' | 'cooked';

interface RecipesFiltersProps {
  activeTab: ActiveTab;
  selectedFilters: string[];
  myRecipesFilter: MyRecipesFilter;
  myRecipesTab: MyRecipesTab;
  filtersCollapsed: boolean;
  onFiltersChange: (filters: string[]) => void;
  onMyRecipesFilterChange: (filter: MyRecipesFilter) => void;
  onMyRecipesTabChange: (tab: MyRecipesTab) => void;
  onFiltersCollapsedChange: (collapsed: boolean) => void;
}

const dietaryFilters = [
  { id: 'vegetarian', label: 'Vegetarian', icon: '🥗' },
  { id: 'vegan', label: 'Vegan', icon: '🌱' },
  { id: 'gluten-free', label: 'Gluten-Free', icon: '🌾' },
  { id: 'dairy-free', label: 'Dairy-Free', icon: '🥛' },
  { id: 'low-carb', label: 'Low Carb', icon: '🥖' },
  { id: 'keto', label: 'Keto', icon: '🥑' },
  { id: 'paleo', label: 'Paleo', icon: '🍖' },
  { id: 'mediterranean', label: 'Mediterranean', icon: '🫒' },
];

const cuisineFilters = [
  { id: 'italian', label: 'Italian', icon: '🍝' },
  { id: 'mexican', label: 'Mexican', icon: '🌮' },
  { id: 'asian', label: 'Asian', icon: '🥢' },
  { id: 'american', label: 'American', icon: '🍔' },
  { id: 'indian', label: 'Indian', icon: '🍛' },
  { id: 'french', label: 'French', icon: '🥐' },
  { id: 'japanese', label: 'Japanese', icon: '🍱' },
  { id: 'thai', label: 'Thai', icon: '🍜' },
];

const mealTypeFilters = [
  { id: 'breakfast', label: 'Breakfast', icon: '🍳' },
  { id: 'lunch', label: 'Lunch', icon: '🥪' },
  { id: 'dinner', label: 'Dinner', icon: '🍽️' },
  { id: 'snack', label: 'Snack', icon: '🍿' },
  { id: 'dessert', label: 'Dessert', icon: '🍰' },
  { id: 'appetizer', label: 'Appetizer', icon: '🥟' },
  { id: 'soup', label: 'Soup', icon: '🍲' },
  { id: 'salad', label: 'Salad', icon: '🥗' },
];

export default function RecipesFilters({
  activeTab,
  selectedFilters,
  myRecipesFilter,
  myRecipesTab,
  filtersCollapsed,
  onFiltersChange,
  onMyRecipesFilterChange,
  onMyRecipesTabChange,
  onFiltersCollapsedChange,
}: RecipesFiltersProps) {
  const filterHeight = useRef(new Animated.Value(1)).current;

  const toggleFilter = (filterId: string) => {
    const newFilters = selectedFilters.includes(filterId) 
      ? selectedFilters.filter(f => f !== filterId)
      : [...selectedFilters, filterId];
    onFiltersChange(newFilters);
  };

  const handleFilterCollapse = () => {
    if (filtersCollapsed) {
      onFiltersCollapsedChange(false);
      Animated.timing(filterHeight, {
        toValue: 1,
        duration: 300,
        useNativeDriver: false,
      }).start();
    }
  };

  // My Recipes Tab Filters
  if (activeTab === 'my-recipes') {
    return (
      <View style={styles.myRecipesTabContainer}>
        {/* Saved/Cooked Tabs */}
        <View testID="my-recipes-tabs" style={styles.myRecipesTabs}>
          <TouchableOpacity
            testID="saved-tab"
            style={[
              styles.myRecipesTab,
              myRecipesTab === 'saved' && styles.myRecipesTabActive
            ]}
            onPress={() => onMyRecipesTabChange('saved')}
          >
            <Text style={[
              styles.myRecipesTabText,
              myRecipesTab === 'saved' && styles.myRecipesTabTextActive
            ]}>
              🔖 Saved
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="cooked-tab"
            style={[
              styles.myRecipesTab,
              myRecipesTab === 'cooked' && styles.myRecipesTabActive
            ]}
            onPress={() => onMyRecipesTabChange('cooked')}
          >
            <Text style={[
              styles.myRecipesTabText,
              myRecipesTab === 'cooked' && styles.myRecipesTabTextActive
            ]}>
              🍳 Cooked
            </Text>
          </TouchableOpacity>
        </View>
        
        {/* Only show rating filters in Cooked tab */}
        {myRecipesTab === 'cooked' && (
          <View style={styles.filterContainer}>
            <ScrollView 
              horizontal
              style={styles.filterScrollView}
              contentContainerStyle={styles.filterContent}
              showsHorizontalScrollIndicator={false}
            >
              <TouchableOpacity
                testID="filter-all"
                style={[
                  styles.filterButton,
                  myRecipesFilter === 'all' && styles.filterButtonActive
                ]}
                onPress={() => onMyRecipesFilterChange('all')}
              >
                <Text style={styles.filterIcon}>📋</Text>
                <Text style={[
                  styles.filterText,
                  myRecipesFilter === 'all' && styles.filterTextActive
                ]}>
                  All
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                testID="filter-thumbs-up"
                style={[
                  styles.filterButton,
                  myRecipesFilter === 'thumbs_up' && styles.filterButtonActive
                ]}
                onPress={() => onMyRecipesFilterChange('thumbs_up')}
              >
                <Text style={styles.filterIcon}>👍</Text>
                <Text style={[
                  styles.filterText,
                  myRecipesFilter === 'thumbs_up' && styles.filterTextActive
                ]}>
                  Liked
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                testID="filter-thumbs-down"
                style={[
                  styles.filterButton,
                  myRecipesFilter === 'thumbs_down' && styles.filterButtonActive
                ]}
                onPress={() => onMyRecipesFilterChange('thumbs_down')}
              >
                <Text style={styles.filterIcon}>👎</Text>
                <Text style={[
                  styles.filterText,
                  myRecipesFilter === 'thumbs_down' && styles.filterTextActive
                ]}>
                  Disliked
                </Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        )}
      </View>
    );
  }

  // Discover Tab Filters (Collapsible)
  if (activeTab === 'discover') {
    return (
      <Animated.View 
        style={[
          styles.discoverFiltersContainer,
          {
            maxHeight: filterHeight.interpolate({
              inputRange: [0, 1],
              outputRange: [32, 150],
            }),
          }
        ]}
      >
        <TouchableOpacity 
          style={styles.collapsedFilterBar}
          onPress={handleFilterCollapse}
          activeOpacity={filtersCollapsed ? 0.7 : 1}
        >
          {selectedFilters.length > 0 && (
            <Text style={styles.collapsedFilterText}>
              {selectedFilters.length} filters active
            </Text>
          )}
          <Animated.View
            style={{
              transform: [{
                rotate: filterHeight.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0deg', '180deg'],
                })
              }]
            }}
          >
            <Ionicons name="chevron-down" size={20} color="#666" />
          </Animated.View>
        </TouchableOpacity>
        <Animated.View
          style={{
            opacity: filterHeight,
            transform: [{
              translateY: filterHeight.interpolate({
                inputRange: [0, 1],
                outputRange: [-20, 0],
              })
            }]
          }}
        >
        {/* Dietary Filters Row */}
        <View style={styles.filterRow}>
          <ScrollView 
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filterRowContent}
          >
            {dietaryFilters.map(filter => (
              <TouchableOpacity
                key={filter.id}
                testID={`dietary-filter-${filter.id}`}
                style={[
                  styles.filterButton,
                  selectedFilters.includes(filter.id) && styles.filterButtonActive
                ]}
                onPress={() => toggleFilter(filter.id)}
              >
                <Text style={styles.filterIcon}>{filter.icon}</Text>
                <Text style={[
                  styles.filterText,
                  selectedFilters.includes(filter.id) && styles.filterTextActive
                ]}>
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Cuisine Filters Row */}
        <View style={styles.filterRow}>
          <ScrollView 
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filterRowContent}
          >
            {cuisineFilters.map(filter => (
              <TouchableOpacity
                key={filter.id}
                testID={`cuisine-filter-${filter.id}`}
                style={[
                  styles.filterButton,
                  selectedFilters.includes(filter.id) && styles.filterButtonActive
                ]}
                onPress={() => toggleFilter(filter.id)}
              >
                <Text style={styles.filterIcon}>{filter.icon}</Text>
                <Text style={[
                  styles.filterText,
                  selectedFilters.includes(filter.id) && styles.filterTextActive
                ]}>
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Meal Type Filters Row */}
        <View style={styles.filterRow}>
          <ScrollView 
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filterRowContent}
          >
            {mealTypeFilters.map(filter => (
              <TouchableOpacity
                key={filter.id}
                testID={`meal-type-filter-${filter.id}`}
                style={[
                  styles.filterButton,
                  selectedFilters.includes(filter.id) && styles.filterButtonActive
                ]}
                onPress={() => toggleFilter(filter.id)}
              >
                <Text style={styles.filterIcon}>{filter.icon}</Text>
                <Text style={[
                  styles.filterText,
                  selectedFilters.includes(filter.id) && styles.filterTextActive
                ]}>
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
        </Animated.View>
      </Animated.View>
    );
  }

  // Pantry Tab Filters (Simple)
  if (activeTab === 'pantry') {
    return (
      <View style={styles.filterContainer}>
        <ScrollView 
          horizontal
          style={styles.filterScrollView}
          contentContainerStyle={styles.filterContent}
          showsHorizontalScrollIndicator={false}
        >
          {mealTypeFilters.slice(0, 4).map(filter => (
            <TouchableOpacity
              key={filter.id}
              testID={`pantry-filter-${filter.id}`}
              style={[
                styles.filterButton,
                selectedFilters.includes(filter.id) && styles.filterButtonActive
              ]}
              onPress={() => toggleFilter(filter.id)}
            >
              <Text style={styles.filterIcon}>{filter.icon}</Text>
              <Text style={[
                styles.filterText,
                selectedFilters.includes(filter.id) && styles.filterTextActive
              ]}>
                {filter.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  filterContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  myRecipesTabContainer: {
    backgroundColor: '#fff',
  },
  myRecipesTabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  myRecipesTab: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  myRecipesTabActive: {
    backgroundColor: '#297A56',
  },
  myRecipesTabText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  myRecipesTabTextActive: {
    color: '#fff',
  },
  discoverFiltersContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    overflow: 'hidden',
  },
  collapsedFilterBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    height: 32,
  },
  collapsedFilterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
    marginRight: 8,
  },
  filterRow: {
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  filterRowContent: {
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  filterScrollView: {
    flexGrow: 0,
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
    minWidth: 90,
    justifyContent: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#E6F7F0',
    borderWidth: 1,
    borderColor: '#297A56',
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  filterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#297A56',
  },
});