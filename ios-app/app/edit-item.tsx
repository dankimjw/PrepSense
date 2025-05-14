import { useLocalSearchParams, router } from 'expo-router';
import { Buffer } from 'buffer';
import {
  View, Text, TextInput, FlatList,
  Pressable, StyleSheet,
  Modal,
  Platform,
} from 'react-native';
import { useState } from 'react';     // ✅ add useState
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';

const units = ['pcs', 'bag', 'kg', 'g', 'L', 'ml', 'pack', 'bottle', 'can'];
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

type Item = {
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  count?: number;
};

export default function EditItem() {
  const { index, data, photoUri } =
    useLocalSearchParams<{ index: string; data: string; photoUri?: string }>();

  const list = dec(data);
  const idx  = Number(index);
  const [form, setForm] = useState<Item>(list[idx]);
  const [show, setShow] = useState(false);
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  const expirationDate = form.expected_expiration ? new Date(form.expected_expiration) : new Date();

  const pick = (u: string) => {
    setForm((f: Item) => ({ ...f, quantity_unit: u }));
    setShow(false);
  };

  const save = () => {
    list[idx] = form;
    router.replace({
      pathname: '/items-detected',
      params: { data: enc(list), photoUri },
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edit Item Details</Text>
      <Text style={styles.label}>Name</Text>
      <TextInput
        style={styles.input}
        value={form.item_name}
        onChangeText={(t) => setForm((f: Item) => ({ ...f, item_name: t }))}
      />

      <Text style={styles.label}>Quantity per Unit</Text>
      <TextInput
        style={styles.input}
        value={String(form.quantity_amount)}
        keyboardType="numeric"
        onChangeText={(t) =>
          setForm((f: Item) => ({ ...f, quantity_amount: Number(t) || 0 }))
        }
      />

      <Text style={styles.label}>Count</Text>
      <TextInput
        style={styles.input}
        value={String(form.count ?? 1)}
        keyboardType="numeric"
        onChangeText={(t) =>
          setForm((f: Item) => ({ ...f, count: Math.max(1, Number(t) || 1) }))
        }
      />

      <Text style={styles.label}>Unit</Text>
      <Pressable onPress={() => setShow(true)}>
        <Text style={styles.unit}>{form.quantity_unit} ▼</Text>
      </Pressable>

      <Text style={styles.label}>Expiration Date</Text>
      <Pressable onPress={() => setDatePickerVisible(true)}>
        <Text style={styles.input}>{expirationDate.toLocaleDateString()}</Text>
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
              display={Platform.OS === 'ios' ? 'inline' : 'default'}
              onChange={(event: any, selectedDate?: Date) => {
                if (Platform.OS !== 'ios') setDatePickerVisible(false);
                if (selectedDate) {
                  setForm((f: Item) => ({ ...f, expected_expiration: selectedDate.toISOString().slice(0, 10) }));
                }
              }}
              style={{ width: '100%', backgroundColor: '#fff', borderRadius: 12 }}
            />
            <Pressable
              style={styles.pickerDone}
              onPress={() => setDatePickerVisible(false)}
            >
              <Text style={styles.pickerDoneTxt}>Done</Text>
            </Pressable>
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
    borderWidth: 0,
    borderRadius: 12,
    padding: 12,
    backgroundColor: '#fff',
    fontSize: 16,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    marginBottom: 4,
  },
  unit:  {
    borderWidth: 0,
    borderRadius: 12,
    padding: 12,
    backgroundColor: '#fff',
    fontSize: 16,
    textAlign: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    marginBottom: 4,
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
