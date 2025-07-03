import React, { useState, useRef, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Dimensions,
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
} from 'react-native';
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Picker } from '@react-native-picker/picker';
import { UnitSelector } from '../UnitSelector';
import { useItems } from '../../context/ItemsContext';
import { Config } from '../../config';

const { width } = Dimensions.get('window');

const categories = [
  'Dairy',
  'Meat',
  'Produce',
  'Bakery',
  'Pantry',
  'Beverages',
  'Frozen',
  'Snacks',
  'Canned Goods',
  'Deli',
  'Seafood',
  'Dairy & Eggs',
  'Bakery & Bread',
  'Meat & Seafood',
  'Fruits & Vegetables',
  'Dairy & Alternatives',
  'Bakery & Pastries',
  'Meat & Poultry',
  'Fruits',
  'Vegetables',
  'Other'
];

interface EditItemModalProps {
  visible: boolean;
  item: any;
  onClose: () => void;
  onUpdate?: (updatedItem: any) => void;
}

export default function EditItemModal({ visible, item, onClose, onUpdate }: EditItemModalProps) {
  const [focusedInput, setFocusedInput] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  const amountInputRef = useRef<TextInput>(null);
  
  const [form, setForm] = useState({
    item_name: '',
    quantity_amount: 0,
    quantity_amount_text: '',
    quantity_unit: 'each',
    expected_expiration: new Date().toISOString().split('T')[0],
    category: 'Other'
  });

  const { updateItem } = useItems();

  // Initialize form when item changes
  useEffect(() => {
    if (item && visible) {
      setForm({
        item_name: item.name || item.item_name || '',
        quantity_amount: item.quantity_amount || 0,
        quantity_amount_text: (item.quantity_amount || 0).toString(),
        quantity_unit: item.quantity_unit || 'each',
        expected_expiration: item.expected_expiration || new Date().toISOString().split('T')[0],
        category: item.category || 'Other'
      });
    }
  }, [item, visible]);

  const expirationDate = form.expected_expiration ? new Date(form.expected_expiration) : new Date();

  const validateForm = (): boolean => {
    if (!form.item_name.trim()) {
      Alert.alert('Validation Error', 'Please enter an item name.');
      return false;
    }

    if (form.quantity_amount <= 0) {
      Alert.alert('Validation Error', 'Quantity must be greater than 0.');
      return false;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expDate = new Date(form.expected_expiration);
    expDate.setHours(0, 0, 0, 0);
    
    if (expDate < today) {
      Alert.alert('Validation Error', 'Expiration date cannot be in the past.');
      return false;
    }

    return true;
  };

  const handleSave = async () => {
    if (!validateForm() || !item) {
      return;
    }

    try {
      setSaving(true);
      
      // Update via API
      const response = await fetch(`${Config.API_BASE_URL}/pantry/items/${item.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_name: form.item_name.trim(),
          quantity: form.quantity_amount,
          unit_of_measurement: form.quantity_unit,
          expiration_date: form.expected_expiration,
          category: form.category || 'Other',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update item');
      }

      // Update local state
      const updatedItem = {
        ...item,
        name: form.item_name.trim(),
        item_name: form.item_name.trim(),
        quantity_amount: form.quantity_amount,
        quantity_unit: form.quantity_unit,
        expected_expiration: form.expected_expiration,
        category: form.category || 'Other',
      };

      updateItem(item.id, updatedItem);
      
      // Call onUpdate callback if provided
      if (onUpdate) {
        onUpdate(updatedItem);
      }

      Alert.alert('Success', 'Item updated successfully', [
        { text: 'OK', onPress: onClose }
      ]);
    } catch (error) {
      console.error('Error updating item:', error);
      Alert.alert('Error', 'Failed to update item. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Item',
      `Are you sure you want to delete ${form.item_name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              setSaving(true);
              const response = await fetch(`${Config.API_BASE_URL}/pantry/items/${item.id}`, {
                method: 'DELETE',
              });

              if (!response.ok) {
                throw new Error('Failed to delete item');
              }

              Alert.alert('Success', 'Item deleted successfully', [
                { text: 'OK', onPress: onClose }
              ]);
            } catch (error) {
              console.error('Error deleting item:', error);
              Alert.alert('Error', 'Failed to delete item. Please try again.');
            } finally {
              setSaving(false);
            }
          }
        }
      ]
    );
  };

  if (!item) return null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <Text style={styles.title}>Edit Item</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <MaterialCommunityIcons name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollContainer} showsVerticalScrollIndicator={false}>
            <View style={styles.formContainer}>
              <Text style={styles.label}>Name *</Text>
              <TextInput
                style={[
                  styles.input,
                  focusedInput === 'item_name' && styles.inputFocused
                ]}
                value={form.item_name}
                onChangeText={(t) => setForm((f) => ({ ...f, item_name: t }))}
                onFocus={() => setFocusedInput('item_name')}
                onBlur={() => setFocusedInput(null)}
                placeholder="Enter item name"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Amount *</Text>
              <View 
                style={[
                  styles.amountOuterContainer,
                  (focusedInput === 'amount' || focusedInput === 'unit') && styles.amountContainerFocused
                ]}
              >
                <View style={styles.amountContainer}>
                  <TextInput
                    ref={amountInputRef}
                    style={[
                      styles.input,
                      styles.amountInput,
                      (focusedInput === 'amount' || focusedInput === 'unit') && { 
                        borderColor: 'transparent',
                        color: '#297A56' 
                      }
                    ]}
                    value={form.quantity_amount_text}
                    keyboardType={Platform.OS === 'ios' ? 'decimal-pad' : 'numeric'}
                    onChangeText={(t) => {
                      const cleaned = t.replace(/[^0-9.]/g, '');
                      const parts = cleaned.split('.');
                      const formatted = parts.length > 2 ? parts[0] + '.' + parts.slice(1).join('') : cleaned;
                      
                      setForm((f) => ({ 
                        ...f, 
                        quantity_amount_text: formatted,
                        quantity_amount: Number(formatted) || 0 
                      }));
                    }}
                    onFocus={() => setFocusedInput('amount')}
                    placeholder="0"
                    placeholderTextColor="#9CA3AF"
                  />
                  <View style={styles.unitSelectorContainer}>
                    <View style={[
                      styles.divider,
                      (focusedInput === 'amount' || focusedInput === 'unit') && styles.dividerFocused
                    ]} />
                    <UnitSelector
                      value={form.quantity_unit}
                      onValueChange={(unit) => {
                        setForm((f) => ({ ...f, quantity_unit: unit }));
                        setFocusedInput(null);
                      }}
                      style={[
                        styles.unitSelector,
                        (focusedInput === 'amount' || focusedInput === 'unit') && styles.unitSelectorFocused
                      ]}
                    />
                  </View>
                </View>
              </View>

              <Text style={styles.label}>Category</Text>
              <Pressable 
                onPress={() => {
                  setFocusedInput('category');
                  setShowCategoryPicker(true);
                }}
                style={[
                  styles.input,
                  { 
                    justifyContent: 'center',
                    ...(focusedInput === 'category' ? styles.inputFocused : {})
                  }
                ]}
              >
                <Text style={{
                  color: focusedInput === 'category' ? '#297A56' : '#2d3748'
                }}>
                  {form.category || 'Select a category'}
                </Text>
              </Pressable>

              <Text style={styles.label}>Expiration Date *</Text>
              <Pressable 
                onPress={() => {
                  setFocusedInput('expiration');
                  setDatePickerVisible(true);
                }}
                style={[
                  styles.input,
                  { 
                    justifyContent: 'center',
                    ...(focusedInput === 'expiration' ? styles.inputFocused : {})
                  }
                ]}
              >
                <Text style={{
                  color: focusedInput === 'expiration' ? '#297A56' : '#2d3748'
                }}>
                  {new Date(form.expected_expiration).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </Text>
              </Pressable>
            </View>
          </ScrollView>

          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={[styles.button, styles.deleteButton]} 
              onPress={handleDelete}
              disabled={saving}
            >
              <Text style={styles.deleteButtonText}>Delete</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.button, styles.saveButton]} 
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <Text style={styles.saveButtonText}>Save Changes</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Category Picker Modal */}
          <Modal visible={showCategoryPicker} transparent animationType="slide">
            <View style={styles.pickerModalOverlay}>
              <View style={styles.pickerModalContent}>
                <Picker
                  selectedValue={form.category || 'Other'}
                  onValueChange={(category) => {
                    setForm((f) => ({ ...f, category }));
                    setShowCategoryPicker(false);
                  }}
                  style={styles.picker}
                  itemStyle={styles.pickerItem}
                >
                  {categories.map(category => (
                    <Picker.Item label={category} value={category} key={category} />
                  ))}
                </Picker>
                <Pressable 
                  onPress={() => setShowCategoryPicker(false)} 
                  style={styles.pickerDone}
                >
                  <Text style={styles.pickerDoneTxt}>Done</Text>
                </Pressable>
              </View>
            </View>
          </Modal>

          {/* Date Picker Modal */}
          <Modal
            visible={datePickerVisible}
            transparent
            animationType="slide"
            onRequestClose={() => setDatePickerVisible(false)}
          >
            <View style={styles.pickerModalOverlay}>
              <View style={[styles.pickerModalContent, { padding: 0 }]}>
                <View style={styles.datePickerHeader}>
                  <Text style={styles.datePickerTitle}>Select Expiration Date</Text>
                </View>
                <DateTimePicker
                  value={expirationDate}
                  mode="date"
                  display="spinner"
                  themeVariant="light"
                  minimumDate={new Date()}
                  onChange={(event: any, selectedDate?: Date) => {
                    if (selectedDate) {
                      setForm((f) => ({
                        ...f,
                        expected_expiration: selectedDate.toISOString().split('T')[0]
                      }));
                      setDatePickerVisible(Platform.OS === 'ios');
                    } else {
                      setDatePickerVisible(false);
                    }
                  }}
                  style={styles.dateTimePicker}
                />
                <View style={styles.pickerButtons}>
                  <Pressable
                    style={styles.pickerButton}
                    onPress={() => setDatePickerVisible(false)}
                  >
                    <Text style={styles.pickerButtonText}>Cancel</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.pickerButton, styles.pickerButtonPrimary]}
                    onPress={() => setDatePickerVisible(false)}
                  >
                    <Text style={[styles.pickerButtonText, styles.pickerButtonPrimaryText]}>Done</Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </Modal>
        </View>
      </View>
    </Modal>
  );
}

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
    maxHeight: '90%',
    minHeight: '75%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    padding: 4,
  },
  scrollContainer: {
    flex: 1,
  },
  formContainer: {
    padding: 20,
    gap: 16,
  },
  label: { 
    fontSize: 15, 
    color: '#222', 
    fontWeight: '600', 
    marginBottom: 2 
  },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 12,
    backgroundColor: '#fff',
    fontSize: 16,
    color: '#2d3748',
    marginBottom: 4,
  },
  inputFocused: {
    borderColor: '#297A56',
    color: '#297A56',
  },
  amountOuterContainer: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#fff',
    marginBottom: 4,
    overflow: 'hidden',
  },
  amountContainerFocused: {
    borderColor: '#297A56',
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative',
  },
  amountInput: {
    flex: 2,
    borderWidth: 0,
    borderRadius: 0,
    marginBottom: 0,
    marginRight: 0,
    backgroundColor: 'transparent',
  },
  divider: {
    position: 'absolute',
    left: 0,
    top: 12,
    bottom: 12,
    width: 1,
    backgroundColor: '#d1d5db',
    zIndex: 1,
  },
  dividerFocused: {
    backgroundColor: '#297A56',
  },
  unitSelectorContainer: {
    flex: 1,
    position: 'relative',
  },
  unitSelector: {
    backgroundColor: 'transparent',
    borderWidth: 0,
    borderRadius: 0,
    height: 48,
    paddingVertical: 0,
  },
  unitSelectorFocused: {
    backgroundColor: '#F0F7F4',
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 16,
    padding: 20,
    paddingTop: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  deleteButton: {
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#DC2626',
  },
  deleteButtonText: {
    color: '#DC2626',
    fontWeight: '600',
    fontSize: 16,
  },
  saveButton: {
    backgroundColor: '#297A56',
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  pickerModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  pickerModalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 0,
    width: '90%',
    maxWidth: 400,
    maxHeight: '80%',
    overflow: 'hidden',
  },
  picker: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  pickerItem: {
    fontSize: 18,
    color: '#222',
  },
  pickerDone: {
    marginTop: 12,
    alignSelf: 'center',
    backgroundColor: '#297A56',
    paddingVertical: 10,
    paddingHorizontal: 32,
    borderRadius: 8,
    marginBottom: 20,
  },
  pickerDoneTxt: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  datePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    width: '100%',
  },
  datePickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  dateTimePicker: {
    width: '100%',
    backgroundColor: '#fff',
  },
  pickerButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    width: '100%',
    marginTop: 16,
    paddingBottom: 30,
    paddingHorizontal: 16,
    gap: 12,
  },
  pickerButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  pickerButtonPrimary: {
    backgroundColor: '#297A56',
  },
  pickerButtonText: {
    fontSize: 16,
    color: '#4A4A4A',
    fontWeight: '500',
  },
  pickerButtonPrimaryText: {
    color: '#fff',
  },
});