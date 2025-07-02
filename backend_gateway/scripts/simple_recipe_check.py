#!/usr/bin/env python3
"""Simple script to check saved chat recipes"""

from google.cloud import bigquery
import json
import os

# Set up BigQuery client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/danielkim/_Capstone/PrepSense/config/adsp-34002-on02-prep-sense-ef1111b0833b.json'
client = bigquery.Client(project='adsp-34002-on02-prep-sense')

query = """
SELECT 
    recipe_title,
    recipe_id,
    is_favorite,
    TO_JSON_STRING(recipe_data) as recipe_data_json,
    created_at
FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE source = 'chat'
ORDER BY created_at DESC
"""

print("Checking chat recipes in BigQuery...\n")

results = client.query(query).result()

for row in results:
    print(f"Recipe: {row['recipe_title']}")
    print(f"Recipe ID: {row['recipe_id']}")
    print(f"Is Favorite: {row['is_favorite']}")
    print(f"Created: {row['created_at']}")
    
    print("\nRecipe Data Structure:")
    recipe_data = json.loads(row['recipe_data_json'])
    
    # Show the structure
    print(f"- name: {recipe_data.get('name', 'N/A')}")
    print(f"- ingredients: {type(recipe_data.get('ingredients', [])).__name__} with {len(recipe_data.get('ingredients', []))} items")
    if recipe_data.get('ingredients'):
        print(f"  First ingredient: {recipe_data['ingredients'][0]}")
    print(f"- instructions: {type(recipe_data.get('instructions', [])).__name__} with {len(recipe_data.get('instructions', []))} items")
    print(f"- nutrition: {recipe_data.get('nutrition', {})}")
    print(f"- time: {recipe_data.get('time', 'N/A')} minutes")
    print(f"- match_score: {recipe_data.get('match_score', 'N/A')}")
    print(f"- expected_joy: {recipe_data.get('expected_joy', 'N/A')}")
    
    print("\n" + "="*60 + "\n")