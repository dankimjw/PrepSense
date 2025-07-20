import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { UNITS, UNIT_CATEGORIES, getUnitsByCategory, getUnitByValue, normalizeUnit } from '../constants/units';

interface UnitSelectorProps {
  value: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  style?: any;
}

export const UnitSelector: React.FC<UnitSelectorProps> = ({
  value,
  onValueChange,
  placeholder = 'Select unit',
  style,
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Handle unknown units by creating a temporary unit option
  let selectedUnit = getUnitByValue(value);
  const availableUnits = [...UNITS];
  
  // If the unit doesn't exist in our predefined list, add it as a custom unit
  if (!selectedUnit && value) {
    const normalizedValue = normalizeUnit(value);
    selectedUnit = getUnitByValue(normalizedValue);
    
    if (!selectedUnit) {
      // Create a temporary unit for the unknown unit
      const customUnit = {
        value: value,
        label: value.charAt(0).toUpperCase() + value.slice(1),
        category: 'count' as const,
        abbreviation: value,
        plural: value + 's'
      };
      availableUnits.unshift(customUnit); // Add to beginning so it appears first
      selectedUnit = customUnit;
    }
  }

  const filteredUnits = availableUnits.filter(unit => {
    const matchesSearch = unit.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         unit.value.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         unit.abbreviation.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || unit.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleSelectUnit = (unitValue: string) => {
    onValueChange(unitValue);
    setModalVisible(false);
    setSearchQuery('');
  };

  return (
    <>
      <TouchableOpacity
        style={[styles.selector, style]}
        onPress={() => setModalVisible(true)}
      >
        <Text style={styles.selectorText}>
          {selectedUnit ? selectedUnit.label : placeholder}
        </Text>
        <Ionicons name="chevron-down" size={20} color="#6B7280" />
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Unit</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <View style={styles.searchContainer}>
              <Ionicons name="search" size={20} color="#6B7280" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search units..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <View style={styles.categoryTabs}>
              <TouchableOpacity
                style={[styles.categoryTab, !selectedCategory && styles.categoryTabActive]}
                onPress={() => setSelectedCategory(null)}
              >
                <Text style={[styles.categoryTabText, !selectedCategory && styles.categoryTabTextActive]}>
                  All
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.categoryTab, selectedCategory === UNIT_CATEGORIES.WEIGHT && styles.categoryTabActive]}
                onPress={() => setSelectedCategory(UNIT_CATEGORIES.WEIGHT)}
              >
                <Text style={[styles.categoryTabText, selectedCategory === UNIT_CATEGORIES.WEIGHT && styles.categoryTabTextActive]}>
                  Weight
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.categoryTab, selectedCategory === UNIT_CATEGORIES.VOLUME && styles.categoryTabActive]}
                onPress={() => setSelectedCategory(UNIT_CATEGORIES.VOLUME)}
              >
                <Text style={[styles.categoryTabText, selectedCategory === UNIT_CATEGORIES.VOLUME && styles.categoryTabTextActive]}>
                  Volume
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.categoryTab, selectedCategory === UNIT_CATEGORIES.COUNT && styles.categoryTabActive]}
                onPress={() => setSelectedCategory(UNIT_CATEGORIES.COUNT)}
              >
                <Text style={[styles.categoryTabText, selectedCategory === UNIT_CATEGORIES.COUNT && styles.categoryTabTextActive]}>
                  Count
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.unitsList} showsVerticalScrollIndicator={false}>
              {filteredUnits.map((unit) => (
                <TouchableOpacity
                  key={unit.value}
                  style={[styles.unitItem, value === unit.value && styles.unitItemSelected]}
                  onPress={() => handleSelectUnit(unit.value)}
                >
                  <View>
                    <Text style={[styles.unitLabel, value === unit.value && styles.unitLabelSelected]}>
                      {unit.label}
                    </Text>
                    <Text style={styles.unitAbbreviation}>
                      {unit.abbreviation} {unit.plural && `• ${unit.plural}`}
                    </Text>
                  </View>
                  {value === unit.value && (
                    <Ionicons name="checkmark-circle" size={24} color="#297A56" />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </TouchableOpacity>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  selector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectorText: {
    fontSize: 16,
    color: '#111827',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 20,
    marginBottom: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#111827',
  },
  categoryTabs: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  categoryTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  categoryTabActive: {
    backgroundColor: '#297A56',
  },
  categoryTabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  categoryTabTextActive: {
    color: '#fff',
  },
  unitsList: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  unitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  unitItemSelected: {
    backgroundColor: '#F0F9FF',
    marginHorizontal: -20,
    paddingHorizontal: 20,
  },
  unitLabel: {
    fontSize: 16,
    color: '#111827',
    marginBottom: 2,
  },
  unitLabelSelected: {
    fontWeight: '600',
    color: '#297A56',
  },
  unitAbbreviation: {
    fontSize: 14,
    color: '#6B7280',
  },
});