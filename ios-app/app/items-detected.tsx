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

// Helper function to get category color
const getCategoryColor = (category: string) => {
  const colors = {
    'Dairy': '#E0F2FE',
    'Meat': '#FEE2E2',
    'Produce': '#DCFCE7',
    'Bakery': '#FEF3C7',
    'Pantry': '#EDE9FE',
    'Beverages': '#E0E7FF',
    'Frozen': '#E0F2F9',
    'Snacks': '#FCE7F3',
    'Canned Goods': '#F3E8FF',
    'Deli': '#FEF08A',
    'Seafood': '#BFDBFE',
    'Dairy & Eggs': '#DBEAFE',
    'Bakery & Bread': '#FEF3C7',
    'Meat & Seafood': '#FECACA',
    'Fruits & Vegetables': '#DCFCE7',
    'Dairy & Alternatives': '#E0F2FE',
    'Bakery & Pastries': '#FEF3C7',
    'Meat & Poultry': '#FEE2E2',
    'Fruits': '#DCFCE7',
    'Vegetables': '#DCFCE7',
    'Default': '#F3F4F6',
  };
  
  return colors[category as keyof typeof colors] || colors['Default'];
};

// Using Item type from ItemsContext

export default function ItemsDetected() {
  const { data: initialData = '', photoUri, index, newUnit, newItem } =
    useLocalSearchParams<{
      data?: string; photoUri?: string;
      index?: string; newUnit?: string; newItem?: string;
    }>();

  /* decode on initial load */
  const [items, setItems] = useState<Item[]>(() => (initialData ? dec(initialData) : []));

  // Handle updates when navigating back with new data
  useEffect(() => {
    if (initialData) {
      const decodedData = dec(initialData);
      setItems(prevItems => {
        // Only update if the data has actually changed
        return JSON.stringify(prevItems) !== JSON.stringify(decodedData) 
          ? decodedData 
          : prevItems;
      });
    }
  }, [initialData]);

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

  const goEdit = (i: number) => {
    router.push({
      pathname: '/edit-item',
      params: { 
        index: String(i), 
        data: enc(items), 
        photoUri,
        // Add a timestamp to force re-render when navigating back
        _t: Date.now().toString()
      },
    });
  };

  const { addItems } = useItems();
  
  const done = () => {
    // Add all items to the context
    addItems(items);
    // Navigate back to home
    router.replace('/(tabs)');
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      'Dairy': '#4F46E5',
      'Meat': '#DC2626',
      'Produce': '#16A34A',
      'Bakery': '#D97706',
      'Pantry': '#9333EA',
      'Beverages': '#0284C7',
      'Frozen': '#0EA5E9',
      'Snacks': '#E11D48',
      'Canned Goods': '#F59E0B',
      'Deli': '#10B981',
      'Seafood': '#06B6D4',
      'Dairy & Eggs': '#8B5CF6',
      'Bakery & Bread': '#F59E0B',
      'Meat & Seafood': '#EF4444',
      'Fruits & Vegetables': '#10B981',
      'Dairy & Alternatives': '#3B82F6',
      'Bakery & Pastries': '#D97706',
      'Meat & Poultry': '#DC2626',
      'Fruits': '#22C55E',
      'Vegetables': '#10B981',
    };
    return colors[category] || '#6B7280';
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
                  params: { 
                    index: String(index), 
                    data: enc(items), 
                    photoUri,
                    // Add a timestamp to force re-render when navigating back
                    _t: Date.now().toString()
                  },
                });
              }}
            >
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.item_name}</Text>
                <Text style={styles.details}>
                  {(item.count ?? 1)} × {item.quantity_amount} {item.quantity_unit}
                </Text>
                <View style={styles.metaContainer}>
                  <Text style={styles.expiry}>
                    Expires: {item.expected_expiration}
                  </Text>
                  <View style={[
                    styles.categoryChip,
                    { 
                      backgroundColor: getCategoryColor(item.category || 'Uncategorized'),
                      opacity: item.category ? 1 : 0.7
                    }
                  ]}>
                    <Text style={styles.categoryText}>
                      {item.category || 'Uncategorized'}
                    </Text>
                  </View>
                </View>
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
  metaContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  expiry: { 
    fontSize: 13, 
    color: '#666666',
    fontWeight: '500',
    backgroundColor: '#F0EFED',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  category: {
    fontSize: 13,
    color: '#fff',
    fontWeight: '500',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
    overflow: 'hidden',
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
  metaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginTop: 4,
    gap: 8,
  },
  categoryChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#E5F5EA',
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#0F5C36',
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
