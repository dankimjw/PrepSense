import { calculateIngredientAvailability, validateIngredientCounts } from "../ingredientMatcher";

// Mock pantry items – egg is available, milk is not
const pantryItems = [
  { product_name: "egg" }
];

describe("ingredientMatcher duplicate-ID handling", () => {
  it("counts duplicate IDs individually while preserving fast look-ups", () => {
    const recipeIngredients = [
      { id: 1, name: "egg", original: "1 large egg" },
      { id: 1, name: "egg", original: "1 large egg, divided" },
      { id: 2, name: "milk", original: "1 cup milk" }
    ];

    const result = calculateIngredientAvailability(recipeIngredients as any, pantryItems as any);

    // When logic is correct, totalCount should be 3
    expect(result.totalCount).toBe(3);
    // Two egg items should be marked available, milk missing
    expect(result.availableCount).toBe(2);
    expect(result.missingCount).toBe(1);
    // Validation helper should pass
    expect(validateIngredientCounts(result)).toBe(true);
  });
});
