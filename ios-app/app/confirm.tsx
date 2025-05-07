import { useLocalSearchParams, router } from 'expo-router';
import { useState, useEffect } from 'react';
import {
  View, Image, FlatList, Text, TextInput, StyleSheet, Pressable,
} from 'react-native';

/* ---> temporary dummy parse  -------------------------------- */
const demoItems = [
  { id: '1', name: 'Avocado', qty: '2', unit: 'pcs' },
  { id: '2', name: 'Banana', qty: '5', unit: 'pcs' },
  { id: '3', name: 'Macaroni', qty: '1', unit: 'bag' },
];
/* ------------------------------------------------------------- */

export default function ConfirmScreen() {
  const { photoUri, id, newUnit } = useLocalSearchParams<{
    photoUri?: string;
    id?: string;
    newUnit?: string;
  }>();
  const [items, setItems] = useState(demoItems); // Editable list

  // Update the unit of the item when returning from the select-unit screen
  useEffect(() => {
    if (id && newUnit) {
      setItems((prevItems) =>
        prevItems.map((item) =>
          item.id === id ? { ...item, unit: newUnit } : item
        )
      );
    }
  }, [id, newUnit]);

  /* Cancel -> go back to the index screen */
  function cancel() {
    router.push('/index'); // Navigate to the index screen
  }

  /* Confirm -> later POST to gateway */
  function confirm() {
    console.log('Would POST these items:', items);
    router.back();
  }

  /* Handle quantity change */
  const handleQuantityChange = (id: string, newQty: string) => {
    setItems((prevItems) =>
      prevItems.map((item) =>
        item.id === id ? { ...item, qty: newQty } : item
      )
    );
  };

  /* Navigate to Unit Selection Screen */
  const navigateToUnitSelection = (id: string, currentUnit: string) => {
    router.push({
      pathname: '/select-unit',
      params: { id, currentUnit, photoUri }, // Pass photoUri to retain the image
    });
  };

  return (
    <View style={styles.container}>
      {photoUri && <Image source={{ uri: photoUri }} style={styles.preview} />}

      <Text style={styles.header}>Detected Items</Text>

      <FlatList
        data={items}
        keyExtractor={(i) => i.id}
        contentContainerStyle={{ gap: 6 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.name}</Text>
            <View style={styles.quantityContainer}>
              <TextInput
                style={styles.quantityInput}
                value={item.qty}
                onChangeText={(text) => handleQuantityChange(item.id, text)}
                keyboardType="numeric"
              />
              <Pressable onPress={() => navigateToUnitSelection(item.id, item.unit)}>
                <Text style={styles.unitText}>{item.unit}</Text>
              </Pressable>
            </View>
            <Pressable style={styles.editBtn}>
              <Text style={styles.editBtnText}>Edit</Text>
            </Pressable>
          </View>
        )}
      />

      <View style={styles.row}>
        <Pressable style={styles.cancelButton} onPress={cancel}>
          <Text style={styles.buttonText}>Cancel</Text>
        </Pressable>
        <Pressable style={styles.confirmButton} onPress={confirm}>
          <Text style={styles.buttonText}>Confirm</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 14 },
  preview: { width: '100%', height: 250, borderRadius: 12, marginBottom: 6 },
  header: { fontSize: 18, fontWeight: '600', marginTop: 6 },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
  },
  name: { flex: 1, fontSize: 16 },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  quantityInput: {
    width: 50,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 6,
    padding: 4,
    textAlign: 'center',
  },
  unitText: {
    fontSize: 14,
    color: '#007bff',
    textDecorationLine: 'underline',
  },
  editBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  editBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  cancelButton: {
    backgroundColor: '#d9534f',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  confirmButton: {
    backgroundColor: '#297A56',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});