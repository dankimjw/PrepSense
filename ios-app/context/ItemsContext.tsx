import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { defaultItems } from '../constants/defaultItems';

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
};

const ItemsContext = createContext<ItemsContextType | undefined>(undefined);

const STORAGE_KEY = 'prepsense_items';

export const ItemsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Load items from storage on initial render
  useEffect(() => {
    const loadItems = async () => {
      try {
        // In a real app, you would load from AsyncStorage here
        // For now, we'll just check if we have any items
        if (items.length === 0) {
          // Add default items if no items exist
          addItems(defaultItems);
        }
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to load items', error);
        setIsInitialized(true);
      }
    };
    
    loadItems();
  }, []);

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

  return (
    <ItemsContext.Provider value={{ items, addItems, removeItem, updateItem }}>
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
};
