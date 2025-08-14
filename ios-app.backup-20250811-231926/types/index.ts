// Shared type definitions for the PrepSense app

// Base item type from the context
export interface Item {
  id: string;
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  count?: number;
  category?: string;
  addedDate?: string;
}

// Extended item type with display properties
export interface PantryItemDisplay extends Item {
  name: string;
  expiry: string;
  daysUntilExpiry: number;
  expirationDate: Date;
  icon: string;
  color?: string;
  iconColor?: string;
  bgColor?: string;
  isCommunity?: boolean;
  isBox?: boolean;
  isProduce?: boolean;
  isCan?: boolean;
}

// Filter types
export interface ItemFilters {
  searchQuery: string;
  selectedCategories: string[];
  sortBy: 'name' | 'expiry' | 'category';
  sortOrder: 'asc' | 'desc';
}

// Navigation params
export interface EditItemParams {
  index: string;
  data: string; // Base64 encoded item data
}

// Component prop interfaces
export interface QuickActionItem {
  id: string;
  icon: string;
  title: string;
  color: string;
  route?: string;
  onPress?: () => void;
}

export interface TipInfo {
  title?: string;
  text: string;
  iconName?: string;
  iconColor?: string;
}