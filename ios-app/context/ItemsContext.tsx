// context/ItemsContext.tsx - Part of the PrepSense mobile app
import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { fetchPantryItems } from '../services/api';

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
      const transformedItems = pantryItems.map(item => ({
        ...item,
        id: item.pantry_item_id?.toString() || Math.random().toString(36).substr(2, 9), // Use pantry_item_id as the ID
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

  const addItems = (newItems: Item[]) => {
    setItems(prevItems => {
      // Add unique IDs and timestamps to new items
      const processedItems = newItems.map(item => ({
        ...item,
        id: item.id || Math.random().toString(36).substr(2, 9),
        addedDate: new Date().toISOString(),
      }));
      
      // Combine with existing items, avoiding duplicates
      const existingIds = new Set(prevItems.map(item => item.id));
      const uniqueNewItems = processedItems.filter(item => !existingIds.has(item.id));
      
      return [...prevItems, ...uniqueNewItems];
    });
    
    // After adding items, refetch to ensure we have the latest data
    fetchItems();
  };

  const removeItem = (id: string) => {
    setItems(prevItems => prevItems.filter(item => item.id !== id));
  };

  const updateItem = (id: string, updates: Partial<Item>) => {
    setItems(prevItems =>
      prevItems.map(item =>
        item.id === id ? { ...item, ...updates } : item
      )
    );
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
