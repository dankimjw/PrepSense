/**\n * This module is part of the PrepSense React Native app.\n * It defines a screen or component and interacts with context and API services.\n */
import { Item } from '../context/ItemsContext';

// Helper to get a date X days from now
const getExpirationDate = (daysFromNow: number): string => {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().split('T')[0];
};

export const defaultItems: Item[] = [
  // Dairy & Eggs
  {
    id: 'milk-1',
    item_name: 'Milk',
    quantity_amount: 1,
    quantity_unit: 'gal',
    expected_expiration: getExpirationDate(7),
    category: 'Dairy'
  },
  {
    id: 'eggs-1',
    item_name: 'Eggs',
    quantity_amount: 12,
    quantity_unit: 'piece',
    expected_expiration: getExpirationDate(14),
    category: 'Dairy'
  },
  {
    id: 'butter-1',
    item_name: 'Butter',
    quantity_amount: 1,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(30),
    category: 'Dairy'
  },
  {
    id: 'yogurt-1',
    item_name: 'Greek Yogurt',
    quantity_amount: 4,
    quantity_unit: 'pack',
    expected_expiration: getExpirationDate(14),
    category: 'Dairy'
  },
  {
    id: 'cheese-1',
    item_name: 'Cheddar Cheese',
    quantity_amount: 8,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(21),
    category: 'Dairy'
  },
  {
    id: 'cream-1',
    item_name: 'Heavy Cream',
    quantity_amount: 16,
    quantity_unit: 'fl oz',
    expected_expiration: getExpirationDate(10),
    category: 'Dairy'
  },
  
  // Meats
  {
    id: 'chicken-1',
    item_name: 'Chicken Breast',
    quantity_amount: 2,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(2),
    category: 'Meat'
  },
  {
    id: 'beef-1',
    item_name: 'Ground Beef',
    quantity_amount: 1,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(2),
    category: 'Meat'
  },
  {
    id: 'bacon-1',
    item_name: 'Bacon',
    quantity_amount: 12,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(5),
    category: 'Meat'
  },
  
  // Produce
  {
    id: 'bananas-1',
    item_name: 'Bananas',
    quantity_amount: 6,
    quantity_unit: 'piece',
    expected_expiration: getExpirationDate(5),
    category: 'Produce'
  },
  {
    id: 'apples-1',
    item_name: 'Apples',
    quantity_amount: 5,
    quantity_unit: 'piece',
    expected_expiration: getExpirationDate(14),
    category: 'Produce'
  },
  {
    id: 'carrots-1',
    item_name: 'Carrots',
    quantity_amount: 1,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(21),
    category: 'Produce'
  },
  
  // Pantry
  {
    id: 'pasta-1',
    item_name: 'Pasta',
    quantity_amount: 16,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(365),
    category: 'Pantry'
  },
  {
    id: 'rice-1',
    item_name: 'White Rice',
    quantity_amount: 2,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(730),
    category: 'Pantry'
  },
  {
    id: 'cereal-1',
    item_name: 'Breakfast Cereal',
    quantity_amount: 12,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(180),
    category: 'Pantry'
  },
  
  // Canned Goods
  {
    id: 'beans-1',
    item_name: 'Black Beans',
    quantity_amount: 15,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(1095),
    category: 'Canned Goods'
  },
  {
    id: 'soup-1',
    item_name: 'Tomato Soup',
    quantity_amount: 10.5,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(730),
    category: 'Canned Goods'
  },
  
  // Beverages
  {
    id: 'soda-1',
    item_name: 'Soda',
    quantity_amount: 12,
    quantity_unit: 'pack',
    expected_expiration: getExpirationDate(180),
    category: 'Beverages'
  },
  {
    id: 'water-1',
    item_name: 'Bottled Water',
    quantity_amount: 24,
    quantity_unit: 'bottle',
    expected_expiration: getExpirationDate(730),
    category: 'Beverages'
  },
  
  // Baking
  {
    id: 'flour-1',
    item_name: 'All-Purpose Flour',
    quantity_amount: 5,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(365),
    category: 'Baking'
  },
  {
    id: 'sugar-1',
    item_name: 'Granulated Sugar',
    quantity_amount: 4,
    quantity_unit: 'lb',
    expected_expiration: getExpirationDate(730),
    category: 'Baking'
  },
  
  // Spices & Oils
  {
    id: 'olive-oil-1',
    item_name: 'Olive Oil',
    quantity_amount: 16.9,
    quantity_unit: 'fl oz',
    expected_expiration: getExpirationDate(730),
    category: 'Pantry'
  },
  {
    id: 'salt-1',
    item_name: 'Sea Salt',
    quantity_amount: 26,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(1825),
    category: 'Pantry'
  },
  
  // Frozen
  {
    id: 'veggies-1',
    item_name: 'Mixed Vegetables',
    quantity_amount: 16,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(180),
    category: 'Frozen'
  },
  {
    id: 'pizza-1',
    item_name: 'Frozen Pizza',
    quantity_amount: 1,
    quantity_unit: 'piece',
    expected_expiration: getExpirationDate(90),
    category: 'Frozen'
  },
  
  // Additional unique items
  {
    id: 'garlic-1',
    item_name: 'Garlic',
    quantity_amount: 3,
    quantity_unit: 'bulb',
    expected_expiration: getExpirationDate(60),
    category: 'Produce'
  },
  {
    id: 'lettuce-1',
    item_name: 'Lettuce',
    quantity_amount: 1,
    quantity_unit: 'head',
    expected_expiration: getExpirationDate(7),
    category: 'Vegetables'
  },
  {
    id: 'tomato-sauce-1',
    item_name: 'Tomato Sauce',
    quantity_amount: 15,
    quantity_unit: 'oz',
    expected_expiration: getExpirationDate(365),
    category: 'Canned Goods'
  },
  {
    id: 'coffee-1',
    item_name: 'Coffee Beans',
    quantity_amount: 454,
    quantity_unit: 'g',
    expected_expiration: getExpirationDate(90),
    category: 'Beverages'
  },
  {
    id: 'bread-1',
    item_name: 'Bread',
    quantity_amount: 1,
    quantity_unit: 'loaf',
    expected_expiration: getExpirationDate(7),
    category: 'Bakery'
  }
];
