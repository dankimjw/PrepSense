// Centralized food category configuration
// This ensures consistent icons and colors across all components

export interface FoodCategory {
  id: string;
  label: string;
  emoji: string;
  materialIcon: string;
  color: string;
  bgColor: string;
}

export const FOOD_CATEGORIES: FoodCategory[] = [
  { 
    id: 'produce', 
    label: 'Produce', 
    emoji: '🥬', 
    materialIcon: 'leaf', 
    color: '#4ADE80',
    bgColor: '#DCFCE7'
  },
  { 
    id: 'dairy', 
    label: 'Dairy', 
    emoji: '🥛', 
    materialIcon: 'cow', 
    color: '#60A5FA',
    bgColor: '#E0F2FE'
  },
  { 
    id: 'meat', 
    label: 'Meat', 
    emoji: '🥩', 
    materialIcon: 'food-steak', 
    color: '#F87171',
    bgColor: '#FEE2E2'
  },
  { 
    id: 'seafood', 
    label: 'Seafood', 
    emoji: '🐟', 
    materialIcon: 'fish', 
    color: '#93C5FD',
    bgColor: '#E0F2FE'
  },
  { 
    id: 'grains', 
    label: 'Grains', 
    emoji: '🌾', 
    materialIcon: 'grain', 
    color: '#FBBF24',
    bgColor: '#FEF3C7'
  },
  { 
    id: 'bakery', 
    label: 'Bakery', 
    emoji: '🍞', 
    materialIcon: 'bread-slice', 
    color: '#D97706',
    bgColor: '#FEF3C7'
  },
  { 
    id: 'beverages', 
    label: 'Beverages', 
    emoji: '🥤', 
    materialIcon: 'cup', 
    color: '#06B6D4',
    bgColor: '#E0F2F9'
  },
  { 
    id: 'condiments', 
    label: 'Condiments', 
    emoji: '🍯', 
    materialIcon: 'bottle-soda-classic', 
    color: '#F59E0B',
    bgColor: '#FEF3C7'
  },
  { 
    id: 'oils', 
    label: 'Oils & Vinegars', 
    emoji: '🫒', 
    materialIcon: 'oil', 
    color: '#84CC16',
    bgColor: '#DCFCE7'
  },
  { 
    id: 'baking', 
    label: 'Baking', 
    emoji: '🧁', 
    materialIcon: 'cupcake', 
    color: '#F472B6',
    bgColor: '#FCE7F3'
  },
  { 
    id: 'spices', 
    label: 'Spices', 
    emoji: '🌶️', 
    materialIcon: 'shaker-outline', 
    color: '#EF4444',
    bgColor: '#FEE2E2'
  },
  { 
    id: 'pasta', 
    label: 'Pasta & Rice', 
    emoji: '🍝', 
    materialIcon: 'pasta', 
    color: '#A78BFA',
    bgColor: '#EDE9FE'
  },
  { 
    id: 'canned', 
    label: 'Canned Goods', 
    emoji: '🥫', 
    materialIcon: 'food-variant', 
    color: '#FB923C',
    bgColor: '#FED7AA'
  },
  { 
    id: 'frozen', 
    label: 'Frozen', 
    emoji: '🧊', 
    materialIcon: 'snowflake', 
    color: '#67E8F9',
    bgColor: '#E0F2F9'
  },
  { 
    id: 'snacks', 
    label: 'Snacks', 
    emoji: '🍿', 
    materialIcon: 'popcorn', 
    color: '#FACC15',
    bgColor: '#FEF3C7'
  },
  { 
    id: 'other', 
    label: 'Other', 
    emoji: '📦', 
    materialIcon: 'package-variant', 
    color: '#9CA3AF',
    bgColor: '#F3F4F6'
  },
];

// Create lookup maps for easy access
export const CATEGORY_BY_ID = FOOD_CATEGORIES.reduce((acc, cat) => {
  acc[cat.id] = cat;
  return acc;
}, {} as Record<string, FoodCategory>);

export const CATEGORY_BY_LABEL = FOOD_CATEGORIES.reduce((acc, cat) => {
  acc[cat.label] = cat;
  acc[cat.label.toLowerCase()] = cat;
  return acc;
}, {} as Record<string, FoodCategory>);

// Helper functions
export const getCategoryById = (id: string): FoodCategory | null => {
  return CATEGORY_BY_ID[id] || null;
};

export const getCategoryByLabel = (label: string): FoodCategory | null => {
  return CATEGORY_BY_LABEL[label] || CATEGORY_BY_LABEL[label.toLowerCase()] || null;
};

export const getCategoryIcon = (categoryInput: string, useEmoji: boolean = true): string => {
  const category = getCategoryById(categoryInput) || getCategoryByLabel(categoryInput);
  if (!category) {
    return useEmoji ? '📦' : 'package-variant';
  }
  return useEmoji ? category.emoji : category.materialIcon;
};

export const getCategoryColor = (categoryInput: string): string => {
  const category = getCategoryById(categoryInput) || getCategoryByLabel(categoryInput);
  return category?.color || '#9CA3AF';
};

export const getCategoryBgColor = (categoryInput: string): string => {
  const category = getCategoryById(categoryInput) || getCategoryByLabel(categoryInput);
  return category?.bgColor || '#F3F4F6';
};

// Default category for items without a category or with "Uncategorized"
export const getDefaultCategory = (): FoodCategory => {
  return CATEGORY_BY_ID.other;
};

// Handle legacy "Uncategorized" items
export const normalizeCategoryLabel = (label: string): string => {
  if (!label || label.toLowerCase() === 'uncategorized') {
    return getDefaultCategory().label;
  }
  return label;
};