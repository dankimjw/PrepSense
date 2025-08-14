import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AddToPantryModal } from '../../components/modals/AddToPantryModal';
import { TabScreenTransition } from '../../components/navigation/TabScreenTransition';

interface ShoppingItem {
  id: string;
  name: string;
  quantity?: string;
  checked: boolean;
  addedAt: Date;
}

const STORAGE_KEY = '@PrepSense_ShoppingList';

export default function ShoppingListScreen() {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQuantity, setNewItemQuantity] = useState('');
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [showAddToPantryModal, setShowAddToPantryModal] = useState(false);
  const [selectedItemsForPantry, setSelectedItemsForPantry] = useState<ShoppingItem[]>([]);
  const insets = useSafeAreaInsets();

  // Load shopping list from storage
  useEffect(() => {
    loadShoppingList();
  }, []);

  // Save shopping list to storage whenever it changes
  useEffect(() => {
    saveShoppingList();
  }, [items]);

  const loadShoppingList = async () => {
    try {
      const savedList = await AsyncStorage.getItem(STORAGE_KEY);
      if (savedList) {
        const parsedList = JSON.parse(savedList);
        // Convert date strings back to Date objects
        const itemsWithDates = parsedList.map((item: any) => ({
          ...item,
          addedAt: new Date(item.addedAt),
        }));
        setItems(itemsWithDates);
      }
    } catch (error) {
      console.error('Error loading shopping list:', error);
    }
  };

  const saveShoppingList = async () => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (error) {
      console.error('Error saving shopping list:', error);
    }
  };

  const addItem = () => {
    if (!newItemName.trim()) {
      Alert.alert('Error', 'Please enter an item name');
      return;
    }

    const newItem: ShoppingItem = {
      id: Date.now().toString(),
      name: newItemName.trim(),
      quantity: newItemQuantity.trim() || undefined,
      checked: false,
      addedAt: new Date(),
    };

    setItems([...items, newItem]);
    setNewItemName('');
    setNewItemQuantity('');
    setIsAddingItem(false);
  };

  const toggleItem = (id: string) => {
    setItems(items.map(item => 
      item.id === id ? { ...item, checked: !item.checked } : item
    ));
  };

  const deleteItem = (id: string) => {
    Alert.alert(
      'Delete Item',
      'Are you sure you want to remove this item?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: () => setItems(items.filter(item => item.id !== id))
        }
      ]
    );
  };

  const clearCheckedItems = () => {
    const checkedCount = items.filter(item => item.checked).length;
    if (checkedCount === 0) {
      Alert.alert('Info', 'No checked items to clear');
      return;
    }

    Alert.alert(
      'Clear Checked Items',
      `Remove ${checkedCount} checked item${checkedCount > 1 ? 's' : ''}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear', 
          style: 'destructive',
          onPress: () => setItems(items.filter(item => !item.checked))
        }
      ]
    );
  };

  const clearAllItems = () => {
    if (items.length === 0) {
      Alert.alert('Info', 'Shopping list is already empty');
      return;
    }

    Alert.alert(
      'Clear All Items',
      'Are you sure you want to clear the entire shopping list?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear All', 
          style: 'destructive',
          onPress: () => setItems([])
        }
      ]
    );
  };

  const handleAddToPantry = () => {
    const checkedItemsToAdd = items.filter(item => item.checked);
    if (checkedItemsToAdd.length === 0) {
      Alert.alert('No Items Selected', 'Please check items to add to pantry');
      return;
    }
    setSelectedItemsForPantry(checkedItemsToAdd);
    setShowAddToPantryModal(true);
  };

  const handlePantryAddComplete = (pantryItems: any[]) => {
    // Remove checked items after they're added to pantry
    setItems(items.filter(item => !item.checked));
    setShowAddToPantryModal(false);
    setSelectedItemsForPantry([]);
    Alert.alert('Success', `Added ${pantryItems.length} items to pantry`);
  };

  const uncheckedItems = items.filter(item => !item.checked);
  const checkedItems = items.filter(item => item.checked);

  return (
    <TabScreenTransition routeName="shopping-list" transitionStyle="fade">
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
      <View style={[styles.header, { paddingTop: insets.top }]}>
        <Text style={styles.headerTitle}>Shopping List</Text>
        <View style={styles.headerButtons}>
          {checkedItems.length > 0 && (
            <TouchableOpacity onPress={handleAddToPantry} style={styles.headerButton}>
              <Ionicons name="add-circle-outline" size={24} color="#297A56" />
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={clearCheckedItems} style={styles.headerButton}>
            <MaterialCommunityIcons name="broom" size={24} color="#297A56" />
          </TouchableOpacity>
          <TouchableOpacity onPress={clearAllItems} style={styles.headerButton}>
            <Ionicons name="trash-outline" size={24} color="#297A56" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Add new item section */}
        {isAddingItem ? (
          <View style={styles.addItemContainer}>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.itemNameInput}
                placeholder="Item name"
                value={newItemName}
                onChangeText={setNewItemName}
                autoFocus
                onSubmitEditing={addItem}
              />
              <TextInput
                style={styles.quantityInput}
                placeholder="Qty"
                value={newItemQuantity}
                onChangeText={setNewItemQuantity}
                onSubmitEditing={addItem}
              />
            </View>
            <View style={styles.addItemButtons}>
              <TouchableOpacity 
                style={[styles.button, styles.cancelButton]} 
                onPress={() => {
                  setIsAddingItem(false);
                  setNewItemName('');
                  setNewItemQuantity('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.button, styles.addButton]} 
                onPress={addItem}
              >
                <Text style={styles.addButtonText}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <TouchableOpacity 
            style={styles.addNewButton}
            onPress={() => setIsAddingItem(true)}
          >
            <Ionicons name="add-circle-outline" size={24} color="#297A56" />
            <Text style={styles.addNewButtonText}>Add item</Text>
          </TouchableOpacity>
        )}

        {/* Unchecked items */}
        {uncheckedItems.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>To Buy ({uncheckedItems.length})</Text>
            {uncheckedItems.map(item => (
              <TouchableOpacity
                key={item.id}
                style={styles.itemContainer}
                onPress={() => toggleItem(item.id)}
              >
                <TouchableOpacity 
                  style={styles.checkbox}
                  onPress={() => toggleItem(item.id)}
                >
                  <Ionicons 
                    name="square-outline" 
                    size={24} 
                    color="#297A56" 
                  />
                </TouchableOpacity>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  {item.quantity && (
                    <Text style={styles.itemQuantity}>{item.quantity}</Text>
                  )}
                </View>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => deleteItem(item.id)}
                >
                  <Ionicons name="close-circle" size={22} color="#DC2626" />
                </TouchableOpacity>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Checked items */}
        {checkedItems.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Completed ({checkedItems.length})</Text>
            {checkedItems.map(item => (
              <TouchableOpacity
                key={item.id}
                style={[styles.itemContainer, styles.checkedItem]}
                onPress={() => toggleItem(item.id)}
              >
                <TouchableOpacity 
                  style={styles.checkbox}
                  onPress={() => toggleItem(item.id)}
                >
                  <Ionicons 
                    name="checkbox" 
                    size={24} 
                    color="#4CAF50" 
                  />
                </TouchableOpacity>
                <View style={styles.itemInfo}>
                  <Text style={[styles.itemName, styles.checkedText]}>{item.name}</Text>
                  {item.quantity && (
                    <Text style={[styles.itemQuantity, styles.checkedText]}>{item.quantity}</Text>
                  )}
                </View>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => deleteItem(item.id)}
                >
                  <Ionicons name="close-circle" size={22} color="#999" />
                </TouchableOpacity>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Empty state */}
        {items.length === 0 && (
          <View style={styles.emptyContainer}>
            <MaterialCommunityIcons name="cart-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>Your shopping list is empty</Text>
            <Text style={styles.emptySubtext}>Add items to get started</Text>
          </View>
        )}
      </ScrollView>

      {/* Add to Pantry Modal */}
      {showAddToPantryModal && (
        <AddToPantryModal
          visible={showAddToPantryModal}
          onClose={() => {
            setShowAddToPantryModal(false);
            setSelectedItemsForPantry([]);
          }}
          onConfirm={handlePantryAddComplete}
          shoppingItems={selectedItemsForPantry}
        />
      )}
    </KeyboardAvoidingView>
    </TabScreenTransition>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#297A56',
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  addItemContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  inputRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  itemNameInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  quantityInput: {
    width: 80,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  addItemButtons: {
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'flex-end',
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  cancelButton: {
    backgroundColor: '#F3F4F6',
  },
  cancelButtonText: {
    color: '#666',
    fontWeight: '600',
  },
  addButton: {
    backgroundColor: '#297A56',
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  addNewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    borderStyle: 'dashed',
  },
  addNewButtonText: {
    fontSize: 16,
    color: '#297A56',
    fontWeight: '600',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  itemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  checkedItem: {
    opacity: 0.7,
    backgroundColor: '#F3F4F6',
  },
  checkbox: {
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  itemQuantity: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  checkedText: {
    textDecorationLine: 'line-through',
    color: '#999',
  },
  deleteButton: {
    padding: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 100,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 16,
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
});