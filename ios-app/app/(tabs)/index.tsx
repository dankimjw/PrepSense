// app/(tabs)/index.tsx - Part of the PrepSense mobile app
import React, { useMemo, useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Buffer } from 'buffer';
import { useItems } from '../../context/ItemsContext';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { SearchBar } from '../../components/SearchBar';
import { FilterModal } from '../../components/FilterModal';

// Helper functions for encoding/decoding data
function enc(o: any): string {
  return Buffer.from(JSON.stringify(o)).toString('base64');
}

function dec(s: string): any {
  return JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
}

// Type definitions
type SortBy = 'name' | 'expiry' | 'category';
type SortOrder = 'asc' | 'desc';

// Helper function to get icon and color based on item details
const getItemStyle = (item: { name: string; unit: string; category?: string }) => {
  const unit = item.unit.toLowerCase();
  const name = item.name.toLowerCase();
  const category = item.category?.toLowerCase() || '';

  // Define icon mappings
  const iconMappings: { [key: string]: { icon: string; color: string } } = {
    // Weight-based items
    'kg': { icon: 'scale', color: '#4F46E5' },
    'g': { icon: 'scale', color: '#4F46E5' },
    'lb': { icon: 'scale', color: '#4F46E5' },
    'oz': { icon: 'scale', color: '#4F46E5' },
    
    // Volume-based items
    'l': { icon: 'water', color: '#3B82F6' },
    'ml': { icon: 'water', color: '#3B82F6' },
    'gallon': { icon: 'water', color: '#3B82F6' },
    'quart': { icon: 'water', color: '#3B82F6' },
    'pint': { icon: 'water', color: '#3B82F6' },
    'cup': { icon: 'cup', color: '#8B5CF6' },
    'tbsp': { icon: 'silverware', color: '#8B5CF6' },
    'tsp': { icon: 'silverware', color: '#8B5CF6' },
    
    // Count-based items
    'count': { icon: 'numeric', color: '#10B981' },
    'dozen': { icon: 'egg-easter', color: '#10B981' },
    
    // Category-based overrides
    'dairy': { icon: 'cow', color: '#F59E0B' },
    'meat': { icon: 'food-steak', color: '#DC2626' },
    'produce': { icon: 'food-apple', color: '#10B981' },
    'bakery': { icon: 'bread-slice', color: '#D97706' },
    'beverage': { icon: 'cup-water', color: '#3B82F6' },
    'snack': { icon: 'popcorn', color: '#8B5CF6' },
    'frozen': { icon: 'snowflake', color: '#06B6D4' },
    'canned': { icon: 'can', color: '#6B7280' },
    'dry': { icon: 'barley', color: '#A16207' },
    'spice': { icon: 'shaker', color: '#D946EF' },
    'condiment': { icon: 'bottle-tonic', color: '#EC4899' },
  };

  // Check category first
  if (category && iconMappings[category]) {
    return iconMappings[category];
  }

  // Then check unit
  if (iconMappings[unit]) {
    return iconMappings[unit];
  }

  // Default icon
  return { icon: 'food', color: '#6B7280' };
};

// Group items by name and unit for consistent grouping with items-detected screen
const groupItems = (items: any[]) => {
  const grouped: Record<string, any> = {};
  
  items.forEach(item => {
    const key = `${item.item_name}-${item.quantity_unit}`;
    
    if (!grouped[key]) {
      grouped[key] = {
        ...item,
        count: 1,
      };
    } else {
      grouped[key].count += 1;
    }
  });

  return Object.values(grouped);
};

const IndexScreen: React.FC = () => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isFilterModalVisible, setIsFilterModalVisible] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>('expiry');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  
  // Context hooks after state - must be in consistent order
  const { items, isInitialized, fetchItems } = useItems();
  const router = useRouter();

  // Format, filter, group, and sort items - using useMemo for performance
  const recentItems = useMemo(() => {
    if (!items) return [];
    
    // Filter by search query
    const filteredBySearch = items.filter(item => 
      item.item_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    // Filter by category if any are selected
    const filteredByCategory = selectedCategories.length > 0
      ? filteredBySearch.filter(item => 
          item.category && selectedCategories.includes(item.category)
        )
      : filteredBySearch;
    
    // Format each item with its styles and metadata
    const formattedItems = filteredByCategory.map(item => {
      const expirationDate = item.expected_expiration || new Date().toISOString();
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
        daysUntilExpiry: (() => {
          try {
            const expDate = new Date(expirationDate);
            expDate.setHours(23, 59, 59, 999);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            return Math.max(0, Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
          } catch (e) {
            return 0; // Default to 0 days if date parsing fails
          }
        })(),
        ...getItemStyle({
          name: item.item_name,
          unit: item.quantity_unit,
          category: item.category
        })
      };
    });
    
    // Group items by name and unit
    const groupedItems = groupItems(formattedItems);
    
    // Sort items based on selected criteria and order
    return groupedItems.sort((a: any, b: any) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'category':
          comparison = (a.category || '').localeCompare(b.category || '');
          if (comparison === 0) {
            comparison = a.name.localeCompare(b.name);
          }
          break;
        case 'expiry':
        default:
          if (a.daysUntilExpiry !== b.daysUntilExpiry) {
            comparison = a.daysUntilExpiry - b.daysUntilExpiry;
          } else {
            comparison = a.name.localeCompare(b.name);
          }
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [items, searchQuery, selectedCategories, sortBy, sortOrder]);

  // Fetch items when the component mounts or fetchItems changes
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

  // Quick action buttons with proper typing
  const quickActions = [
    { 
      id: 'add', 
      icon: 'add-circle' as const, 
      title: 'Add Item',
      color: '#297A56',
      route: '/add-item' as const
    },
    { 
      id: 'scan', 
      icon: 'barcode' as const, 
      title: 'Scan Barcode',
      color: '#4F46E5',
      onPress: () => Alert.alert('Barcode Scanner', 'Barcode scanning functionality will be implemented soon.')
    },
    { 
      id: 'recipe', 
      icon: 'restaurant' as const, 
      title: 'Recipes',
      color: '#DB2777',
      route: '/recipes' as const
    },
    { 
      id: 'shopping', 
      icon: 'cart' as const, 
      title: 'Shopping List',
      color: '#7C3AED',
      route: '/shopping-list' as const
    },
  ];

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  // Handle filter apply
  const handleFilterApply = (filters: { categories: string[]; sortBy: SortBy; sortOrder: SortOrder }) => {
    setSelectedCategories(filters.categories);
    setSortBy(filters.sortBy);
    setSortOrder(filters.sortOrder);
    setIsFilterModalVisible(false);
  };

  // Handle item press
  const handleItemPress = (item: any) => {
    // Using relative path for navigation
    router.push({
      pathname: '/item-details',
      params: { item: enc(item) }
    } as any);
  };

  // Handle quick action press
  const handleQuickAction = (actionId: string) => {
    const action = quickActions.find(a => a.id === actionId);
    if (!action) return;
    
    if ('onPress' in action && action.onPress) {
      action.onPress();
    } else if ('route' in action && action.route) {
      router.push(action.route as any);
    }
  };
  
  // Reset filters function
  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategories([]);
  };

  // Helper function to format expiration date
  function formatExpirationDate(dateString: string) {
    const date = new Date(dateString);
    // If the date is invalid, return a placeholder
    if (isNaN(date.getTime())) return 'No date';
    
    // Set time to end of day for the expiration date and start of day for today
    const expirationDate = new Date(date);
    expirationDate.setHours(23, 59, 59, 999);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const diffTime = expirationDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return `Expired ${Math.abs(diffDays)} days ago`;
    } else if (diffDays === 0) {
      return 'Expires: Today';
    } else if (diffDays === 1) {
      return 'Expires: Tomorrow';
    } else {
      return `Expires: ${diffDays} days`;
    }
  }
  const currentDate = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'long', 
    day: 'numeric' 
  });

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello, User</Text>
          <Text style={styles.date}>{currentDate}</Text>
        </View>
        <TouchableOpacity style={styles.profileButton}>
          <Ionicons name="person-circle" size={32} color="#297A56" />
        </TouchableOpacity>
      </View>
      
      {/* Search, Filter, and Sort Bar */}
      <SearchBar
        searchQuery={searchQuery}
        onSearch={handleSearch}
        onFilterPress={() => setIsFilterModalVisible(true)}
        onSortPress={() => {
          setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
        }}
      />
      
      {/* Filter Modal */}
      <FilterModal
        visible={isFilterModalVisible}
        onClose={() => setIsFilterModalVisible(false)}
        onApply={handleFilterApply}
        selectedCategories={selectedCategories}
        sortBy={sortBy}
        sortOrder={sortOrder}
      />
      
      {/* Active Filters */}
      {(searchQuery || selectedCategories.length > 0) && (
        <View style={styles.activeFiltersContainer}>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.activeFiltersScroll}
          >
            {searchQuery && (
              <View style={styles.activeFilter}>
                <Text style={styles.activeFilterText}>Search: {searchQuery}</Text>
                <TouchableOpacity 
                  onPress={() => setSearchQuery('')}
                  style={styles.removeFilterButton}
                >
                  <Ionicons name="close" size={14} color="#6B7280" />
                </TouchableOpacity>
              </View>
            )}
            {selectedCategories.map(category => (
              <View key={category} style={styles.activeFilter}>
                <Text style={styles.activeFilterText}>{category}</Text>
                <TouchableOpacity 
                  onPress={() => setSelectedCategories(selectedCategories.filter(c => c !== category))}
                  style={styles.removeFilterButton}
                >
                  <Ionicons name="close" size={14} color="#6B7280" />
                </TouchableOpacity>
              </View>
            ))}
            {(searchQuery || selectedCategories.length > 0) && (
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

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActions}>
          {quickActions.map((action) => (
            <TouchableOpacity 
              key={action.id}
              style={[styles.actionCard, { backgroundColor: action.color + '15' }]}
              onPress={() => {
                if ('route' in action && action.route) {
                  router.push(action.route as any);
                } else if ('onPress' in action && action.onPress) {
                  action.onPress();
                }
              }}
            >
              <View style={[styles.actionIcon, { backgroundColor: action.color }]}>
                <Ionicons name={action.icon as any} size={24} color="white" />
              </View>
              <Text style={styles.actionText}>{action.title}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Recent Items */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Expiring Soon</Text>
          <TouchableOpacity>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.recentItems}>
          {recentItems.map((item) => (
            <TouchableOpacity 
              key={item.id} 
              style={styles.itemCard}
              onPress={() => {
                // Navigate to edit screen with the item data
                router.push({
                  pathname: '/edit-item',
                  params: { 
                    index: '0', // Not used for single item edit
                    data: enc([{
                      ...item,
                      // Ensure we have all required fields
                      id: item.id,
                      item_name: item.name,
                      quantity_amount: item.quantity_amount,
                      quantity_unit: item.quantity_unit,
                      expected_expiration: item.expirationDate.toISOString().split('T')[0],
                      category: item.category
                    }])
                  }
                });
              }}
            >
              <View style={[
                styles.itemIcon,
                { 
                  backgroundColor: item.bgColor,
                  borderRadius: item.isBox ? 6 : 20,
                },
                item.isProduce && styles.produceIcon,
                item.isBox && styles.boxIcon,
                item.isCan && styles.canIcon
              ]}>
                <MaterialIcons 
                  name={item.icon} 
                  size={24} 
                  color={item.iconColor}
                />
              </View>
              <View style={styles.itemInfo}>
                <View style={styles.itemNameRow}>
                  <View style={styles.itemNameContainer}>
                    <Text 
                      style={styles.itemName} 
                      numberOfLines={1} 
                      ellipsizeMode="tail"
                    >
                      {item.name}
                    </Text>
                    {item.count > 1 && (
                      <View style={styles.itemCountBadge}>
                        <Text style={styles.itemCountText}>×{item.count}</Text>
                      </View>
                    )}
                  </View>
                  <View style={styles.itemAmountContainer}>
                    <Text 
                      style={styles.itemAmount}
                      numberOfLines={1}
                    >
                      {item.count > 1 ? (
                        <>
                          {item.quantities ? item.quantities.join(' + ') : item.quantity_amount} {item.quantity_unit} {item.totalQuantity ? `(total: ${item.totalQuantity} ${item.quantity_unit})` : ''}
                        </>
                      ) : (
                        `${item.quantity_amount} ${item.quantity_unit}`
                      )}
                    </Text>
                  </View>
                </View>
                <View style={styles.itemDetails}>
                  <View style={[styles.categoryTag, { 
                    backgroundColor: getCategoryColor(item.category),
                    opacity: item.daysUntilExpiry <= 3 ? 0.9 : 0.7
                  }]}>
                    <Text style={styles.categoryText}>{item.category}</Text>
                  </View>
                  <Text style={[
                    styles.itemExpiry,
                    item.daysUntilExpiry <= 0 ? styles.expired : null,
                    item.daysUntilExpiry <= 3 ? styles.expiringSoon : null
                  ]}>
                    {item.expiry}
                  </Text>
                </View>
              </View>
              <View style={styles.moreButton}>
                <Ionicons name="ellipsis-vertical" size={20} color="#6B7280" />
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Tips Section */}
        <View style={styles.tipCard}>
          <Ionicons name="bulb" size={24} color="#F59E0B" />
          <View style={styles.tipContent}>
            <Text style={styles.tipTitle}>Storage Tip</Text>
            <Text style={styles.tipText}>
              Store bananas separately from other fruits to prevent them from ripening too quickly.
            </Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

export default IndexScreen;

// Helper function to get category color
const getCategoryColor = (category: string) => {
  const colors = {
    'Dairy': '#E0F2FE',
    'Meat': '#FEE2E2',
    'Produce': '#DCFCE7',
    'Bakery': '#FEF3C7',
    'Pantry': '#EDE9FE',
    'Beverages': '#E0E7FF',
    'Frozen': '#E0F2F9',
    'Default': '#F3F4F6',
  };
  
  return colors[category as keyof typeof colors] || colors.Default;
};

// Add these new styles
const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#DC2626',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retryButtonText: {
    color: 'white',
    fontWeight: '600',
    marginLeft: 8,
  },
  addButton: {
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  addButtonText: {
    color: 'white',
    fontWeight: '600',
    marginLeft: 8,
    fontSize: 16,
  },
  // New styles for search and filter components
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
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  date: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  profileButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  actionCard: {
    flex: 1,
    marginHorizontal: 4,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'center',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  seeAll: {
    color: '#297A56',
    fontWeight: '500',
  },
  recentItems: {
    marginBottom: 24,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  itemIcon: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  boxIcon: {
    // Styles applied via inline style
  },
  canIcon: {
    // Styles applied via inline style
  },
  produceIcon: {
    // Styles applied via inline style
  },
  itemInfo: {
    flex: 1,
    flexDirection: 'column',
  },
  itemNameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
    flex: 1,
  },
  itemDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    flexShrink: 1,
    flexWrap: 'wrap',
  },
  itemNameContainer: {
    flex: 1,
    marginRight: 8,
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  itemCountBadge: {
    backgroundColor: '#E5E7EB',
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 6,
    alignSelf: 'flex-start',
  },
  itemCountText: {
    fontSize: 12,
    color: '#4B5563',
    fontWeight: '500',
  },
  itemAmountContainer: {
    flexShrink: 0,
  },
  itemAmount: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'right',
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  itemExpiry: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 8,
    fontWeight: '500',
  },
  expiringSoon: {
    color: '#D97706',
  },
  expired: {
    color: '#DC2626',
    fontWeight: '600',
  },
  categoryTag: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 12,
    color: '#4B5563',
    fontWeight: '500',
  },
  moreButton: {
    padding: 8,
  },
  tipCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  tipContent: {
    flex: 1,
    marginLeft: 12,
  },
  tipTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  tipText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
});
