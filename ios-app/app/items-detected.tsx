// app/items-detected.tsx - Part of the PrepSense mobile app
import { useLocalSearchParams, router, Stack } from 'expo-router';
import { Buffer } from 'buffer';
import {
  View, FlatList, Text, TextInput,
  StyleSheet, Pressable, Image,
  Alert,
  SafeAreaView,
  ActivityIndicator
} from 'react-native';
import { useMemo, useState, useEffect } from 'react';
import { Feather } from '@expo/vector-icons';
import { CustomHeader } from './components/CustomHeader';
import { SafeAreaView as SafeAreaViewRN } from 'react-native-safe-area-context';
import { useItems, type Item } from '../context/ItemsContext';
import { Config } from '../config';

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
  const [isSaving, setIsSaving] = useState(false);
  const [savedToBigQuery, setSavedToBigQuery] = useState(false);
  
  // Just add to local context and navigate home
  const done = () => {
    // Add all items to the context
    addItems(items);
    // Navigate back to home
    router.replace('/(tabs)');
  };
  
  // Save items to BigQuery and add to local context
  const saveToDatabase = async () => {
    if (isSaving || items.length === 0) return;
    
    try {
      setIsSaving(true);
      
      // Transform items to match backend expectations
      const transformedItems = items.map(item => ({
        item_name: item.item_name,
        quantity_amount: item.quantity_amount,
        quantity_unit: item.quantity_unit,
        expected_expiration: item.expected_expiration,
        category: item.category || 'Uncategorized',
        brand: item.brand || 'Generic'
      }));
      
      // Call the backend API endpoint to save items to BigQuery
      const response = await fetch(`${Config.API_BASE_URL}/images/save-detected-items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: transformedItems,
          user_id: 111 // Default demo user ID
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(errorData.detail || 'Failed to save items');
      }
      
      const result = await response.json();
      console.log('Items saved to BigQuery:', result);
      
      // Add to local context as well
      addItems(items);
      
      // Show success message with more details
      const errorInfo = result.error_count > 0 
        ? `\n${result.error_count} items had errors.` 
        : '';
      
      Alert.alert(
        'Success', 
        `${result.saved_count} items saved to database successfully!${errorInfo}`,
        [{ text: 'OK', onPress: () => {
          setSavedToBigQuery(true);
          router.replace('/(tabs)');
        }}]
      );
      
    } catch (error: any) {
      console.error('Error saving items to BigQuery:', error);
      Alert.alert('Error', `Failed to save items: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
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
      <View style={{ flex: 1, backgroundColor: '#F9F7F4' }}>
        <View style={styles.summaryContainer}>
          <Text style={styles.summaryText}>
            {items.length} {items.length === 1 ? 'item' : 'items'} detected
          </Text>
          <Text style={styles.summarySubtext}>
            Review and confirm before saving
          </Text>
        </View>
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
          contentContainerStyle={{ padding: 20, paddingBottom: 120 }}
        />
      </View>
      <View style={styles.bottomBar}>
        <View style={styles.buttonContainer}>
          <Pressable style={styles.skipButton} onPress={done}>
            <Text style={styles.skipButtonText}>Skip</Text>
          </Pressable>
          <Pressable 
            style={[styles.confirmButton, { opacity: isSaving ? 0.7 : 1 }]} 
            onPress={saveToDatabase}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Feather name="check" size={20} color="#fff" style={{ marginRight: 8 }} />
                <Text style={styles.confirmButtonText}>Confirm & Save</Text>
              </>
            )}
          </Pressable>
        </View>
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
  summaryContainer: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  summaryText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  summarySubtext: {
    fontSize: 14,
    color: '#6B7280',
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
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  skipButton: {
    flex: 1,
    height: 52,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  skipButtonText: {
    color: '#6B7280',
    fontSize: 16,
    fontWeight: '600',
  },
  confirmButton: {
    flex: 2,
    height: 52,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    flexDirection: 'row',
    shadowColor: '#297A56',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  confirmButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
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
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingBottom: 32,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: -4 },
    elevation: 10,
  },
});
