import { useLocalSearchParams, useRouter, useNavigation } from 'expo-router';
import { useItems } from '../context/ItemsContext';
import { Buffer } from 'buffer';
import {
  View, Text, TextInput, FlatList,
  Pressable, StyleSheet,
  Modal,
  Platform,
} from 'react-native';
import { useState, useRef } from 'react';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';

const units = ['pcs', 'bag', 'kg', 'g', 'L', 'ml', 'pack', 'bottle', 'can'];

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
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

type Item = {
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  count?: number;
  category?: string;
};

export default function EditItem() {
  const [focusedInput, setFocusedInput] = useState<string | null>(null);
  const amountInputRef = useRef<TextInput>(null);
  const { index, data, photoUri } =
    useLocalSearchParams<{ index: string; data: string; photoUri?: string }>();

  const list = dec(data);
  const idx  = Number(index);
  const [form, setForm] = useState<Item>(list[idx]);
  const [show, setShow] = useState(false);
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  const expirationDate = form.expected_expiration ? new Date(form.expected_expiration) : new Date();

  const pick = (u: string) => {
    setForm((f: Item) => ({ ...f, quantity_unit: u }));
    setShow(false);
    // Focus the amount input after selecting a unit
    setTimeout(() => {
      amountInputRef.current?.focus();
      setFocusedInput('amount');
    }, 0);
  };

  const router = useRouter();
  const navigation = useNavigation();
  const { updateItem } = useItems();
  
  const save = () => {
    // Update the item in the global state
    updateItem(list[idx].id, form);
    
    // Go back to the previous screen
    if (navigation.canGoBack()) {
      navigation.goBack();
    } else {
      // Fallback to home screen if can't go back
      router.replace({
        pathname: '/(tabs)' as const,
        params: { updated: 'true' },
      });
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edit Item Details</Text>
      <Text style={styles.label}>Name</Text>
      <TextInput
        style={[
          styles.input,
          focusedInput === 'item_name' && styles.inputFocused
        ]}
        value={form.item_name}
        onChangeText={(t) => setForm((f: Item) => ({ ...f, item_name: t }))}
        onFocus={() => setFocusedInput('item_name')}
        onBlur={() => setFocusedInput(null)}
      />

      <Text style={styles.label}>Amount</Text>
      <View 
        style={[
          styles.amountOuterContainer,
          (focusedInput === 'amount' || focusedInput === 'unit') && styles.amountContainerFocused
        ]}
        onStartShouldSetResponder={() => true}
        onResponderGrant={() => setFocusedInput('amount')}
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
            value={String(form.quantity_amount)}
            keyboardType="numeric"
            onChangeText={(t) =>
              setForm((f: Item) => ({ ...f, quantity_amount: Number(t) || 0 }))
            }
            onFocus={() => setFocusedInput('amount')}
          />
          <View style={styles.unitButtonContainer}>
            <View style={[
              styles.divider,
              (focusedInput === 'amount' || focusedInput === 'unit') && styles.dividerFocused
            ]} />
            <Pressable 
              style={({ pressed }) => ({
                ...styles.unitButton,
                ...(pressed && styles.unitButtonPressed),
                ...((focusedInput === 'amount' || focusedInput === 'unit') && { borderColor: 'transparent' })
              })}
              onPress={() => {
                setFocusedInput('unit');
                setShow(true);
              }}
            >
              {({ pressed }) => (
                <Text style={[
                  styles.unitText,
                  (pressed || focusedInput === 'amount' || focusedInput === 'unit') && styles.unitTextPressed
                ]}>
                  {form.quantity_unit}
                  <Text style={[
                    styles.unitCaret,
                    (pressed || focusedInput === 'amount' || focusedInput === 'unit') && { color: '#297A56' }
                  ]}> ▼</Text>
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </View>

      <Text style={styles.label}>Number of Items</Text>
      <TextInput
        style={[
          styles.input,
          focusedInput === 'count' && styles.inputFocused
        ]}
        value={String(form.count ?? 1)}
        keyboardType="numeric"
        onChangeText={(t) =>
          setForm((f: Item) => ({ ...f, count: Math.max(1, Number(t) || 1) }))
        }
        onFocus={() => setFocusedInput('count')}
        onBlur={() => setFocusedInput(null)}
      />

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

      <Text style={styles.label}>Expiration Date</Text>
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
          <View style={styles.modalContent}>
            <DateTimePicker
              value={expirationDate}
              mode="date"
              display="spinner"
              themeVariant="light"
              onChange={(event: any, selectedDate?: Date) => {
                if (selectedDate) {
                  setForm((f: Item) => ({
                    ...f,
                    expected_expiration: selectedDate.toISOString().split('T')[0]
                  }));
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

      <Modal visible={show} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Picker
              selectedValue={form.quantity_unit}
              onValueChange={(u) => {
                setForm((f: Item) => ({ ...f, quantity_unit: u }));
                setShow(false);
              }}
              style={styles.picker}
              itemStyle={styles.pickerItem}
            >
              {units.map(unit => (
                <Picker.Item label={unit} value={unit} key={unit} />
              ))}
            </Picker>
            <Pressable onPress={() => setShow(false)} style={styles.pickerDone}>
              <Text style={styles.pickerDoneTxt}>Done</Text>
            </Pressable>
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

      <Pressable style={styles.save} onPress={save}>
        <Text style={styles.saveTxt}>Save</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 16,
    backgroundColor: '#f8fafc', // Brighter modern iOS background
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
  label: { fontSize: 15, color: '#222', fontWeight: '600', marginBottom: 2 },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 12,
    backgroundColor: '#fff',
    fontSize: 16,
    color: '#2d3748',
    shadowColor: 'transparent',
    shadowOpacity: 0,
    shadowRadius: 0,
    shadowOffset: { width: 0, height: 0 },
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
    position: 'relative',
    marginRight: 0,
    backgroundColor: 'transparent',
  },
  unitButton: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 12,
    height: 48,
    borderWidth: 0,
    borderLeftWidth: 0,
    position: 'relative',
  },
  divider: {
    position: 'absolute',
    left: 0,
    top: 12,
    bottom: 12,
    width: 1, // Match container border width
    backgroundColor: '#d1d5db',
    zIndex: 1,
  },
  dividerFocused: {
    backgroundColor: '#297A56',
  },
  unitButtonContainer: {
    flex: 1,
    position: 'relative',
  },
  unitButtonPressed: {
    backgroundColor: '#f0f9f5',
  },
  unitTextPressed: {
    color: '#297A56',
  },
  dateText: {
    color: '#2d3748',
  },
  dateTextPressed: {
    color: '#297A56',
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
  unitText: {
    fontSize: 16,
    color: '#2d3748',
    fontWeight: '500',
  },
  unitCaret: {
    color: '#718096',
    fontSize: 12,
    opacity: 0.7,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#f8fafc',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: -2 },
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
  pickerDoneTxt: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  save: {
    marginTop: 32,
    alignSelf: 'center',
    backgroundColor: '#297A56',
    paddingVertical: 14,
    paddingHorizontal: 48,
    borderRadius: 12,
    shadowColor: '#297A56',
    shadowOpacity: 0.12,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  saveTxt: { color: '#fff', fontWeight: 'bold', fontSize: 17 },
});
