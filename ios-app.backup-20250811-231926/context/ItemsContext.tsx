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
  fetchItems: (forceRefresh?: boolean) => Promise<Item[]>;
  isInitialized: boolean;
};

const ItemsContext = createContext<ItemsContextType | undefined>(undefined);

const STORAGE_KEY = 'prepsense_items';

export const ItemsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState<number | null>(null);
  const [needsRefresh, setNeedsRefresh] = useState(false);
  
  // Data is considered stale after 5 minutes
  const STALE_TIME = 5 * 60 * 1000;
  
  // Check if data is stale
  const isDataStale = useCallback(() => {
    if (!lastFetchTime) return true;
    return Date.now() - lastFetchTime > STALE_TIME;
  }, [lastFetchTime]);
  
  // Fetch pantry items from backend with smart refresh
  const fetchItems = useCallback(async (forceRefresh: boolean = false) => {
    // Skip fetch if data is fresh and no force refresh
    if (!forceRefresh && !needsRefresh && lastFetchTime && !isDataStale()) {
      console.log('Skipping fetch - data is fresh');
      return items;
    }
    try {
      console.log('Fetching pantry items for user 111...');
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
      setLastFetchTime(Date.now());
      setNeedsRefresh(false);
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
  }, [isInitialized, items, needsRefresh, lastFetchTime, isDataStale]);

  // Load items from backend on initial render
  useEffect(() => {
    if (!isInitialized) {
      fetchItems().catch(console.error);
    }
  }, [fetchItems, isInitialized]);

  const addItems = async (newItems: Item[]) => {
    // Mark data as needing refresh on mutations
    setNeedsRefresh(true);
    
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
    // Mark data as needing refresh on mutations
    setNeedsRefresh(true);
    
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
    // Mark data as needing refresh on mutations
    setNeedsRefresh(true);
    
    try {
      const itemToUpdate = items.find(item => item.id === id);
      if (!itemToUpdate) return;
      
      // Update the item directly without count logic
      const updatedItem = { ...itemToUpdate, ...updates };
      const savedItem = await savePantryItem(111, updatedItem);
      
      // Transform the API response to match the UI format
      const transformedItem = {
        ...itemToUpdate,
        ...updates,
        id: (savedItem.pantry_item_id || savedItem.id || id).toString(),
        item_name: savedItem.product_name || updates.item_name || itemToUpdate.item_name,
        quantity_amount: savedItem.quantity || updates.quantity_amount || itemToUpdate.quantity_amount,
        quantity_unit: savedItem.unit_of_measurement || updates.quantity_unit || itemToUpdate.quantity_unit,
        expected_expiration: savedItem.expiration_date || updates.expected_expiration || itemToUpdate.expected_expiration,
        category: savedItem.category || updates.category || itemToUpdate.category,
        addedDate: itemToUpdate.addedDate
      };
      
      setItems(prevItems =>
        prevItems.map(item =>
          item.id === id ? transformedItem : item
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
