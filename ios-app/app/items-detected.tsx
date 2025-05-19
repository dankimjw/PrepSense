import { useLocalSearchParams, router, Stack } from 'expo-router';
import { Buffer } from 'buffer';
import {
  View, FlatList, Text, TextInput,
  StyleSheet, Pressable, Image,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useMemo, useState, useEffect } from 'react';
import { Feather } from '@expo/vector-icons';
import { CustomHeader } from './components/CustomHeader';
import { SafeAreaView as SafeAreaViewRN } from 'react-native-safe-area-context';
import { useItems, type Item } from '../context/ItemsContext';

/* helpers */
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
const CAMERA_ROUTE = '/upload-photo';

// Using Item type from ItemsContext

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

  const { addItems } = useItems();
  
  const done = () => {
    // Add all items to the context
    addItems(items);
    // Navigate back to home
    router.replace('/(tabs)');
  };

  if (items.length === 0) {
    return (
      <View style={styles.center}>
        <Text>No items detected.</Text>
        <Pressable onPress={done}><Text style={styles.link}>Back</Text></Pressable>
      </View>
    );
  }

  return (
    <SafeAreaViewRN style={{ flex: 1, backgroundColor: '#fff' }}>
      <Stack.Screen
        options={{
          headerShown: true,
          header: () => (
            <CustomHeader 
              title="Review Items"
              showBackButton={true}
            />
          ),
        }}
      />
      <View style={{ flex: 1, paddingTop: 16, backgroundColor: '#F9F7F4' }}>
        <FlatList
          data={items}
          keyExtractor={(_, i) => i.toString()}
          ListHeaderComponent={
            photoUri ? <Image source={{ uri: photoUri }} style={styles.header} /> : null
          }
          ItemSeparatorComponent={() => <View style={{ height: 6 }} />}
          renderItem={({ item, index }) => (
            <Pressable
              style={styles.card}
              onPress={() => {
                router.push({
                  pathname: '/edit-item',
                  params: { index: String(index), data: enc(items), photoUri },
                });
              }}
            >
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.item_name}</Text>
                <Text style={styles.details}>
                  {(item.count ?? 1)} × {item.quantity_amount} {item.quantity_unit}
                </Text>
                <Text style={styles.expiry}>
                  Expires: {item.expected_expiration}
                </Text>
              </View>
            </Pressable>
          )}
          contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
        />
      </View>
      <View style={styles.bottomBar}>
        <Pressable style={styles.done} onPress={done}>
          <Text style={styles.doneTxt}>Done</Text>
        </Pressable>
      </View>
    </SafeAreaViewRN>
  );
}

/* styles */
const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#F9F7F4',
  },
  header: { 
    width: '100%', 
    height: 220, 
    borderRadius: 12, 
    marginBottom: 16,
    backgroundColor: '#F9F7F4',
  },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  link: { color: '#007bff', textDecorationLine: 'underline' },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    shadowColor: 'rgba(0, 0, 0, 0.05)',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 1,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 10,
    borderWidth: 0,
    borderLeftWidth: 4,
    borderLeftColor: '#297A56',
  },
  name: { 
    flex: 1, 
    fontSize: 16, 
    fontWeight: '600',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  details: { 
    fontSize: 14, 
    color: '#4A4A4A',
    marginBottom: 4,
  },
  expiry: { 
    fontSize: 13, 
    color: '#666666',
    marginTop: 4,
    fontWeight: '500',
    backgroundColor: '#F0EFED',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  done: {
    width: '100%',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 0,
    marginBottom: 0,
  },
  doneTxt: { color: '#fff', fontWeight: 'bold' },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#222',
    marginTop: 8,
    marginBottom: 16,
    alignSelf: 'center',
    letterSpacing: 0.2,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#eee',
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
  },
});
