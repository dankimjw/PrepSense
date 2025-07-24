export const mockPantryItems = [
  {
    id: '1',
    pantry_item_id: 1,
    product_name: 'All-Purpose Flour',
    item_name: 'All-Purpose Flour',
    quantity: 3,
    quantity_amount: 3,
    unit: 'cups',
    quantity_unit: 'cups',
    unit_of_measurement: 'cups',
    expiration_date: '2025-01-28',
    added_date: '2025-01-15',
    category: 'Baking'
  },
  {
    id: '2',
    pantry_item_id: 2,
    product_name: 'Whole Wheat Flour',
    item_name: 'Whole Wheat Flour',
    quantity: 1,
    quantity_amount: 1,
    unit: 'cups',
    quantity_unit: 'cups',
    unit_of_measurement: 'cups',
    expiration_date: '2025-02-15',
    added_date: '2025-01-10',
    category: 'Baking'
  },
  {
    id: '3',
    pantry_item_id: 3,
    product_name: 'Granulated Sugar',
    item_name: 'Granulated Sugar',
    quantity: 2,
    quantity_amount: 2,
    unit: 'cups',
    quantity_unit: 'cups',
    unit_of_measurement: 'cups',
    expiration_date: '2025-12-31',
    added_date: '2024-12-01',
    category: 'Baking'
  },
  {
    id: '4',
    pantry_item_id: 4,
    product_name: 'Butter',
    item_name: 'Butter',
    quantity: 0.5,
    quantity_amount: 0.5,
    unit: 'cups',
    quantity_unit: 'cups',
    unit_of_measurement: 'cups',
    expiration_date: '2025-01-25',
    added_date: '2025-01-20',
    category: 'Dairy'
  }
];

export const mockRecipe = {
  id: 1,
  name: 'Chocolate Chip Cookies',
  description: 'Classic homemade chocolate chip cookies',
  prepTime: 15,
  cookTime: 12,
  servings: 24,
  ingredients: [
    '2 cups all-purpose flour',
    '1 cup granulated sugar',
    '1/2 cup butter',
    '1 tsp vanilla extract',
    '2 eggs',
    '1 cup chocolate chips'
  ],
  instructions: [
    'Preheat oven to 375°F',
    'Mix dry ingredients',
    'Cream butter and sugar',
    'Add eggs and vanilla',
    'Combine wet and dry ingredients',
    'Fold in chocolate chips',
    'Drop onto baking sheet',
    'Bake for 10-12 minutes'
  ],
  nutritionInfo: {
    calories: 150,
    protein: 2,
    carbs: 20,
    fat: 8
  }
};