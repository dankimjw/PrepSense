/**
 * Quantity validation rules for different types of items
 */

export interface QuantityRule {
  allowDecimals: boolean;
  minValue?: number;
  maxValue?: number;
  step?: number;
}

// Items that must have whole number quantities only
const WHOLE_NUMBER_ITEMS = [
  // Fruits
  'banana', 'bananas', 'apple', 'apples', 'orange', 'oranges', 'pear', 'pears',
  'avocado', 'avocados', 'lemon', 'lemons', 'lime', 'limes', 'mango', 'mangos', 'mangoes',
  'peach', 'peaches', 'plum', 'plums', 'kiwi', 'kiwis', 'coconut', 'coconuts',
  'pineapple', 'pineapples', 'melon', 'melons', 'watermelon', 'watermelons',
  'cantaloupe', 'cantaloupes', 'honeydew', 'grapefruit', 'grapefruits',
  
  // Vegetables
  'potato', 'potatoes', 'onion', 'onions', 'tomato', 'tomatoes', 'cucumber', 'cucumbers',
  'bell pepper', 'bell peppers', 'pepper', 'peppers', 'carrot', 'carrots',
  'zucchini', 'zucchinis', 'eggplant', 'eggplants', 'corn', 'corn cob', 'corn cobs',
  'cabbage', 'cabbages', 'lettuce', 'lettuces', 'cauliflower', 'cauliflowers',
  'broccoli', 'brocolis', 'squash', 'squashes', 'sweet potato', 'sweet potatoes',
  
  // Proteins
  'egg', 'eggs', 'chicken breast', 'chicken breasts', 'chicken thigh', 'chicken thighs',
  'chicken leg', 'chicken legs', 'drumstick', 'drumsticks', 'chicken wing', 'chicken wings',
  'pork chop', 'pork chops', 'steak', 'steaks', 'fish fillet', 'fish fillets',
  'salmon fillet', 'salmon fillets', 'shrimp', 'shrimps',
  
  // Packaged items
  'can', 'cans', 'bottle', 'bottles', 'jar', 'jars', 'box', 'boxes',
  'package', 'packages', 'bag', 'bags', 'pack', 'packs', 'tube', 'tubes',
  'container', 'containers', 'carton', 'cartons', 'loaf', 'loaves',
  'roll', 'rolls', 'stick', 'sticks', 'bar', 'bars', 'block', 'blocks',
  
  // Bakery
  'bread', 'breads', 'bagel', 'bagels', 'muffin', 'muffins', 'croissant', 'croissants',
  'donut', 'donuts', 'doughnut', 'doughnuts', 'cookie', 'cookies', 'cracker', 'crackers',
  
  // Other countable items
  'pill', 'pills', 'tablet', 'tablets', 'capsule', 'capsules',
  'slice', 'slices', 'piece', 'pieces', 'item', 'items'
];

// Units that typically indicate whole items
const WHOLE_NUMBER_UNITS = [
  'each', 'ea', 'piece', 'pieces', 'item', 'items', 'pcs', 'pc',
  'bottle', 'bottles', 'can', 'cans', 'jar', 'jars',
  'package', 'packages', 'pkg', 'pack', 'packs',
  'bag', 'bags', 'box', 'boxes', 'carton', 'cartons',
  'container', 'containers', 'tube', 'tubes', 'roll', 'rolls',
  'stick', 'sticks', 'bar', 'bars', 'block', 'blocks',
  'loaf', 'loaves', 'slice', 'slices',
  'bunch', 'bunches', 'head', 'heads', 'dozen', 'dozens',
  'clove', 'cloves', 'bulb', 'bulbs', 'stalk', 'stalks',
  'sprig', 'sprigs', 'leaf', 'leaves', 'pod', 'pods',
  'ear', 'ears', 'kernel', 'kernels', 'berry', 'berries',
  'whole', 'halves', 'quarter', 'quarters',
  'serving', 'servings', 'portion', 'portions'
];

/**
 * Determines if an item should only allow whole number quantities
 */
export function shouldAllowDecimals(itemName: string, unit: string): boolean {
  const normalizedName = itemName.toLowerCase().trim();
  const normalizedUnit = unit.toLowerCase().trim();
  
  // Always allow decimals for liquid/volume units regardless of name
  const LIQUID_VOLUME_UNITS = [
    'ml', 'milliliter', 'millilitre', 'milliliters', 'millilitres',
    'l', 'liter', 'litre', 'liters', 'litres',
    'fl oz', 'fluid ounce', 'fluid ounces', 'floz',
    'cup', 'cups', 'c',
    'tbsp', 'tablespoon', 'tablespoons', 'tbs', 'tb',
    'tsp', 'teaspoon', 'teaspoons', 'ts', 't',
    'pint', 'pints', 'pt', 'pts',
    'quart', 'quarts', 'qt', 'qts',
    'gallon', 'gallons', 'gal', 'gals'
  ];
  
  // Always allow decimals for weight units regardless of name
  const WEIGHT_UNITS = [
    'g', 'gram', 'grams', 'gr', 'grs',
    'kg', 'kilogram', 'kilograms', 'kilo', 'kilos',
    'oz', 'ounce', 'ounces', 'ounce',
    'lb', 'lbs', 'pound', 'pounds', 'lbm',
    'mg', 'milligram', 'milligrams'
  ];
  
  // Always allow decimals for liquid/volume/weight units
  if (LIQUID_VOLUME_UNITS.includes(normalizedUnit) || WEIGHT_UNITS.includes(normalizedUnit)) {
    return true;
  }
  
  // Check if unit requires whole numbers (count-based units)
  if (WHOLE_NUMBER_UNITS.includes(normalizedUnit)) {
    return false;
  }
  
  // Check if item name contains any whole number keywords, but only for count-type units
  // Don't apply this restriction if it's clearly a liquid/continuous item
  const isLiquidItem = normalizedName.includes('oil') || 
                      normalizedName.includes('sauce') || 
                      normalizedName.includes('vinegar') || 
                      normalizedName.includes('juice') || 
                      normalizedName.includes('milk') || 
                      normalizedName.includes('cream') ||
                      normalizedName.includes('syrup') ||
                      normalizedName.includes('honey') ||
                      normalizedName.includes('liquid') ||
                      normalizedName.includes('water') ||
                      normalizedName.includes('broth') ||
                      normalizedName.includes('stock') ||
                      normalizedName.includes('wine') ||
                      normalizedName.includes('beer') ||
                      normalizedName.includes('vodka') ||
                      normalizedName.includes('whiskey') ||
                      normalizedName.includes('rum') ||
                      normalizedName.includes('gin') ||
                      normalizedName.includes('tequila') ||
                      normalizedName.includes('brandy') ||
                      normalizedName.includes('liqueur') ||
                      normalizedName.includes('extract') ||
                      normalizedName.includes('essence') ||
                      normalizedName.includes('paste') ||
                      normalizedName.includes('puree') ||
                      normalizedName.includes('concentrate');
  
  if (isLiquidItem) {
    return true;
  }
  
  // Check if item name contains any whole number keywords
  const containsWholeNumberItem = WHOLE_NUMBER_ITEMS.some(item => 
    normalizedName.includes(item)
  );
  
  if (containsWholeNumberItem) {
    return false;
  }
  
  // Default to allowing decimals for weight/volume units
  return true;
}

/**
 * Gets quantity validation rules for an item
 */
export function getQuantityRules(itemName: string, unit: string): QuantityRule {
  const allowDecimals = shouldAllowDecimals(itemName, unit);
  
  return {
    allowDecimals,
    minValue: allowDecimals ? 0.1 : 1,
    step: allowDecimals ? 0.1 : 1,
  };
}

/**
 * Validates a quantity value against the rules
 */
export function validateQuantity(quantity: number, itemName: string, unit: string): {
  isValid: boolean;
  error?: string;
} {
  const rules = getQuantityRules(itemName, unit);
  
  if (quantity <= 0) {
    return {
      isValid: false,
      error: 'Quantity must be greater than 0'
    };
  }
  
  if (!rules.allowDecimals && quantity % 1 !== 0) {
    return {
      isValid: false,
      error: `${itemName} must be a whole number (no decimals)`
    };
  }
  
  if (rules.minValue && quantity < rules.minValue) {
    return {
      isValid: false,
      error: `Minimum quantity is ${rules.minValue}`
    };
  }
  
  if (rules.maxValue && quantity > rules.maxValue) {
    return {
      isValid: false,
      error: `Maximum quantity is ${rules.maxValue}`
    };
  }
  
  return { isValid: true };
}

/**
 * Formats input text according to quantity rules
 */
export function formatQuantityInput(input: string, itemName: string, unit: string): string {
  const rules = getQuantityRules(itemName, unit);
  
  if (!rules.allowDecimals) {
    // Remove any decimal points and everything after them
    return input.replace(/\..*/, '');
  }
  
  // For decimal-allowed items, allow one decimal point
  const cleaned = input.replace(/[^0-9.]/g, '');
  const parts = cleaned.split('.');
  
  if (parts.length > 2) {
    // Only allow one decimal point
    return parts[0] + '.' + parts.slice(1).join('');
  }
  
  return cleaned;
}