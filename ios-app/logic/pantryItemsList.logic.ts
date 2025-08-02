/**
 * Business logic for PantryItemsList component
 * Extracted for comprehensive testing without StyleSheet issues
 */

export interface PantryItemData {
  id: string;
  item_name: string;
  brand?: string;
  category?: string;
  expiry_date?: string;
  days_until_expiry?: number;
  quantity?: number;
  unit?: string;
  is_expiring_soon?: boolean;
  nutritional_info?: any;
  purchase_date?: string;
  location?: string;
}

/**
 * Logic for filtering pantry items by expiration status
 */
export function filterItemsByExpirationStatus(
  items: PantryItemData[],
  status: 'expiring' | 'fresh' | 'expired' | 'all' = 'all'
): PantryItemData[] {
  const now = new Date();
  const threeDaysFromNow = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000);
  
  switch (status) {
    case 'expiring':
      return items.filter(item => {
        if (!item.expiry_date) return false;
        const expiryDate = new Date(item.expiry_date);
        return expiryDate <= threeDaysFromNow && expiryDate >= now;
      });
    case 'fresh':
      return items.filter(item => {
        if (!item.expiry_date) return true;
        const expiryDate = new Date(item.expiry_date);
        return expiryDate > threeDaysFromNow;
      });
    case 'expired':
      return items.filter(item => {
        if (!item.expiry_date) return false;
        const expiryDate = new Date(item.expiry_date);
        return expiryDate < now;
      });
    case 'all':
    default:
      return items;
  }
}

/**
 * Logic for sorting pantry items by various criteria
 */
export type PantrySortOption = 'expiry' | 'name' | 'category' | 'purchase_date' | 'quantity';

export function sortPantryItems(
  items: PantryItemData[],
  sortBy: PantrySortOption = 'expiry'
): PantryItemData[] {
  const sortedItems = [...items];
  
  switch (sortBy) {
    case 'expiry':
      return sortedItems.sort((a, b) => {
        if (!a.expiry_date && !b.expiry_date) return 0;
        if (!a.expiry_date) return 1;
        if (!b.expiry_date) return -1;
        return new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime();
      });
    case 'name':
      return sortedItems.sort((a, b) => a.item_name.localeCompare(b.item_name));
    case 'category':
      return sortedItems.sort((a, b) => {
        const categoryA = a.category || 'Other';
        const categoryB = b.category || 'Other';
        return categoryA.localeCompare(categoryB);
      });
    case 'purchase_date':
      return sortedItems.sort((a, b) => {
        if (!a.purchase_date && !b.purchase_date) return 0;
        if (!a.purchase_date) return 1;
        if (!b.purchase_date) return -1;
        return new Date(b.purchase_date).getTime() - new Date(a.purchase_date).getTime();
      });
    case 'quantity':
      return sortedItems.sort((a, b) => (b.quantity || 0) - (a.quantity || 0));
    default:
      return sortedItems;
  }
}

/**
 * Logic for calculating days until expiry
 */
export function calculateDaysUntilExpiry(expiryDate: string | Date): number {
  if (!expiryDate) return Infinity;
  
  const expiry = typeof expiryDate === 'string' ? new Date(expiryDate) : expiryDate;
  const now = new Date();
  const diffTime = expiry.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}

/**
 * Logic for determining expiry status with color coding
 */
export interface ExpiryStatus {
  status: 'expired' | 'expiring' | 'warning' | 'fresh';
  color: string;
  backgroundColor: string;
  text: string;
  urgent: boolean;
}

export function getExpiryStatus(item: PantryItemData): ExpiryStatus {
  if (!item.expiry_date) {
    return {
      status: 'fresh',
      color: '#6B7280',
      backgroundColor: '#F9FAFB',
      text: 'No expiry date',
      urgent: false
    };
  }
  
  const daysUntilExpiry = calculateDaysUntilExpiry(item.expiry_date);
  
  if (daysUntilExpiry < 0) {
    return {
      status: 'expired',
      color: '#DC2626',
      backgroundColor: '#FEF2F2',
      text: `Expired ${Math.abs(daysUntilExpiry)} days ago`,
      urgent: true
    };
  }
  
  if (daysUntilExpiry === 0) {
    return {
      status: 'expiring',
      color: '#DC2626',
      backgroundColor: '#FEF2F2',
      text: 'Expires today',
      urgent: true
    };
  }
  
  if (daysUntilExpiry <= 3) {
    return {
      status: 'expiring',
      color: '#F59E0B',
      backgroundColor: '#FFFBEB',
      text: `Expires in ${daysUntilExpiry} days`,
      urgent: true
    };
  }
  
  if (daysUntilExpiry <= 7) {
    return {
      status: 'warning',
      color: '#F59E0B',
      backgroundColor: '#FFFBEB',
      text: `Expires in ${daysUntilExpiry} days`,
      urgent: false
    };
  }
  
  return {
    status: 'fresh',
    color: '#10B981',
    backgroundColor: '#F0FDF4',
    text: `Expires in ${daysUntilExpiry} days`,
    urgent: false
  };
}

/**
 * Logic for grouping items by category
 */
export interface CategoryGroup {
  category: string;
  items: PantryItemData[];
  count: number;
}

export function groupItemsByCategory(items: PantryItemData[]): CategoryGroup[] {
  const groups = items.reduce((acc, item) => {
    const category = item.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {} as Record<string, PantryItemData[]>);
  
  return Object.entries(groups)
    .map(([category, items]) => ({
      category,
      items: sortPantryItems(items, 'expiry'),
      count: items.length
    }))
    .sort((a, b) => a.category.localeCompare(b.category));
}

/**
 * Logic for search filtering
 */
export function filterItemsBySearch(
  items: PantryItemData[],
  searchQuery: string
): PantryItemData[] {
  if (!searchQuery.trim()) return items;
  
  const query = searchQuery.toLowerCase();
  return items.filter(item => 
    item.item_name.toLowerCase().includes(query) ||
    (item.brand && item.brand.toLowerCase().includes(query)) ||
    (item.category && item.category.toLowerCase().includes(query))
  );
}

/**
 * Logic for determining list display modes
 */
export type ListDisplayMode = 'grid' | 'list' | 'compact';

export interface DisplayModeConfig {
  itemsPerRow: number;
  showDetails: boolean;
  showThumbnails: boolean;
  cardHeight: number;
}

export function getDisplayModeConfig(mode: ListDisplayMode): DisplayModeConfig {
  switch (mode) {
    case 'grid':
      return {
        itemsPerRow: 2,
        showDetails: true,
        showThumbnails: true,
        cardHeight: 180
      };
    case 'list':
      return {
        itemsPerRow: 1,
        showDetails: true,
        showThumbnails: true,
        cardHeight: 120
      };
    case 'compact':
      return {
        itemsPerRow: 1,
        showDetails: false,
        showThumbnails: false,
        cardHeight: 60
      };
    default:
      return getDisplayModeConfig('list');
  }
}

/**
 * Logic for quantity formatting
 */
export function formatQuantity(quantity?: number, unit?: string): string {
  if (!quantity) return '';
  
  if (!unit) return quantity.toString();
  
  // Handle plural/singular units
  if (quantity === 1) {
    // Remove 's' from plural units
    const singularUnit = unit.endsWith('s') ? unit.slice(0, -1) : unit;
    return `${quantity} ${singularUnit}`;
  }
  
  return `${quantity} ${unit}`;
}

/**
 * Logic for calculating pantry statistics
 */
export interface PantryStats {
  totalItems: number;
  expiringItems: number;
  expiredItems: number;
  categoriesCount: number;
  averageDaysUntilExpiry: number;
  urgentItemsCount: number;
}

export function calculatePantryStats(items: PantryItemData[]): PantryStats {
  const now = new Date();
  const expiringItems = filterItemsByExpirationStatus(items, 'expiring');
  const expiredItems = filterItemsByExpirationStatus(items, 'expired');
  const categories = new Set(items.map(item => item.category || 'Other'));
  
  const itemsWithExpiry = items.filter(item => item.expiry_date);
  const totalDays = itemsWithExpiry.reduce((sum, item) => {
    return sum + calculateDaysUntilExpiry(item.expiry_date!);
  }, 0);
  const averageDaysUntilExpiry = itemsWithExpiry.length > 0 
    ? totalDays / itemsWithExpiry.length 
    : 0;
  
  const urgentItems = items.filter(item => {
    const status = getExpiryStatus(item);
    return status.urgent;
  });
  
  return {
    totalItems: items.length,
    expiringItems: expiringItems.length,
    expiredItems: expiredItems.length,
    categoriesCount: categories.size,
    averageDaysUntilExpiry: Math.round(averageDaysUntilExpiry),
    urgentItemsCount: urgentItems.length
  };
}

/**
 * Logic for action button states
 */
export interface ItemActionState {
  canEdit: boolean;
  canDelete: boolean;
  canMarkUsed: boolean;
  canExtendExpiry: boolean;
  showQuickActions: boolean;
}

export function getItemActionState(
  item: PantryItemData,
  isOwner: boolean = true
): ItemActionState {
  const expiryStatus = getExpiryStatus(item);
  
  return {
    canEdit: isOwner,
    canDelete: isOwner,
    canMarkUsed: isOwner,
    canExtendExpiry: isOwner && expiryStatus.status !== 'fresh',
    showQuickActions: expiryStatus.urgent
  };
}

/**
 * Logic for list performance optimization
 */
export interface ListPerformanceConfig {
  shouldUseVirtualization: boolean;
  itemHeight: number;
  windowSize: number;
  initialNumToRender: number;
}

export function getListPerformanceConfig(
  itemCount: number,
  displayMode: ListDisplayMode
): ListPerformanceConfig {
  const shouldUseVirtualization = itemCount > 50;
  const displayConfig = getDisplayModeConfig(displayMode);
  
  return {
    shouldUseVirtualization,
    itemHeight: displayConfig.cardHeight,
    windowSize: Math.min(20, itemCount),
    initialNumToRender: Math.min(10, itemCount)
  };
}