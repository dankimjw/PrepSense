// app/(tabs)/index.tsx - Part of the PrepSense mobile app
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { TabScreenTransition } from '../../components/navigation/TabScreenTransition';
import { View, Text, StyleSheet, ScrollView, Alert, ActivityIndicator, RefreshControl, TouchableOpacity, NativeScrollEvent, NativeSyntheticEvent } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  interpolate,
  runOnJS
} from 'react-native-reanimated';
import { useRouter, Stack, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { CustomHeader } from '../components/CustomHeader';
import { SearchBar } from '../../components/SearchBar';
import { FilterModal } from '../../components/FilterModal';
import { QuickActions } from '../../components/home/QuickActions';
import { PantryItemsList } from '../../components/home/PantryItemsList';
import { SortFilterBar } from '../../components/home/SortFilterBar';
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
import { normalizeCategoryLabel } from '../../utils/categoryConfig';
import { ExpirationDateModal } from '../../components/modals/ExpirationDateModal';
import { PantryItemActionSheet } from '../../components/modals/PantryItemActionSheet';
import EditItemModal from '../../components/modals/EditItemModal';
import { deletePantryItem } from '../../services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import WasteImpactCard from '../../components/WasteImpactCard';
// import { useSupplyChainImpact } from '../../hooks/useSupplyChainImpact'; // Disabled for demo

const AnimatedTouchableOpacity = Animated.createAnimatedComponent(TouchableOpacity);

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
  const [showScrollToTop, setShowScrollToTop] = useState(false);
  
  // Refs and animated values
  const scrollViewRef = useRef<ScrollView>(null);
  const scrollY = useSharedValue(0);
  const fabOpacity = useSharedValue(0);
  const fabScale = useSharedValue(0.8);
  
  // Hooks
  const { items, filters, updateFilters, fetchItems, isInitialized } = useItemsWithFilters();
  // const { todayImpact } = useSupplyChainImpact('demo_user'); // Disabled for demo
  const todayImpact = null; // Disabled for demo
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
        category: normalizeCategoryLabel(item.category || ''),
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

  // Smart refresh when screen comes into focus - only if data is stale
  useFocusEffect(
    useCallback(() => {
      if (!isLoading && isInitialized) {
        // Let the PantryDataContext handle the smart refresh logic
        // It will only fetch if data is stale or needs refresh
        fetchItems(false).catch(console.error);
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
    sortBy: 'name' | 'expiry' | 'category' | 'dateAdded'; 
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

  // Handle edit item (from more button)
  const handleEditItem = (item: PantryItemData) => {
    setSelectedItemForAction(item);
    setActionSheetVisible(true);
  };

  // Handle swipe edit item (direct to edit modal)
  const handleSwipeEditItem = (item: PantryItemData) => {
    setSelectedItemForEdit(item);
    setEditModalVisible(true);
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

  // Handle swipe delete item (without confirmation)
  const handleSwipeDelete = async (item: PantryItemData) => {
    try {
      await deletePantryItem(item.id);
      // Refresh the items list
      fetchItems();
    } catch (error) {
      console.error('Error deleting item:', error);
      Alert.alert('Error', 'Failed to delete item');
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
    <TabScreenTransition routeName="index" transitionStyle="slideUp">
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
      
      {/* Sort Filter Bar */}
      <SortFilterBar
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
        onSortChange={(sortBy) => updateFilters({ sortBy })}
        onSortOrderToggle={() => updateFilters({ sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc' })}
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
        ref={scrollViewRef}
        style={styles.scrollView} 
        showsVerticalScrollIndicator={false}
        onScroll={(event: NativeSyntheticEvent<NativeScrollEvent>) => {
          const offsetY = event.nativeEvent.contentOffset.y;
          scrollY.value = offsetY;
          
          // Show button when scrolled down more than 200 pixels
          const shouldShow = offsetY > 200;
          if (shouldShow !== showScrollToTop) {
            setShowScrollToTop(shouldShow);
            fabOpacity.value = withSpring(shouldShow ? 1 : 0);
            fabScale.value = withSpring(shouldShow ? 1 : 0.8);
          }
        }}
        scrollEventThrottle={16}
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

        {/* Supply Chain Impact Alert */}
        {todayImpact && todayImpact.items_at_risk > 0 && (
          <WasteImpactCard
            expiringItems={todayImpact.items.map(item => ({
              name: item.name,
              daysLeft: item.daysLeft,
              quantity: item.quantity,
              unit: item.unit
            }))}
            onPress={() => router.push('/supply-chain-impact')}
          />
        )}

        {/* Pantry Items */}
        <PantryItemsList
          items={recentItems}
          onItemPress={handleItemPress}
          onEditPress={handleEditItem}
          onSwipeEdit={handleSwipeEditItem}
          onDelete={handleSwipeDelete}
        />

        {/* Tips Section */}
        <TouchableOpacity
          onLongPress={() => {
            if (__DEV__) {
              // @ts-ignore
              if (global.showIntroAnimation) {
                // @ts-ignore
                global.showIntroAnimation();
              }
            }
          }}
          activeOpacity={1}
          delayLongPress={800}
        >
          <TipCard
            text="Store bananas separately from other fruits to prevent them from ripening too quickly."
          />
        </TouchableOpacity>
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

      {/* Animated Scroll to Top Button */}
      <AnimatedScrollToTop
        fabOpacity={fabOpacity}
        fabScale={fabScale}
        onPress={() => {
          scrollViewRef.current?.scrollTo({ x: 0, y: 0, animated: true });
          // Hide button after scrolling
          setTimeout(() => {
            setShowScrollToTop(false);
            fabOpacity.value = withSpring(0);
            fabScale.value = withSpring(0.8);
          }, 300);
        }}
        />

      </View>
    </TabScreenTransition>
  );
};

// Animated Scroll to Top Button Component
const AnimatedScrollToTop = ({ 
  fabOpacity, 
  fabScale, 
  onPress 
}: { 
  fabOpacity: any; 
  fabScale: any; 
  onPress: () => void;
}) => {
  const animatedStyle = useAnimatedStyle(() => ({
    opacity: fabOpacity.value,
    transform: [
      { scale: fabScale.value },
      { translateY: interpolate(fabOpacity.value, [0, 1], [50, 0]) }
    ],
    // Hide from touch events when not visible
    pointerEvents: fabOpacity.value > 0 ? 'auto' : 'none' as any,
  }));

  return (
    <AnimatedTouchableOpacity
      style={[styles.scrollToTopButton, animatedStyle]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <Ionicons name="arrow-up" size={24} color="#fff" />
    </AnimatedTouchableOpacity>
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
  scrollToTopButton: {
    position: 'absolute',
    bottom: 90,
    left: 20,  // Changed from right to left to avoid conflicts
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#297A56',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  demoButton: {
    position: 'absolute',
    bottom: 90,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#5BA041',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  demoButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
});