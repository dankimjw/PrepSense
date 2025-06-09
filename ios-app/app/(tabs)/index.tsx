// app/(tabs)/index.tsx - Part of the PrepSense mobile app
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, ActivityIndicator, RefreshControl, TouchableOpacity } from 'react-native';
import { useRouter, Stack, useFocusEffect } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { CustomHeader } from '../components/CustomHeader';
import { SearchBar } from '../../components/SearchBar';
import { FilterModal } from '../../components/FilterModal';
import { QuickActions } from '../../components/home/QuickActions';
import { PantryItemsList } from '../../components/home/PantryItemsList';
import { TipCard } from '../../components/home/TipCard';
import { useItemsWithFilters } from '../../hooks/useItemsWithFilters';
import { 
  getItemStyle, 
  formatExpirationDate, 
  calculateDaysUntilExpiry,
  groupItems 
} from '../../utils/itemHelpers';
import { enc } from '../../utils/encoding';
import type { PantryItemData } from '../../components/home/PantryItem';

const IndexScreen: React.FC = () => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFilterModalVisible, setIsFilterModalVisible] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Hooks
  const { items, filters, updateFilters, fetchItems, isInitialized } = useItemsWithFilters();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  // Transform items for display
  const recentItems = React.useMemo(() => {
    // Format each item with its styles and metadata
    const formattedItems = items.map(item => {
      const expirationDate = item.expected_expiration || new Date().toISOString();
      const itemStyle = getItemStyle({
        name: item.item_name,
        unit: item.quantity_unit,
        category: item.category
      });
      
      return {
        id: item.id,
        item_name: item.item_name?.trim() || 'Unnamed Item',
        name: item.item_name?.trim() || 'Unnamed Item',
        expiry: formatExpirationDate(expirationDate),
        category: item.category || 'Uncategorized',
        quantity_amount: item.quantity_amount || 0,
        quantity_unit: (item.quantity_unit || 'each').trim(),
        expected_expiration: expirationDate,
        expirationDate: new Date(expirationDate),
        daysUntilExpiry: calculateDaysUntilExpiry(expirationDate),
        ...itemStyle
      } as PantryItemData;
    });
    
    // Group items by name and unit
    return groupItems(formattedItems);
  }, [items]);

  // Fetch items when the component mounts
  useEffect(() => {
    let isMounted = true;
    
    const loadItems = async () => {
      try {
        if (isMounted) {
          setIsLoading(true);
          setError(null);
        }
        
        await fetchItems();
        
        if (isMounted) {
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Failed to load items:', err);
        if (isMounted) {
          setError('Failed to load pantry items. Please try again.');
          setIsLoading(false);
        }
      }
    };

    if (!isInitialized) {
      loadItems();
    } else if (isMounted) {
      setIsLoading(false);
    }
    
    return () => {
      isMounted = false;
    };
  }, [fetchItems, isInitialized]);

  // Refresh when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      if (!isLoading && isInitialized) {
        fetchItems().catch(console.error);
      }
    }, [isLoading, isInitialized, fetchItems])
  );

  // Pull to refresh handler
  const onRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await fetchItems();
    } catch (error) {
      console.error('Error refreshing items:', error);
      Alert.alert('Error', 'Failed to refresh items');
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchItems]);

  // Handle filter apply
  const handleFilterApply = (filterData: { 
    categories: string[]; 
    sortBy: 'name' | 'expiry' | 'category'; 
    sortOrder: 'asc' | 'desc' 
  }) => {
    updateFilters({
      selectedCategories: filterData.categories,
      sortBy: filterData.sortBy,
      sortOrder: filterData.sortOrder,
    });
    setIsFilterModalVisible(false);
  };

  // Handle item press
  const handleItemPress = (item: PantryItemData) => {
    router.push({
      pathname: '/edit-item',
      params: { 
        index: '0',
        data: enc([{
          ...item,
          id: item.id,
          item_name: item.name,
          quantity_amount: item.quantity_amount,
          quantity_unit: item.quantity_unit,
          expected_expiration: item.expirationDate.toISOString().split('T')[0],
          category: item.category,
          count: item.count || 1
        }])
      }
    });
  };

  // Reset filters function
  const resetFilters = () => {
    updateFilters({
      searchQuery: '',
      selectedCategories: [],
    });
  };

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          header: () => (
            <CustomHeader 
              title="Home"
              showBackButton={false}
              showChatButton={true}
              showAdminButton={true}
            />
          )
        }}
      />
      
      {/* Search, Filter, and Sort Bar */}
      <SearchBar
        searchQuery={filters.searchQuery}
        onSearch={(query) => updateFilters({ searchQuery: query })}
        onFilterPress={() => setIsFilterModalVisible(true)}
        onSortPress={() => {
          updateFilters({ sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc' });
        }}
      />
      
      {/* Filter Modal */}
      <FilterModal
        visible={isFilterModalVisible}
        onClose={() => setIsFilterModalVisible(false)}
        onApply={handleFilterApply}
        selectedCategories={filters.selectedCategories}
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
      />
      
      {/* Active Filters */}
      {(filters.searchQuery || filters.selectedCategories.length > 0) && (
        <View style={styles.activeFiltersContainer}>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.activeFiltersScroll}
          >
            {filters.searchQuery && (
              <View style={styles.activeFilter}>
                <Text style={styles.activeFilterText}>Search: {filters.searchQuery}</Text>
                <TouchableOpacity 
                  onPress={() => updateFilters({ searchQuery: '' })}
                  style={styles.removeFilterButton}
                >
                  <Ionicons name="close" size={14} color="#6B7280" />
                </TouchableOpacity>
              </View>
            )}
            {filters.selectedCategories.map(category => (
              <View key={category} style={styles.activeFilter}>
                <Text style={styles.activeFilterText}>{category}</Text>
                <TouchableOpacity 
                  onPress={() => updateFilters({ 
                    selectedCategories: filters.selectedCategories.filter(c => c !== category) 
                  })}
                  style={styles.removeFilterButton}
                >
                  <Ionicons name="close" size={14} color="#6B7280" />
                </TouchableOpacity>
              </View>
            ))}
            {(filters.searchQuery || filters.selectedCategories.length > 0) && (
              <TouchableOpacity 
                onPress={resetFilters}
                style={styles.clearAllButton}
              >
                <Text style={styles.clearAllText}>Clear all</Text>
              </TouchableOpacity>
            )}
          </ScrollView>
        </View>
      )}

      <ScrollView 
        style={styles.scrollView} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={onRefresh}
            colors={['#297A56']}
            tintColor="#297A56"
          />
        }
      >
        {/* Quick Actions */}
        <QuickActions />

        {/* Pantry Items */}
        <PantryItemsList
          items={recentItems}
          onItemPress={handleItemPress}
        />

        {/* Tips Section */}
        <TipCard
          text="Store bananas separately from other fruits to prevent them from ripening too quickly."
        />
      </ScrollView>
    </View>
  );
};

export default IndexScreen;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    padding: 16,
  },
  activeFiltersContainer: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#F9FAFB',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  activeFiltersScroll: {
    paddingRight: 16,
  },
  activeFilter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E5F7EF',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  activeFilterText: {
    color: '#065F46',
    fontSize: 14,
    marginRight: 6,
  },
  removeFilterButton: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: 'rgba(6, 95, 70, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  clearAllButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    justifyContent: 'center',
  },
  clearAllText: {
    color: '#297A56',
    fontWeight: '500',
    fontSize: 14,
  },
});