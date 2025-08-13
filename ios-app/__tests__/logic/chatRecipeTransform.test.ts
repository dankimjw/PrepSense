import { describe, it, expect } from '@jest/globals';

// Use relative imports to avoid alias issues
import type { Recipe as UIRecipe } from '../../services/recipeService';
import type { Recipe as ChatApiRecipe } from '../../services/api';
import { transformChatRecipeToUI, transformChatRecipes } from '../../utils/chatRecipeTransform';

function isPositiveInt(n: unknown): n is number {
  return typeof n === 'number' && Number.isInteger(n) && n > 0;
}

describe('chatRecipeTransform', () => {
  it('transforms a simple chat recipe into a comprehensive UI recipe', () => {
    const input: Partial<ChatApiRecipe> = {
      name: 'Simple Pasta',
      ingredients: ['200 g pasta', '2 tbsp olive oil', '1 clove garlic'],
      instructions: ['Boil pasta', 'Saute garlic in oil', 'Combine and serve'],
      nutrition: { calories: 420, protein: 12 },
      time: 20,
      available_ingredients: ['pasta', 'olive oil'],
      missing_ingredients: ['garlic'],
      available_count: 2,
      missing_count: 1,
      match_score: 85,
    };

    const out = transformChatRecipeToUI(input as ChatApiRecipe);

    expect(out.title).toBe('Simple Pasta');
    expect(out.name).toBe('Simple Pasta');
    expect(isPositiveInt(out.id)).toBe(true);
    expect(out.readyInMinutes).toBe(20);
    expect(out.time).toBe(20);

    // Ingredients mapping
    expect(Array.isArray(out.ingredients)).toBe(true);
    expect(out.ingredients).toEqual(['200 g pasta', '2 tbsp olive oil', '1 clove garlic']);
    expect(out.extendedIngredients).toHaveLength(3);
    expect(out.extendedIngredients?.[0].original).toContain('pasta');

    // Instructions mapping
    expect(Array.isArray(out.analyzedInstructions)).toBe(true);
    expect(out.analyzedInstructions?.[0].steps).toHaveLength(3);
    expect(out.analyzedInstructions?.[0].steps[0].step).toContain('Boil pasta');

    // Nutrition convenience fields
    expect(out.nutrition?.calories).toBe(420);
    expect(out.nutrition?.protein).toBe(12);

    // Pantry matching pass-through
    expect(out.available_ingredients).toEqual(['pasta', 'olive oil']);
    expect(out.missing_ingredients).toEqual(['garlic']);
    expect(out.available_count).toBe(2);
    expect(out.missing_count).toBe(1);
    expect(out.match_score).toBe(85);
  });

  it('preserves comprehensive fields and derives convenience fields', () => {
    const input: any = {
      id: 12345,
      title: 'Comprehensive Salad',
      image: 'https://example.com/salad.jpg',
      readyInMinutes: 10,
      servings: 2,
      cuisines: ['mediterranean'],
      diets: ['vegan'],
      dishTypes: ['salad'],
      extendedIngredients: [
        { name: 'lettuce', original: '2 cups lettuce' },
        { name: 'olive oil', original: '1 tbsp olive oil' },
      ],
      analyzedInstructions: [
        { steps: [{ number: 1, step: 'Chop lettuce' }, { number: 2, step: 'Dress with oil' }] },
      ],
      nutrition: {
        nutrients: [
          { name: 'Calories', amount: 150, unit: 'kcal' },
          { name: 'Protein', amount: 5, unit: 'g' },
        ],
      },
      sourceUrl: 'https://example.com/recipe',
      available_ingredients: ['lettuce'],
      missing_ingredients: ['olive oil'],
    };

    const out = transformChatRecipeToUI(input);

    expect(out.id).toBe(12345);
    expect(out.title).toBe('Comprehensive Salad');
    expect(out.image).toBe('https://example.com/salad.jpg');
    expect(out.readyInMinutes).toBe(10);
    expect(out.time).toBe(10);
    expect(out.servings).toBe(2);
    expect(out.cuisines).toEqual(['mediterranean']);
    expect(out.diets).toEqual(['vegan']);
    expect(out.dishTypes).toEqual(['salad']);
    expect(out.extendedIngredients).toHaveLength(2);
    expect(out.analyzedInstructions?.[0].steps).toHaveLength(2);
    // convenience strings
    expect(out.ingredients).toEqual(['2 cups lettuce', '1 tbsp olive oil']);
    expect(Array.isArray(out.instructions)).toBe(true);
    expect((out.instructions as string[])[0]).toContain('Chop lettuce');
    // nutrition convenience
    expect(out.nutrition?.calories).toBe(150);
    expect(out.nutrition?.protein).toBe(5);
  });

  it('handles missing fields with sensible defaults and deterministic id', () => {
    const input: any = { title: 'No Frills' };
    const out1 = transformChatRecipeToUI(input);
    const out2 = transformChatRecipeToUI(input);

    expect(out1.title).toBe('No Frills');
    expect(out1.readyInMinutes).toBe(30);
    expect(out1.time).toBe(30);
    expect(out1.nutrition?.calories).toBe(0);
    expect(out1.nutrition?.protein).toBe(0);
    expect(isPositiveInt(out1.id)).toBe(true);
    expect(out1.id).toBe(out2.id); // deterministic
  });

  it('bulk transforms arrays safely', () => {
    const inputs: any[] = [
      { name: 'A', ingredients: ['x'], instructions: ['y'], nutrition: { calories: 1, protein: 1 }, time: 5 },
      { title: 'B' },
    ];
    const outs: UIRecipe[] = transformChatRecipes(inputs);
    expect(outs).toHaveLength(2);
    expect(outs[0].title).toBe('A');
    expect(outs[1].title).toBe('B');
  });
});
