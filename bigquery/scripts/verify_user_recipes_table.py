#!/usr/bin/env python3
"""
Simple script to verify the user_recipes table was created in BigQuery.
"""

import os
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up credentials
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not credentials_path:
    credentials_path = str(Path(__file__).parent.parent.parent / "config" / "adsp-34002-on02-prep-sense-ef1111b0833b.json")

# Initialize BigQuery client
credentials = service_account.Credentials.from_service_account_file(
    credentials_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
client = bigquery.Client(credentials=credentials, project='adsp-34002-on02-prep-sense')

# List all tables in the Inventory dataset
dataset_ref = client.dataset('Inventory')
tables = list(client.list_tables(dataset_ref))

print("\n=== Tables in Inventory dataset ===")
for table in tables:
    print(f"- {table.table_id}")

# Check if user_recipes exists
table_exists = any(table.table_id == 'user_recipes' for table in tables)

if table_exists:
    print("\n✓ SUCCESS: user_recipes table exists!")
    
    # Get table schema
    table_ref = dataset_ref.table('user_recipes')
    table = client.get_table(table_ref)
    
    print(f"\nTable details:")
    print(f"- Total rows: {table.num_rows}")
    print(f"- Created: {table.created}")
    print(f"- Modified: {table.modified}")
    print(f"\nSchema ({len(table.schema)} fields):")
    
    for field in table.schema[:10]:  # Show first 10 fields
        print(f"  - {field.name} ({field.field_type})")
    
    if len(table.schema) > 10:
        print(f"  ... and {len(table.schema) - 10} more fields")
        
    # Also check for views
    print("\n=== Views in Inventory dataset ===")
    query = """
    SELECT table_name, table_type
    FROM `adsp-34002-on02-prep-sense.Inventory.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'VIEW'
    """
    
    results = client.query(query).result()
    for row in results:
        print(f"- {row.table_name}")
    
else:
    print("\n✗ ERROR: user_recipes table not found!")