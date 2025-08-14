import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { parseIngredientsList } from '../utils/ingredientParser';
import { formatIngredientQuantity } from '../utils/numberFormatting';

interface SelectableIngredient {
  original: string;
  name: string;
  quantity?: string;
  selected: boolean;
}

export default function SelectIngredientsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const [ingredients, setIngredients] = useState<SelectableIngredient[]>([]);
  const [selectAll, setSelectAll] = useState(true);

  useEffect(() => {
    if (params.ingredients) {
      try {
        const ingredientsList = JSON.parse(params.ingredients as string);
        
        // Parse and prepare ingredients for selection
        const selectableIngredients = ingredientsList.map((ing: string) => {
          const parsed = parseIngredientsList([ing])[0];
          
          let displayName = '';
          let displayQuantity = '';
          
          if (parsed && parsed.name && parsed.name.trim()) {
            displayName = parsed.name;
            if (parsed.quantity && parsed.unit) {
              // Use proper fraction formatting
              const formattedQuantity = formatIngredientQuantity(parsed.quantity, parsed.unit);
              displayQuantity = formattedQuantity ? `${formattedQuantity} ${parsed.unit}` : `${parsed.quantity} ${parsed.unit}`;
            } else if (parsed.quantity) {
              // Use proper fraction formatting for quantity only
              displayQuantity = formatIngredientQuantity(parsed.quantity, '') || `${parsed.quantity}`;
            }
          } else {
            displayName = ing;
          }
          
          return {
            original: ing,
            name: displayName,
            quantity: displayQuantity,
            selected: true,
          };
        });
        
        setIngredients(selectableIngredients);
      } catch (error) {
        console.error('Error parsing ingredients:', error);
        Alert.alert('Error', 'Failed to load ingredients');
        router.back();
      }
    }
  }, [params.ingredients]);

  const toggleIngredient = (index: number) => {
    const updated = [...ingredients];
    updated[index].selected = !updated[index].selected;
    setIngredients(updated);
    
    // Update select all state
    const allSelected = updated.every(ing => ing.selected);
    setSelectAll(allSelected);
  };

  const toggleSelectAll = () => {
    const newSelectAll = !selectAll;
    setSelectAll(newSelectAll);
    setIngredients(ingredients.map(ing => ({ ...ing, selected: newSelectAll })));
  };

  const handleAddSelected = async () => {
    const selectedIngredients = ingredients.filter(ing => ing.selected);
    
    if (selectedIngredients.length === 0) {
      Alert.alert('No Selection', 'Please select at least one ingredient');
      return;
    }

    try {
      // Get existing shopping list from AsyncStorage
      const STORAGE_KEY = '@PrepSense_ShoppingList';
      const savedList = await AsyncStorage.getItem(STORAGE_KEY);
      let existingItems = [];
      
      if (savedList) {
        existingItems = JSON.parse(savedList);
      }

      // Convert selected ingredients to shopping list items
      const newItems = selectedIngredients.map((ingredient, index) => ({
        id: `${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`,
        name: ingredient.name,
        quantity: ingredient.quantity || undefined,
        checked: false,
        addedAt: new Date(),
      }));

      // Combine with existing items
      const updatedList = [...existingItems, ...newItems];
      
      // Save back to AsyncStorage
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updatedList));

      Alert.alert(
        'Added to Shopping List',
        `${selectedIngredients.length} item${selectedIngredients.length > 1 ? 's' : ''} added to your shopping list.`,
        [
          { 
            text: 'View List', 
            onPress: () => {
              router.back();
              router.push('/(tabs)/shopping-list');
            }
          },
          { 
            text: 'OK',
            onPress: () => router.back()
          }
        ]
      );
    } catch (error) {
      console.error('Error adding to shopping list:', error);
      Alert.alert('Error', 'Failed to add items to shopping list. Please try again.');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.title}>Select Ingredients</Text>
        <View style={styles.placeholder} />
      </View>

      <View style={styles.subHeader}>
        <Text style={styles.recipeName}>{params.recipeName as string}</Text>
        <TouchableOpacity onPress={toggleSelectAll} style={styles.selectAllButton}>
          <Ionicons 
            name={selectAll ? "checkbox" : "square-outline"} 
            size={20} 
            color="#297A56" 
          />
          <Text style={styles.selectAllText}>Select All</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {ingredients.map((ingredient, index) => (
          <TouchableOpacity
            key={index}
            style={styles.ingredientItem}
            onPress={() => toggleIngredient(index)}
          >
            <Ionicons 
              name={ingredient.selected ? "checkbox" : "square-outline"} 
              size={24} 
              color={ingredient.selected ? "#297A56" : "#999"} 
            />
            <View style={styles.ingredientInfo}>
              <Text style={styles.ingredientName}>{ingredient.name}</Text>
              {ingredient.quantity && (
                <Text style={styles.ingredientQuantity}>{ingredient.quantity}</Text>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.bottomActions}>
        <TouchableOpacity
          style={[styles.addButton, ingredients.filter(i => i.selected).length === 0 && styles.addButtonDisabled]}
          onPress={handleAddSelected}
          disabled={ingredients.filter(i => i.selected).length === 0}
        >
          <Ionicons name="cart" size={20} color="#fff" />
          <Text style={styles.addButtonText}>
            Add {ingredients.filter(i => i.selected).length} to Shopping List
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    padding: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  placeholder: {
    width: 32,
  },
  subHeader: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  recipeName: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  selectAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  selectAllText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  ingredientItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    gap: 12,
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  ingredientQuantity: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  bottomActions: {
    backgroundColor: '#fff',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  addButton: {
    backgroundColor: '#297A56',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  addButtonDisabled: {
    backgroundColor: '#ccc',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});