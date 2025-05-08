import { useLocalSearchParams, router } from 'expo-router';
import { Buffer } from 'buffer';
import {
  View, FlatList, Text, TextInput,
  StyleSheet, Pressable, Image,
} from 'react-native';
import { useMemo, useState, useEffect } from 'react';
import { Feather } from '@expo/vector-icons';

/* helpers */
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
const CAMERA_ROUTE = '/';

type Item = {
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
};

export default function ItemsDetected() {
  const { data = '', photoUri, index, newUnit, newItem } =
    useLocalSearchParams<{
      data?: string; photoUri?: string;
      index?: string; newUnit?: string; newItem?: string;
    }>();

  /* decode on every param change */
  const [items, setItems] = useState<Item[]>(() => (data ? dec(data) : []));

  useEffect(() => {
    if (data) setItems(dec(data));
  }, [data]);

  /* row-level changes update local state */
  const setQty = (i: number, v: string) =>
    setItems((prev) =>
      prev.map((it, idx) =>
        idx === i ? { ...it, quantity_amount: Number(v) || 0 } : it,
      ),
    );

  const goSelect = (i: number) =>
    router.push({
      pathname: '/select-unit',
      params: { index: String(i), data: enc(items), photoUri },
    });

  const goEdit = (i: number) =>
    router.push({
      pathname: '/edit-item',
      params: { index: String(i), data: enc(items), photoUri },
    });

  const done = () =>
    router.replace({ pathname: CAMERA_ROUTE, params: { action: 'reset_image' } });

  if (items.length === 0) {
    return (
      <View style={styles.center}>
        <Text>No items detected.</Text>
        <Pressable onPress={done}><Text style={styles.link}>Back</Text></Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(_, i) => i.toString()}
        ListHeaderComponent={
          photoUri ? <Image source={{ uri: photoUri }} style={styles.header} /> : null
        }
        ItemSeparatorComponent={() => <View style={{ height: 6 }} />}
        renderItem={({ item, index }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.item_name}</Text>
            <TextInput
              style={styles.qty}
              value={String(item.quantity_amount)}
              keyboardType="numeric"
              onChangeText={(t) => setQty(index, t)}
            />
            <Pressable onPress={() => goSelect(index)}>
              <Text style={styles.unit}>{item.quantity_unit}</Text>
            </Pressable>
            <Pressable onPress={() => goEdit(index)}>
              <Feather name="edit-2" size={18} color="#007bff" />
            </Pressable>
          </View>
        )}
        contentContainerStyle={{ padding: 20, paddingBottom: 80 }}
      />

      <Pressable style={styles.done} onPress={done}>
        <Text style={styles.doneTxt}>Done</Text>
      </Pressable>
    </View>
  );
}

/* styles */
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { width: '100%', height: 220, borderRadius: 12, marginBottom: 10 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  link: { color: '#007bff', textDecorationLine: 'underline' },
  card: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    padding: 8, borderWidth: 1, borderColor: '#ccc', borderRadius: 8,
  },
  name: { flex: 1, fontSize: 16 },
  qty: {
    width: 50, borderWidth: 1, borderColor: '#ccc',
    borderRadius: 6, padding: 4, textAlign: 'center',
  },
  unit: { fontSize: 14, color: '#007bff', textDecorationLine: 'underline' },
  done: {
    position: 'absolute', bottom: 24, alignSelf: 'center',
    backgroundColor: '#297A56', paddingVertical: 12,
    paddingHorizontal: 32, borderRadius: 8,
  },
  doneTxt: { color: '#fff', fontWeight: 'bold' },
});
