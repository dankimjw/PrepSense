export interface Batch {
  batch_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  expiration_date: Date;
  status: string;
}

export interface IngredientNeed {
  ingredient_name: string;
  required_quantity: number;
  unit: string;
}

export interface BatchPickResult {
  batch_id: string;
  use_quantity: number;
  unit: string;
}

export interface BatchSelection {
  selections: BatchPickResult[];
  total_fulfilled: number;
  shortfall: number;
  is_fulfilled: boolean;
}

export interface BatchPickerOptions {
  skipExpired?: boolean;
}

export class BatchPicker {
  selectBatchesForIngredient(
    availableBatches: Batch[],
    ingredientNeed: IngredientNeed,
    options: BatchPickerOptions = {}
  ): BatchSelection {
    const { skipExpired = false } = options;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Filter available batches by product name and optionally skip expired
    let eligibleBatches = availableBatches.filter(
      batch => batch.product_name === ingredientNeed.ingredient_name
    );

    if (skipExpired) {
      eligibleBatches = eligibleBatches.filter(
        batch => batch.expiration_date >= today
      );
    }

    // Sort by expiration date (FEFO - First Expired, First Out)
    eligibleBatches.sort((a, b) => 
      a.expiration_date.getTime() - b.expiration_date.getTime()
    );

    const selections: BatchPickResult[] = [];
    let remainingNeed = ingredientNeed.required_quantity;
    let totalFulfilled = 0;

    // Select batches using FEFO strategy
    for (const batch of eligibleBatches) {
      if (remainingNeed <= 0) break;

      const useQuantity = Math.min(batch.quantity, remainingNeed);
      
      selections.push({
        batch_id: batch.batch_id,
        use_quantity: useQuantity,
        unit: batch.unit
      });

      totalFulfilled += useQuantity;
      remainingNeed -= useQuantity;
    }

    const shortfall = Math.max(0, remainingNeed);
    const isFulfilled = shortfall === 0;

    return {
      selections,
      total_fulfilled: totalFulfilled,
      shortfall,
      is_fulfilled: isFulfilled
    };
  }
}