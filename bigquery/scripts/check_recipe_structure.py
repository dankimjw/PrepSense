#!/usr/bin/env python3
"""Quick script to check the structure of saved chat recipes"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.services.bigquery_service import BigQueryService
import json

def main():
    bq_service = BigQueryService()
    
    query = """
    SELECT 
        recipe_title,
        TO_JSON_STRING(recipe_data) as recipe_data_json
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat'
    LIMIT 1
    """
    
    results = bq_service.execute_query(query)
    
    for row in results:
        print(f"Recipe: {row['recipe_title']}")
        print("\nRaw recipe_data structure:")
        
        recipe_data = json.loads(row['recipe_data_json'])
        print(json.dumps(recipe_data, indent=2))

if __name__ == "__main__":
    main()