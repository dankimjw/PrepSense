import { useLocalSearchParams, router } from 'expo-router';
import {
  View, Text, FlatList, Pressable, StyleSheet,
} from 'react-native';
import { useState } from 'react';
import { Buffer } from 'buffer';

/* helpers */
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

const units = ['pcs', 'bag', 'kg', 'g', 'L', 'ml', 'pack', 'bottle', 'can'];

export default function SelectUnit() {
  const { index, data, photoUri } =
    useLocalSearchParams<{ index: string; data: string; photoUri?: string }>();

  const list = dec(data);
  const idx  = Number(index);
  const [selected, setSelected] = useState(list[idx].quantity_unit);

  const choose = (u: string) => {
    /* mutate the array, then encode once */
    list[idx].quantity_unit = u;
    router.replace({
      pathname: '/items-detected',
      params: { data: enc(list), photoUri },   // ← only what ItemsDetected needs
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Select Unit</Text>
      <FlatList
        data={units}
        keyExtractor={(u) => u}
        renderItem={({ item }) => (
          <Pressable
            style={[
              styles.opt,
              selected === item && styles.optSel,
            ]}
            onPress={() => { setSelected(item); choose(item); }}
          >
            <Text style={[
              styles.txt,
              selected === item && styles.txtSel,
            ]}>
              {item}
            </Text>
          </Pressable>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  header: { fontSize: 18, fontWeight: '600', marginBottom: 10 },
  opt: { padding: 12, borderBottomWidth: 1, borderBottomColor: '#ccc' },
  optSel: { backgroundColor: '#e0f7fa' },
  txt: { fontSize: 16 },
  txtSel: { fontWeight: 'bold', color: '#007bff' },
});
