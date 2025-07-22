import { BatchPicker, Batch, IngredientNeed, BatchSelection } from '../../src/domain/BatchPicker';

describe('BatchPicker FEFO Auto-Selection', () => {
  let batchPicker: BatchPicker;

  beforeEach(() => {
    batchPicker = new BatchPicker();
  });

  describe('selectBatchesForIngredient', () => {
    it('should select earliest-expiring batches first (FEFO) and calculate correct quantities', () => {
      // Arrange: Create test batches with different expiration dates
      const availableBatches: Batch[] = [
        {
          batch_id: 'B001',
          product_name: 'flour',
          quantity: 500,
          unit: 'g',
          expiration_date: new Date('2024-02-15'), // Expires second
          status: 'available'
        },
        {
          batch_id: 'B002',
          product_name: 'flour',
          quantity: 300,
          unit: 'g',
          expiration_date: new Date('2024-02-10'), // Expires first (earliest)
          status: 'available'
        },
        {
          batch_id: 'B003',
          product_name: 'flour',
          quantity: 200,
          unit: 'g',
          expiration_date: new Date('2024-02-20'), // Expires last
          status: 'available'
        }
      ];

      const ingredientNeed: IngredientNeed = {
        ingredient_name: 'flour',
        required_quantity: 600,
        unit: 'g'
      };

      // Act: Perform FEFO selection
      const result: BatchSelection = batchPicker.selectBatchesForIngredient(
        availableBatches,
        ingredientNeed
      );

      // Assert: Verify FEFO order and quantities
      expect(result.selections).toHaveLength(2);
      
      // First batch should be B002 (earliest expiration)
      expect(result.selections[0]).toEqual({
        batch_id: 'B002',
        use_quantity: 300,
        unit: 'g'
      });
      
      // Second batch should be B001 (next earliest expiration)
      expect(result.selections[1]).toEqual({
        batch_id: 'B001',
        use_quantity: 300, // Only 300g needed from 500g available
        unit: 'g'
      });

      // Verify total fulfilled quantity
      expect(result.total_fulfilled).toBe(600);
      expect(result.shortfall).toBe(0);
      expect(result.is_fulfilled).toBe(true);
    });

    it('should handle shortfall when pantry has insufficient quantity', () => {
      // Arrange: Limited pantry stock
      const availableBatches: Batch[] = [
        {
          batch_id: 'B001',
          product_name: 'sugar',
          quantity: 150,
          unit: 'g',
          expiration_date: new Date('2024-02-12'),
          status: 'available'
        },
        {
          batch_id: 'B002',
          product_name: 'sugar',
          quantity: 100,
          unit: 'g',
          expiration_date: new Date('2024-02-08'), // Expires first
          status: 'available'
        }
      ];

      const ingredientNeed: IngredientNeed = {
        ingredient_name: 'sugar',
        required_quantity: 400,
        unit: 'g'
      };

      // Act
      const result = batchPicker.selectBatchesForIngredient(
        availableBatches,
        ingredientNeed
      );

      // Assert: Verify FEFO order is maintained even with shortfall
      expect(result.selections).toHaveLength(2);
      expect(result.selections[0].batch_id).toBe('B002'); // Earlier expiration
      expect(result.selections[0].use_quantity).toBe(100);
      expect(result.selections[1].batch_id).toBe('B001');
      expect(result.selections[1].use_quantity).toBe(150);
      
      expect(result.total_fulfilled).toBe(250);
      expect(result.shortfall).toBe(150);
      expect(result.is_fulfilled).toBe(false);
    });

    it('should handle exact match from single batch', () => {
      // Arrange
      const availableBatches: Batch[] = [
        {
          batch_id: 'B001',
          product_name: 'milk',
          quantity: 1000,
          unit: 'mL',
          expiration_date: new Date('2024-02-05'),
          status: 'available'
        }
      ];

      const ingredientNeed: IngredientNeed = {
        ingredient_name: 'milk',
        required_quantity: 250,
        unit: 'mL'
      };

      // Act
      const result = batchPicker.selectBatchesForIngredient(
        availableBatches,
        ingredientNeed
      );

      // Assert
      expect(result.selections).toHaveLength(1);
      expect(result.selections[0]).toEqual({
        batch_id: 'B001',
        use_quantity: 250,
        unit: 'mL'
      });
      expect(result.total_fulfilled).toBe(250);
      expect(result.shortfall).toBe(0);
      expect(result.is_fulfilled).toBe(true);
    });

    it('should return empty selection for unavailable ingredient', () => {
      // Arrange
      const availableBatches: Batch[] = [];
      const ingredientNeed: IngredientNeed = {
        ingredient_name: 'eggs',
        required_quantity: 3,
        unit: 'pcs'
      };

      // Act
      const result = batchPicker.selectBatchesForIngredient(
        availableBatches,
        ingredientNeed
      );

      // Assert
      expect(result.selections).toHaveLength(0);
      expect(result.total_fulfilled).toBe(0);
      expect(result.shortfall).toBe(3);
      expect(result.is_fulfilled).toBe(false);
    });

    it('should skip expired batches', () => {
      // Arrange: Mix of expired and valid batches
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const availableBatches: Batch[] = [
        {
          batch_id: 'B001',
          product_name: 'butter',
          quantity: 100,
          unit: 'g',
          expiration_date: yesterday, // Already expired
          status: 'available'
        },
        {
          batch_id: 'B002',
          product_name: 'butter',
          quantity: 200,
          unit: 'g',
          expiration_date: tomorrow, // Still valid
          status: 'available'
        }
      ];

      const ingredientNeed: IngredientNeed = {
        ingredient_name: 'butter',
        required_quantity: 150,
        unit: 'g'
      };

      // Act
      const result = batchPicker.selectBatchesForIngredient(
        availableBatches,
        ingredientNeed,
        { skipExpired: true }
      );

      // Assert: Should only use the non-expired batch
      expect(result.selections).toHaveLength(1);
      expect(result.selections[0].batch_id).toBe('B002');
      expect(result.selections[0].use_quantity).toBe(150);
      expect(result.total_fulfilled).toBe(150);
      expect(result.shortfall).toBe(0);
    });
  });
});