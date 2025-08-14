/**
 * Automatic food categorization utility
 * Intelligently categorizes food items based on their names
 * Also suggests appropriate units for different food categories
 */

import { FOOD_CATEGORIES, getCategoryByLabel, getDefaultCategory } from './categoryConfig';
import { UnitOption, UNITS } from '../constants/units';

interface CategoryKeywords {
  [categoryId: string]: string[];
}

/**
 * Keywords for automatic categorization.
 * Each category has an array of keywords that help identify items belonging to that category.
 */
const CATEGORY_KEYWORDS: CategoryKeywords = {
  produce: [
    // Fruits
    'apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry', 'raspberry', 'blackberry',
    'cherry', 'peach', 'pear', 'plum', 'apricot', 'mango', 'pineapple', 'watermelon', 'cantaloupe',
    'honeydew', 'kiwi', 'papaya', 'coconut', 'avocado', 'lemon', 'lime', 'grapefruit',
    
    // Vegetables
    'lettuce', 'spinach', 'kale', 'arugula', 'cabbage', 'broccoli', 'cauliflower', 'brussels sprouts',
    'carrot', 'celery', 'onion', 'garlic', 'shallot', 'leek', 'potato', 'sweet potato', 'yam',
    'tomato', 'cucumber', 'bell pepper', 'jalapeño', 'serrano', 'poblano', 'mushroom',
    'zucchini', 'yellow squash', 'butternut squash', 'acorn squash', 'eggplant', 'okra',
    'corn', 'peas', 'green beans', 'lima beans', 'asparagus', 'artichoke', 'beets', 'turnip',
    'radish', 'parsnip', 'rutabaga', 'bok choy', 'collard greens', 'swiss chard',
    
    // Herbs
    'basil', 'oregano', 'thyme', 'rosemary', 'sage', 'parsley', 'cilantro', 'dill', 'mint',
    'chives', 'scallion', 'green onion'
  ],
  
  dairy: [
    'milk', 'whole milk', '2% milk', 'skim milk', 'almond milk', 'soy milk', 'oat milk',
    'cheese', 'cheddar', 'mozzarella', 'parmesan', 'swiss', 'gouda', 'brie', 'camembert',
    'feta', 'goat cheese', 'ricotta', 'cottage cheese', 'cream cheese', 'mascarpone',
    'yogurt', 'greek yogurt', 'sour cream', 'heavy cream', 'half and half', 'buttermilk',
    'butter', 'margarine', 'whipped cream', 'ice cream'
  ],
  
  meat: [
    'chicken', 'chicken breast', 'chicken thigh', 'chicken wing', 'ground chicken',
    'beef', 'ground beef', 'steak', 'ribeye', 'sirloin', 'filet mignon', 'chuck roast',
    'brisket', 'short ribs', 'pork', 'pork chop', 'pork tenderloin', 'bacon', 'ham',
    'sausage', 'italian sausage', 'bratwurst', 'chorizo', 'pepperoni', 'salami',
    'turkey', 'ground turkey', 'turkey breast', 'deli meat', 'lunch meat',
    'lamb', 'leg of lamb', 'lamb chop', 'venison', 'duck', 'goose'
  ],
  
  seafood: [
    'salmon', 'tuna', 'cod', 'halibut', 'tilapia', 'mahi mahi', 'sea bass', 'snapper',
    'trout', 'mackerel', 'sardines', 'anchovies', 'shrimp', 'prawns', 'crab', 'lobster',
    'scallops', 'mussels', 'clams', 'oysters', 'calamari', 'squid', 'octopus', 'fish'
  ],
  
  grains: [
    'rice', 'brown rice', 'white rice', 'jasmine rice', 'basmati rice', 'wild rice',
    'quinoa', 'barley', 'oats', 'oatmeal', 'steel cut oats', 'rolled oats',
    'wheat', 'flour', 'all purpose flour', 'bread flour', 'whole wheat flour',
    'cornmeal', 'polenta', 'millet', 'buckwheat', 'bulgur', 'farro', 'freekeh'
  ],
  
  bakery: [
    'bread', 'white bread', 'whole wheat bread', 'sourdough', 'rye bread', 'pumpernickel',
    'bagel', 'english muffin', 'croissant', 'danish', 'muffin', 'donut', 'pastry',
    'roll', 'dinner roll', 'hamburger bun', 'hot dog bun', 'pita', 'naan', 'tortilla',
    'cake', 'cupcake', 'cookie', 'brownie', 'pie', 'tart'
  ],
  
  beverages: [
    'water', 'sparkling water', 'soda', 'cola', 'sprite', 'ginger ale', 'root beer',
    'juice', 'orange juice', 'apple juice', 'cranberry juice', 'grape juice',
    'coffee', 'tea', 'green tea', 'black tea', 'herbal tea', 'beer', 'wine',
    'kombucha', 'energy drink', 'sports drink'
  ],
  
  condiments: [
    'ketchup', 'mustard', 'mayonnaise', 'mayo', 'bbq sauce', 'hot sauce', 'sriracha',
    'soy sauce', 'teriyaki sauce', 'worcestershire', 'ranch', 'italian dressing',
    'balsamic vinegar', 'apple cider vinegar', 'white vinegar', 'honey', 'maple syrup',
    'jam', 'jelly', 'peanut butter', 'almond butter', 'nutella', 'relish', 'pickles'
  ],
  
  oils: [
    'olive oil', 'extra virgin olive oil', 'vegetable oil', 'canola oil', 'coconut oil',
    'avocado oil', 'sesame oil', 'peanut oil', 'sunflower oil', 'safflower oil',
    'grapeseed oil', 'walnut oil', 'flaxseed oil', 'cooking spray'
  ],
  
  baking: [
    'sugar', 'brown sugar', 'powdered sugar', 'confectioners sugar', 'honey', 'molasses',
    'vanilla extract', 'almond extract', 'baking powder', 'baking soda', 'yeast',
    'cocoa powder', 'chocolate chips', 'dark chocolate', 'white chocolate',
    'cornstarch', 'gelatin', 'cream of tartar', 'food coloring'
  ],
  
  spices: [
    'salt', 'black pepper', 'white pepper', 'cayenne', 'paprika', 'chili powder',
    'cumin', 'coriander', 'turmeric', 'ginger', 'cinnamon', 'nutmeg', 'cloves',
    'allspice', 'cardamom', 'fennel', 'star anise', 'bay leaves', 'curry powder',
    'garam masala', 'italian seasoning', 'herbs de provence', 'old bay'
  ],
  
  pasta: [
    'pasta', 'spaghetti', 'penne', 'rigatoni', 'fusilli', 'farfalle', 'linguine',
    'fettuccine', 'angel hair', 'lasagna', 'ravioli', 'tortellini', 'gnocchi',
    'macaroni', 'elbow pasta', 'orzo', 'couscous', 'ramen', 'udon', 'soba'
  ],
  
  canned: [
    'canned', 'can of', 'diced tomatoes', 'tomato sauce', 'tomato paste', 'tomato soup',
    'chicken broth', 'beef broth', 'vegetable broth', 'coconut milk', 'evaporated milk',
    'condensed milk', 'beans', 'black beans', 'kidney beans', 'chickpeas', 'lentils',
    'corn', 'green beans', 'peas', 'carrots', 'pumpkin', 'sweet potato',
    'tuna', 'salmon', 'sardines', 'soup', 'chili'
  ],
  
  frozen: [
    'frozen', 'ice cream', 'frozen yogurt', 'sorbet', 'popsicle', 'frozen pizza',
    'frozen vegetables', 'frozen fruit', 'frozen berries', 'frozen peas',
    'frozen corn', 'frozen broccoli', 'frozen spinach', 'hash browns', 'french fries',
    'chicken nuggets', 'fish sticks', 'frozen dinner', 'frozen meal'
  ],
  
  snacks: [
    'chips', 'potato chips', 'tortilla chips', 'pretzels', 'popcorn', 'crackers',
    'cheese crackers', 'graham crackers', 'granola bar', 'protein bar', 'nuts',
    'almonds', 'walnuts', 'pecans', 'cashews', 'peanuts', 'pistachios',
    'trail mix', 'dried fruit', 'raisins', 'dates', 'candy', 'chocolate'
  ]
};

/**
 * Automatically categorizes a food item based on its name.
 * Uses keyword matching to determine the most appropriate category.
 * 
 * @param itemName - The name of the food item to categorize
 * @returns The category label that best matches the item
 * 
 * @example
 * categorizeFood("Organic Bananas") // returns "Produce"
 * categorizeFood("Whole Milk") // returns "Dairy" 
 * categorizeFood("Ground Beef") // returns "Meat"
 */
export const categorizeFood = (itemName: string): string => {
  if (!itemName || typeof itemName !== 'string') {
    return getDefaultCategory().label;
  }

  const normalizedName = itemName.toLowerCase().trim();
  
  // Check each category's keywords
  for (const [categoryId, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (normalizedName.includes(keyword.toLowerCase())) {
        const category = FOOD_CATEGORIES.find(cat => cat.id === categoryId);
        if (category) {
          return category.label;
        }
      }
    }
  }
  
  // If no match found, return default category
  return getDefaultCategory().label;
};

/**
 * Get suggested categories for a food item (returns top 3 matches).
 * Useful for providing multiple options to users.
 * 
 * @param itemName - The name of the food item
 * @returns Array of category labels sorted by relevance
 */
export const getSuggestedCategories = (itemName: string): string[] => {
  if (!itemName || typeof itemName !== 'string') {
    return [getDefaultCategory().label];
  }

  const normalizedName = itemName.toLowerCase().trim();
  const categoryScores: { [categoryId: string]: number } = {};
  
  // Score each category based on keyword matches
  for (const [categoryId, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    let score = 0;
    for (const keyword of keywords) {
      if (normalizedName.includes(keyword.toLowerCase())) {
        // Give higher score for exact matches and longer keywords
        score += keyword.length;
        if (normalizedName === keyword.toLowerCase()) {
          score += 10; // Bonus for exact match
        }
      }
    }
    if (score > 0) {
      categoryScores[categoryId] = score;
    }
  }
  
  // Sort categories by score and return top 3
  const sortedCategories = Object.entries(categoryScores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)
    .map(([categoryId]) => {
      const category = FOOD_CATEGORIES.find(cat => cat.id === categoryId);
      return category?.label || getDefaultCategory().label;
    });
    
  // If no matches, return default
  if (sortedCategories.length === 0) {
    return [getDefaultCategory().label];
  }
  
  return sortedCategories;
};

/**
 * Check if a category name is valid.
 * 
 * @param categoryName - The category name to validate
 * @returns True if the category exists, false otherwise
 */
export const isValidCategory = (categoryName: string): boolean => {
  return getCategoryByLabel(categoryName) !== null;
};

/**
 * Get confidence score (0-1) for a categorization.
 * Higher scores indicate more confident matches.
 * 
 * @param itemName - The name of the food item
 * @param categoryName - The suggested category
 * @returns Confidence score between 0 and 1
 */
export const getCategorizedConfidence = (itemName: string, categoryName: string): number => {
  if (!itemName || !categoryName) return 0;
  
  const category = getCategoryByLabel(categoryName);
  if (!category) return 0;
  
  const normalizedName = itemName.toLowerCase().trim();
  const keywords = CATEGORY_KEYWORDS[category.id] || [];
  
  let maxScore = 0;
  for (const keyword of keywords) {
    if (normalizedName.includes(keyword.toLowerCase())) {
      const score = keyword.length / normalizedName.length;
      maxScore = Math.max(maxScore, score);
      
      // Exact match gets full confidence
      if (normalizedName === keyword.toLowerCase()) {
        return 1.0;
      }
    }
  }
  
  return Math.min(maxScore * 2, 1.0); // Scale up but cap at 1.0
};

/**
 * Category-specific unit preferences based on how items are typically measured in recipes
 */
const CATEGORY_UNIT_PREFERENCES: { [categoryId: string]: string[] } = {
  produce: [
    // Fruits and vegetables are often counted or weighed
    'each', 'lb', 'oz', 'cup', 'pcs', 'bag'
  ],
  dairy: [
    // Dairy products are usually measured by volume or weight
    'cup', 'oz', 'lb', 'ml', 'l', 'package', 'carton'
  ],
  meat: [
    // Meat is typically weighed
    'lb', 'oz', 'kg', 'g', 'package', 'each'
  ],
  seafood: [
    // Seafood is typically weighed or counted
    'lb', 'oz', 'kg', 'g', 'each', 'package'
  ],
  grains: [
    // Grains are measured by volume or weight
    'cup', 'lb', 'oz', 'g', 'kg', 'bag', 'package'
  ],
  bakery: [
    // Bakery items are often counted or packaged
    'each', 'loaf', 'package', 'bag', 'box', 'pcs'
  ],
  beverages: [
    // Beverages are measured by volume
    'fl oz', 'cup', 'ml', 'l', 'bottle', 'can', 'carton', 'gal'
  ],
  condiments: [
    // Condiments are typically small volume measurements
    'tbsp', 'tsp', 'cup', 'oz', 'jar', 'bottle', 'package'
  ],
  oils: [
    // Oils are measured by volume
    'tbsp', 'tsp', 'cup', 'fl oz', 'ml', 'bottle'
  ],
  baking: [
    // Baking ingredients are precisely measured
    'cup', 'tbsp', 'tsp', 'oz', 'lb', 'g', 'package'
  ],
  spices: [
    // Spices are small precise measurements
    'tsp', 'tbsp', 'oz', 'g', 'jar', 'package'
  ],
  pasta: [
    // Pasta and rice are measured by weight or volume
    'lb', 'oz', 'cup', 'g', 'kg', 'package', 'box'
  ],
  canned: [
    // Canned goods come in standard sizes
    'can', 'oz', 'cup', 'package'
  ],
  frozen: [
    // Frozen items are typically packaged
    'package', 'bag', 'box', 'oz', 'lb', 'each'
  ],
  snacks: [
    // Snacks are often packaged or weighed
    'package', 'bag', 'oz', 'lb', 'box', 'each'
  ],
  other: [
    // Default units for uncategorized items
    'each', 'package', 'oz', 'cup'
  ]
};

/**
 * Get suggested units for a food item based on its category and specific characteristics.
 * Returns units in order of preference for the given food item.
 * 
 * @param itemName - The name of the food item
 * @param categoryName - The category of the food item (optional, will auto-detect if not provided)
 * @returns Array of suggested unit values ordered by preference
 * 
 * @example
 * getSuggestedUnits("Bananas") // returns ["each", "lb", "oz", "cup", "pcs", "bag"]
 * getSuggestedUnits("Olive Oil") // returns ["tbsp", "tsp", "cup", "fl oz", "ml", "bottle"]
 * getSuggestedUnits("Ground Beef") // returns ["lb", "oz", "kg", "g", "package", "each"]
 */
export const getSuggestedUnits = (itemName: string, categoryName?: string): string[] => {
  // Auto-detect category if not provided
  const category = categoryName || categorizeFood(itemName);
  const categoryData = getCategoryByLabel(category);
  const categoryId = categoryData?.id || 'other';
  
  const normalizedName = itemName.toLowerCase().trim();
  
  // Get base units for the category
  let suggestedUnits = [...(CATEGORY_UNIT_PREFERENCES[categoryId] || CATEGORY_UNIT_PREFERENCES.other)];
  
  // Item-specific unit adjustments
  if (normalizedName.includes('milk') || normalizedName.includes('juice')) {
    // Liquids should prioritize volume measurements
    suggestedUnits = ['cup', 'fl oz', 'ml', 'l', 'carton', 'bottle', ...suggestedUnits.filter(u => !['cup', 'fl oz', 'ml', 'l', 'carton', 'bottle'].includes(u))];
  } else if (normalizedName.includes('oil') || normalizedName.includes('vinegar')) {
    // Cooking oils and vinegars are typically small measurements
    suggestedUnits = ['tbsp', 'tsp', 'fl oz', 'cup', 'ml', 'bottle', ...suggestedUnits.filter(u => !['tbsp', 'tsp', 'fl oz', 'cup', 'ml', 'bottle'].includes(u))];
  } else if (normalizedName.includes('salt') || normalizedName.includes('pepper') || normalizedName.includes('spice')) {
    // Seasonings are very small measurements
    suggestedUnits = ['tsp', 'tbsp', 'oz', 'g', 'jar', ...suggestedUnits.filter(u => !['tsp', 'tbsp', 'oz', 'g', 'jar'].includes(u))];
  } else if (normalizedName.includes('flour') || normalizedName.includes('sugar')) {
    // Baking staples are often measured by cups or weight
    suggestedUnits = ['cup', 'lb', 'oz', 'g', 'kg', 'bag', ...suggestedUnits.filter(u => !['cup', 'lb', 'oz', 'g', 'kg', 'bag'].includes(u))];
  } else if (normalizedName.includes('egg')) {
    // Eggs are counted
    suggestedUnits = ['each', 'dozen', 'carton', ...suggestedUnits.filter(u => !['each', 'dozen', 'carton'].includes(u))];
  } else if (normalizedName.includes('bread') || normalizedName.includes('loaf')) {
    // Bread items
    suggestedUnits = ['loaf', 'each', 'package', 'slice', ...suggestedUnits.filter(u => !['loaf', 'each', 'package', 'slice'].includes(u))];
  } else if (normalizedName.includes('can') || normalizedName.includes('canned')) {
    // Canned items
    suggestedUnits = ['can', 'oz', 'cup', ...suggestedUnits.filter(u => !['can', 'oz', 'cup'].includes(u))];
  } else if (normalizedName.includes('frozen')) {
    // Frozen items are typically packaged
    suggestedUnits = ['package', 'bag', 'box', 'oz', 'lb', ...suggestedUnits.filter(u => !['package', 'bag', 'box', 'oz', 'lb'].includes(u))];
  }
  
  // Remove duplicates while preserving order
  return [...new Set(suggestedUnits)];
};

/**
 * Get the most appropriate default unit for a food item.
 * This is the first (most preferred) unit from the suggestion list.
 * 
 * @param itemName - The name of the food item
 * @param categoryName - The category of the food item (optional)
 * @returns The most appropriate unit value for the item
 * 
 * @example
 * getDefaultUnitForItem("Bananas") // returns "each"
 * getDefaultUnitForItem("Olive Oil") // returns "tbsp"
 * getDefaultUnitForItem("Ground Beef") // returns "lb"
 */
export const getDefaultUnitForItem = (itemName: string, categoryName?: string): string => {
  const suggestedUnits = getSuggestedUnits(itemName, categoryName);
  return suggestedUnits[0] || 'each';
};

/**
 * Check if a unit is appropriate for a given food item.
 * 
 * @param itemName - The name of the food item
 * @param unit - The unit to check
 * @param categoryName - The category of the food item (optional)
 * @returns True if the unit is appropriate for the item
 */
export const isUnitAppropriateForItem = (itemName: string, unit: string, categoryName?: string): boolean => {
  const suggestedUnits = getSuggestedUnits(itemName, categoryName);
  return suggestedUnits.includes(unit.toLowerCase());
};