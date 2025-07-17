// utils/ingredientParser.ts - Parse quantities and units from ingredient strings

export interface ParsedIngredient {
  name: string;
  quantity?: number;
  unit?: string;
  originalString: string;
}

// Common unit mappings
const unitMappings: { [key: string]: string } = {
  'cups': 'cup',
  'cup': 'cup',
  'tablespoons': 'tbsp',
  'tablespoon': 'tbsp',
  'tbsp': 'tbsp',
  'teaspoons': 'tsp',
  'teaspoon': 'tsp',
  'tsp': 'tsp',
  'pounds': 'lb',
  'pound': 'lb',
  'lbs': 'lb',
  'lb': 'lb',
  'ounces': 'oz',
  'ounce': 'oz',
  'oz': 'oz',
  'grams': 'g',
  'gram': 'g',
  'g': 'g',
  'kilograms': 'kg',
  'kilogram': 'kg',
  'kg': 'kg',
  'milliliters': 'ml',
  'milliliter': 'ml',
  'ml': 'ml',
  'liters': 'l',
  'liter': 'l',
  'l': 'l',
  'pieces': 'piece',
  'piece': 'piece',
  'pcs': 'piece',
  'cloves': 'clove',
  'clove': 'clove',
  'cans': 'can',
  'can': 'can',
  'bunch': 'bunch',
  'bunches': 'bunch',
};

export function parseIngredient(ingredientString: string): ParsedIngredient {
  const original = ingredientString.trim();
  
  // Common patterns:
  // "2 cups of flour"
  // "1/2 tsp salt"
  // "3 tomatoes"
  // "Salt to taste"
  // "Olive oil"
  
  // Remove common phrases but keep the ingredient name intact
  let cleaned = original
    .replace(/\s+of\s+/gi, ' ')
    .replace(/\s+to taste/gi, '')
    .replace(/,.*$/, '') // Remove everything after comma
    .trim();
  
  // Try to extract quantity and unit
  // Match patterns like "2 cups", "1/2 tsp", "3.5 kg"
  const quantityUnitPattern = /^(\d+(?:\.\d+)?|\d+\/\d+)\s*([a-zA-Z]+)?/;
  const match = cleaned.match(quantityUnitPattern);
  
  if (match) {
    let quantity: number | undefined;
    let unit: string | undefined;
    let name = cleaned;
    
    // Parse quantity
    const quantityStr = match[1];
    if (quantityStr.includes('/')) {
      // Handle fractions
      const [numerator, denominator] = quantityStr.split('/').map(Number);
      quantity = numerator / denominator;
    } else {
      quantity = parseFloat(quantityStr);
    }
    
    // Parse unit if present
    if (match[2]) {
      const unitCandidate = match[2].toLowerCase();
      
      // Check if this is actually a unit or part of the ingredient name
      if (unitMappings[unitCandidate] || 
          ['small', 'medium', 'large', 'whole'].includes(unitCandidate)) {
        // It's a valid unit
        unit = unitMappings[unitCandidate] || unitCandidate;
        // Remove quantity and unit from name
        name = cleaned.substring(match[0].length).trim();
      } else {
        // It's not a unit, it's part of the ingredient name
        // Only remove the quantity, keep the rest as the name
        name = cleaned.substring(match[1].length).trim();
        unit = 'piece'; // Default unit for countable items
      }
    } else {
      // No unit found, the rest is the name
      name = cleaned.substring(match[1].length).trim();
      unit = 'piece'; // Default unit for countable items
    }
    
    // If name is empty, it means the whole string was quantity + unit
    if (!name) {
      name = original;
      quantity = undefined;
      unit = undefined;
    }
    
    return {
      name,
      quantity,
      unit,
      originalString: original,
    };
  }
  
  // No quantity found, treat the whole string as the ingredient name
  return {
    name: original,
    originalString: original,
  };
}

export function parseIngredientsList(ingredients: string[]): ParsedIngredient[] {
  return ingredients.map(parseIngredient);
}