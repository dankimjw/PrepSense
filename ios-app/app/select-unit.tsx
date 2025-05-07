import { useLocalSearchParams, router } from 'expo-router';
import { useState } from 'react';
import { View, Text, FlatList, Pressable, StyleSheet } from 'react-native';

const quantityUnitOptions = ['pcs', 'bag', 'kg', 'g', 'L', 'ml', 'pack', 'bottle', 'can'];

export default function SelectUnitScreen() {
  const { id, currentUnit, photoUri } = useLocalSearchParams<{
    id: string;
    currentUnit: string;
    photoUri?: string;
  }>();
  const [selectedUnit, setSelectedUnit] = useState(currentUnit); // Track the selected unit

  const handleUnitSelect = (unit: string) => {
    setSelectedUnit(unit); // Highlight the selected unit
    router.replace({
      pathname: '/confirm', // Ensure this matches the file name
      params: { id, newUnit: unit, photoUri }, // Pass the selected unit and photoUri back to the confirm screen
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Select Unit</Text>
      <FlatList
        data={quantityUnitOptions}
        keyExtractor={(item) => item}
        renderItem={({ item }) => (
          <Pressable
            style={[
              styles.unitOption,
              selectedUnit === item && styles.selectedUnitOption, // Highlight selected unit
            ]}
            onPress={() => handleUnitSelect(item)}
          >
            <Text
              style={[
                styles.unitText,
                selectedUnit === item && styles.selectedUnitText, // Highlight selected text
              ]}
            >
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
  unitOption: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
  selectedUnitOption: {
    backgroundColor: '#e0f7fa', // Highlight background color
  },
  unitText: { fontSize: 16 },
  selectedUnitText: {
    fontWeight: 'bold', // Highlight text style
    color: '#007bff',
  },
});