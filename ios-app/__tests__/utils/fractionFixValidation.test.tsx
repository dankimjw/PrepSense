import { parseIngredient, parseIngredientsList } from '@/utils/ingredientParser';
import { formatAsFraction } from '@/utils/numberFormatting';

/**
 * Validation test to verify the fraction display bug is completely fixed
 * 🟢 WORKING - Validated with tests
 */
describe('Fraction Display Fix Validation', () => {
  describe('Core Bug Fix - Simple Fractions', () => {
    it('should correctly parse and display common fractions', () => {
      const testCases = [
        { input: '1/2 cup parmesan cheese', expectedDisplay: 'Needs: ½ cup' },
        { input: '3/4 tsp salt', expectedDisplay: 'Needs: ¾ tsp' },
        { input: '1/4 cup butter', expectedDisplay: 'Needs: ¼ cup' },
        { input: '2/3 cup flour', expectedDisplay: 'Needs: ⅔ cup' },
        { input: '1/3 cup sugar', expectedDisplay: 'Needs: ⅓ cup' },
        { input: '3/8 cup milk', expectedDisplay: 'Needs: ⅜ cup' },
        { input: '5/8 cup water', expectedDisplay: 'Needs: ⅝ cup' },
        { input: '7/8 cup cream', expectedDisplay: 'Needs: ⅞ cup' }
      ];

      testCases.forEach(({ input, expectedDisplay }) => {
        const parsed = parseIngredient(input);
        const displayText = `Needs: ${formatAsFraction(parsed.quantity)} ${parsed.unit}`;
        
        console.log(`✅ "${input}" → Display: "${displayText}"`);
        
        expect(parsed.quantity).toBeDefined();
        expect(parsed.unit).toBeDefined();
        expect(parsed.name).toBeDefined();
        expect(displayText).toBe(expectedDisplay);
      });
    });

    it('should not show missing numerators (regression test)', () => {
      const problematicInputs = [
        '1/2 cup parmesan cheese',
        '3/4 teaspoon vanilla',
        '1/4 pound ground beef',
        '2/3 cup breadcrumbs'
      ];

      problematicInputs.forEach(input => {
        const parsed = parseIngredient(input);
        
        // Ensure no missing numerators in name
        expect(parsed.name).not.toMatch(/^\/\d+/); // Should not start with "/2", "/4", etc.
        expect(parsed.name).not.toContain('/'); // Name should not contain fractions
        
        // Ensure valid quantity
        expect(parsed.quantity).toBeGreaterThan(0);
        expect(parsed.quantity).toBeLessThan(1); // These are all fractions less than 1
        
        console.log(`✅ No regression for "${input}": name="${parsed.name}", quantity=${parsed.quantity}`);
      });
    });
  });

  describe('Enhanced Display Experience', () => {
    it('should display fractions with Unicode symbols instead of decimals', () => {
      const testCases = [
        { quantity: 0.5, expected: '½' },
        { quantity: 0.25, expected: '¼' },
        { quantity: 0.75, expected: '¾' },
        { quantity: 0.333, expected: '⅓' },
        { quantity: 0.667, expected: '⅔' },
        { quantity: 1.5, expected: '1½' },
        { quantity: 2.25, expected: '2¼' }
      ];

      testCases.forEach(({ quantity, expected }) => {
        const result = formatAsFraction(quantity);
        expect(result).toBe(expected);
        console.log(`✅ ${quantity} → "${result}"`);
      });
    });

    it('should handle edge cases gracefully', () => {
      const edgeCases = [
        { input: null, expected: '0' },
        { input: undefined, expected: '0' },
        { input: 0, expected: '0' },
        { input: 1, expected: '1' },
        { input: 2, expected: '2' },
        { input: 0.1, expected: '0.1' }, // No common fraction equivalent
        { input: 0.9, expected: '0.9' }   // No common fraction equivalent
      ];

      edgeCases.forEach(({ input, expected }) => {
        const result = formatAsFraction(input);
        expect(result).toBe(expected);
        console.log(`✅ Edge case ${input} → "${result}"`);
      });
    });
  });

  describe('Integration with Existing Features', () => {
    it('should work with parseIngredientsList for recipe completion', () => {
      const recipeIngredients = [
        '1/2 cup parmesan cheese',
        '2 cups flour',
        '3/4 tsp salt',
        '0.5 cup milk',
        '1 egg'
      ];

      const parsed = parseIngredientsList(recipeIngredients);
      
      expect(parsed).toHaveLength(5);
      
      // Verify each ingredient
      expect(parsed[0]).toEqual({
        name: 'parmesan cheese',
        quantity: 0.5,
        unit: 'cup',
        originalString: '1/2 cup parmesan cheese'
      });

      expect(parsed[1]).toEqual({
        name: 'flour',
        quantity: 2,
        unit: 'cup',
        originalString: '2 cups flour'
      });

      expect(parsed[2]).toEqual({
        name: 'salt',
        quantity: 0.75,
        unit: 'tsp',
        originalString: '3/4 tsp salt'
      });

      console.log('✅ parseIngredientsList works correctly with fractions');
    });

    it('should preserve non-fraction quantities', () => {
      const mixedIngredients = [
        '2 cups flour',        // whole number
        '1.5 cups milk',       // decimal
        '1/2 cup butter',      // fraction
        '3 eggs',              // whole number, no unit
        'salt to taste'        // no quantity
      ];

      const parsed = parseIngredientsList(mixedIngredients);
      
      expect(parsed[0].quantity).toBe(2);
      expect(parsed[1].quantity).toBe(1.5);
      expect(parsed[2].quantity).toBe(0.5);
      expect(parsed[3].quantity).toBe(3);
      expect(parsed[4].quantity).toBeUndefined();

      console.log('✅ Mixed ingredient types handled correctly');
    });
  });

  describe('Performance and Reliability', () => {
    it('should handle malformed input gracefully', () => {
      const malformedInputs = [
        '',
        '/',
        '/2',
        '1/',
        'cup',
        'random text',
        '1/0 cup sugar', // Division by zero
        '1/2/',          // Extra slash
        '1/2/3 cup'      // Multiple slashes
      ];

      malformedInputs.forEach(input => {
        expect(() => {
          const parsed = parseIngredient(input);
          console.log(`✅ Handled malformed input "${input}": ${JSON.stringify(parsed)}`);
        }).not.toThrow();
      });
    });

    it('should be fast enough for real-time parsing', () => {
      const startTime = Date.now();
      
      for (let i = 0; i < 1000; i++) {
        parseIngredient('1/2 cup parmesan cheese');
        formatAsFraction(0.5);
      }
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      expect(duration).toBeLessThan(100); // Should complete in under 100ms
      console.log(`✅ Performance test: 2000 operations in ${duration}ms`);
    });
  });
});