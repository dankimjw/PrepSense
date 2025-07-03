import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Switch,
  Alert,
  TextInput,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Item } from '../../types';
import { useToast } from '../../hooks/useToast';

interface AIBulkEditModalProps {
  visible: boolean;
  items: Item[];
  onClose: () => void;
  onApplyChanges: (selectedItems: string[], options: BulkEditOptions) => void;
}

interface BulkEditOptions {
  correctUnits: boolean;
  updateCategories: boolean;
  estimateExpirations: boolean;
  enableRecurring: boolean;
  recurringOptions?: {
    addToShoppingList: boolean;
    daysBeforeExpiry: number;
  };
}

interface SelectableItem extends Item {
  selected: boolean;
}

export const AIBulkEditModal: React.FC<AIBulkEditModalProps> = ({
  visible,
  items,
  onClose,
  onApplyChanges,
}) => {
  const [selectableItems, setSelectableItems] = useState<SelectableItem[]>([]);
  const [selectAll, setSelectAll] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const { showToast } = useToast();

  // AI correction options
  const [correctUnits, setCorrectUnits] = useState(true);
  const [updateCategories, setUpdateCategories] = useState(true);
  const [estimateExpirations, setEstimateExpirations] = useState(true);
  
  // Recurring shopping list options
  const [enableRecurring, setEnableRecurring] = useState(false);
  const [addToShoppingList, setAddToShoppingList] = useState(true);
  const [daysBeforeExpiry, setDaysBeforeExpiry] = useState(7);

  useEffect(() => {
    if (visible && items.length > 0) {
      setSelectableItems(
        items.map(item => ({ 
          ...item, 
          selected: false,
          name: item.name || item.item_name || 'Unnamed Item',
          category: item.category || 'Uncategorized',
          quantity_amount: item.quantity_amount || 0,
          quantity_unit: item.quantity_unit || 'each'
        }))
      );
    }
  }, [visible, items]);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(items.map(item => item.category || 'Uncategorized'));
    return Array.from(cats).sort();
  }, [items]);

  // Filter items based on search and categories
  const filteredItems = useMemo(() => {
    return selectableItems.filter(item => {
      const matchesSearch = searchQuery === '' || 
        item.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategories.length === 0 || 
        selectedCategories.includes(item.category || 'Uncategorized');
      return matchesSearch && matchesCategory;
    });
  }, [selectableItems, searchQuery, selectedCategories]);

  const toggleItemSelection = (itemId: string, index: number) => {
    setSelectableItems(prev =>
      prev.map((item, idx) =>
        idx === index ? { ...item, selected: !item.selected } : item
      )
    );
  };

  const toggleSelectAll = () => {
    const newSelectAll = !selectAll;
    setSelectAll(newSelectAll);
    
    // Get IDs of currently filtered items
    const filteredIds = new Set(filteredItems.map(item => item.id));
    
    setSelectableItems(prev =>
      prev.map(item => ({
        ...item,
        selected: filteredIds.has(item.id) ? newSelectAll : item.selected
      }))
    );
  };

  const getSelectedCount = () => {
    return selectableItems.filter(item => item.selected).length;
  };

  const handleApply = () => {
    const selectedItems = selectableItems
      .filter(item => item.selected)
      .map(item => item.id);

    if (selectedItems.length === 0) {
      Alert.alert('No Items Selected', 'Please select at least one item to process.');
      return;
    }

    const options: BulkEditOptions = {
      correctUnits,
      updateCategories,
      estimateExpirations,
      enableRecurring,
      recurringOptions: enableRecurring
        ? {
            addToShoppingList,
            daysBeforeExpiry,
          }
        : undefined,
    };

    onApplyChanges(selectedItems, options);
  };

  const getCategoryIcon = (category: string) => {
    const iconMap: { [key: string]: string } = {
      'Dairy': 'cheese',
      'Meat': 'food-steak',
      'Produce': 'apple',
      'Grains': 'barley',
      'Beverages': 'cup',
      'Snacks': 'cookie',
      'Condiments': 'bottle-tonic',
      'Other': 'dots-horizontal',
    };
    return iconMap[category] || 'dots-horizontal';
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <MaterialCommunityIcons name="robot" size={24} color="#297A56" />
            <Text style={styles.headerTitle}>AI Bulk Editor</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={28} color="#333" />
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Search and Filter Bar */}
          <View style={styles.searchFilterContainer}>
            <View style={styles.searchBar}>
              <Ionicons name="search" size={20} color="#666" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search items..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                placeholderTextColor="#999"
              />
            </View>
            <TouchableOpacity 
              style={styles.filterButton} 
              onPress={() => setShowFilters(!showFilters)}
            >
              <Ionicons name="filter" size={20} color="#297A56" />
            </TouchableOpacity>
          </View>

          {/* Category Filters */}
          {showFilters && (
            <View style={styles.filterSection}>
              <Text style={styles.filterTitle}>Filter by Category</Text>
              <View style={styles.categoryFilters}>
                {categories.map(category => (
                  <TouchableOpacity
                    key={category}
                    style={[
                      styles.categoryChip,
                      selectedCategories.includes(category) && styles.categoryChipActive
                    ]}
                    onPress={() => {
                      setSelectedCategories(prev =>
                        prev.includes(category)
                          ? prev.filter(c => c !== category)
                          : [...prev, category]
                      );
                    }}
                  >
                    <Text style={[
                      styles.categoryChipText,
                      selectedCategories.includes(category) && styles.categoryChipTextActive
                    ]}>
                      {category}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              {selectedCategories.length > 0 && (
                <TouchableOpacity
                  style={styles.clearFiltersButton}
                  onPress={() => setSelectedCategories([])}
                >
                  <Text style={styles.clearFiltersText}>Clear filters</Text>
                </TouchableOpacity>
              )}
            </View>
          )}

          {/* Selection Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryText}>
              {getSelectedCount()} of {filteredItems.length} items selected
              {searchQuery || selectedCategories.length > 0 ? ` (${items.length} total)` : ''}
            </Text>
            <TouchableOpacity onPress={toggleSelectAll} style={styles.selectAllButton}>
              <Text style={styles.selectAllText}>
                {selectAll ? 'Deselect All' : 'Select All'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* AI Correction Options */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>AI Corrections</Text>
            <Text style={styles.sectionSubtitle}>
              Let AI automatically fix common data issues
            </Text>

            <View style={styles.optionRow}>
              <View style={styles.optionInfo}>
                <Ionicons name="resize" size={20} color="#297A56" />
                <View style={styles.optionText}>
                  <Text style={styles.optionTitle}>Correct Units</Text>
                  <Text style={styles.optionDescription}>
                    Fix incorrect units (e.g., "1 milk" → "1 gallon milk")
                  </Text>
                </View>
              </View>
              <Switch
                value={correctUnits}
                onValueChange={setCorrectUnits}
                trackColor={{ false: '#E5E7EB', true: '#297A56' }}
                thumbColor="#fff"
              />
            </View>

            <View style={styles.optionRow}>
              <View style={styles.optionInfo}>
                <Ionicons name="grid" size={20} color="#297A56" />
                <View style={styles.optionText}>
                  <Text style={styles.optionTitle}>Update Categories</Text>
                  <Text style={styles.optionDescription}>
                    Automatically categorize items correctly
                  </Text>
                </View>
              </View>
              <Switch
                value={updateCategories}
                onValueChange={setUpdateCategories}
                trackColor={{ false: '#E5E7EB', true: '#297A56' }}
                thumbColor="#fff"
              />
            </View>

            <View style={styles.optionRow}>
              <View style={styles.optionInfo}>
                <Ionicons name="calendar" size={20} color="#297A56" />
                <View style={styles.optionText}>
                  <Text style={styles.optionTitle}>Estimate Expirations</Text>
                  <Text style={styles.optionDescription}>
                    Set smart expiration dates based on item type
                  </Text>
                </View>
              </View>
              <Switch
                value={estimateExpirations}
                onValueChange={setEstimateExpirations}
                trackColor={{ false: '#E5E7EB', true: '#297A56' }}
                thumbColor="#fff"
              />
            </View>
          </View>

          {/* Recurring Shopping List Options */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recurring Items</Text>
            <Text style={styles.sectionSubtitle}>
              Automatically add items to shopping list when running low
            </Text>

            <View style={styles.optionRow}>
              <View style={styles.optionInfo}>
                <Ionicons name="repeat" size={20} color="#297A56" />
                <View style={styles.optionText}>
                  <Text style={styles.optionTitle}>Enable Recurring</Text>
                  <Text style={styles.optionDescription}>
                    Auto-add to shopping list before expiration
                  </Text>
                </View>
              </View>
              <Switch
                value={enableRecurring}
                onValueChange={setEnableRecurring}
                trackColor={{ false: '#E5E7EB', true: '#297A56' }}
                thumbColor="#fff"
              />
            </View>

            {enableRecurring && (
              <View style={styles.recurringOptions}>
                <View style={styles.daysSelector}>
                  <Text style={styles.daysLabel}>Add to list</Text>
                  <View style={styles.daysButtons}>
                    {[3, 5, 7, 10].map(days => (
                      <TouchableOpacity
                        key={days}
                        style={[
                          styles.dayButton,
                          daysBeforeExpiry === days && styles.dayButtonActive,
                        ]}
                        onPress={() => setDaysBeforeExpiry(days)}
                      >
                        <Text
                          style={[
                            styles.dayButtonText,
                            daysBeforeExpiry === days && styles.dayButtonTextActive,
                          ]}
                        >
                          {days}d
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                  <Text style={styles.daysLabel}>before expiry</Text>
                </View>
              </View>
            )}
          </View>

          {/* Selected Items List */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Select Items</Text>
            <View style={styles.itemsList}>
              {filteredItems.length === 0 ? (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyStateText}>
                    {searchQuery || selectedCategories.length > 0
                      ? 'No items match your filters'
                      : 'No items available'}
                  </Text>
                </View>
              ) : (
                filteredItems.map((item, index) => (
                <TouchableOpacity
                  key={`${item.id}-${index}`}
                  style={[styles.itemRow, item.selected && styles.itemRowSelected]}
                  onPress={() => toggleItemSelection(item.id, index)}
                  activeOpacity={0.7}
                >
                  <View style={styles.checkbox}>
                    {item.selected && (
                      <Ionicons name="checkmark" size={16} color="#297A56" />
                    )}
                  </View>
                  <View style={styles.itemInfo}>
                    <Text style={styles.itemName} numberOfLines={2}>{item.name}</Text>
                    <View style={styles.itemDetails}>
                      <View style={styles.itemDetail}>
                        <MaterialCommunityIcons
                          name={getCategoryIcon(item.category)}
                          size={14}
                          color="#666"
                        />
                        <Text style={styles.itemDetailText}>
                          {item.category || 'Uncategorized'}
                        </Text>
                      </View>
                      <View style={styles.itemDetail}>
                        <Ionicons name="cube-outline" size={14} color="#666" />
                        <Text style={styles.itemDetailText}>
                          {item.quantity_amount} {item.quantity_unit}
                        </Text>
                      </View>
                    </View>
                  </View>
                </TouchableOpacity>
              )))}
            </View>
          </View>
        </ScrollView>

        {/* Apply Button */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={[
              styles.applyButton,
              getSelectedCount() === 0 && styles.applyButtonDisabled,
            ]}
            onPress={handleApply}
            disabled={getSelectedCount() === 0 || isProcessing}
          >
            {isProcessing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <MaterialCommunityIcons name="magic-staff" size={20} color="#fff" />
                <Text style={styles.applyButtonText}>
                  Apply AI Corrections
                </Text>
              </>
            )}
          </TouchableOpacity>
          <Text style={styles.costNote}>
            Estimated cost: ${(getSelectedCount() * 0.002).toFixed(3)}
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    paddingTop: 50,
    paddingBottom: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
  },
  closeButton: {
    position: 'absolute',
    right: 20,
    padding: 4,
  },
  content: {
    flex: 1,
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  summaryText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  selectAllButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#297A56',
    borderRadius: 20,
  },
  selectAllText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  optionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  optionText: {
    marginLeft: 12,
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  optionDescription: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  recurringOptions: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  daysSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  daysLabel: {
    fontSize: 14,
    color: '#666',
    marginHorizontal: 8,
  },
  daysButtons: {
    flexDirection: 'row',
    marginHorizontal: 8,
  },
  dayButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginHorizontal: 4,
  },
  dayButtonActive: {
    backgroundColor: '#297A56',
    borderColor: '#297A56',
  },
  dayButtonText: {
    fontSize: 14,
    color: '#666',
  },
  dayButtonTextActive: {
    color: '#fff',
  },
  itemsList: {
    marginTop: 8,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#f9f9f9',
    minHeight: 72,
  },
  itemRowSelected: {
    backgroundColor: '#E8F5E9',
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
    backgroundColor: '#fff',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
    flexWrap: 'wrap',
  },
  itemDetails: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  itemDetailText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  footer: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  applyButton: {
    backgroundColor: '#297A56',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  applyButtonDisabled: {
    backgroundColor: '#ccc',
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  costNote: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
  },
  searchFilterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 44,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  filterButton: {
    width: 44,
    height: 44,
    backgroundColor: '#fff',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  filterSection: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  filterTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  categoryFilters: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  categoryChipActive: {
    backgroundColor: '#E8F5E9',
    borderColor: '#297A56',
  },
  categoryChipText: {
    fontSize: 14,
    color: '#666',
  },
  categoryChipTextActive: {
    color: '#297A56',
    fontWeight: '500',
  },
  clearFiltersButton: {
    marginTop: 12,
    alignSelf: 'flex-start',
  },
  clearFiltersText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
  },
});