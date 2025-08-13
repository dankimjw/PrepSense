// utils/chatRecipeTransform.ts
// Pure utility to transform chat API recipe objects into comprehensive UI Recipe format

import type { Recipe as UIRecipe, ExtendedIngredient, AnalyzedInstruction } from '../services/recipeService';
import type { Recipe as ChatApiRecipe } from '../services/api';

function toPositiveInt(value: unknown): number | null {
  if (typeof value === 'number' && Number.isInteger(value) && value > 0) return value;
  if (typeof value === 'string') {
    const n = parseInt(value, 10);
    if (!isNaN(n) && n > 0) return n;
  }
  return null;
}

function hashFromTitle(title: string): number {
  let hash = 0;
  for (let i = 0; i < title.length; i++) {
    const char = title.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // 32-bit
  }
  const positive = Math.abs(hash) || 1;
  return positive;
}

function extractId(input: any): number {
  const idFields = ['id', 'recipe_id', 'spoonacularId', 'external_id', 'recipeId'];
  for (const key of idFields) {
    if (key in input) {
      const val = (input as any)[key];
      const n = toPositiveInt(val);
      if (n) return n;
    }
  }
  const title = input?.title || input?.name || 'Untitled Recipe';
  return hashFromTitle(title);
}

function mapIngredients(input: any): { ingredients?: UIRecipe['ingredients']; extendedIngredients?: ExtendedIngredient[] } {
  // Prefer extendedIngredients if present
  if (Array.isArray(input?.extendedIngredients) && input.extendedIngredients.length > 0) {
    const ext: ExtendedIngredient[] = input.extendedIngredients.map((ing: any) => ({
      id: toPositiveInt(ing?.id) || undefined,
      aisle: ing?.aisle,
      image: ing?.image,
      consistency: ing?.consistency,
      name: ing?.name || ing?.ingredient_name || ing?.original || 'ingredient',
      nameClean: ing?.nameClean,
      original: ing?.original || ing?.originalString || ing?.name || '',
      originalString: ing?.originalString,
      originalName: ing?.originalName,
      amount: typeof ing?.amount === 'number' ? ing.amount : (typeof ing?.quantity === 'number' ? ing.quantity : undefined),
      unit: ing?.unit,
      meta: ing?.meta,
      metaInformation: ing?.metaInformation,
      measures: ing?.measures,
    }));
    const ingredientStrings = ext.map(i => i.original || i.name).filter(Boolean) as string[];
    return { ingredients: ingredientStrings, extendedIngredients: ext };
  }

  // Fallback: build extendedIngredients from simple strings
  if (Array.isArray(input?.ingredients)) {
    const strings: string[] = input.ingredients.filter((s: any) => typeof s === 'string');
    const ext: ExtendedIngredient[] = strings.map((s, idx) => ({
      id: undefined,
      name: s, // keep simple; parsing quantities not required for UI
      original: s,
      amount: undefined,
      unit: undefined,
    }));
    return { ingredients: strings, extendedIngredients: ext };
  }

  return {};
}

function mapInstructions(input: any): { instructions?: UIRecipe['instructions']; analyzedInstructions?: AnalyzedInstruction[] } {
  if (Array.isArray(input?.analyzedInstructions) && input.analyzedInstructions.length > 0) {
    const analyzed: AnalyzedInstruction[] = input.analyzedInstructions.map((ai: any) => ({
      name: ai?.name,
      steps: Array.isArray(ai?.steps) ? ai.steps.map((st: any, idx: number) => ({
        number: toPositiveInt(st?.number) || (idx + 1),
        step: st?.step || '',
        ingredients: st?.ingredients,
        equipment: st?.equipment,
        length: st?.length,
      })) : [],
    }));
    const strings = analyzed.flatMap(ai => ai.steps.map(s => s.step)).filter(Boolean);
    return { instructions: strings, analyzedInstructions: analyzed };
  }

  if (Array.isArray(input?.instructions)) {
    const strings: string[] = input.instructions.filter((s: any) => typeof s === 'string');
    const analyzed: AnalyzedInstruction[] = [{
      name: undefined,
      steps: strings.map((s, idx) => ({ number: idx + 1, step: s })),
    }];
    return { instructions: strings, analyzedInstructions: analyzed };
  }

  return {};
}

function mapNutrition(input: any): UIRecipe['nutrition'] {
  const nutrition = input?.nutrition || {};
  const nutrients = Array.isArray(nutrition?.nutrients) ? nutrition.nutrients : undefined;

  const getNutrient = (name: string): number | undefined => {
    const found = nutrients?.find((n: any) => typeof n?.name === 'string' && n.name.toLowerCase() === name.toLowerCase());
    return typeof found?.amount === 'number' ? found.amount : undefined;
  };

  const calories = typeof nutrition?.calories === 'number' ? nutrition.calories : (getNutrient('Calories') ?? 0);
  const protein = typeof nutrition?.protein === 'number' ? nutrition.protein : (getNutrient('Protein') ?? 0);

  return {
    ...nutrition,
    nutrients,
    calories,
    protein,
  };
}

export function transformChatRecipeToUI(input: ChatApiRecipe | any): UIRecipe {
  const title = input?.title || input?.name || 'Untitled Recipe';
  const name = input?.name || input?.title || title;
  const id = extractId(input);
  const readyInMinutes = typeof input?.readyInMinutes === 'number' ? input.readyInMinutes : (typeof input?.time === 'number' ? input.time : 30);
  const time = readyInMinutes;

  const { ingredients, extendedIngredients } = mapIngredients(input);
  const { instructions, analyzedInstructions } = mapInstructions(input);
  const nutrition = mapNutrition(input);

  const out: UIRecipe = {
    id,
    title,
    name,
    image: typeof input?.image === 'string' ? input.image : undefined,
    readyInMinutes,
    time,
    servings: input?.servings,
    sourceUrl: input?.sourceUrl || input?.spoonacularSourceUrl,
    cuisines: input?.cuisines,
    diets: input?.diets || input?.dietary_tags,
    dishTypes: input?.dishTypes,
    ingredients,
    extendedIngredients,
    instructions,
    analyzedInstructions,
    nutrition,
    available_ingredients: input?.available_ingredients || [],
    missing_ingredients: input?.missing_ingredients || [],
    available_count: input?.available_count || input?.usedIngredientCount || 0,
    missing_count: input?.missing_count || input?.missedIngredientCount || 0,
    match_score: input?.match_score || 0,
  };

  return out;
}

export function transformChatRecipes(inputs: any[]): UIRecipe[] {
  if (!Array.isArray(inputs)) return [];
  return inputs.map(r => transformChatRecipeToUI(r));
}
