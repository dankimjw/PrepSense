/**
 * Shared utility for consistent ingredient matching across the app
 */

interface PantryItem {
  product_name: string;
  [key: string]: any;
}

interface RecipeIngredient {
  id: number;
  name: string;
  original: string;
  [key: string]: any;
}

interface IngredientMatchResult {
  availableIngredients: Set<number>;
  missingIngredients: Set<number>;
  availableCount: number;
  missingCount: number;
  totalCount: number;
}

/**
 * Normalize ingredient name for matching
 */
export function normalizeIngredientName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    // Remove common adjectives and preparation methods
    .replace(/\b(fresh|dried|chopped|minced|sliced|diced|whole|ground|powdered|grated|crushed|finely|roughly|thinly|thickly)\b/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Extract key words from ingredient name for matching
 */
export function extractKeyWords(ingredientName: string): string[] {
  const normalized = normalizeIngredientName(ingredientName);
  const words = normalized.split(/\s+/).filter(word => word.length > 2);
  
  // For multi-word ingredients, also consider the last 2 words as a unit
  if (words.length > 2) {
    const lastTwoWords = words.slice(-2).join(' ');
    words.push(lastTwoWords);
  }
  
  return words;
}

/**
 * Check if an ingredient is available in the pantry
 */
export function isIngredientAvailable(ingredient: RecipeIngredient, pantryItems: PantryItem[]): boolean {
  const ingredientName = ingredient.name;
  const originalText = ingredient.original;
  
  // Normalize pantry items
  const normalizedPantryItems = pantryItems.map(item => ({
    ...item,
    normalized: normalizeIngredientName(item.product_name)
  }));
  
  // Try multiple matching strategies
  
  // 1. Direct normalized match
  const normalizedIngredient = normalizeIngredientName(ingredientName);
  if (normalizedPantryItems.some(item => item.normalized === normalizedIngredient)) {
    return true;
  }
  
  // 2. Check if pantry item contains ingredient name
  if (normalizedPantryItems.some(item => item.normalized.includes(normalizedIngredient))) {
    return true;
  }
  
  // 3. Check if ingredient name contains pantry item
  if (normalizedPantryItems.some(item => normalizedIngredient.includes(item.normalized))) {
    return true;
  }
  
  // 4. Keyword matching
  const ingredientKeywords = extractKeyWords(ingredientName);
  const hasKeywordMatch = normalizedPantryItems.some(pantryItem => {
    return ingredientKeywords.some(keyword => 
      pantryItem.normalized.includes(keyword) || keyword.includes(pantryItem.normalized)
    );
  });
  
  if (hasKeywordMatch) {
    return true;
  }
  
  // 5. Also try matching against the original ingredient text
  if (originalText && originalText !== ingredientName) {
    const normalizedOriginal = normalizeIngredientName(originalText);
    const originalKeywords = extractKeyWords(originalText);
    
    if (normalizedPantryItems.some(item => 
      item.normalized.includes(normalizedOriginal) || 
      normalizedOriginal.includes(item.normalized) ||
      originalKeywords.some(keyword => 
        item.normalized.includes(keyword) || keyword.includes(item.normalized)
      )
    )) {
      return true;
    }
  }
  
  return false;
}

/**
 * Calculate ingredient availability for a recipe
 * IMPORTANT: This function handles duplicate IDs by counting each ingredient instance,
 * not unique IDs. Two ingredients with the same ID are counted as two separate ingredients.
 */
export function calculateIngredientAvailability(
  recipeIngredients: RecipeIngredient[],
  pantryItems: PantryItem[]
): IngredientMatchResult {
  const availableIngredients = new Set<number>();
  const missingIngredients = new Set<number>();
  
  let availableCount = 0;
  let missingCount = 0;
  
  // Count each ingredient individually, even if they have the same ID
  recipeIngredients.forEach(ingredient => {
    if (isIngredientAvailable(ingredient, pantryItems)) {
      availableIngredients.add(ingredient.id);
      availableCount++;
    } else {
      missingIngredients.add(ingredient.id);
      missingCount++;
    }
  });
  
  return {
    availableIngredients,
    missingIngredients,
    availableCount,
    missingCount,
    totalCount: recipeIngredients.length
  };
}

/**
 * Validate that ingredient counts add up correctly
 */
export function validateIngredientCounts(result: IngredientMatchResult): boolean {
  return result.availableCount + result.missingCount === result.totalCount;
}