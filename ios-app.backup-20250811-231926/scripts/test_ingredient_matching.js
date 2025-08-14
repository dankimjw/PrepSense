// Test script to verify ingredient matching logic
const { calculateIngredientAvailability } = require('../utils/ingredientMatcher');

// Mock pantry items from user 111
const pantryItems = [
  { product_name: "Strawberries" },
  { product_name: "Madagascar 70% Cacao Chocolate" },
  { product_name: "Bell Peppers" },
  { product_name: "Paneer" },
  { product_name: "turkey sausage" },
  { product_name: "avocado" },
  { product_name: "ground turkey" }
];

// Mock recipe ingredients from the turkey wraps recipe
const recipeIngredients = [
  {
    id: 1,
    name: "ground turkey",
    original: "300g ground turkey"
  },
  {
    id: 2,
    name: "avocado",
    original: "1 large avocado, sliced"
  },
  {
    id: 3,
    name: "lettuce",
    original: "lettuce leaves"
  },
  {
    id: 4,
    name: "cilantro",
    original: "fresh cilantro"
  }
];

console.log('Testing ingredient matching...');
console.log('Pantry items:', pantryItems.map(item => item.product_name));
console.log('Recipe ingredients:', recipeIngredients.map(ing => ing.name));

try {
  const result = calculateIngredientAvailability(recipeIngredients, pantryItems);
  
  console.log('\nResults:');
  console.log('Available ingredients:', result.availableCount);
  console.log('Missing ingredients:', result.missingCount);
  console.log('Total ingredients:', result.totalCount);
  
  console.log('\nAvailable ingredient IDs:', Array.from(result.availableIngredients));
  console.log('Missing ingredient IDs:', Array.from(result.missingIngredients));
  
  // Show which ingredients are available
  const availableIngredients = recipeIngredients.filter(ing => 
    result.availableIngredients.has(ing.id)
  );
  const missingIngredients = recipeIngredients.filter(ing => 
    result.missingIngredients.has(ing.id)
  );
  
  console.log('\nAvailable ingredients:', availableIngredients.map(ing => ing.name));
  console.log('Missing ingredients:', missingIngredients.map(ing => ing.name));
  
} catch (error) {
  console.error('Error in ingredient matching:', error);
}

