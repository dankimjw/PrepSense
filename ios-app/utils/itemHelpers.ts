// Item formatting and styling utilities

export interface ItemStyle {
  icon: string;
  color: string;
  isCommunity?: boolean;
}

// Icon mappings for different units and categories
const iconMappings: { [key: string]: ItemStyle } = {
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
  
  // Category-based overrides
  'dairy': { icon: 'cow', color: '#F59E0B', isCommunity: true },
  'Dairy': { icon: 'cow', color: '#F59E0B', isCommunity: true },
  'meat': { icon: 'food-steak', color: '#DC2626', isCommunity: true },
  'Meat': { icon: 'food-steak', color: '#DC2626', isCommunity: true },
  'produce': { icon: 'fruit-watermelon', color: '#10B981', isCommunity: true },
  'Produce': { icon: 'fruit-watermelon', color: '#10B981', isCommunity: true },
  'bakery': { icon: 'bread-slice', color: '#D97706', isCommunity: true },
  'Bakery': { icon: 'bread-slice', color: '#D97706', isCommunity: true },
  'beverage': { icon: 'cup-water', color: '#3B82F6', isCommunity: true },
  'Beverage': { icon: 'cup-water', color: '#3B82F6', isCommunity: true },
  'snack': { icon: 'popcorn', color: '#8B5CF6', isCommunity: true },
  'Snack': { icon: 'popcorn', color: '#8B5CF6', isCommunity: true },
  'frozen': { icon: 'snowflake', color: '#06B6D4', isCommunity: true },
  'Frozen': { icon: 'snowflake', color: '#06B6D4', isCommunity: true },
  'canned': { icon: 'food-variant', color: '#6B7280', isCommunity: true },
  'Canned': { icon: 'food-variant', color: '#6B7280', isCommunity: true },
  'dry': { icon: 'grain', color: '#A16207', isCommunity: true },
  'Dry': { icon: 'grain', color: '#A16207', isCommunity: true },
  'spice': { icon: 'shaker-outline', color: '#D946EF', isCommunity: true },
  'Spice': { icon: 'shaker-outline', color: '#D946EF', isCommunity: true },
  'condiment': { icon: 'bottle-soda-classic', color: '#EC4899', isCommunity: true },
  'Condiment': { icon: 'bottle-soda-classic', color: '#EC4899', isCommunity: true },
};

export const getItemStyle = (item: { name: string; unit: string; category?: string }): ItemStyle => {
  const unit = item.unit.toLowerCase();
  const name = item.name.toLowerCase();
  const category = item.category?.toLowerCase() || '';

  // Check category first with exact match
  if (category && iconMappings[category]) {
    return iconMappings[category];
  }

  // Then check unit
  if (iconMappings[unit]) {
    return iconMappings[unit];
  }
  
  // Special case handling for specific items
  const productNameLower = name.toLowerCase();
  if (productNameLower.includes('banana')) {
    return { icon: 'fruit-cherries', color: '#EAB308', isCommunity: true };
  }
  if (productNameLower.includes('milk')) {
    return { icon: 'cup-water', color: '#F59E0B', isCommunity: true };
  }
  if (productNameLower.includes('chicken') || productNameLower.includes('breast')) {
    return { icon: 'food-steak', color: '#DC2626', isCommunity: true };
  }

  // Default icon
  return { icon: 'basket-outline', color: '#6B7280', isCommunity: true };
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

export const getCategoryColor = (category: string): string => {
  const colors: { [key: string]: string } = {
    'Dairy': '#E0F2FE',
    'Meat': '#FEE2E2',
    'Produce': '#DCFCE7',
    'Bakery': '#FEF3C7',
    'Pantry': '#EDE9FE',
    'Beverages': '#E0E7FF',
    'Frozen': '#E0F2F9',
    'Default': '#F3F4F6',
  };
  
  return colors[category] || colors.Default;
};

// Format the date when an item was added to pantry
export const formatAddedDate = (dateString: string): string => {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Unknown';
  
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  // For dates older than a week, show the actual date
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
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