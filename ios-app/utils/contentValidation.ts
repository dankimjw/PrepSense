export const INAPPROPRIATE_KEYWORDS = [
  'fevikol', 'glue', 'adhesive', 'poison', 'toxic', 'inedible',
  'cement', 'paint', 'chemical', 'bleach', 'detergent', 'soap',
  'shampoo', 'cleaning', 'disinfectant', 'pesticide', 'insecticide'
];

export const NONSENSE_PATTERNS = [
  /(.)\1{5,}/,  // Same character repeated 6+ times
  /[^\x00-\x7F]{10,}/,  // Long sequences of non-ASCII characters
  /\b(?:aaa|bbb|ccc|ddd|eee|fff|ggg|hhh|iii|jjj|kkk|lll|mmm|nnn|ooo|ppp|qqq|rrr|sss|ttt|uuu|vvv|www|xxx|yyy|zzz){3,}\b/i,  // Repeated letter patterns
];

export function isInappropriateContent(text: string): boolean {
  if (!text) return false;
  
  const lowerText = text.toLowerCase();
  
  // Check for inappropriate keywords
  for (const keyword of INAPPROPRIATE_KEYWORDS) {
    if (lowerText.includes(keyword)) {
      return true;
    }
  }
  
  // Check for nonsense patterns
  for (const pattern of NONSENSE_PATTERNS) {
    if (pattern.test(text)) {
      return true;
    }
  }
  
  // Check for non-English content
  // Count non-ASCII characters (excluding common punctuation)
  const nonAsciiChars = text.match(/[^\x00-\x7F]/g) || [];
  const asciiChars = text.match(/[a-zA-Z]/g) || [];
  
  // If more than 30% of alphabetic characters are non-ASCII, likely not English
  if (nonAsciiChars.length > 0 && asciiChars.length > 0) {
    const nonEnglishRatio = nonAsciiChars.length / (nonAsciiChars.length + asciiChars.length);
    if (nonEnglishRatio > 0.3) {
      return true;
    }
  }
  
  // Check for common non-English patterns (like transliterated text)
  const transliteratedPatterns = [
    /\b(?:kya|hai|ka|ke|ki|ko|se|me|ne|ye|wo|jo|to|ho|na|hi|bhi|aur|ya|par|mein|tha|thi|the)\b/i, // Hindi/Urdu
    /\b(?:da|de|di|do|la|le|li|lo|ma|mi|mo|na|ne|ni|no|pa|pe|pi|po)\b.*\b(?:da|de|di|do|la|le|li|lo|ma|mi|mo|na|ne|ni|no|pa|pe|pi|po)\b/i, // Romance languages pattern
    /[а-яА-Я]/,  // Cyrillic
    /[α-ωΑ-Ω]/,  // Greek
    /[\u4e00-\u9fff]/,  // Chinese
    /[\u3040-\u309f\u30a0-\u30ff]/,  // Japanese
    /[\uac00-\ud7af]/,  // Korean
    /[\u0600-\u06ff]/,  // Arabic
  ];
  
  for (const pattern of transliteratedPatterns) {
    if (pattern.test(text)) {
      return true;
    }
  }
  
  // Check for excessive non-alphabetic characters (excluding common punctuation and numbers)
  // For recipe instructions, we need to be more lenient with measurements, temperatures, etc.
  const nonAlphaCount = (text.match(/[^a-zA-Z0-9\s.,!?;:'"()°F°C/-]/g) || []).length;
  const totalLength = text.length;
  // Increased threshold from 0.5 to 0.7 to handle recipe instructions better
  if (totalLength > 20 && nonAlphaCount / totalLength > 0.7) {
    return true;
  }
  
  return false;
}

function preprocessInstruction(instruction: string): string {
  // Fix common formatting issues in instructions
  let processed = instruction.trim();
  
  // Add space after periods if missing
  processed = processed.replace(/\.([A-Z])/g, '. $1');
  
  // Add space after commas if missing
  processed = processed.replace(/,([A-Za-z])/g, ', $1');
  
  // Fix temperature formatting
  processed = processed.replace(/(\d+)degrees/g, '$1 degrees');
  
  return processed;
}

export function validateInstructions(instructions: string[] | undefined): string[] | null {
  if (!instructions || instructions.length === 0) {
    return null;
  }
  
  const validInstructions: string[] = [];
  
  for (const instruction of instructions) {
    if (typeof instruction !== 'string') continue;
    
    // Preprocess the instruction to fix formatting issues
    const preprocessed = preprocessInstruction(instruction);
    const trimmed = preprocessed.trim();
    if (!trimmed) continue;
    
    // Skip placeholder text from backend
    if (trimmed.toLowerCase() === 'no instructions available') {
      continue;
    }
    
    if (!isInappropriateContent(trimmed)) {
      validInstructions.push(trimmed);
    } else {
      // Debug: log what was filtered out
      console.log('Filtered inappropriate instruction:', trimmed);
    }
  }
  
  return validInstructions.length > 0 ? validInstructions : null;
}

export function hasValidInstructions(recipe: any): boolean {
  // Check if recipe has instructions field
  if (!recipe.instructions || !Array.isArray(recipe.instructions) || recipe.instructions.length === 0) {
    // Also check for Spoonacular's analyzedInstructions format
    if (recipe.analyzedInstructions && Array.isArray(recipe.analyzedInstructions) && recipe.analyzedInstructions.length > 0) {
      const steps = recipe.analyzedInstructions[0]?.steps || [];
      const instructions = steps.map((step: any) => step.step);
      if (instructions.length < 3) {
        return false; // Must have at least 3 steps
      }
      const validatedInstructions = validateInstructions(instructions);
      return validatedInstructions !== null && validatedInstructions.length >= 3;
    }
    return false;
  }
  
  // Validate the instructions
  const validatedInstructions = validateInstructions(recipe.instructions);
  
  // Recipe must have at least 3 valid instructions
  return validatedInstructions !== null && validatedInstructions.length >= 3;
}

// Simple validation cache to avoid re-validating the same recipes
const validationCache = new Map<number, boolean>();

export function isValidRecipe(recipe: any): boolean {
  // Check cache first
  if (recipe.id && validationCache.has(recipe.id)) {
    return validationCache.get(recipe.id)!;
  }
  
  // Quick checks first to fail fast
  
  // Check if recipe has a valid title
  if (!recipe.title || recipe.title.trim().length === 0) {
    if (recipe.id) validationCache.set(recipe.id, false);
    return false;
  }
  
  // Check Spoonacular score if available (must be above 20%)
  if (recipe.spoonacularScore !== undefined && recipe.spoonacularScore < 20) {
    if (recipe.id) validationCache.set(recipe.id, false);
    return false;
  }
  
  // Check if title contains inappropriate content (quick check)
  if (isInappropriateContent(recipe.title)) {
    if (recipe.id) validationCache.set(recipe.id, false);
    return false;
  }
  
  // Check if recipe has valid instructions (most expensive check last)
  if (!hasValidInstructions(recipe)) {
    if (recipe.id) validationCache.set(recipe.id, false);
    return false;
  }
  
  // Cache successful validation
  if (recipe.id) validationCache.set(recipe.id, true);
  return true;
}

// Clear cache when needed (e.g., on memory pressure)
export function clearValidationCache() {
  validationCache.clear();
}

export function getDefaultInstructions(recipeName: string): string[] {
  const lowerName = recipeName.toLowerCase();
  
  // Specific instructions for different recipe types
  if (lowerName.includes('omelette') || lowerName.includes('omelet')) {
    return [
      "Beat eggs in a bowl with salt and pepper",
      "Heat butter or oil in a non-stick pan over medium heat",
      "Pour in the beaten eggs and let them set for 30 seconds",
      "Gently stir the eggs, pulling edges toward center",
      "Add your fillings to one half of the omelette",
      "Fold the omelette in half and slide onto plate",
      "Serve immediately while hot"
    ];
  }
  
  if (lowerName.includes('smoothie')) {
    return [
      "Add all ingredients to a blender",
      "Blend on high speed for 60-90 seconds",
      "Check consistency and blend more if needed",
      "Pour into glasses and serve immediately",
      "Garnish with fresh fruit if desired"
    ];
  }
  
  if (lowerName.includes('soup')) {
    return [
      "Heat oil in a large pot over medium heat",
      "Add aromatics and cook until fragrant",
      "Add main ingredients and cook for 5 minutes",
      "Pour in liquid and bring to a boil",
      "Reduce heat and simmer for 20-25 minutes",
      "Season with salt and pepper to taste",
      "Serve hot with desired garnishes"
    ];
  }
  
  if (lowerName.includes('grilled') || lowerName.includes('chicken')) {
    return [
      "Preheat grill or grill pan to medium-high heat",
      "Season the protein with salt and pepper",
      "Oil the grill grates to prevent sticking",
      "Cook for 6-8 minutes on the first side",
      "Flip and cook for another 6-8 minutes",
      "Check internal temperature reaches safe levels",
      "Let rest for 5 minutes before serving"
    ];
  }
  
  if (lowerName.includes('stir-fry') || lowerName.includes('stir fry')) {
    return [
      "Heat oil in a large wok or skillet over high heat",
      "Add protein and cook until almost done",
      "Remove protein and set aside",
      "Add vegetables in order of cooking time needed",
      "Return protein to the pan",
      "Add sauce and toss everything together",
      "Serve immediately over rice or noodles"
    ];
  }
  
  if (lowerName.includes('custard') || lowerName.includes('pudding')) {
    return [
      "Preheat oven to 325°F (165°C)",
      "In a bowl, whisk together eggs, sugar, and vanilla until well combined",
      "Heat milk in a saucepan until just steaming (do not boil)",
      "Slowly pour hot milk into egg mixture, whisking constantly",
      "Strain mixture through a fine-mesh sieve to remove any lumps",
      "Pour into ramekins or a baking dish",
      "Place in a larger pan and add hot water halfway up the sides",
      "Bake for 40-50 minutes until center is just set but still jiggles slightly",
      "Remove from water bath and cool to room temperature",
      "Refrigerate for at least 2 hours before serving"
    ];
  }
  
  // Generic fallback instructions
  return [
    `Prepare all ingredients for ${recipeName}.`,
    'Follow standard cooking procedures for this type of dish.',
    'Cook until done according to your preference.',
    'Season to taste and serve hot.'
  ];
}