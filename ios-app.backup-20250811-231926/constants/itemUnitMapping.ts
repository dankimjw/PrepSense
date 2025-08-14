/**
 * Item category to unit mapping for PrepSense
 * Defines which units are appropriate for different types of food items
 */

import { UnitOption, UNITS } from './units';

// Define food categories
export const FoodCategory = {
  PRODUCE_COUNTABLE: 'produce_countable',  // Items typically counted (bananas, apples)
  PRODUCE_BULK: 'produce_bulk',  // Items typically sold by weight (grapes, berries)
  LIQUIDS: 'liquids',  // Milk, juice, oil
  DRY_GOODS: 'dry_goods',  // Flour, sugar, rice
  MEAT_SEAFOOD: 'meat_seafood',  // Meat, fish, poultry
  DAIRY_SOLID: 'dairy_solid',  // Cheese, butter
  EGGS: 'eggs',  // Eggs
  BREAD_BAKERY: 'bread_bakery',  // Bread, rolls, pastries
  CANNED_JARRED: 'canned_jarred',  // Canned goods, jarred items
  CONDIMENTS: 'condiments',  // Sauces, dressings, spreads
  SPICES_HERBS: 'spices_herbs',  // Spices, herbs, seasonings
  SNACKS: 'snacks',  // Chips, crackers, cookies
  FROZEN: 'frozen',  // Frozen foods
  BEVERAGES: 'beverages',  // Non-liquid beverages (soda cans, bottles)
  GENERAL: 'general',  // Default category
} as const;

export type FoodCategoryType = typeof FoodCategory[keyof typeof FoodCategory];

// Map categories to allowed units
export const CATEGORY_UNIT_MAPPING: Record<string, string[]> = {
  [FoodCategory.PRODUCE_COUNTABLE]: [
    'each',
    'g',
    'kg',
    'oz',
    'lb',
    'bag',
    'package',
  ],
  
  [FoodCategory.PRODUCE_BULK]: [
    'g',
    'kg',
    'oz',
    'lb',
    'cup',
    'bag',
    'package',
  ],
  
  [FoodCategory.LIQUIDS]: [
    'ml',
    'l',
    'fl oz',
    'cup',
    'pt',
    'qt',
    'gal',
    'tbsp',
    'tsp',
    'each',  // For bottles/containers
    'package',
  ],
  
  [FoodCategory.DRY_GOODS]: [
    'g',
    'kg',
    'oz',
    'lb',
    'cup',
    'tbsp',
    'tsp',
    'bag',
    'package',
  ],
  
  [FoodCategory.MEAT_SEAFOOD]: [
    'g',
    'kg',
    'oz',
    'lb',
    'each',  // For steaks, chops, fillets
    'package',
  ],
  
  [FoodCategory.DAIRY_SOLID]: [
    'g',
    'kg',
    'oz',
    'lb',
    'cup',
    'tbsp',
    'each',  // For sticks of butter
    'package',
  ],
  
  [FoodCategory.EGGS]: [
    'each',
    'carton',
    'case',
  ],
  
  [FoodCategory.BREAD_BAKERY]: [
    'each',
    'package',
    'bag',
    'g',
    'oz',
    'lb',
  ],
  
  [FoodCategory.CANNED_JARRED]: [
    'each',
    'ml',
    'l',
    'fl oz',
    'cup',
    'g',
    'oz',
    'package',
    'case',
  ],
  
  [FoodCategory.CONDIMENTS]: [
    'ml',
    'l',
    'fl oz',
    'cup',
    'tbsp',
    'tsp',
    'g',
    'oz',
    'each',  // For bottles/jars
    'package',
  ],
  
  [FoodCategory.SPICES_HERBS]: [
    'g',
    'oz',
    'tbsp',
    'tsp',
    'each',  // For containers
    'package',
  ],
  
  [FoodCategory.SNACKS]: [
    'g',
    'kg',
    'oz',
    'lb',
    'cup',
    'each',
    'package',
    'bag',
    'case',
  ],
  
  [FoodCategory.FROZEN]: [
    'g',
    'kg',
    'oz',
    'lb',
    'cup',
    'each',
    'package',
    'bag',
  ],
  
  [FoodCategory.BEVERAGES]: [
    'each',
    'package',
    'case',
    'carton',
  ],
  
  // Default for unknown categories
  [FoodCategory.GENERAL]: [
    'each',
    'g',
    'kg',
    'oz',
    'lb',
    'ml',
    'l',
    'cup',
    'package',
  ],
};

// Keywords to help categorize items
export const CATEGORY_KEYWORDS: Record<string, string[]> = {
  [FoodCategory.PRODUCE_COUNTABLE]: [
    'banana', 'apple', 'orange', 'lemon', 'lime', 'peach', 'pear', 
    'plum', 'avocado', 'mango', 'kiwi', 'onion', 'potato', 'tomato',
    'cucumber', 'pepper', 'corn', 'eggplant', 'zucchini',
  ],
  
  [FoodCategory.PRODUCE_BULK]: [
    'grape', 'berry', 'berries', 'strawberry', 'blueberry', 'raspberry',
    'blackberry', 'cherry', 'cherries', 'spinach', 'lettuce', 'kale',
    'arugula', 'herbs', 'cilantro', 'parsley', 'basil',
  ],
  
  [FoodCategory.LIQUIDS]: [
    'milk', 'juice', 'oil', 'vinegar', 'water', 'broth', 'stock',
    'cream', 'yogurt', 'kefir', 'smoothie', 'drink', 'beverage',
  ],
  
  [FoodCategory.DRY_GOODS]: [
    'flour', 'sugar', 'rice', 'pasta', 'noodle', 'cereal', 'oats',
    'quinoa', 'barley', 'lentil', 'bean', 'pea', 'chickpea', 
    'salt', 'baking powder', 'baking soda', 'yeast',
  ],
  
  [FoodCategory.MEAT_SEAFOOD]: [
    'chicken', 'beef', 'pork', 'lamb', 'turkey', 'duck', 'fish',
    'salmon', 'tuna', 'shrimp', 'lobster', 'crab', 'scallop',
    'steak', 'ground', 'mince', 'chop', 'breast', 'thigh', 'wing',
  ],
  
  [FoodCategory.DAIRY_SOLID]: [
    'cheese', 'butter', 'margarine', 'cream cheese', 'cottage cheese',
    'mozzarella', 'cheddar', 'parmesan', 'feta', 'brie',
  ],
  
  [FoodCategory.EGGS]: [
    'egg', 'eggs',
  ],
  
  [FoodCategory.BREAD_BAKERY]: [
    'bread', 'roll', 'bagel', 'muffin', 'croissant', 'pastry',
    'cake', 'cookie', 'donut', 'pie', 'tart', 'baguette', 'loaf',
  ],
  
  [FoodCategory.CANNED_JARRED]: [
    'can', 'canned', 'jar', 'jarred', 'sauce', 'salsa', 'pickle',
    'olive', 'preserve', 'jam', 'jelly', 'honey', 'syrup',
  ],
  
  [FoodCategory.CONDIMENTS]: [
    'ketchup', 'mustard', 'mayonnaise', 'mayo', 'dressing', 'sauce',
    'hot sauce', 'soy sauce', 'worcestershire', 'bbq sauce',
  ],
  
  [FoodCategory.SPICES_HERBS]: [
    'spice', 'pepper', 'paprika', 'cumin', 'coriander', 'turmeric',
    'cinnamon', 'nutmeg', 'oregano', 'thyme', 'rosemary', 'sage',
  ],
  
  [FoodCategory.SNACKS]: [
    'chip', 'cracker', 'pretzel', 'popcorn', 'nut', 'candy',
    'chocolate', 'granola', 'protein bar', 'trail mix',
  ],
  
  [FoodCategory.FROZEN]: [
    'frozen', 'ice cream', 'popsicle', 'pizza', 'meal', 'dinner',
  ],
  
  [FoodCategory.BEVERAGES]: [
    'soda', 'cola', 'beer', 'wine', 'spirits', 'bottle', 'can',
  ],
};

/**
 * Categorize an item based on its name
 * Returns the most appropriate category
 */
export function categorizeItem(itemName: string, existingCategory?: string): string {
  // If an existing category is provided and valid, use it
  if (existingCategory && CATEGORY_UNIT_MAPPING[existingCategory]) {
    return existingCategory;
  }
  
  const itemLower = itemName.toLowerCase();
  
  // Check each category's keywords
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (itemLower.includes(keyword)) {
        return category;
      }
    }
  }
  
  // Default to general category
  return FoodCategory.GENERAL;
}

/**
 * Get the list of allowed units for an item
 */
export function getAllowedUnits(itemName: string, category?: string): string[] {
  const itemCategory = categorizeItem(itemName, category);
  return CATEGORY_UNIT_MAPPING[itemCategory] || CATEGORY_UNIT_MAPPING[FoodCategory.GENERAL];
}

/**
 * Get the list of allowed unit options (full UnitOption objects) for an item
 */
export function getAllowedUnitOptions(itemName: string, category?: string): UnitOption[] {
  const allowedUnitValues = getAllowedUnits(itemName, category);
  return UNITS.filter(unit => allowedUnitValues.includes(unit.value));
}

/**
 * Check if a unit is allowed for a specific item
 */
export function isUnitAllowed(itemName: string, unit: string, category?: string): boolean {
  const allowedUnits = getAllowedUnits(itemName, category);
  return allowedUnits.includes(unit);
}

/**
 * Get the default unit for an item
 */
export function getDefaultUnit(itemName: string, category?: string): string {
  const itemCategory = categorizeItem(itemName, category);
  const allowedUnits = CATEGORY_UNIT_MAPPING[itemCategory] || ['each'];
  
  // Prefer 'each' for countable items
  if ([FoodCategory.PRODUCE_COUNTABLE, FoodCategory.EGGS, 
       FoodCategory.BREAD_BAKERY, FoodCategory.BEVERAGES].includes(itemCategory)) {
    return 'each';
  }
  
  // Prefer weight for bulk items
  else if ([FoodCategory.PRODUCE_BULK, FoodCategory.MEAT_SEAFOOD,
            FoodCategory.DRY_GOODS].includes(itemCategory)) {
    return allowedUnits.includes('lb') ? 'lb' : 'g';
  }
  
  // Prefer volume for liquids
  else if (itemCategory === FoodCategory.LIQUIDS) {
    return 'fl oz';
  }
  
  // Default to first allowed unit
  return allowedUnits[0] || 'each';
}