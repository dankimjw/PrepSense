import { useMemo, useState, useCallback } from 'react';
import { useItems as useItemsContext } from '../context/ItemsContext';

export interface UseItemsFilters {
  searchQuery: string;
  selectedCategories: string[];
  sortBy: 'name' | 'expiry' | 'category';
  sortOrder: 'asc' | 'desc';
}

export const useItemsWithFilters = () => {
  const { items, fetchItems, isInitialized } = useItemsContext();
  const [filters, setFilters] = useState<UseItemsFilters>({
    searchQuery: '',
    selectedCategories: [],
    sortBy: 'expiry',
    sortOrder: 'asc',
  });

  const updateFilters = useCallback((newFilters: Partial<UseItemsFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const filteredAndSortedItems = useMemo(() => {
    if (!items) return [];
    
    // Filter by search query
    let filtered = items.filter(item => 
      item.item_name?.toLowerCase().includes(filters.searchQuery.toLowerCase())
    );
    
    // Filter by category
    if (filters.selectedCategories.length > 0) {
      filtered = filtered.filter(item => 
        item.category && filters.selectedCategories.includes(item.category)
      );
    }
    
    // Sort items
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0;
      
      switch (filters.sortBy) {
        case 'name':
          comparison = a.item_name.localeCompare(b.item_name);
          break;
        case 'category':
          comparison = (a.category || '').localeCompare(b.category || '');
          break;
        case 'expiry':
          const dateA = new Date(a.expected_expiration).getTime();
          const dateB = new Date(b.expected_expiration).getTime();
          comparison = dateA - dateB;
          break;
      }
      
      return filters.sortOrder === 'asc' ? comparison : -comparison;
    });
    
    return sorted;
  }, [items, filters]);

  return {
    items: filteredAndSortedItems,
    filters,
    updateFilters,
    fetchItems,
    isInitialized,
    rawItems: items,
  };
};