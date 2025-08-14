import { normalizeUnit, getUnitLabel, getUnitAbbreviation } from '../constants/units';

// Re-export normalized functions for backward compatibility
export { normalizeUnit, getUnitLabel, getUnitAbbreviation };

// Helper to format quantity with proper unit display
export const formatQuantityWithUnit = (quantity: number, unit: string): string => {
  const abbreviation = getUnitAbbreviation(unit);
  
  // Format number to remove unnecessary decimals
  const formattedQuantity = quantity % 1 === 0 ? quantity.toString() : quantity.toFixed(1);
  
  return `${formattedQuantity} ${abbreviation}`;
};

// Helper to parse quantity strings that might include units
export const parseQuantityString = (input: string): { quantity: number; unit?: string } => {
  const trimmed = input.trim();
  const match = trimmed.match(/^(\d+\.?\d*)\s*(.*)$/);
  
  if (match) {
    const quantity = parseFloat(match[1]);
    const unit = match[2] ? normalizeUnit(match[2]) : undefined;
    return { quantity, unit };
  }
  
  return { quantity: 0 };
};