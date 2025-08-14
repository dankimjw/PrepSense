import { apiClient } from './apiClient';

export interface UnitValidationResult {
  is_valid: boolean;
  current_unit: string;
  suggested_unit: string;
  suggested_units: string[];
  category: string;
  reason: string;
  severity: 'error' | 'warning' | 'info';
}

export interface UnitSuggestion {
  item_name: string;
  category: string;
  recommended_units: string[];
  default_unit: string;
}

export interface CategoryUnits {
  description: string;
  allowed_units: string[];
  forbidden_units: string[];
  examples: string;
}

/**
 * Validate if a unit is appropriate for a food item
 */
export const validateUnit = async (
  itemName: string,
  unit: string,
  quantity?: number
): Promise<UnitValidationResult> => {
  try {
    const response = await apiClient.post('/units/validate', {
      item_name: itemName,
      unit: unit,
      quantity: quantity
    });
    return response.data;
  } catch (error) {
    console.error('Error validating unit:', error);
    // Return a default validation result on error
    return {
      is_valid: true,
      current_unit: unit,
      suggested_unit: unit,
      suggested_units: [unit],
      category: 'Unknown',
      reason: 'Unable to validate unit',
      severity: 'info'
    };
  }
};

/**
 * Get suggested units for a food item
 */
export const getUnitSuggestions = async (
  itemName: string
): Promise<UnitSuggestion> => {
  try {
    const response = await apiClient.get(`/units/suggestions/${encodeURIComponent(itemName)}`);
    return response.data;
  } catch (error) {
    console.error('Error getting unit suggestions:', error);
    // Return default suggestions on error
    return {
      item_name: itemName,
      category: 'Other',
      recommended_units: ['each', 'lb', 'oz', 'g', 'kg'],
      default_unit: 'each'
    };
  }
};

/**
 * Get all unit categories and their rules
 */
export const getUnitCategories = async (): Promise<Record<string, CategoryUnits>> => {
  try {
    const response = await apiClient.get('/units/categories');
    return response.data;
  } catch (error) {
    console.error('Error getting unit categories:', error);
    return {};
  }
};

/**
 * Batch validate multiple items
 */
export const batchValidateUnits = async (
  items: Array<{ item_name: string; unit: string; quantity?: number }>
): Promise<{
  total_items: number;
  errors: number;
  warnings: number;
  results: Array<{ item_name: string; validation: UnitValidationResult }>;
}> => {
  try {
    const response = await apiClient.post('/units/batch-validate', items);
    return response.data;
  } catch (error) {
    console.error('Error batch validating units:', error);
    // Return empty results on error
    return {
      total_items: items.length,
      errors: 0,
      warnings: 0,
      results: []
    };
  }
};

/**
 * Helper function to determine if a unit change is recommended
 */
export const shouldSuggestUnitChange = (validation: UnitValidationResult): boolean => {
  return validation.severity === 'error' || 
         (validation.severity === 'warning' && validation.suggested_unit !== validation.current_unit);
};

/**
 * Helper function to get user-friendly unit display names
 */
export const getUnitDisplayName = (unit: string): string => {
  const displayNames: Record<string, string> = {
    'ea': 'each',
    'lb': 'pounds',
    'oz': 'ounces',
    'g': 'grams',
    'kg': 'kilograms',
    'ml': 'milliliters',
    'l': 'liters',
    'fl oz': 'fluid ounces',
    'cup': 'cups',
    'tbsp': 'tablespoons',
    'tsp': 'teaspoons',
    'pt': 'pints',
    'qt': 'quarts',
    'gal': 'gallons'
  };
  
  return displayNames[unit] || unit;
};