#!/usr/bin/env python3
"""Check pantry_items table schema"""

from google.cloud import bigquery
import os

# Set up BigQuery client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/danielkim/_Capstone/PrepSense/config/adsp-34002-on02-prep-sense-ef1111b0833b.json'
client = bigquery.Client(project='adsp-34002-on02-prep-sense')

# Get table schema
table_ref = client.dataset('Inventory').table('pantry_items')
table = client.get_table(table_ref)

print("=== Pantry Items Table Schema ===\n")
for field in table.schema:
    print(f"{field.name}: {field.field_type} {field.mode}")
    if field.description:
        print(f"  Description: {field.description}")