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
    // Generate temporary IDs for immediate UI update
    const tempItems = newItems.map((item, index) => ({
      ...item,
      id: item.id || `temp-${Date.now()}-${index}`,
      addedDate: item.addedDate || new Date().toISOString(),
    }));

    // Immediately update the UI (optimistic update)
    setItems(prevItems => [...prevItems, ...tempItems]);

    // Save to backend in the background
    try {
      const savedItems = await Promise.all(
        tempItems.map(async (item, index) => {
          try {
            const savedItem = await savePantryItem(111, {
              ...item,
              id: undefined, // Let the server generate the ID
            });
            
            return {
              tempId: item.id,
              savedItem: {
                ...savedItem,
                id: savedItem.id.toString(),
                item_name: savedItem.item_name,
                quantity_amount: savedItem.quantity_amount,
                quantity_unit: savedItem.quantity_unit,
                expected_expiration: savedItem.expected_expiration,
                category: savedItem.category,
                addedDate: savedItem.addedDate || new Date().toISOString(),
              }
            };
          } catch (error) {
            console.error('Error saving item:', error);
            return null;
          }
        })
      );

      // Update items with real IDs from backend
      setItems(prevItems => {
        const updatedItems = [...prevItems];
        savedItems.forEach(result => {
          if (result) {
            const index = updatedItems.findIndex(item => item.id === result.tempId);
            if (index !== -1) {
              updatedItems[index] = result.savedItem;
            }
          }
        });
        return updatedItems;
      });

      // Refresh the entire list to ensure consistency
      // Do it immediately after backend sync completes
      fetchItems().catch(console.error);

      return savedItems.filter(item => item !== null).map(item => item!.savedItem);
    } catch (error) {
      console.error('Error adding items:', error);
      // Remove the temp items if backend save failed
      setItems(prevItems => 
        prevItems.filter(item => !tempItems.some(tempItem => tempItem.id === item.id))
      );
      Alert.alert('Error', 'Failed to save items to the server');
      throw error;
    }
  };

  const removeItem = async (id: string) => {
    // Store the item in case we need to restore it
    const removedItem = items.find(item => item.id === id);
    
    // Immediately remove from UI (optimistic update)
    setItems(prevItems => prevItems.filter(item => item.id !== id));
    
    try {
      // Delete from backend
      await deletePantryItem(id);
    } catch (error) {
      console.error('Error deleting item:', error);
      // Restore the item if backend deletion failed
      if (removedItem) {
        setItems(prevItems => [...prevItems, removedItem]);
      }
      Alert.alert('Error', 'Failed to delete item from the server');
      throw error;
    }
  };

  const updateItem = async (id: string, updates: Partial<Item>) => {
    try {
      const itemToUpdate = items.find(item => item.id === id);
      if (!itemToUpdate) return;
      
      // Handle count changes by creating/deleting duplicate items
      const oldCount = itemToUpdate.count || 1;
      const newCount = updates.count || oldCount;
      
      if (newCount !== oldCount) {
        // Find all items with the same name and unit
        const similarItems = items.filter(item => 
          item.item_name === itemToUpdate.item_name && 
          item.quantity_unit === itemToUpdate.quantity_unit
        );
        
        if (newCount > oldCount) {
          // Need to create additional items
          const itemsToAdd = newCount - oldCount;
          const newItems = [];
          
          for (let i = 0; i < itemsToAdd; i++) {
            const newItem = {
              ...itemToUpdate,
              ...updates,
              id: undefined, // Let the server generate a new ID
              count: 1,
            };
            delete newItem.id;
            newItems.push(newItem);
          }
          
          // Add the new items
          await addItems(newItems);
          
          // Update the original item
          const updatedItem = { ...itemToUpdate, ...updates, count: 1 };
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
        } else if (newCount < oldCount) {
          // Need to delete some items
          const itemsToDelete = oldCount - newCount;
          let deleted = 0;
          
          // Delete extra items (but not the one being edited)
          for (const item of similarItems) {
            if (item.id !== id && deleted < itemsToDelete) {
              await removeItem(item.id);
              deleted++;
            }
          }
          
          // Update the original item
          const updatedItem = { ...itemToUpdate, ...updates, count: 1 };
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
        }
      } else {
        // No count change, just update the item normally
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
      }
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
