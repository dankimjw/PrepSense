// context/ItemsContext.tsx - Part of the PrepSense mobile app
import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { fetchPantryItems, savePantryItem, deletePantryItem } from '../services/api';
import { Alert } from 'react-native';

export type Item = {
  id: string;
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  count?: number;
  category?: string;
  addedDate?: string;
};

type ItemsContextType = {
  items: Item[];
  addItems: (newItems: Item[]) => void;
  removeItem: (id: string) => void;
  updateItem: (id: string, updates: Partial<Item>) => void;
  fetchItems: () => Promise<Item[]>;
  isInitialized: boolean;
};

const ItemsContext = createContext<ItemsContextType | undefined>(undefined);

const STORAGE_KEY = 'prepsense_items';

export const ItemsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Fetch pantry items from backend
  const fetchItems = useCallback(async () => {
    try {
      // Use default user_id 111 as specified
      const pantryItems = await fetchPantryItems(111);
      
      // Transform the pantry items to match the Item type
      const transformedItems = pantryItems.map((item, index) => ({
        ...item,
        id: item.pantry_item_id?.toString() || `temp-${index}-${Date.now()}`, // More unique fallback ID
        item_name: item.product_name || 'Unknown Item',
        quantity_amount: item.quantity || 1,
        quantity_unit: item.unit_of_measurement || 'unit',
        expected_expiration: item.expiration_date || new Date().toISOString(),
        category: item.food_category || 'Uncategorized',
        addedDate: item.pantry_item_created_at || new Date().toISOString()
      }));
      
      setItems(transformedItems);
      return transformedItems;
    } catch (error) {
      console.error('Failed to fetch pantry items:', error);
      setItems([]); // Clear items on error to prevent showing stale data
      throw error; // Re-throw to allow error handling in components
    } finally {
      if (!isInitialized) {
        setIsInitialized(true);
      }
    }
  }, [isInitialized]);

  // Load items from backend on initial render
  useEffect(() => {
    if (!isInitialized) {
      fetchItems().catch(console.error);
    }
  }, [fetchItems, isInitialized]);

  const addItems = async (newItems: Item[]) => {
    try {
      // Add unique IDs and timestamps to new items
      const processedItems = await Promise.all(
        newItems.map(async (item) => {
          try {
            const savedItem = await savePantryItem(111, {
              ...item,
              id: item.id || undefined, // Let the server generate the ID for new items
            });
            
            return {
              ...savedItem,
              id: savedItem.id.toString(),
              item_name: savedItem.item_name,
              quantity_amount: savedItem.quantity_amount,
              quantity_unit: savedItem.quantity_unit,
              expected_expiration: savedItem.expected_expiration,
              category: savedItem.category,
              addedDate: savedItem.addedDate || new Date().toISOString(),
            };
          } catch (error) {
            console.error('Error saving item:', error);
            // Return the original item so it still gets added to local state
            return item;
          }
        })
      );

      // Update local state with the saved items
      setItems(prevItems => {
        const existingIds = new Set(prevItems.map(item => item.id));
        const uniqueNewItems = processedItems.filter(item => !existingIds.has(item.id));
        return [...prevItems, ...uniqueNewItems];
      });

      return processedItems;
    } catch (error) {
      console.error('Error adding items:', error);
      Alert.alert('Error', 'Failed to save items to the server');
      throw error;
    }
  };

  const removeItem = async (id: string) => {
    try {
      await deletePantryItem(id);
      setItems(prevItems => prevItems.filter(item => item.id !== id));
    } catch (error) {
      console.error('Error deleting item:', error);
      Alert.alert('Error', 'Failed to delete item from the server');
      throw error;
    }
  };

  const updateItem = async (id: string, updates: Partial<Item>) => {
    try {
      const itemToUpdate = items.find(item => item.id === id);
      if (!itemToUpdate) return;
      
      const updatedItem = { ...itemToUpdate, ...updates };
      const savedItem = await savePantryItem(111, updatedItem);
      
      setItems(prevItems =>
        prevItems.map(item =>
          item.id === id ? {
            ...savedItem,
            id: savedItem.id.toString(),
            item_name: savedItem.item_name,
            quantity_amount: savedItem.quantity_amount,
            quantity_unit: savedItem.quantity_unit,
            expected_expiration: savedItem.expected_expiration,
            category: savedItem.category,
          } : item
        )
      );
      
      return savedItem;
    } catch (error) {
      console.error('Error updating item:', error);
      Alert.alert('Error', 'Failed to update item on the server');
      throw error;
    }
  };

  const contextValue = {
    items,
    addItems,
    removeItem,
    updateItem,
    fetchItems,
    isInitialized
  };

  return (
    <ItemsContext.Provider value={contextValue}>
      {children}
    </ItemsContext.Provider>
  );
};

export const useItems = (): ItemsContextType => {
  const context = useContext(ItemsContext);
  if (!context) {
    throw new Error('useItems must be used within an ItemsProvider');
  }
  return context;
}
