// components/FilterModal.tsx - Part of the PrepSense mobile app
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FOOD_CATEGORIES } from '../utils/categoryConfig';

interface FilterModalProps {
  visible: boolean;
  onClose: () => void;
  onApply: (filters: {
    categories: string[];
    sortBy: 'name' | 'expiry' | 'category' | 'dateAdded';
    sortOrder: 'asc' | 'desc';
  }) => void;
  selectedCategories: string[];
  sortBy: 'name' | 'expiry' | 'category' | 'dateAdded';
  sortOrder: 'asc' | 'desc';
}

export const FilterModal: React.FC<FilterModalProps> = ({
  visible,
  onClose,
  onApply,
  selectedCategories,
  sortBy,
  sortOrder,
}) => {
  const [localSelectedCategories, setLocalSelectedCategories] = React.useState<string[]>(selectedCategories);
  const [localSortBy, setLocalSortBy] = React.useState(sortBy);
  const [localSortOrder, setLocalSortOrder] = React.useState(sortOrder);

  const toggleCategory = (category: string) => {
    if (localSelectedCategories.includes(category)) {
      setLocalSelectedCategories(localSelectedCategories.filter(c => c !== category));
    } else {
      setLocalSelectedCategories([...localSelectedCategories, category]);
    }
  };

  const handleApply = () => {
    onApply({
      categories: localSelectedCategories,
      sortBy: localSortBy,
      sortOrder: localSortOrder,
    });
    onClose();
  };

  const toggleSortOrder = () => {
    setLocalSortOrder(localSortOrder === 'asc' ? 'desc' : 'asc');
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Filter & Sort</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close" size={24} color="#4B5563" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollView}>
            <Text style={styles.sectionTitle}>Categories</Text>
            <View style={styles.categoriesContainer}>
              {FOOD_CATEGORIES.map(category => (
                <TouchableOpacity
                  key={category.id}
                  style={[
                    styles.categoryButton,
                    localSelectedCategories.includes(category.label) && styles.categoryButtonSelected,
                  ]}
                  onPress={() => toggleCategory(category.label)}
                >
                  <Text
                    style={[
                      styles.categoryText,
                      localSelectedCategories.includes(category.label) && styles.categoryTextSelected,
                    ]}
                  >
                    {category.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Sort By</Text>
            <View style={styles.sortOptions}>
              <TouchableOpacity
                style={[styles.sortOption, localSortBy === 'name' && styles.sortOptionSelected]}
                onPress={() => setLocalSortBy('name')}
              >
                <Ionicons
                  name="text"
                  size={20}
                  color={localSortBy === 'name' ? '#297A56' : '#4B5563'}
                />
                <Text
                  style={[
                    styles.sortOptionText,
                    localSortBy === 'name' && styles.sortOptionTextSelected,
                  ]}
                >
                  Name
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.sortOption, localSortBy === 'expiry' && styles.sortOptionSelected]}
                onPress={() => setLocalSortBy('expiry')}
              >
                <Ionicons
                  name="calendar"
                  size={20}
                  color={localSortBy === 'expiry' ? '#297A56' : '#4B5563'}
                />
                <Text
                  style={[
                    styles.sortOptionText,
                    localSortBy === 'expiry' && styles.sortOptionTextSelected,
                  ]}
                >
                  Expiry
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.sortOption, localSortBy === 'category' && styles.sortOptionSelected]}
                onPress={() => setLocalSortBy('category')}
              >
                <Ionicons
                  name="pricetags"
                  size={20}
                  color={localSortBy === 'category' ? '#297A56' : '#4B5563'}
                />
                <Text
                  style={[
                    styles.sortOptionText,
                    localSortBy === 'category' && styles.sortOptionTextSelected,
                  ]}
                >
                  Category
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.sortOption, localSortBy === 'dateAdded' && styles.sortOptionSelected]}
                onPress={() => setLocalSortBy('dateAdded')}
              >
                <Ionicons
                  name="time"
                  size={20}
                  color={localSortBy === 'dateAdded' ? '#297A56' : '#4B5563'}
                />
                <Text
                  style={[
                    styles.sortOptionText,
                    localSortBy === 'dateAdded' && styles.sortOptionTextSelected,
                  ]}
                >
                  Date Added
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.sortOrderButton}
                onPress={toggleSortOrder}
              >
                <Ionicons
                  name={localSortOrder === 'asc' ? 'arrow-up' : 'arrow-down'}
                  size={20}
                  color="#4B5563"
                />
                <Text style={styles.sortOrderText}>
                  {localSortOrder === 'asc' ? 'Ascending' : 'Descending'}
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity
              style={[styles.button, styles.resetButton]}
              onPress={() => {
                setLocalSelectedCategories([]);
                setLocalSortBy('expiry');
                setLocalSortOrder('asc');
              }}
            >
              <Text style={styles.resetButtonText}>Reset</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.applyButton]}
              onPress={handleApply}
            >
              <Text style={styles.applyButtonText}>Apply Filters</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
  },
  scrollView: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  categoriesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  categoryButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  categoryButtonSelected: {
    backgroundColor: '#E5F7EF',
    borderColor: '#297A56',
  },
  categoryText: {
    color: '#4B5563',
    fontSize: 14,
  },
  categoryTextSelected: {
    color: '#297A56',
    fontWeight: '500',
  },
  sortOptions: {
    flexDirection: 'column',
    gap: 8,
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
  },
  sortOptionSelected: {
    backgroundColor: '#E5F7EF',
  },
  sortOptionText: {
    marginLeft: 8,
    color: '#4B5563',
    fontSize: 16,
  },
  sortOptionTextSelected: {
    color: '#297A56',
    fontWeight: '500',
  },
  sortOrderButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    marginTop: 8,
    justifyContent: 'center',
  },
  sortOrderText: {
    marginLeft: 8,
    color: '#4B5563',
    fontSize: 16,
    fontWeight: '500',
  },
  modalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetButton: {
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  applyButton: {
    backgroundColor: '#297A56',
    marginLeft: 8,
  },
  resetButtonText: {
    color: '#4B5563',
    fontSize: 16,
    fontWeight: '500',
  },
  applyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
});
