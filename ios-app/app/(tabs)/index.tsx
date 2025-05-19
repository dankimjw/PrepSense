import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Buffer } from 'buffer';

// Helper functions for encoding/decoding data
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { useItems } from '../../context/ItemsContext';
import { SearchBar } from '../../components/SearchBar';
import { FilterModal } from '../../components/FilterModal';

// Helper function to get icon and color based on item details
const getItemStyle = (item: { name: string; unit: string; category?: string }) => {
  const lowerName = item.name.toLowerCase();
  const lowerUnit = item.unit.toLowerCase();
  
  // Default style
  let style = {
    icon: 'shopping-bag' as keyof typeof MaterialIcons.glyphMap,
    bgColor: '#F0F7F4',
    iconColor: '#297A56',
    isProduce: false,
    isBox: false,
    isCan: false
  };
  
  // Check for specific food categories
  // Fruits
  if (/apple|pear|peach|plum|nectarine|apricot|banana|orange|tangerine|clementine|mandarin|strawberr|blueberr|raspberr|blackberr|berry|berries|grape|watermelon|cantaloupe|honeydew|melon|pineapple|mango|papaya|guava|kiwi|dragonfruit|passionfruit|avocado|tomato|cherr/i.test(lowerName)) {
    style = { ...style, icon: 'eco', bgColor: '#FEF3F2', iconColor: '#DC2626', isProduce: true };
  }
  
  // Vegetables
  if (/carrot|potato|onion|garlic|ginger|beet|radish|turnip|parsnip|rutabaga|broccoli|cauliflower|cabbage|brussel|kale|lettuce|spinach|arugula|chard|collard|pepper|chili|jalapeno|habanero|poblano|serrano|cucumber|zucchini|squash|pumpkin|eggplant|corn|peas|bean|legume|lentil|chickpea|edamame|soy/i.test(lowerName)) {
    style = { ...style, icon: 'eco', bgColor: '#F0FDF4', iconColor: '#16A34A', isProduce: true };
  }
  
  // Packaging types
  if (/can|tin/i.test(lowerName) || /can|tin/i.test(lowerUnit)) {
    style = { ...style, icon: 'local-drink', bgColor: '#EFF6FF', iconColor: '#2563EB', isCan: true };
  }
  if (/box|pack|package|cereal/i.test(lowerName) || /box|pack|package/i.test(lowerUnit)) {
    style = { ...style, icon: 'inventory-2', bgColor: '#F5F3FF', iconColor: '#7C3AED', isBox: true };
  }
  if (/bottle|bottles|jar|beverage|drink|soda|water|juice/i.test(lowerName) || /bottle|bottles|jar/i.test(lowerUnit)) {
    style = { ...style, icon: 'local-drink', bgColor: '#E0F2FE', iconColor: '#0284C7' };
  }
  if (/bag|pouch|sack/i.test(lowerName) || /bag|pouch|sack/i.test(lowerUnit)) {
    style = { ...style, icon: 'shopping-bag', bgColor: '#FEF3C7', iconColor: '#D97706' };
  }
  if (/carton|milk|cream|yogurt|cheese|dairy/i.test(lowerName) || /carton/i.test(lowerUnit)) {
    style = { ...style, icon: 'local-drink', bgColor: '#FEF2F2', iconColor: '#DC2626' };
  }
  
  // Category-based fallback
  const categoryStyles: Record<string, Partial<typeof style>> = {
    'Dairy': { icon: 'local-drink', bgColor: '#FEF2F2', iconColor: '#DC2626' },
    'Meat': { icon: 'restaurant', bgColor: '#FEF2F2', iconColor: '#B91C1C' },
    'Produce': { ...style, isProduce: true },
    'Bakery': { icon: 'breakfast-dining', bgColor: '#FEF3F2', iconColor: '#9A3412' },
    'Pantry': { icon: 'kitchen', bgColor: '#F5F3FF', iconColor: '#7C3AED' },
    'Beverages': { icon: 'local-cafe', bgColor: '#EFF6FF', iconColor: '#2563EB' },
    'Frozen': { icon: 'ac-unit', bgColor: '#E0F2FE', iconColor: '#0C4A6E' },
  };
  
  return { ...style, ...(categoryStyles[item.category || ''] || {}) };
};

// Group items by name and unit for consistent grouping with items-detected screen
const groupItems = (items: any[]) => {
  const grouped: Record<string, any> = {};
  
  items.forEach(item => {
    // Create a consistent key using name and unit
    const key = `${item.item_name.trim().toLowerCase()}_${item.quantity_unit.trim().toLowerCase()}`;
    
    if (!grouped[key]) {
      // If this is the first item with this key, initialize the group
      grouped[key] = {
        ...item,
        count: 1,
        ids: [item.id],
        // Sum quantities for identical items
        totalQuantity: item.quantity_amount,
        // Keep track of individual quantities
        quantities: [item.quantity_amount]
      };
    } else {
      // If we already have this item, increment the count and update quantities
      grouped[key].count += 1;
      grouped[key].ids.push(item.id);
      grouped[key].totalQuantity = (grouped[key].totalQuantity || 0) + item.quantity_amount;
      grouped[key].quantities.push(item.quantity_amount);
    }
  });
  
  // Convert the grouped object to an array and sort by name
  return Object.values(grouped).sort((a: any, b: any) => 
    a.item_name.localeCompare(b.item_name)
  );
};

const quickActions = [
  { id: 'add', title: 'Add Item', icon: 'add-circle', color: '#297A56', route: '/upload-photo' },
  { id: 'scan', title: 'Scan Receipt', icon: 'receipt', color: '#3B82F6', route: '/scan-receipt' },
  { id: 'recipes', title: 'Recipes', icon: 'restaurant', color: '#8B5CF6', route: '/recipes' },
];



type SortBy = 'name' | 'expiry' | 'category';
type SortOrder = 'asc' | 'desc';

export default function HomeScreen() {
  const { items } = useItems();
  const router = useRouter();
  
  // State for search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [isFilterModalVisible, setIsFilterModalVisible] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>('expiry');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  
  const handleSearch = (text: string) => {
    setSearchQuery(text);
  };
  
  const handleFilterApply = (filters: {
    categories: string[];
    sortBy: SortBy;
    sortOrder: SortOrder;
  }) => {
    setSelectedCategories(filters.categories);
    setSortBy(filters.sortBy);
    setSortOrder(filters.sortOrder);
  };
  
  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategories([]);
    setSortBy('expiry');
    setSortOrder('asc');
  };

  // Format, filter, group, and sort items
  const recentItems = useMemo(() => {
    // Filter items by search query
    const filteredBySearch = items.filter(item => 
      item.item_name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    // Filter by selected categories if any are selected
    const filteredByCategory = selectedCategories.length > 0
      ? filteredBySearch.filter(item => item.category && selectedCategories.includes(item.category))
      : filteredBySearch;
    
    // Format each item with its styles and metadata
    const formattedItems = filteredByCategory.map(item => ({
      id: item.id,
      item_name: item.item_name.trim(),
      name: item.item_name.trim(),
      expiry: formatExpirationDate(item.expected_expiration),
      category: item.category || 'Uncategorized',
      quantity_amount: item.quantity_amount,
      quantity_unit: item.quantity_unit.trim(),
      expirationDate: new Date(item.expected_expiration),
      daysUntilExpiry: (() => {
        const expDate = new Date(item.expected_expiration);
        expDate.setHours(23, 59, 59, 999);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return Math.max(0, Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
      })(),
      ...getItemStyle({
        name: item.item_name,
        unit: item.quantity_unit,
        category: item.category
      })
    }));
    
    // Group items by name and unit
    const groupedItems = groupItems(formattedItems);
    
    // Sort items based on selected criteria and order
    return [...groupedItems].sort((a: any, b: any) => {
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
              onPress={() => router.push(action.route as any)}
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
                          {item.quantities.join(' + ')} {item.quantity_unit} (total: {item.totalQuantity} {item.quantity_unit})
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
}

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

const styles = StyleSheet.create({
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
