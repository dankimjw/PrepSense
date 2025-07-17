// app/(tabs)/index.tsx - Part of the PrepSense mobile app
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, ActivityIndicator, RefreshControl, TouchableOpacity } from 'react-native';
import { useRouter, Stack, useFocusEffect, useLocalSearchParams } from 'expo-router';
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
import ConsumptionModal from '../../components/modals/ConsumptionModal';
import { ExpirationDateModal } from '../../components/modals/ExpirationDateModal';
import { PantryItemActionSheet } from '../../components/modals/PantryItemActionSheet';
import EditItemModal from '../../components/modals/EditItemModal';
import { deletePantryItem } from '../../services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const IndexScreen: React.FC = () => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFilterModalVisible, setIsFilterModalVisible] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [consumptionModalVisible, setConsumptionModalVisible] = useState(false);
  const [selectedItemForConsumption, setSelectedItemForConsumption] = useState<PantryItemData | null>(null);
  const [expirationModalVisible, setExpirationModalVisible] = useState(false);
  const [selectedItemForExpiration, setSelectedItemForExpiration] = useState<PantryItemData | null>(null);
  const [actionSheetVisible, setActionSheetVisible] = useState(false);
  const [selectedItemForAction, setSelectedItemForAction] = useState<PantryItemData | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedItemForEdit, setSelectedItemForEdit] = useState<PantryItemData | null>(null);
  
  // Hooks
  const { items, filters, updateFilters, fetchItems, isInitialized } = useItemsWithFilters();
  const router = useRouter();
  const params = useLocalSearchParams();
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

  // Handle item press - now opens consumption modal directly
  const handleItemPress = (item: PantryItemData) => {
    setSelectedItemForConsumption(item);
    setConsumptionModalVisible(true);
  };

  // Handle edit item
  const handleEditItem = (item: PantryItemData) => {
    setSelectedItemForAction(item);
    setActionSheetVisible(true);
  };

  // Handle update expiration date from action sheet
  const handleUpdateExpiration = () => {
    if (selectedItemForAction) {
      setSelectedItemForExpiration(selectedItemForAction);
      setExpirationModalVisible(true);
    }
  };

  // Handle consume item
  const handleConsumeItem = () => {
    if (selectedItemForAction) {
      setSelectedItemForConsumption(selectedItemForAction);
      setConsumptionModalVisible(true);
    }
  };

  // Handle edit item details
  const handleEditItemDetails = () => {
    if (selectedItemForAction) {
      router.push({
        pathname: '/edit-item',
        params: { 
          index: '0',
          data: enc([{
            ...selectedItemForAction,
            id: selectedItemForAction.id,
            item_name: selectedItemForAction.name,
            quantity_amount: selectedItemForAction.quantity_amount,
            quantity_unit: selectedItemForAction.quantity_unit,
            expected_expiration: selectedItemForAction.expirationDate.toISOString().split('T')[0],
            category: selectedItemForAction.category,
            count: selectedItemForAction.count || 1
          }])
        }
      });
    }
  };

  // Handle delete item
  const handleDeleteItem = async () => {
    if (selectedItemForAction) {
      Alert.alert(
        'Delete Item',
        `Are you sure you want to delete ${selectedItemForAction.name}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: async () => {
              try {
                await deletePantryItem(selectedItemForAction.id);
                Alert.alert('Success', 'Item deleted successfully');
                fetchItems();
              } catch (error) {
                console.error('Error deleting item:', error);
                Alert.alert('Error', 'Failed to delete item');
              }
            },
          },
        ]
      );
    }
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
              title="PrepSense"
              showBackButton={false}
              showAIBulkEditButton={true}
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
      
      {/* Quick Test Filter Toggle */}
      <TouchableOpacity
        style={[
          styles.testFilterToggle,
          filters.selectedCategories.includes('Test') && styles.testFilterToggleActive
        ]}
        onPress={() => {
          const isTestSelected = filters.selectedCategories.includes('Test');
          updateFilters({
            selectedCategories: isTestSelected ? [] : ['Test']
          });
        }}
      >
        <MaterialCommunityIcons 
          name="test-tube" 
          size={20} 
          color={filters.selectedCategories.includes('Test') ? '#fff' : '#297A56'} 
        />
        <Text style={[
          styles.testFilterText,
          filters.selectedCategories.includes('Test') && styles.testFilterTextActive
        ]}>
          {filters.selectedCategories.includes('Test') ? 'Showing Test Items' : 'Show Test Items Only'}
        </Text>
      </TouchableOpacity>
      
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
          onEditPress={handleEditItem}
        />

        {/* Tips Section */}
        <TipCard
          text="Store bananas separately from other fruits to prevent them from ripening too quickly."
        />
      </ScrollView>

      {/* Consumption Modal */}
      <ConsumptionModal
        visible={consumptionModalVisible}
        item={selectedItemForConsumption}
        onClose={() => {
          setConsumptionModalVisible(false);
          setSelectedItemForConsumption(null);
        }}
        onExpirationPress={() => {
          if (selectedItemForConsumption) {
            setSelectedItemForExpiration(selectedItemForConsumption);
            setConsumptionModalVisible(false); // Close consumption modal first
            setTimeout(() => {
              setExpirationModalVisible(true); // Then open expiration modal
            }, 300);
          }
        }}
        onEditPress={() => {
          if (selectedItemForConsumption) {
            setSelectedItemForEdit(selectedItemForConsumption);
            setConsumptionModalVisible(false);
            setTimeout(() => {
              setEditModalVisible(true);
            }, 300);
          }
        }}
      />

      {/* Action Sheet */}
      <PantryItemActionSheet
        visible={actionSheetVisible}
        item={selectedItemForAction}
        onClose={() => {
          setActionSheetVisible(false);
          setSelectedItemForAction(null);
        }}
        onUpdateExpiration={handleUpdateExpiration}
        onEditItem={handleEditItemDetails}
        onConsumeItem={handleConsumeItem}
        onDeleteItem={handleDeleteItem}
      />

      {/* Expiration Date Modal */}
      <ExpirationDateModal
        visible={expirationModalVisible}
        item={selectedItemForExpiration}
        onClose={() => {
          setExpirationModalVisible(false);
          setSelectedItemForExpiration(null);
          // Reopen consumption modal if we came from it
          if (selectedItemForConsumption) {
            setTimeout(() => {
              setConsumptionModalVisible(true);
            }, 300);
          }
        }}
        onUpdate={(newDate: Date) => {
          // Optimistically update the local state
          if (selectedItemForConsumption) {
            const updatedExpiry = formatExpirationDate(newDate.toISOString());
            const updatedDaysUntilExpiry = calculateDaysUntilExpiry(newDate.toISOString());
            
            // Update the consumption modal item with new expiration data
            setSelectedItemForConsumption({
              ...selectedItemForConsumption,
              expirationDate: newDate,
              expected_expiration: newDate.toISOString(),
              expiry: updatedExpiry,
              daysUntilExpiry: updatedDaysUntilExpiry
            });
          }
          
          // Fetch items in the background to sync with server
          fetchItems();
          setExpirationModalVisible(false);
          setSelectedItemForExpiration(null);
          
          // Reopen consumption modal after update
          if (selectedItemForConsumption) {
            setTimeout(() => {
              setConsumptionModalVisible(true);
            }, 300);
          }
        }}
      />

      {/* Edit Item Modal */}
      <EditItemModal
        visible={editModalVisible}
        item={selectedItemForEdit}
        onClose={() => {
          setEditModalVisible(false);
          setSelectedItemForEdit(null);
          // Reopen consumption modal if we came from it
          if (selectedItemForConsumption) {
            setTimeout(() => {
              setConsumptionModalVisible(true);
            }, 300);
          }
        }}
        onUpdate={(updatedItem) => {
          // Update the consumption modal item with new data
          if (selectedItemForConsumption) {
            setSelectedItemForConsumption({
              ...selectedItemForConsumption,
              ...updatedItem,
              name: updatedItem.item_name || updatedItem.name,
            });
          }
          // Fetch items in the background to sync with server
          fetchItems();
        }}
      />

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
  testFilterToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    marginHorizontal: 16,
    marginVertical: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  testFilterToggleActive: {
    backgroundColor: '#297A56',
    borderColor: '#297A56',
  },
  testFilterText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '500',
    color: '#297A56',
  },
  testFilterTextActive: {
    color: '#fff',
  },
});