/**
 * Test the business logic of PantryItemsList without importing the component
 * This bypasses StyleSheet.create issues and focuses on pure logic testing
 */

import {
  filterItemsByExpirationStatus,
  sortPantryItems,
  calculateDaysUntilExpiry,
  getExpiryStatus,
  groupItemsByCategory,
  filterItemsBySearch,
  getDisplayModeConfig,
  formatQuantity,
  calculatePantryStats,
  getItemActionState,
  getListPerformanceConfig,
  PantryItemData,
  PantrySortOption,
  ExpiryStatus,
  CategoryGroup,
  ListDisplayMode,
  DisplayModeConfig,
  PantryStats,
  ItemActionState,
  ListPerformanceConfig
} from '../../logic/pantryItemsList.logic';

describe('PantryItemsList Logic Tests', () => {

  // Mock data for testing
  const mockItems: PantryItemData[] = [
    {
      id: '1',
      item_name: 'Milk',
      brand: 'Organic Valley',
      category: 'Dairy',
      expiry_date: '2024-01-15',
      quantity: 1,
      unit: 'gallon',
      purchase_date: '2024-01-10'
    },
    {
      id: '2',
      item_name: 'Eggs',
      category: 'Dairy',
      expiry_date: '2024-01-20',
      quantity: 12,
      unit: 'pieces',
      purchase_date: '2024-01-08'
    },
    {
      id: '3',
      item_name: 'Bread',
      brand: 'Wonder',
      category: 'Bakery',
      expiry_date: '2024-01-12',
      quantity: 1,
      unit: 'loaf',
      purchase_date: '2024-01-11'
    },
    {
      id: '4',
      item_name: 'Apples',
      category: 'Produce',
      expiry_date: '2024-01-25',
      quantity: 6,
      unit: 'pieces',
      purchase_date: '2024-01-09'
    },
    {
      id: '5',
      item_name: 'Rice',
      category: 'Grains',
      // No expiry date
      quantity: 2,
      unit: 'pounds',
      purchase_date: '2024-01-05'
    }
  ];

  describe('Expiration Status Filtering', () => {
    // Mock current date to January 14, 2024 for consistent testing
    const mockCurrentDate = new Date('2024-01-14T10:00:00Z');
    
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(mockCurrentDate);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should filter expiring items (within 3 days)', () => {
      const result = filterItemsByExpirationStatus(mockItems, 'expiring');
      
      expect(result).toHaveLength(1);
      expect(result[0].item_name).toBe('Milk'); // Expires Jan 15, within 3 days
    });

    it('should filter fresh items (more than 3 days)', () => {
      const result = filterItemsByExpirationStatus(mockItems, 'fresh');
      
      expect(result).toHaveLength(3);
      expect(result.map(item => item.item_name)).toContain('Eggs');
      expect(result.map(item => item.item_name)).toContain('Apples');
      expect(result.map(item => item.item_name)).toContain('Rice'); // No expiry treated as fresh
    });

    it('should filter expired items', () => {
      const result = filterItemsByExpirationStatus(mockItems, 'expired');
      
      expect(result).toHaveLength(1);
      expect(result[0].item_name).toBe('Bread'); // Expired Jan 12
    });

    it('should return all items when filter is all', () => {
      const result = filterItemsByExpirationStatus(mockItems, 'all');
      
      expect(result).toHaveLength(5);
    });
  });

  describe('Pantry Items Sorting', () => {
    it('should sort by expiry date (earliest first)', () => {
      const result = sortPantryItems(mockItems, 'expiry');
      
      expect(result[0].item_name).toBe('Bread'); // Jan 12
      expect(result[1].item_name).toBe('Milk'); // Jan 15
      expect(result[2].item_name).toBe('Eggs'); // Jan 20
      expect(result[3].item_name).toBe('Apples'); // Jan 25
      expect(result[4].item_name).toBe('Rice'); // No expiry, last
    });

    it('should sort by name alphabetically', () => {
      const result = sortPantryItems(mockItems, 'name');
      
      expect(result[0].item_name).toBe('Apples');
      expect(result[1].item_name).toBe('Bread');
      expect(result[2].item_name).toBe('Eggs');
      expect(result[3].item_name).toBe('Milk');
      expect(result[4].item_name).toBe('Rice');
    });

    it('should sort by category alphabetically', () => {
      const result = sortPantryItems(mockItems, 'category');
      
      expect(result[0].category).toBe('Bakery');
      expect(result[1].category).toBe('Dairy');
      expect(result[2].category).toBe('Dairy');
      expect(result[3].category).toBe('Grains');
      expect(result[4].category).toBe('Produce');
    });

    it('should sort by purchase date (newest first)', () => {
      const result = sortPantryItems(mockItems, 'purchase_date');
      
      expect(result[0].item_name).toBe('Bread'); // Jan 11
      expect(result[1].item_name).toBe('Milk'); // Jan 10
      expect(result[2].item_name).toBe('Apples'); // Jan 9
      expect(result[3].item_name).toBe('Eggs'); // Jan 8
      expect(result[4].item_name).toBe('Rice'); // Jan 5
    });

    it('should sort by quantity (highest first)', () => {
      const result = sortPantryItems(mockItems, 'quantity');
      
      expect(result[0].item_name).toBe('Eggs'); // 12
      expect(result[1].item_name).toBe('Apples'); // 6
      expect(result[2].item_name).toBe('Rice'); // 2
      expect(result[3].item_name).toBe('Milk'); // 1
      expect(result[4].item_name).toBe('Bread'); // 1
    });

    it('should not mutate original array', () => {
      const originalOrder = mockItems.map(item => item.item_name);
      sortPantryItems(mockItems, 'name');
      
      expect(mockItems.map(item => item.item_name)).toEqual(originalOrder);
    });
  });

  describe('Days Until Expiry Calculation', () => {
    const mockCurrentDate = new Date('2024-01-14T10:00:00Z');
    
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(mockCurrentDate);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should calculate days until expiry for string date', () => {
      const result = calculateDaysUntilExpiry('2024-01-17');
      expect(result).toBe(3);
    });

    it('should calculate days until expiry for Date object', () => {
      const result = calculateDaysUntilExpiry(new Date('2024-01-16'));
      expect(result).toBe(2);
    });

    it('should return negative for expired items', () => {
      const result = calculateDaysUntilExpiry('2024-01-12');
      expect(result).toBe(-2);
    });

    it('should return Infinity for no expiry date', () => {
      const result = calculateDaysUntilExpiry('');
      expect(result).toBe(Infinity);
    });
  });

  describe('Expiry Status Determination', () => {
    const mockCurrentDate = new Date('2024-01-14T10:00:00Z');
    
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(mockCurrentDate);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return expired status for past dates', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Expired Item',
        expiry_date: '2024-01-12'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('expired');
      expect(result.urgent).toBe(true);
      expect(result.color).toBe('#DC2626');
      expect(result.text).toBe('Expired 2 days ago');
    });

    it('should return expiring status for today', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Expiring Today',
        expiry_date: '2024-01-14'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('expiring');
      expect(result.urgent).toBe(true);
      expect(result.text).toBe('Expires today');
    });

    it('should return expiring status for within 3 days', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Expiring Soon',
        expiry_date: '2024-01-16'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('expiring');
      expect(result.urgent).toBe(true);
      expect(result.text).toBe('Expires in 2 days');
    });

    it('should return warning status for within 7 days', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Warning Item',
        expiry_date: '2024-01-20'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('warning');
      expect(result.urgent).toBe(false);
      expect(result.text).toBe('Expires in 6 days');
    });

    it('should return fresh status for more than 7 days', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Fresh Item',
        expiry_date: '2024-01-25'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('fresh');
      expect(result.urgent).toBe(false);
      expect(result.text).toBe('Expires in 11 days');
    });

    it('should return fresh status for no expiry date', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'No Expiry Item'
      };

      const result = getExpiryStatus(item);

      expect(result.status).toBe('fresh');
      expect(result.urgent).toBe(false);
      expect(result.text).toBe('No expiry date');
    });
  });

  describe('Category Grouping', () => {
    it('should group items by category and sort within groups', () => {
      const result = groupItemsByCategory(mockItems);

      expect(result).toHaveLength(4); // Bakery, Dairy, Grains, Produce
      
      const dairyGroup = result.find(group => group.category === 'Dairy');
      expect(dairyGroup?.count).toBe(2);
      expect(dairyGroup?.items.map(item => item.item_name)).toEqual(['Milk', 'Eggs']); // Sorted by expiry
    });

    it('should handle items without category', () => {
      const itemsWithoutCategory: PantryItemData[] = [
        { id: '1', item_name: 'Mystery Item 1' },
        { id: '2', item_name: 'Mystery Item 2' }
      ];

      const result = groupItemsByCategory(itemsWithoutCategory);

      expect(result).toHaveLength(1);
      expect(result[0].category).toBe('Other');
      expect(result[0].count).toBe(2);
    });
  });

  describe('Search Filtering', () => {
    it('should filter by item name', () => {
      const result = filterItemsBySearch(mockItems, 'milk');

      expect(result).toHaveLength(1);
      expect(result[0].item_name).toBe('Milk');
    });

    it('should filter by brand', () => {
      const result = filterItemsBySearch(mockItems, 'wonder');

      expect(result).toHaveLength(1);
      expect(result[0].item_name).toBe('Bread');
    });

    it('should filter by category', () => {
      const result = filterItemsBySearch(mockItems, 'dairy');

      expect(result).toHaveLength(2);
      expect(result.map(item => item.item_name)).toContain('Milk');
      expect(result.map(item => item.item_name)).toContain('Eggs');
    });

    it('should be case insensitive', () => {
      const result = filterItemsBySearch(mockItems, 'EGGS');

      expect(result).toHaveLength(1);
      expect(result[0].item_name).toBe('Eggs');
    });

    it('should return all items for empty search', () => {
      const result = filterItemsBySearch(mockItems, '');

      expect(result).toHaveLength(5);
    });
  });

  describe('Display Mode Configuration', () => {
    it('should return grid configuration', () => {
      const result = getDisplayModeConfig('grid');

      expect(result.itemsPerRow).toBe(2);
      expect(result.showDetails).toBe(true);
      expect(result.showThumbnails).toBe(true);
      expect(result.cardHeight).toBe(180);
    });

    it('should return list configuration', () => {
      const result = getDisplayModeConfig('list');

      expect(result.itemsPerRow).toBe(1);
      expect(result.showDetails).toBe(true);
      expect(result.showThumbnails).toBe(true);
      expect(result.cardHeight).toBe(120);
    });

    it('should return compact configuration', () => {
      const result = getDisplayModeConfig('compact');

      expect(result.itemsPerRow).toBe(1);
      expect(result.showDetails).toBe(false);
      expect(result.showThumbnails).toBe(false);
      expect(result.cardHeight).toBe(60);
    });
  });

  describe('Quantity Formatting', () => {
    it('should format with unit', () => {
      const result = formatQuantity(2, 'pounds');
      expect(result).toBe('2 pounds');
    });

    it('should handle singular units', () => {
      const result = formatQuantity(1, 'gallons');
      expect(result).toBe('1 gallon');
    });

    it('should handle no unit', () => {
      const result = formatQuantity(5, '');
      expect(result).toBe('5');
    });

    it('should handle no quantity', () => {
      const result = formatQuantity(undefined, 'pieces');
      expect(result).toBe('');
    });

    it('should handle both missing', () => {
      const result = formatQuantity();
      expect(result).toBe('');
    });
  });

  describe('Pantry Statistics', () => {
    const mockCurrentDate = new Date('2024-01-14T10:00:00Z');
    
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(mockCurrentDate);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should calculate comprehensive pantry stats', () => {
      const result = calculatePantryStats(mockItems);

      expect(result.totalItems).toBe(5);
      expect(result.expiringItems).toBe(1); // Milk
      expect(result.expiredItems).toBe(1); // Bread
      expect(result.categoriesCount).toBe(4); // Bakery, Dairy, Grains, Produce
      expect(result.urgentItemsCount).toBe(2); // Bread (expired) + Milk (expiring)
      expect(result.averageDaysUntilExpiry).toBeGreaterThan(0);
    });

    it('should handle empty pantry', () => {
      const result = calculatePantryStats([]);

      expect(result.totalItems).toBe(0);
      expect(result.expiringItems).toBe(0);
      expect(result.expiredItems).toBe(0);
      expect(result.categoriesCount).toBe(0);
      expect(result.urgentItemsCount).toBe(0);
      expect(result.averageDaysUntilExpiry).toBe(0);
    });
  });

  describe('Item Action State', () => {
    const mockCurrentDate = new Date('2024-01-14T10:00:00Z');
    
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(mockCurrentDate);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return correct actions for owner of fresh item', () => {
      const freshItem: PantryItemData = {
        id: '1',
        item_name: 'Fresh Item',
        expiry_date: '2024-01-25'
      };

      const result = getItemActionState(freshItem, true);

      expect(result.canEdit).toBe(true);
      expect(result.canDelete).toBe(true);
      expect(result.canMarkUsed).toBe(true);
      expect(result.canExtendExpiry).toBe(false); // Fresh items don't need extension
      expect(result.showQuickActions).toBe(false);
    });

    it('should return correct actions for owner of urgent item', () => {
      const urgentItem: PantryItemData = {
        id: '1',
        item_name: 'Urgent Item',
        expiry_date: '2024-01-15' // Expiring soon
      };

      const result = getItemActionState(urgentItem, true);

      expect(result.canEdit).toBe(true);
      expect(result.canDelete).toBe(true);
      expect(result.canMarkUsed).toBe(true);
      expect(result.canExtendExpiry).toBe(true);
      expect(result.showQuickActions).toBe(true);
    });

    it('should return limited actions for non-owner', () => {
      const item: PantryItemData = {
        id: '1',
        item_name: 'Shared Item',
        expiry_date: '2024-01-15'
      };

      const result = getItemActionState(item, false);

      expect(result.canEdit).toBe(false);
      expect(result.canDelete).toBe(false);
      expect(result.canMarkUsed).toBe(false);
      expect(result.canExtendExpiry).toBe(false);
    });
  });

  describe('List Performance Configuration', () => {
    it('should enable virtualization for large lists', () => {
      const result = getListPerformanceConfig(100, 'list');

      expect(result.shouldUseVirtualization).toBe(true);
      expect(result.itemHeight).toBe(120); // List mode height
      expect(result.windowSize).toBe(20);
      expect(result.initialNumToRender).toBe(10);
    });

    it('should disable virtualization for small lists', () => {
      const result = getListPerformanceConfig(20, 'grid');

      expect(result.shouldUseVirtualization).toBe(false);
      expect(result.itemHeight).toBe(180); // Grid mode height
    });

    it('should adjust initial render for very small lists', () => {
      const result = getListPerformanceConfig(5, 'compact');

      expect(result.initialNumToRender).toBe(5);
      expect(result.itemHeight).toBe(60); // Compact mode height
    });
  });
});