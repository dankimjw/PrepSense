/**
 * Smart Food Animation Utility
 * Provides intelligent Lottie animation selection with category-based fallbacks
 */

export type AnimationContext = 
  | 'category-header'
  | 'empty-state' 
  | 'success-feedback'
  | 'loading-state'
  | 'list-item'
  | 'major-milestone';

interface AnimationConfig {
  source: any;
  size: number;
  loop?: boolean;
  speed?: number;
}

/**
 * Get specific fruit/food animation if available
 */
export const getSpecificFoodAnimation = (itemName: string): any | null => {
  const name = itemName.toLowerCase();
  
  // Specific fruits you have animations for
  if (name.includes('apple')) return require('../assets/lottie/apple.json');
  if (name.includes('banana')) return require('../assets/lottie/banana.json');
  if (name.includes('orange') || name.includes('citrus')) return require('../assets/lottie/orange.json');
  if (name.includes('strawberry') || name.includes('berry')) return require('../assets/lottie/strawberry.json');
  if (name.includes('cherry')) return require('../assets/lottie/cherry.json');
  if (name.includes('kiwi')) return require('../assets/lottie/kiwi.json');
  if (name.includes('mango')) return require('../assets/lottie/mango.json');
  if (name.includes('pear')) return require('../assets/lottie/pear.json');
  if (name.includes('pineapple')) return require('../assets/lottie/pineapple.json');
  if (name.includes('watermelon')) return require('../assets/lottie/watermelon.json');
  
  // Specific foods
  if (name.includes('sandwich')) return require('../assets/lottie/sandwich.json');
  if (name.includes('french fries') || name.includes('fries')) return require('../assets/lottie/french-fries.json');
  if (name.includes('falafel')) return require('../assets/lottie/falafal.json');
  if (name.includes('momo')) return require('../assets/lottie/momos.json');
  
  return null;
};

/**
 * Get category-based animation fallback
 */
export const getCategoryAnimation = (itemName: string): any => {
  const name = itemName.toLowerCase();
  
  // Broad category matching
  if (isFruit(name)) return require('../assets/lottie/fruits.json');
  if (isVegetable(name)) return require('../assets/lottie/vegetables-bag.json');
  if (isBreakfastFood(name)) return require('../assets/lottie/breakfast-items.json');
  if (isSnackFood(name)) return require('../assets/lottie/french-fries.json');
  if (isInternationalFood(name)) return require('../assets/lottie/momos.json');
  
  // Generic food fallback
  return require('../assets/lottie/delicious.json');
};

/**
 * Get universal animation for specific contexts
 */
export const getUniversalAnimation = (context: AnimationContext): any => {
  switch (context) {
    case 'loading-state':
      return require('../assets/lottie/loading-dots.json');
    case 'success-feedback':
      return require('../assets/lottie/success-check.json');
    case 'empty-state':
      return require('../assets/lottie/empty-box.json');
    case 'major-milestone':
      return require('../assets/lottie/delicious.json');
    default:
      return require('../assets/lottie/grocery-bucket.json');
  }
};

/**
 * Main function to get appropriate animation with smart fallbacks
 */
export const getFoodAnimation = (
  itemName: string, 
  context: AnimationContext = 'list-item',
  forceCategory: boolean = false
): AnimationConfig => {
  
  // For non-food contexts, use universal animations
  if (['loading-state', 'success-feedback', 'empty-state'].includes(context)) {
    return {
      source: getUniversalAnimation(context),
      size: getContextSize(context),
      loop: context === 'loading-state',
      speed: context === 'loading-state' ? 1.2 : 1.0
    };
  }
  
  // For food items, try specific first, then category
  let animation;
  
  if (!forceCategory) {
    animation = getSpecificFoodAnimation(itemName);
  }
  
  if (!animation) {
    animation = getCategoryAnimation(itemName);
  }
  
  return {
    source: animation,
    size: getContextSize(context),
    loop: shouldLoop(context),
    speed: getContextSpeed(context)
  };
};

/**
 * Get emoji fallback for foods without animations
 */
export const getFoodEmoji = (itemName: string): string => {
  const name = itemName.toLowerCase();
  
  // Don't show emoji if we have a specific animation
  if (getSpecificFoodAnimation(name)) return '';
  
  // Common food emojis
  if (name.includes('milk')) return '🥛';
  if (name.includes('bread')) return '🍞';
  if (name.includes('egg')) return '🥚';
  if (name.includes('cheese')) return '🧀';
  if (name.includes('meat') || name.includes('beef')) return '🥩';
  if (name.includes('chicken')) return '🍗';
  if (name.includes('fish')) return '🐟';
  if (name.includes('pasta')) return '🍝';
  if (name.includes('rice')) return '🍚';
  if (name.includes('potato')) return '🥔';
  if (name.includes('carrot')) return '🥕';
  if (name.includes('tomato')) return '🍅';
  if (name.includes('onion')) return '🧅';
  if (name.includes('pepper')) return '🌶️';
  if (name.includes('lettuce') || name.includes('salad')) return '🥬';
  if (name.includes('mushroom')) return '🍄';
  if (name.includes('corn')) return '🌽';
  if (name.includes('avocado')) return '🥑';
  
  return '🍽️'; // Generic food emoji
};

/**
 * Determine if animation should be used based on context
 */
export const shouldAnimate = (context: AnimationContext): boolean => {
  return [
    'category-header',
    'empty-state',
    'success-feedback',
    'loading-state',
    'major-milestone'
  ].includes(context);
};

// Helper functions for food categorization
const isFruit = (name: string): boolean => {
  const fruits = [
    'apple', 'banana', 'orange', 'grape', 'melon', 'peach', 'plum', 'berry',
    'cherry', 'kiwi', 'mango', 'pear', 'pineapple', 'watermelon', 'lemon',
    'lime', 'grapefruit', 'coconut', 'papaya', 'fig', 'date'
  ];
  return fruits.some(fruit => name.includes(fruit));
};

const isVegetable = (name: string): boolean => {
  const vegetables = [
    'carrot', 'broccoli', 'spinach', 'lettuce', 'tomato', 'onion', 'pepper',
    'potato', 'cucumber', 'celery', 'cabbage', 'corn', 'peas', 'beans',
    'mushroom', 'zucchini', 'eggplant', 'beet', 'radish', 'turnip'
  ];
  return vegetables.some(veg => name.includes(veg));
};

const isBreakfastFood = (name: string): boolean => {
  const breakfast = [
    'cereal', 'oats', 'granola', 'yogurt', 'pancake', 'waffle', 'toast',
    'bagel', 'muffin', 'croissant', 'jam', 'honey', 'syrup', 'bacon',
    'sausage', 'scrambled', 'fried', 'boiled', 'coffee', 'tea', 'juice'
  ];
  return breakfast.some(item => name.includes(item));
};

const isSnackFood = (name: string): boolean => {
  const snacks = [
    'chips', 'crackers', 'nuts', 'popcorn', 'pretzels', 'cookies', 'candy',
    'chocolate', 'ice cream', 'cake', 'pie', 'donut', 'fries', 'pizza'
  ];
  return snacks.some(snack => name.includes(snack));
};

const isInternationalFood = (name: string): boolean => {
  const international = [
    'sushi', 'ramen', 'curry', 'noodles', 'dumpling', 'taco', 'burrito',
    'pasta', 'pizza', 'sandwich', 'burger', 'hot dog', 'falafel', 'hummus',
    'pita', 'quinoa', 'couscous', 'momo', 'dim sum', 'pad thai'
  ];
  return international.some(food => name.includes(food));
};

// Context-based sizing and behavior
const getContextSize = (context: AnimationContext): number => {
  switch (context) {
    case 'loading-state': return 120;
    case 'success-feedback': return 100;
    case 'empty-state': return 160;
    case 'major-milestone': return 140;
    case 'category-header': return 32;
    case 'list-item': return 24;
    default: return 48;
  }
};

const shouldLoop = (context: AnimationContext): boolean => {
  return context === 'loading-state' || context === 'category-header';
};

const getContextSpeed = (context: AnimationContext): number => {
  switch (context) {
    case 'loading-state': return 1.2;
    case 'success-feedback': return 1.0;
    case 'category-header': return 0.8;
    default: return 1.0;
  }
};

export default {
  getFoodAnimation,
  getSpecificFoodAnimation,
  getCategoryAnimation,
  getUniversalAnimation,
  getFoodEmoji,
  shouldAnimate
};