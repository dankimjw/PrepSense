-- Create a history table to track all pantry changes for rollback capability
CREATE TABLE IF NOT EXISTS `adsp-34002-on02-prep-sense.Inventory.pantry_history` (
  history_id STRING DEFAULT GENERATE_UUID(),
  pantry_item_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  change_type STRING NOT NULL, -- 'ADD', 'UPDATE', 'DELETE', 'RECIPE_SUBTRACT'
  change_source STRING, -- 'manual', 'vision_detected', 'recipe_completion', 'recipe_quick_complete'
  recipe_name STRING, -- Name of recipe if change was from recipe
  recipe_id STRING, -- ID of recipe if applicable
  
  -- Before values
  quantity_before FLOAT,
  used_quantity_before FLOAT,
  
  -- After values
  quantity_after FLOAT,
  used_quantity_after FLOAT,
  
  -- Change amounts
  quantity_changed FLOAT, -- Positive for additions, negative for subtractions
  
  -- Metadata
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  changed_by_user_id INTEGER, -- User who made the change
  
  -- For grouping related changes (e.g., all changes from one recipe completion)
  transaction_id STRING,
  
  -- Additional context
  notes STRING,
  
  PRIMARY KEY (history_id) NOT ENFORCED
);

-- Add index for efficient queries
CREATE INDEX IF NOT EXISTS idx_pantry_history_user_time 
ON `adsp-34002-on02-prep-sense.Inventory.pantry_history` (user_id, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_pantry_history_transaction 
ON `adsp-34002-on02-prep-sense.Inventory.pantry_history` (transaction_id);

-- Add updated_at column to pantry_items if it doesn't exist
ALTER TABLE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP();