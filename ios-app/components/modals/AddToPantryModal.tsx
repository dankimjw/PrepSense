// components/modals/AddToPantryModal.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { UnitSelector } from '../UnitSelector';
import DateTimePicker from '@react-native-community/datetimepicker';

interface ShoppingItem {
  id: string;
  name: string;
  quantity?: string;
  checked: boolean;
  addedAt: Date;
}

interface PantryItemData {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  expirationDate: string;
  category: string;
}

interface AddToPantryModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: (items: PantryItemData[]) => void;
  shoppingItems: ShoppingItem[];
  loading?: boolean;
}

export const AddToPantryModal: React.FC<AddToPantryModalProps> = ({
  visible,
  onClose,
  onConfirm,
  shoppingItems,
  loading = false,
}) => {
  const [pantryItems, setPantryItems] = useState<PantryItemData[]>([]);
  const [showDatePicker, setShowDatePicker] = useState<string | null>(null);

  useEffect(() => {
    if (visible && shoppingItems.length > 0) {
      initializePantryItems();
    }
  }, [visible, shoppingItems]);

  const initializePantryItems = () => {
    const items: PantryItemData[] = shoppingItems.map(item => {
      // Parse quantity from shopping list item
      let quantity = 1;
      let unit = 'each';
      
      if (item.quantity) {
        // Try to extract number and unit from quantity string
        const match = item.quantity.match(/(\\d+(?:\\.\\d+)?)\\s*(.*)$/);
        if (match) {
          quantity = parseFloat(match[1]);
          unit = match[2].trim() || 'each';
        }
      }
      
      return {
        id: item.id,
        name: item.name,
        quantity: quantity,
        unit: unit,
        expirationDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Default to 1 week
        category: 'Other'
      };
    });
    
    setPantryItems(items);
  };

  const updateItem = (itemId: string, field: keyof PantryItemData, value: any) => {
    setPantryItems(prev => 
      prev.map(item => 
        item.id === itemId ? { ...item, [field]: value } : item
      )
    );
  };

  const handleConfirm = () => {
    // Validate all items
    const invalidItems = pantryItems.filter(item => 
      !item.name.trim() || item.quantity <= 0 || !item.unit.trim()
    );
    
    if (invalidItems.length > 0) {
      Alert.alert(
        'Invalid Items',
        'Please ensure all items have a name, valid quantity, and unit.',
        [{ text: 'OK' }]
      );
      return;
    }
    
    onConfirm(pantryItems);
  };

  const renderPantryItem = (item: PantryItemData, index: number) => {
    return (
      <View key={item.id} style={styles.itemCard}>
        <View style={styles.itemHeader}>
          <Text style={styles.itemNumber}>{index + 1}</Text>
          <Text style={styles.itemName}>{item.name}</Text>
        </View>
        
        {/* Quantity and Unit Row */}
        <View style={styles.quantityRow}>
          <View style={styles.quantityContainer}>
            <Text style={styles.fieldLabel}>Quantity</Text>
            <TextInput
              style={styles.quantityInput}
              value={item.quantity.toString()}
              onChangeText={(text) => {
                const num = parseFloat(text) || 0;
                updateItem(item.id, 'quantity', num);
              }}
              keyboardType="numeric"
              placeholder="0"
            />
          </View>
          
          <View style={styles.unitContainer}>
            <Text style={styles.fieldLabel}>Unit</Text>
            <UnitSelector
              value={item.unit}
              onValueChange={(unit) => updateItem(item.id, 'unit', unit)}
              style={styles.unitSelector}
              itemName={item.name}
            />
          </View>
        </View>
        
        {/* Expiration Date */}
        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Expiration Date</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowDatePicker(item.id)}
          >
            <Text style={styles.dateText}>
              {new Date(item.expirationDate).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </Text>
            <Ionicons name="calendar-outline" size={20} color="#666" />
          </TouchableOpacity>
        </View>
        
        {/* Category */}
        <View style={styles.fieldContainer}>
          <Text style={styles.fieldLabel}>Category</Text>
          <View style={styles.categoryContainer}>
            {['Produce', 'Dairy', 'Meat', 'Pantry', 'Snacks', 'Other'].map(category => (
              <TouchableOpacity
                key={category}
                style={[
                  styles.categoryButton,
                  item.category === category && styles.categoryButtonSelected
                ]}
                onPress={() => updateItem(item.id, 'category', category)}
              >
                <Text style={[
                  styles.categoryButtonText,
                  item.category === category && styles.categoryButtonTextSelected
                ]}>
                  {category}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        {/* Date Picker Modal */}
        {showDatePicker === item.id && (
          <Modal transparent animationType="fade">
            <View style={styles.datePickerOverlay}>
              <View style={styles.datePickerContainer}>
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={() => setShowDatePicker(null)}>
                    <Text style={styles.datePickerCancel}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={styles.datePickerTitle}>Expiration Date</Text>
                  <TouchableOpacity onPress={() => setShowDatePicker(null)}>
                    <Text style={styles.datePickerDone}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={new Date(item.expirationDate)}
                  mode="date"
                  display="spinner"
                  minimumDate={new Date()}
                  onChange={(event, selectedDate) => {
                    if (selectedDate) {
                      updateItem(item.id, 'expirationDate', selectedDate.toISOString().split('T')[0]);
                    }
                  }}
                  style={styles.datePicker}
                />
              </View>
            </View>
          </Modal>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#374151" />
          </TouchableOpacity>
          <Text style={styles.title}>Add to Pantry</Text>
          <View style={styles.placeholder} />
        </View>

        <View style={styles.summary}>
          <Text style={styles.summaryText}>
            Adding {pantryItems.length} item{pantryItems.length > 1 ? 's' : ''} to your pantry
          </Text>
          <Text style={styles.summarySubtext}>
            Review and adjust quantities, units, and expiration dates
          </Text>
        </View>

        {/* Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {pantryItems.map(renderPantryItem)}
          <View style={styles.bottomPadding} />
        </ScrollView>

        {/* Footer */}
        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.cancelButton} 
            onPress={onClose}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.confirmButton, loading && styles.confirmButtonDisabled]} 
            onPress={handleConfirm}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="basket" size={20} color="#fff" />
                <Text style={styles.confirmButtonText}>Add to Pantry</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  summary: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  summaryText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  summarySubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  itemNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#297A56',
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  itemName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  quantityRow: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 12,
  },
  quantityContainer: {
    flex: 1,
  },
  unitContainer: {
    flex: 1,
  },
  fieldContainer: {
    marginBottom: 16,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  quantityInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  unitSelector: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    backgroundColor: '#fff',
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#fff',
  },
  dateText: {
    fontSize: 16,
    color: '#374151',
  },
  categoryContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#fff',
  },
  categoryButtonSelected: {
    backgroundColor: '#297A56',
    borderColor: '#297A56',
  },
  categoryButtonText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  categoryButtonTextSelected: {
    color: '#fff',
  },
  datePickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  datePickerContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 0,
    width: '90%',
    maxHeight: '60%',
  },
  datePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  datePickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  datePickerCancel: {
    fontSize: 16,
    color: '#6B7280',
  },
  datePickerDone: {
    fontSize: 16,
    color: '#297A56',
    fontWeight: '600',
  },
  datePicker: {
    backgroundColor: '#fff',
  },
  bottomPadding: {
    height: 20,
  },
  footer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  confirmButton: {
    flex: 2,
    flexDirection: 'row',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  confirmButtonDisabled: {
    opacity: 0.6,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});