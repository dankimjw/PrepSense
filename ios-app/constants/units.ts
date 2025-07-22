export interface UnitOption {
  value: string;
  label: string;
  category: 'weight' | 'volume' | 'count';
  abbreviation: string;
  plural?: string;
}

export const UNIT_CATEGORIES = {
  WEIGHT: 'weight',
  VOLUME: 'volume',
  COUNT: 'count',
} as const;

export const UNITS: UnitOption[] = [
  // Weight
  { value: 'mg', label: 'Milligram', category: 'weight', abbreviation: 'mg', plural: 'Milligrams' },
  { value: 'g', label: 'Gram', category: 'weight', abbreviation: 'g', plural: 'Grams' },
  { value: 'kg', label: 'Kilogram', category: 'weight', abbreviation: 'kg', plural: 'Kilograms' },
  { value: 'oz', label: 'Ounce', category: 'weight', abbreviation: 'oz', plural: 'Ounces' },
  { value: 'lb', label: 'Pound', category: 'weight', abbreviation: 'lb', plural: 'Pounds' },
  
  // Volume
  { value: 'ml', label: 'Milliliter', category: 'volume', abbreviation: 'mL', plural: 'Milliliters' },
  { value: 'l', label: 'Liter', category: 'volume', abbreviation: 'L', plural: 'Liters' },
  { value: 'fl oz', label: 'Fluid Ounce', category: 'volume', abbreviation: 'fl oz', plural: 'Fluid Ounces' },
  { value: 'cup', label: 'Cup', category: 'volume', abbreviation: 'cup', plural: 'Cups' },
  { value: 'tbsp', label: 'Tablespoon', category: 'volume', abbreviation: 'Tbsp', plural: 'Tablespoons' },
  { value: 'tsp', label: 'Teaspoon', category: 'volume', abbreviation: 'tsp', plural: 'Teaspoons' },
  { value: 'pt', label: 'Pint', category: 'volume', abbreviation: 'pt', plural: 'Pints' },
  { value: 'qt', label: 'Quart', category: 'volume', abbreviation: 'qt', plural: 'Quarts' },
  { value: 'gal', label: 'Gallon', category: 'volume', abbreviation: 'gal', plural: 'Gallons' },
  
  // Count & Packaging
  { value: 'each', label: 'Each', category: 'count', abbreviation: 'each', plural: 'Each' },
  { value: 'pcs', label: 'Pieces', category: 'count', abbreviation: 'pcs', plural: 'Pieces' },
  { value: 'package', label: 'Package', category: 'count', abbreviation: 'pkg', plural: 'Packages' },
  { value: 'pack', label: 'Pack', category: 'count', abbreviation: 'pack', plural: 'Packs' },
  { value: 'bag', label: 'Bag', category: 'count', abbreviation: 'bag', plural: 'Bags' },
  { value: 'case', label: 'Case', category: 'count', abbreviation: 'case', plural: 'Cases' },
  { value: 'carton', label: 'Carton', category: 'count', abbreviation: 'carton', plural: 'Cartons' },
  { value: 'bottle', label: 'Bottle', category: 'count', abbreviation: 'bottle', plural: 'Bottles' },
  { value: 'jar', label: 'Jar', category: 'count', abbreviation: 'jar', plural: 'Jars' },
  { value: 'can', label: 'Can', category: 'count', abbreviation: 'can', plural: 'Cans' },
  { value: 'box', label: 'Box', category: 'count', abbreviation: 'box', plural: 'Boxes' },
  { value: 'loaf', label: 'Loaf', category: 'count', abbreviation: 'loaf', plural: 'Loaves' },
  { value: 'unit', label: 'Unit', category: 'count', abbreviation: 'unit', plural: 'Units' },
  { value: 'gross', label: 'Gross', category: 'count', abbreviation: 'gross', plural: 'Gross' },
];

// Helper functions
export const getUnitsByCategory = (category: 'weight' | 'volume' | 'count'): UnitOption[] => {
  return UNITS.filter(unit => unit.category === category);
};

export const getUnitByValue = (value: string): UnitOption | undefined => {
  return UNITS.find(unit => unit.value === value.toLowerCase());
};

export const getUnitLabel = (value: string, quantity?: number): string => {
  const unit = getUnitByValue(value);
  if (!unit) return value;
  
  // Use plural form if quantity > 1 and plural is defined
  if (quantity && quantity > 1 && unit.plural) {
    return unit.plural;
  }
  
  return unit.label;
};

export const getUnitAbbreviation = (value: string): string => {
  const unit = getUnitByValue(value);
  return unit?.abbreviation || value;
};

// Common unit conversions (for future use)
export const UNIT_CONVERSIONS = {
  // Weight conversions to grams
  weight: {
    mg: 0.001,
    g: 1,
    kg: 1000,
    oz: 28.3495,
    lb: 453.592,
  },
  // Volume conversions to milliliters
  volume: {
    ml: 1,
    l: 1000,
    'fl oz': 29.5735,
    cup: 236.588,
    tbsp: 14.7868,
    tsp: 4.92892,
    pt: 473.176,
    qt: 946.353,
    gal: 3785.41,
  },
};

// Normalize unit input (handle variations)
export const normalizeUnit = (input: string): string => {
  const normalized = input.toLowerCase().trim();
  
  // Handle common variations
  const variations: { [key: string]: string } = {
    'cups': 'cup',
    'tablespoon': 'tbsp',
    'tablespoons': 'tbsp',
    'teaspoon': 'tsp',
    'teaspoons': 'tsp',
    'pound': 'lb',
    'pounds': 'lb',
    'lbs': 'lb',
    'ounce': 'oz',
    'ounces': 'oz',
    'fluid ounce': 'fl oz',
    'fluid ounces': 'fl oz',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'liter': 'l',
    'liters': 'l',
    'pint': 'pt',
    'pints': 'pt',
    'quart': 'qt',
    'quarts': 'qt',
    'gallon': 'gal',
    'gallons': 'gal',
    'package': 'package',
    'packages': 'package',
    'pkg': 'package',
    'packs': 'pack',
    'pieces': 'pcs',
    'pc': 'pcs',
    'piece': 'pcs',
    'bags': 'bag',
    'cases': 'case',
    'cartons': 'carton',
    'bottles': 'bottle',
    'jars': 'jar',
    'cans': 'can',
    'boxes': 'box',
    'loaves': 'loaf',
    'units': 'unit',
  };
  
  return variations[normalized] || normalized;
};

// Default unit for new items
export const DEFAULT_UNIT = 'each';