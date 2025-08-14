import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { RecipeCompletionModal } from '../components/modals/RecipeCompletionModal';
import { PantryItem } from '../services/api';

// Test data
const mockRecipe = {
  name: "Chicken Pasta",
  ingredients: [
    "2 cups pasta",
    "500g chicken breast",
    "1 cup heavy cream",
    "2 tbsp olive oil",
    "3 cloves garlic",
    "1/2 cup parmesan cheese",
    "200ml milk",
    "2 tsp salt"
  ],
  pantry_item_matches: {
    "2 cups pasta": [
      { pantry_item_id: 1, product_name: "Pasta", quantity: 3, unit: "cup" }
    ],
    "500g chicken breast": [
      { pantry_item_id: 2, product_name: "Chicken Breast", quantity: 800, unit: "g" }
    ],
    "1 cup heavy cream": [
      { pantry_item_id: 3, product_name: "Heavy Cream", quantity: 250, unit: "ml" }
    ],
    "200ml milk": [
      { pantry_item_id: 4, product_name: "Milk", quantity: 1, unit: "l" }
    ]
  }
};

const mockPantryItems: PantryItem[] = [
  {
    id: "1",
    item_name: "Pasta",
    quantity_amount: "3",
    quantity_unit: "cup",
    expiration_date: "2025-02-15",
    category: "Grains"
  },
  {
    id: "2",
    item_name: "Chicken Breast",
    quantity_amount: "800",
    quantity_unit: "g",
    expiration_date: "2025-01-28",
    category: "Protein"
  },
  {
    id: "3",
    item_name: "Heavy Cream",
    quantity_amount: "250",
    quantity_unit: "ml",
    expiration_date: "2025-02-01",
    category: "Dairy"
  },
  {
    id: "4",
    item_name: "Milk",
    quantity_amount: "1",
    quantity_unit: "l",
    expiration_date: "2025-01-30",
    category: "Dairy"
  }
];

export default function TestRecipeCompletionScreen() {
  const [modalVisible, setModalVisible] = useState(false);

  const handleConfirm = (ingredientUsages: any[]) => {
    console.log('Confirmed ingredient usages:', ingredientUsages);
    setModalVisible(false);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Test Recipe Completion Modal</Text>
        <Text style={styles.subtitle}>
          Enhanced with taller sliders, rounder edges, and unit conversion
        </Text>
      </View>

      <TouchableOpacity
        style={styles.testButton}
        onPress={() => setModalVisible(true)}
      >
        <Text style={styles.buttonText}>Open Recipe Completion Modal</Text>
      </TouchableOpacity>

      <View style={styles.features}>
        <Text style={styles.featureTitle}>New Features:</Text>
        <Text style={styles.featureItem}>✓ Taller slider area for better control</Text>
        <Text style={styles.featureItem}>✓ Rounder card edges (20px radius)</Text>
        <Text style={styles.featureItem}>✓ Discrete quantity slider with cooking-friendly steps</Text>
        <Text style={styles.featureItem}>✓ Smart step sizes (1/4 tsp, 1/8 cup, 5g, etc.)</Text>
        <Text style={styles.featureItem}>✓ Easy-to-use unit dropdown selector</Text>
        <Text style={styles.featureItem}>✓ Modal-based unit picker (no scrolling needed)</Text>
        <Text style={styles.featureItem}>✓ Real-time unit conversion calculations</Text>
        <Text style={styles.featureItem}>✓ Stepped quick buttons (1/4, Half, 3/4, All)</Text>
      </View>

      <RecipeCompletionModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onConfirm={handleConfirm}
        recipe={mockRecipe}
        pantryItems={mockPantryItems}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 60,
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  testButton: {
    margin: 20,
    backgroundColor: '#6366F1',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  features: {
    margin: 20,
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  featureItem: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
    paddingLeft: 8,
  },
});