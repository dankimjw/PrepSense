#!/usr/bin/env python3
"""Add updated_at column to pantry_items table"""

from google.cloud import bigquery
import os

# Set up BigQuery client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/danielkim/_Capstone/PrepSense/config/adsp-34002-on02-prep-sense-ef1111b0833b.json'
client = bigquery.Client(project='adsp-34002-on02-prep-sense')

# Step 1: Add the column without default
query1 = """
ALTER TABLE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
ADD COLUMN IF NOT EXISTS updated_at DATETIME
"""

# Step 2: Set default value
query2 = """
ALTER TABLE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
ALTER COLUMN updated_at SET DEFAULT CURRENT_DATETIME()
"""

# Step 3: Update existing rows
query3 = """
UPDATE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
SET updated_at = COALESCE(updated_at, created_at, CURRENT_DATETIME())
WHERE TRUE
"""

print("Adding updated_at column to pantry_items table...")
try:
    # Step 1
    print("1. Adding column...")
    query_job = client.query(query1)
    query_job.result()
    print("✓ Column added")
    
    # Step 2
    print("2. Setting default value...")
    query_job = client.query(query2)
    query_job.result()
    print("✓ Default value set")
    
    # Step 3
    print("3. Updating existing rows...")
    query_job = client.query(query3)
    result = query_job.result()
    print(f"✓ Updated {query_job.num_dml_affected_rows} rows")
    
    print("\n✓ Successfully added updated_at column to pantry_items table")
except Exception as e:
    print(f"✗ Error: {e}")