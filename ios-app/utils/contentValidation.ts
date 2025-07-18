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
  const nonAlphaCount = (text.match(/[^a-zA-Z0-9\s.,!?;:'"()-]/g) || []).length;
  const totalLength = text.length;
  if (totalLength > 20 && nonAlphaCount / totalLength > 0.5) {
    return true;
  }
  
  return false;
}

export function validateInstructions(instructions: string[] | undefined): string[] | null {
  if (!instructions || instructions.length === 0) {
    return null;
  }
  
  const validInstructions: string[] = [];
  
  for (const instruction of instructions) {
    if (typeof instruction !== 'string') continue;
    
    const trimmed = instruction.trim();
    if (!trimmed) continue;
    
    if (!isInappropriateContent(trimmed)) {
      validInstructions.push(trimmed);
    }
  }
  
  return validInstructions.length > 0 ? validInstructions : null;
}

export function getDefaultInstructions(recipeName: string): string[] {
  return [
    `Prepare all ingredients for ${recipeName}.`,
    'Follow standard cooking procedures for this type of dish.',
    'Cook until done according to your preference.',
    'Season to taste and serve hot.'
  ];
}