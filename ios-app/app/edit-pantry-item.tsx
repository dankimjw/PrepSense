import { useRouter, useLocalSearchParams } from 'expo-router';
import {
  View, Text, TextInput,
  Pressable, StyleSheet,
  Modal,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useState, useRef, useEffect } from 'react';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useItems } from '../context/ItemsContext';
import { UnitSelector } from '../components/UnitSelector';
import { Config } from '../config';

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

type Item = {
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  category: string;
  quantity_amount_text?: string;
};

export default function EditPantryItem() {
  const [focusedInput, setFocusedInput] = useState<string | null>(null);
  const amountInputRef = useRef<TextInput>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Item>({
    item_name: '',
    quantity_amount: 0,
    quantity_amount_text: '',
    quantity_unit: 'each',
    expected_expiration: new Date().toISOString().split('T')[0],
    category: 'Other'
  });
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  
  const router = useRouter();
  const params = useLocalSearchParams();
  const { items, updateItem } = useItems();
  
  const itemId = params.id as string;
  const expirationDate = form.expected_expiration ? new Date(form.expected_expiration) : new Date();

  useEffect(() => {
    // Load item data
    const item = items.find(i => i.id === itemId);
    if (item) {
      setForm({
        item_name: item.item_name || '',
        quantity_amount: item.quantity_amount || 0,
        quantity_amount_text: item.quantity_amount?.toString() || '',
        quantity_unit: item.quantity_unit || 'each',
        expected_expiration: item.expected_expiration || new Date().toISOString().split('T')[0],
        category: item.category || 'Other'
      });
      setLoading(false);
    } else {
      Alert.alert('Error', 'Item not found', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    }
  }, [itemId, items]);

  const validateForm = (): boolean => {
    if (!form.item_name.trim()) {
      Alert.alert('Validation Error', 'Please enter an item name.');
      return false;
    }

    if (form.quantity_amount <= 0) {
      Alert.alert('Validation Error', 'Quantity must be greater than 0.');
      return false;
    }

    // Unit-specific validation
    const unit = form.quantity_unit.toLowerCase();
    
    // For count units, ensure whole numbers
    if (['each', 'package', 'bag', 'case', 'carton', 'gross'].includes(unit)) {
      if (!Number.isInteger(form.quantity_amount)) {
        Alert.alert(
          'Validation Error', 
          `For ${form.quantity_unit}, please enter a whole number (e.g., 1, 2, 3).`
        );
        return false;
      }
    }
    
    // For weight/volume units, validate reasonable ranges
    if (unit === 'mg' && form.quantity_amount > 1000000) {
      Alert.alert(
        'Validation Tip', 
        'That\'s more than 1kg. Consider using grams or kilograms instead.'
      );
      return false;
    }
    
    if (unit === 'ml' && form.quantity_amount > 10000) {
      Alert.alert(
        'Validation Tip', 
        'That\'s more than 10 liters. Consider using liters instead.'
      );
      return false;
    }
    
    if (unit === 'tsp' && form.quantity_amount > 48) {
      Alert.alert(
        'Validation Tip', 
        'That\'s more than 1 cup. Consider using cups or tablespoons instead.'
      );
      return false;
    }
    
    if (unit === 'tbsp' && form.quantity_amount > 16) {
      Alert.alert(
        'Validation Tip', 
        'That\'s more than 1 cup. Consider using cups instead.'
      );
      return false;
    }

    // Validate maximum quantity
    if (form.quantity_amount > 999999) {
      Alert.alert('Validation Error', 'Quantity seems too large. Please check the value.');
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

  const save = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      
      // Update via API
      const response = await fetch(`${Config.API_BASE_URL}/pantry/items/${itemId}`, {
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
      const currentItem = items.find(i => i.id === itemId);
      if (currentItem) {
        updateItem(itemId, {
          ...currentItem,
          item_name: form.item_name.trim(),
          quantity_amount: form.quantity_amount,
          quantity_unit: form.quantity_unit,
          expected_expiration: form.expected_expiration,
          category: form.category || 'Other',
        });
      }

      Alert.alert('Success', 'Item updated successfully', [
        { text: 'OK', onPress: () => router.back() }
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
              const response = await fetch(`${Config.API_BASE_URL}/pantry/items/${itemId}`, {
                method: 'DELETE',
              });

              if (!response.ok) {
                throw new Error('Failed to delete item');
              }

              Alert.alert('Success', 'Item deleted successfully', [
                { text: 'OK', onPress: () => router.replace('/(tabs)') }
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

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color="#297A56" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edit Item</Text>
      <Text style={styles.label}>Name *</Text>
      <TextInput
        style={[
          styles.input,
          focusedInput === 'item_name' && styles.inputFocused
        ]}
        value={form.item_name}
        onChangeText={(t) => setForm((f: Item) => ({ ...f, item_name: t }))}
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
              let formatted = parts.length > 2 ? parts[0] + '.' + parts.slice(1).join('') : cleaned;
              
              // For count units, don't allow decimal points
              const unit = form.quantity_unit.toLowerCase();
              if (['each', 'package', 'bag', 'case', 'carton', 'gross'].includes(unit)) {
                formatted = formatted.split('.')[0]; // Remove decimal part
              }
              
              setForm((f: Item) => ({ 
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
                // If switching to a count unit and we have decimals, round to nearest integer
                const isCountUnit = ['each', 'package', 'bag', 'case', 'carton', 'gross'].includes(unit.toLowerCase());
                if (isCountUnit && form.quantity_amount % 1 !== 0) {
                  const rounded = Math.round(form.quantity_amount);
                  setForm((f: Item) => ({ 
                    ...f, 
                    quantity_unit: unit,
                    quantity_amount: rounded,
                    quantity_amount_text: rounded.toString()
                  }));
                  Alert.alert(
                    'Quantity Adjusted', 
                    `Rounded to ${rounded} for ${unit} unit.`
                  );
                } else {
                  setForm((f: Item) => ({ ...f, quantity_unit: unit }));
                }
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

      <Modal
        visible={datePickerVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setDatePickerVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { padding: 0 }]}>
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
                  setForm((f: Item) => ({
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

      <Modal visible={showCategoryPicker} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Picker
              selectedValue={form.category || 'Other'}
              onValueChange={(category) => {
                setForm((f: Item) => ({ ...f, category }));
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

      <View style={styles.buttonContainer}>
        <Pressable 
          style={[styles.button, styles.deleteButton]} 
          onPress={handleDelete}
          disabled={saving}
        >
          <Text style={styles.deleteButtonText}>Delete Item</Text>
        </Pressable>
        
        <Pressable 
          style={[styles.button, styles.saveButton]} 
          onPress={save}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.saveButtonText}>Save Changes</Text>
          )}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 16,
    backgroundColor: '#f8fafc',
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#222',
    marginTop: 8,
    marginBottom: 16,
    alignSelf: 'center',
    letterSpacing: 0.2,
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
  dateTimePicker: {
    width: '100%',
    backgroundColor: '#fff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  modalContent: {
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
  buttonContainer: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 32,
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
    shadowColor: '#297A56',
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 17,
  },
});