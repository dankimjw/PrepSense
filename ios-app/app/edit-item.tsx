import { useLocalSearchParams, router } from 'expo-router';
import { Buffer } from 'buffer';
import {
  View, Text, TextInput, FlatList,
  Pressable, StyleSheet,
} from 'react-native';
import { useState } from 'react';     // ✅ add useState

const units = ['pcs', 'bag', 'kg', 'g', 'L', 'ml', 'pack', 'bottle', 'can'];
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

export default function EditItem() {
  const { index, data, photoUri } =
    useLocalSearchParams<{ index: string; data: string; photoUri?: string }>();

  const list = dec(data);
  const idx  = Number(index);
  const [form, setForm] = useState(list[idx]);
  const [show, setShow] = useState(false);

  const pick = (u: string) => {
    setForm((f) => ({ ...f, quantity_unit: u }));
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
      <Text style={styles.label}>Name</Text>
      <TextInput
        style={styles.input}
        value={form.item_name}
        onChangeText={(t) => setForm((f) => ({ ...f, item_name: t }))}
      />

      <Text style={styles.label}>Quantity</Text>
      <TextInput
        style={styles.input}
        value={String(form.quantity_amount)}
        keyboardType="numeric"
        onChangeText={(t) =>
          setForm((f) => ({ ...f, quantity_amount: Number(t) || 0 }))
        }
      />

      <Text style={styles.label}>Unit</Text>
      <Pressable onPress={() => setShow(true)}>
        <Text style={styles.unit}>{form.quantity_unit} ▼</Text>
      </Pressable>

      {show && (
        <FlatList
          data={units}
          keyExtractor={(u) => u}
          renderItem={({ item: u }) => (
            <Pressable style={styles.opt} onPress={() => pick(u)}>
              <Text>{u}</Text>
            </Pressable>
          )}
        />
      )}

      <Pressable style={styles.save} onPress={save}>
        <Text style={styles.saveTxt}>Save</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 12 },
  label: { fontSize: 14, color: '#555' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 6, padding: 8 },
  unit:  {
    borderWidth: 1, borderColor: '#ccc', borderRadius: 6,
    padding: 8, width: 120, textAlign: 'center',
  },
  opt: { padding: 10, borderBottomWidth: 1, borderBottomColor: '#eee' },
  save: {
    marginTop: 20, alignSelf: 'center',
    backgroundColor: '#297A56',
    paddingVertical: 12, paddingHorizontal: 40, borderRadius: 8,
  },
  saveTxt: { color: '#fff', fontWeight: 'bold' },
});
