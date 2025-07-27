// Item formatting and styling utilities
import { getCategoryByLabel, getCategoryIcon, getCategoryColor as getCategoryColorFromConfig, normalizeCategoryLabel } from './categoryConfig';

export interface ItemStyle {
  icon: string;
  color: string;
  isCommunity?: boolean;
}

// Icon mappings for different units
const unitIconMappings: { [key: string]: ItemStyle } = {
  // Weight-based items
  'kg': { icon: 'scale-bathroom', color: '#4F46E5', isCommunity: true },
  'g': { icon: 'scale-bathroom', color: '#4F46E5', isCommunity: true },
  'lb': { icon: 'scale-bathroom', color: '#4F46E5', isCommunity: true },
  'oz': { icon: 'scale-bathroom', color: '#4F46E5', isCommunity: true },
  
  // Volume-based items
  'l': { icon: 'water', color: '#3B82F6', isCommunity: true },
  'ml': { icon: 'water', color: '#3B82F6', isCommunity: true },
  'gallon': { icon: 'water-pump', color: '#3B82F6', isCommunity: true },
  'quart': { icon: 'cup', color: '#3B82F6', isCommunity: true },
  'pint': { icon: 'cup', color: '#3B82F6', isCommunity: true },
  'cup': { icon: 'cup', color: '#8B5CF6', isCommunity: true },
  'tbsp': { icon: 'silverware-spoon', color: '#8B5CF6', isCommunity: true },
  'tsp': { icon: 'silverware-spoon', color: '#8B5CF6', isCommunity: true },
  
  // Count-based items
  'count': { icon: 'numeric', color: '#10B981', isCommunity: true },
  'dozen': { icon: 'egg', color: '#10B981', isCommunity: true },
  'piece': { icon: 'fruit-cherries', color: '#10B981', isCommunity: true },
};

export const getItemStyle = (item: { name: string; unit: string; category?: string }): ItemStyle => {
  const unit = item.unit.toLowerCase();
  const name = item.name.toLowerCase();
  const normalizedCategory = normalizeCategoryLabel(item.category || '');

  // Check category first - use centralized category configuration
  const categoryConfig = getCategoryByLabel(normalizedCategory);
  if (categoryConfig) {
    return {
      icon: categoryConfig.materialIcon,
      color: categoryConfig.color,
      isCommunity: true
    };
  }

  // Then check unit
  if (unitIconMappings[unit]) {
    return unitIconMappings[unit];
  }
  
  // Special case handling for specific items
  const productNameLower = name.toLowerCase();
  if (productNameLower.includes('banana')) {
    return { icon: 'fruit-cherries', color: '#EAB308', isCommunity: true };
  }
  if (productNameLower.includes('milk')) {
    return { icon: 'cow', color: '#60A5FA', isCommunity: true };
  }
  if (productNameLower.includes('chicken') || productNameLower.includes('breast')) {
    return { icon: 'food-steak', color: '#F87171', isCommunity: true };
  }

  // Default icon - use the "Other" category
  return { icon: 'package-variant', color: '#9CA3AF', isCommunity: true };
};

export const formatExpirationDate = (dateString: string): string => {
  const date = new Date(dateString);
  // If the date is invalid, return a placeholder
  if (isNaN(date.getTime())) return 'No date';
  
  // Set time to end of day for the expiration date and start of day for today
  const expirationDate = new Date(date);
  expirationDate.setHours(23, 59, 59, 999);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const diffTime = expirationDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    return `Expired ${Math.abs(diffDays)} days ago`;
  } else if (diffDays === 0) {
    return 'Expires: Today';
  } else if (diffDays === 1) {
    return 'Expires: Tomorrow';
  } else {
    return `Expires: ${diffDays} days`;
  }
};

export const calculateDaysUntilExpiry = (expirationDate: string): number => {
  try {
    const expDate = new Date(expirationDate);
    expDate.setHours(23, 59, 59, 999);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.max(0, Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
  } catch (e) {
    return 0;
  }
};

export const formatAddedDate = (dateString: string): string => {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Unknown';
  
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  // For older dates, show the date
  const currentYear = now.getFullYear();
  const dateYear = date.getFullYear();
  
  if (currentYear === dateYear) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
};

export const getCategoryBgColor = (category: string): string => {
  const normalizedCategory = normalizeCategoryLabel(category);
  const categoryConfig = getCategoryByLabel(normalizedCategory);
  return categoryConfig?.bgColor || '#F3F4F6';
};

// Group items by name and unit
export const groupItems = (items: any[]): any[] => {
  const grouped: Record<string, any> = {};
  
  items.forEach(item => {
    const key = `${item.item_name}-${item.quantity_unit}`;
    
    if (!grouped[key]) {
      grouped[key] = {
        ...item,
        count: 1,
      };
    } else {
      grouped[key].count += 1;
    }
  });

  return Object.values(grouped);
};