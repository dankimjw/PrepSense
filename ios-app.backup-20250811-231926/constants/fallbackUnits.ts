/**
 * Comprehensive fallback unit mapping for food items when AI/LLM cannot determine the quantity unit.
 * This system provides sensible defaults based on food categories and types.
 */

export interface FallbackUnitMapping {
  category: string;
  subcategory?: string;
  defaultUnit: string;
  alternativeUnits: string[];
  standardWeight?: number; // in grams
  description: string;
}

// Food category mappings for fallback units
export const FOOD_CATEGORY_FALLBACKS: Record<string, FallbackUnitMapping[]> = {
  'Produce': [
    {
      category: 'Produce',
      subcategory: 'fruits',
      defaultUnit: 'each',
      alternativeUnits: ['medium', 'large', 'small'],
      standardWeight: 182,
      description: 'Default for whole fruits (1 medium apple ≈ 182g)'
    },
    {
      category: 'Produce',
      subcategory: 'berries',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'pint'],
      standardWeight: 150,
      description: 'Berries and small fruits (1 cup ≈ 150g)'
    },
    {
      category: 'Produce',
      subcategory: 'leafy_greens',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'bunch'],
      standardWeight: 30,
      description: 'Leafy greens raw (1 cup ≈ 30g)'
    },
    {
      category: 'Produce',
      subcategory: 'root_vegetables',
      defaultUnit: 'each',
      alternativeUnits: ['medium', 'lb', 'oz'],
      standardWeight: 173,
      description: 'Root vegetables (1 medium potato ≈ 173g)'
    },
    {
      category: 'Produce',
      subcategory: 'cruciferous',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'each'],
      standardWeight: 90,
      description: 'Cruciferous vegetables chopped (1 cup ≈ 90g)'
    },
    {
      category: 'Produce',
      subcategory: 'tomatoes_peppers',
      defaultUnit: 'each',
      alternativeUnits: ['medium', 'cup'],
      standardWeight: 123,
      description: 'Tomatoes and peppers (1 medium ≈ 123g)'
    }
  ],

  'Meat': [
    {
      category: 'Meat',
      subcategory: 'meat_poultry',
      defaultUnit: 'oz',
      alternativeUnits: ['lb', 'piece'],
      standardWeight: 28,
      description: 'Meat and poultry (1 oz ≈ 28g cooked)'
    },
    {
      category: 'Meat',
      subcategory: 'ground_meat',
      defaultUnit: 'oz',
      alternativeUnits: ['lb', 'cup'],
      standardWeight: 28,
      description: 'Ground meat (1 oz ≈ 28g)'
    }
  ],

  'Seafood': [
    {
      category: 'Seafood',
      subcategory: 'fish',
      defaultUnit: 'oz',
      alternativeUnits: ['fillet', 'piece'],
      standardWeight: 28,
      description: 'Fish (1 oz ≈ 28g, 1 fillet ≈ 4 oz)'
    }
  ],

  'Dairy': [
    {
      category: 'Dairy',
      subcategory: 'milk',
      defaultUnit: 'cup',
      alternativeUnits: ['fl oz', 'ml'],
      standardWeight: 240,
      description: 'Milk and milk alternatives (1 cup = 240ml)'
    },
    {
      category: 'Dairy',
      subcategory: 'cheese',
      defaultUnit: 'oz',
      alternativeUnits: ['slice', 'cup'],
      standardWeight: 28,
      description: 'Cheese (1 oz ≈ 28g, 1 slice ≈ 1 oz)'
    },
    {
      category: 'Dairy',
      subcategory: 'yogurt',
      defaultUnit: 'cup',
      alternativeUnits: ['container', 'oz'],
      standardWeight: 245,
      description: 'Yogurt (1 cup ≈ 245g)'
    },
    {
      category: 'Dairy',
      subcategory: 'butter',
      defaultUnit: 'tbsp',
      alternativeUnits: ['tsp', 'oz'],
      standardWeight: 14,
      description: 'Butter and spreads (1 tbsp ≈ 14g)'
    },
    {
      category: 'Dairy',
      subcategory: 'eggs',
      defaultUnit: 'each',
      alternativeUnits: ['large', 'medium'],
      standardWeight: 50,
      description: 'Eggs (1 large egg ≈ 50g)'
    }
  ],

  'Pantry': [
    {
      category: 'Pantry',
      subcategory: 'grains_cooked',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'serving'],
      standardWeight: 195,
      description: 'Cooked grains (rice: 1 cup ≈ 195g)'
    },
    {
      category: 'Pantry',
      subcategory: 'pasta_cooked',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'serving'],
      standardWeight: 200,
      description: 'Cooked pasta (1 cup ≈ 200g)'
    },
    {
      category: 'Pantry',
      subcategory: 'beans_cooked',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'can'],
      standardWeight: 170,
      description: 'Cooked beans (1 cup ≈ 170g)'
    },
    {
      category: 'Pantry',
      subcategory: 'nuts',
      defaultUnit: 'oz',
      alternativeUnits: ['cup', 'tbsp'],
      standardWeight: 30,
      description: 'Nuts (1 oz or 1/4 cup ≈ 30g)'
    },
    {
      category: 'Pantry',
      subcategory: 'oils',
      defaultUnit: 'tbsp',
      alternativeUnits: ['tsp', 'fl oz'],
      standardWeight: 14,
      description: 'Oils and liquid fats (1 tbsp ≈ 14g)'
    },
    {
      category: 'Pantry',
      subcategory: 'nut_butters',
      defaultUnit: 'tbsp',
      alternativeUnits: ['tsp', 'oz'],
      standardWeight: 16,
      description: 'Nut butters (1 tbsp ≈ 16g)'
    },
    {
      category: 'Pantry',
      subcategory: 'seeds',
      defaultUnit: 'tbsp',
      alternativeUnits: ['tsp', 'oz'],
      standardWeight: 10,
      description: 'Seeds (1 tbsp ≈ 10g)'
    },
    {
      category: 'Pantry',
      subcategory: 'spices',
      defaultUnit: 'tsp',
      alternativeUnits: ['tbsp', 'pinch'],
      standardWeight: 5,
      description: 'Spices and seasonings (1 tsp ≈ 5g)'
    }
  ],

  'Bakery': [
    {
      category: 'Bakery',
      subcategory: 'bread',
      defaultUnit: 'slice',
      alternativeUnits: ['piece', 'oz'],
      standardWeight: 28,
      description: 'Bread (1 slice ≈ 25-30g)'
    },
    {
      category: 'Bakery',
      subcategory: 'cookies',
      defaultUnit: 'each',
      alternativeUnits: ['piece', 'cookie'],
      standardWeight: 25,
      description: 'Cookies (1 medium cookie ≈ 25g)'
    },
    {
      category: 'Bakery',
      subcategory: 'muffins',
      defaultUnit: 'each',
      alternativeUnits: ['muffin', 'piece'],
      standardWeight: 60,
      description: 'Muffins (1 medium muffin ≈ 60g)'
    },
    {
      category: 'Bakery',
      subcategory: 'cake',
      defaultUnit: 'slice',
      alternativeUnits: ['piece', 'oz'],
      standardWeight: 80,
      description: 'Cake (1 slice ≈ 80g)'
    }
  ],

  'Beverages': [
    {
      category: 'Beverages',
      subcategory: 'default',
      defaultUnit: 'cup',
      alternativeUnits: ['fl oz', 'ml'],
      standardWeight: 240,
      description: 'Default beverages (1 cup = 8 fl oz ≈ 240ml)'
    },
    {
      category: 'Beverages',
      subcategory: 'alcohol',
      defaultUnit: 'fl oz',
      alternativeUnits: ['serving', 'shot'],
      standardWeight: 30,
      description: 'Alcoholic beverages (1 fl oz ≈ 30ml)'
    }
  ],

  'Snacks': [
    {
      category: 'Snacks',
      subcategory: 'chips_crackers',
      defaultUnit: 'oz',
      alternativeUnits: ['serving', 'bag'],
      standardWeight: 28,
      description: 'Chips and crackers (1 oz ≈ 28g)'
    },
    {
      category: 'Snacks',
      subcategory: 'bars',
      defaultUnit: 'each',
      alternativeUnits: ['bar', 'piece'],
      standardWeight: 40,
      description: 'Snack bars (1 bar ≈ 40g)'
    }
  ],

  'Canned Goods': [
    {
      category: 'Canned Goods',
      subcategory: 'soups',
      defaultUnit: 'cup',
      alternativeUnits: ['can', 'serving'],
      standardWeight: 240,
      description: 'Soups (1 cup ≈ 240ml)'
    },
    {
      category: 'Canned Goods',
      subcategory: 'vegetables',
      defaultUnit: 'cup',
      alternativeUnits: ['can', 'oz'],
      standardWeight: 120,
      description: 'Canned vegetables (1 cup ≈ 120g)'
    }
  ],

  'Frozen': [
    {
      category: 'Frozen',
      subcategory: 'vegetables',
      defaultUnit: 'cup',
      alternativeUnits: ['oz', 'bag'],
      standardWeight: 120,
      description: 'Frozen vegetables (1 cup ≈ 120g)'
    },
    {
      category: 'Frozen',
      subcategory: 'meals',
      defaultUnit: 'each',
      alternativeUnits: ['serving', 'package'],
      standardWeight: 300,
      description: 'Frozen meals (1 meal ≈ 300g)'
    }
  ]
};

// Specific food item patterns for more precise matching
export const FOOD_ITEM_PATTERNS: Record<string, string> = {
  // Fruits
  'apple': 'each',
  'banana': 'each',
  'orange': 'each',
  'strawberry': 'cup',
  'blueberry': 'cup',
  'raspberry': 'cup',
  'grape': 'cup',
  'cherry': 'cup',
  'avocado': 'each',
  
  // Vegetables
  'potato': 'each',
  'onion': 'each',
  'carrot': 'each',
  'tomato': 'each',
  'bell pepper': 'each',
  'spinach': 'cup',
  'lettuce': 'cup',
  'broccoli': 'cup',
  'cauliflower': 'cup',
  
  // Proteins
  'chicken': 'oz',
  'beef': 'oz',
  'pork': 'oz',
  'fish': 'oz',
  'salmon': 'oz',
  'tuna': 'oz',
  'egg': 'each',
  'tofu': 'oz',
  
  // Dairy
  'milk': 'cup',
  'cheese': 'oz',
  'yogurt': 'cup',
  'butter': 'tbsp',
  
  // Grains
  'rice': 'cup',
  'pasta': 'cup',
  'bread': 'slice',
  'cereal': 'cup',
  'oats': 'cup',
  
  // Condiments
  'ketchup': 'tbsp',
  'mustard': 'tbsp',
  'mayo': 'tbsp',
  'oil': 'tbsp',
  'vinegar': 'tbsp',
  'salt': 'tsp',
  'pepper': 'tsp'
};

// Fallback hierarchy for unit determination
export const FALLBACK_HIERARCHY = [
  'Check food-specific common unit',
  'Use category default',
  'Default to serving (100g)',
  'Fall back to piece or item',
  'Prompt user for clarification'
] as const;

// Invalid units that should never be allowed
export const INVALID_UNITS = [
  'B', 'b', // Price formatting characters
  '$', '¢', // Currency symbols
  '%', // Percentage
  '#', // Hash/pound symbol
  '&', // Ampersand
  '@', // At symbol
  '!', '?', // Punctuation
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', // Pure numbers
];

/**
 * Get fallback unit for a food item based on its name and category
 */
export const getFallbackUnit = (itemName: string, category?: string): string => {
  const normalizedName = itemName.toLowerCase().trim();
  
  // Step 1: Check for specific food item patterns
  for (const [pattern, unit] of Object.entries(FOOD_ITEM_PATTERNS)) {
    if (normalizedName.includes(pattern)) {
      return unit;
    }
  }
  
  // Step 2: Use category-based fallback
  if (category && FOOD_CATEGORY_FALLBACKS[category]) {
    const categoryFallbacks = FOOD_CATEGORY_FALLBACKS[category];
    
    // Try to find the most specific subcategory match
    for (const fallback of categoryFallbacks) {
      if (fallback.subcategory) {
        // Check if item name matches subcategory patterns
        if (matchesSubcategory(normalizedName, fallback.subcategory)) {
          return fallback.defaultUnit;
        }
      }
    }
    
    // Fall back to first (most general) category default
    return categoryFallbacks[0].defaultUnit;
  }
  
  // Step 3: Default fallback based on common patterns
  if (isLiquid(normalizedName)) {
    return 'cup';
  } else if (isSpice(normalizedName)) {
    return 'tsp';
  } else if (isCondiment(normalizedName)) {
    return 'tbsp';
  }
  
  // Step 4: Final fallback
  return 'each';
};

/**
 * Check if a unit is invalid and should be rejected
 */
export const isInvalidUnit = (unit: string): boolean => {
  return INVALID_UNITS.includes(unit.trim());
};

/**
 * Get suggested alternative units for a given category
 */
export const getAlternativeUnits = (category: string): string[] => {
  if (!FOOD_CATEGORY_FALLBACKS[category]) {
    return ['each', 'cup', 'oz', 'tbsp'];
  }
  
  const allAlternatives = FOOD_CATEGORY_FALLBACKS[category]
    .flatMap(fallback => [fallback.defaultUnit, ...fallback.alternativeUnits]);
  
  // Remove duplicates and return
  return [...new Set(allAlternatives)];
};

// Helper functions
function matchesSubcategory(itemName: string, subcategory: string): boolean {
  const subcategoryPatterns: Record<string, string[]> = {
    'berries': ['berry', 'strawberry', 'blueberry', 'raspberry', 'blackberry', 'cranberry'],
    'leafy_greens': ['spinach', 'lettuce', 'kale', 'arugula', 'chard', 'greens'],
    'root_vegetables': ['potato', 'carrot', 'beet', 'turnip', 'radish', 'sweet potato'],
    'cruciferous': ['broccoli', 'cauliflower', 'cabbage', 'brussels sprouts'],
    'tomatoes_peppers': ['tomato', 'pepper', 'bell pepper', 'jalapeño'],
    'meat_poultry': ['chicken', 'beef', 'pork', 'turkey', 'lamb'],
    'ground_meat': ['ground beef', 'ground turkey', 'ground chicken', 'hamburger'],
    'fish': ['salmon', 'tuna', 'cod', 'tilapia', 'fish'],
    'milk': ['milk', 'almond milk', 'soy milk', 'oat milk'],
    'cheese': ['cheese', 'cheddar', 'mozzarella', 'swiss'],
    'yogurt': ['yogurt', 'greek yogurt'],
    'butter': ['butter', 'margarine'],
    'eggs': ['egg', 'eggs'],
    'grains_cooked': ['rice', 'quinoa', 'barley', 'cooked'],
    'pasta_cooked': ['pasta', 'spaghetti', 'penne', 'noodles'],
    'beans_cooked': ['beans', 'lentils', 'chickpeas', 'black beans'],
    'nuts': ['nuts', 'almonds', 'walnuts', 'peanuts', 'cashews'],
    'oils': ['oil', 'olive oil', 'vegetable oil', 'coconut oil'],
    'nut_butters': ['peanut butter', 'almond butter', 'nut butter'],
    'seeds': ['seeds', 'sunflower seeds', 'chia seeds', 'flax seeds'],
    'spices': ['salt', 'pepper', 'cinnamon', 'paprika', 'cumin'],
    'bread': ['bread', 'toast', 'baguette', 'roll'],
    'cookies': ['cookie', 'biscuit'],
    'muffins': ['muffin'],
    'cake': ['cake', 'cupcake'],
    'alcohol': ['wine', 'beer', 'vodka', 'whiskey', 'rum'],
    'chips_crackers': ['chips', 'crackers', 'pretzels'],
    'bars': ['bar', 'granola bar', 'protein bar'],
    'soups': ['soup', 'broth', 'stew'],
    'meals': ['meal', 'dinner', 'entree']
  };
  
  const patterns = subcategoryPatterns[subcategory] || [];
  return patterns.some(pattern => itemName.includes(pattern));
}

function isLiquid(itemName: string): boolean {
  const liquidPatterns = ['juice', 'milk', 'water', 'soda', 'tea', 'coffee', 'broth', 'stock'];
  return liquidPatterns.some(pattern => itemName.includes(pattern));
}

function isSpice(itemName: string): boolean {
  const spicePatterns = ['salt', 'pepper', 'cinnamon', 'paprika', 'cumin', 'oregano', 'basil', 'thyme'];
  return spicePatterns.some(pattern => itemName.includes(pattern));
}

function isCondiment(itemName: string): boolean {
  const condimentPatterns = ['ketchup', 'mustard', 'mayo', 'sauce', 'dressing', 'oil', 'vinegar'];
  return condimentPatterns.some(pattern => itemName.includes(pattern));
}
