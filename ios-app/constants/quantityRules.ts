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
  'each', 'piece', 'pieces', 'item', 'items', 'pcs', 'pc',
  'bottle', 'bottles', 'can', 'cans', 'jar', 'jars',
  'package', 'packages', 'pkg', 'pack', 'packs',
  'bag', 'bags', 'box', 'boxes', 'carton', 'cartons',
  'container', 'containers', 'tube', 'tubes', 'roll', 'rolls',
  'stick', 'sticks', 'bar', 'bars', 'block', 'blocks',
  'loaf', 'loaves', 'slice', 'slices'
];

/**
 * Determines if an item should only allow whole number quantities
 */
export function shouldAllowDecimals(itemName: string, unit: string): boolean {
  const normalizedName = itemName.toLowerCase().trim();
  const normalizedUnit = unit.toLowerCase().trim();
  
  // Check if unit requires whole numbers
  if (WHOLE_NUMBER_UNITS.includes(normalizedUnit)) {
    return false;
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