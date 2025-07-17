/**
 * Utility functions for formatting numbers in the app
 */

/**
 * Formats a number to a reasonable number of decimal places
 * - Whole numbers: no decimals (e.g., 2 → "2")
 * - Numbers with decimals: max 2 decimal places (e.g., 2.333 → "2.33")
 * - Very small numbers: max 3 decimal places (e.g., 0.125 → "0.125")
 * @param value The number to format
 * @param maxDecimals Maximum number of decimal places (default: 2)
 * @returns Formatted string
 */
export function formatQuantity(value: number | string | null | undefined, maxDecimals: number = 2): string {
  if (value === null || value === undefined) {
    return '0';
  }

  // Convert to number if string
  const num = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(num)) {
    return '0';
  }

  // Handle whole numbers
  if (Number.isInteger(num)) {
    return num.toString();
  }

  // For very small numbers (less than 0.1), allow up to 3 decimal places
  if (Math.abs(num) < 0.1 && Math.abs(num) > 0) {
    return parseFloat(num.toFixed(3)).toString();
  }

  // For regular decimals, use maxDecimals
  return parseFloat(num.toFixed(maxDecimals)).toString();
}

/**
 * Formats a number as a fraction if it's a common fraction value
 * Otherwise returns the decimal format
 * @param value The number to format
 * @returns Formatted string (fraction or decimal)
 */
export function formatAsFraction(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return '0';
  }

  const num = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(num)) {
    return '0';
  }

  // Common fractions mapping
  const fractions: { [key: number]: string } = {
    0.125: '⅛',
    0.25: '¼',
    0.333: '⅓',
    0.375: '⅜',
    0.5: '½',
    0.625: '⅝',
    0.666: '⅔',
    0.667: '⅔',
    0.75: '¾',
    0.875: '⅞'
  };

  // Check for exact or very close matches to common fractions
  for (const [decimal, fraction] of Object.entries(fractions)) {
    if (Math.abs(num - parseFloat(decimal)) < 0.01) {
      return fraction;
    }
  }

  // Check for mixed numbers (e.g., 1.5 = 1½)
  const wholePart = Math.floor(num);
  const fractionalPart = num - wholePart;
  
  if (wholePart > 0 && fractionalPart > 0) {
    for (const [decimal, fraction] of Object.entries(fractions)) {
      if (Math.abs(fractionalPart - parseFloat(decimal)) < 0.01) {
        return `${wholePart}${fraction}`;
      }
    }
  }

  // Default to decimal format
  return formatQuantity(num);
}

/**
 * Formats ingredient quantities for display in recipes
 * Handles special cases like "pinch", "to taste", etc.
 * @param quantity The quantity value
 * @param unit The unit of measurement
 * @returns Formatted string
 */
export function formatIngredientQuantity(quantity: number | string | null | undefined, unit: string): string {
  // Handle special units that don't need quantities
  const specialUnits = ['pinch', 'to taste', 'dash', 'sprinkle', 'drizzle'];
  if (specialUnits.includes(unit.toLowerCase())) {
    return '';
  }

  // Handle null/undefined/zero quantities
  if (!quantity || quantity === 0) {
    return '';
  }

  // Format the quantity
  return formatAsFraction(quantity);
}

/**
 * Rounds a number to avoid floating point precision issues
 * @param value The number to round
 * @param precision Number of decimal places
 * @returns Rounded number
 */
export function roundToPrecision(value: number, precision: number = 2): number {
  const multiplier = Math.pow(10, precision);
  return Math.round(value * multiplier) / multiplier;
}