import { useLocalSearchParams, router } from 'expo-router';
import {
  View, Text, FlatList, Pressable, StyleSheet,
} from 'react-native';
import { useState } from 'react';
import { Buffer } from 'buffer';

/* helpers */
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

// Units organized by category for better UX
const units = [
  // Count
  { category: 'Count', units: ['piece', 'slice', 'strip', 'head', 'clove', 'egg'] },
  
  // Pack / Carton
  { category: 'Pack / Carton', units: ['pack', 'carton', 'sleeve', 'tray', 'loaf'] },
  
  // Can / Jar / Bottle
  { category: 'Container', units: ['can', 'jar', 'bottle'] },
  
  // Bag / Box
  { category: 'Bag / Box', units: ['bag', 'box'] },
  
  // Weight (Imperial)
  { category: 'Weight (Imperial)', units: ['oz', 'lb'] },
  
  // Weight (Metric)
  { category: 'Weight (Metric)', units: ['g', 'kg'] },
  
  // Volume (Liquid)
  { category: 'Volume (Liquid)', units: ['fl oz', 'cup', 'qt', 'L', 'gal'] },
  
  // Volume (Dry / Baking)
  { category: 'Volume (Dry)', units: ['tsp', 'tbsp', 'cup'] },
  
  // Other common units
  { category: 'Other', units: ['bunch', 'clove', 'loaf', 'serving'] }
];

// Flatten the array for the selector
const allUnits = units.flatMap(group => group.units);

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
        keyExtractor={(item) => item.category}
        renderItem={({ item }) => (
          <View style={styles.categorySection}>
            <Text style={styles.categoryHeader}>{item.category}</Text>
            <View style={styles.categoryContainer}>
              {item.units.map(unit => (
                <Pressable
                  key={unit}
                  style={[
                    styles.opt,
                    selected === unit && styles.optSel,
                  ]}
                  onPress={() => { setSelected(unit); choose(unit); }}
                >
                  <Text style={[
                    styles.txt,
                    selected === unit && styles.txtSel,
                  ]}>
                    {unit}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>
        )}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    padding: 16,
    backgroundColor: '#f8f9fa',
  },
  header: { 
    fontSize: 20, 
    fontWeight: '600', 
    marginBottom: 16,
    color: '#1a1a1a',
  },
  categoryHeader: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
    marginTop: 12,
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  categorySection: {
    marginBottom: 12,
  },
  categoryContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  opt: { 
    paddingVertical: 10,
    paddingHorizontal: 16,
    margin: 4,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    backgroundColor: '#fff',
  },
  optSel: { 
    backgroundColor: '#e3f2fd',
    borderColor: '#90caf9',
  },
  txt: { 
    fontSize: 15,
    color: '#333',
  },
  txtSel: { 
    fontWeight: '600', 
    color: '#1976d2',
  },
});
