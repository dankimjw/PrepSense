#!/usr/bin/env python3
"""View full pantry for testing subtraction"""

from google.cloud import bigquery
import os

# Set up BigQuery client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/danielkim/_Capstone/PrepSense/config/adsp-34002-on02-prep-sense-ef1111b0833b.json'
client = bigquery.Client(project='adsp-34002-on02-prep-sense')

query = """
SELECT 
    pantry_item_id,
    product_name,
    quantity,
    unit_of_measurement,
    used_quantity,
    expiration_date
FROM `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
WHERE user_id = 111
ORDER BY product_name
"""

print("=== Full Pantry for User 111 ===\n")

results = client.query(query).result()

# Group by product name
products = {}
for row in results:
    name = row['product_name']
    if name not in products:
        products[name] = []
    products[name].append({
        'id': row['pantry_item_id'],
        'quantity': row['quantity'],
        'unit': row['unit_of_measurement'],
        'used': row['used_quantity'] or 0,
        'expires': row['expiration_date']
    })

# Display grouped items
for product_name, items in sorted(products.items()):
    print(f"\n{product_name}:")
    total_quantity = sum(item['quantity'] for item in items)
    if len(items) > 1:
        print(f"  Total: {total_quantity} across {len(items)} entries")
    for item in items:
        print(f"  - ID {item['id']}: {item['quantity']} {item['unit']} (used: {item['used']})")
        if item['expires']:
            print(f"    Expires: {item['expires']}")

print(f"\n\nTotal unique products: {len(products)}")