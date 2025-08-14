#!/usr/bin/env python3
"""
Debug script to check burger recipe in database
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend_gateway'))

from backend_gateway.config.database import get_database_service

def main():
    """Debug burger recipe retrieval."""
    
    db_service = get_database_service()
    
    try:
        # Get the current burger recipe
        query = """
        SELECT recipe_title, recipe_data FROM user_recipes 
        WHERE user_id = 111 AND recipe_title LIKE '%Burger%'
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        print("Executing query...")
        result = db_service.execute_query(query)
        print(f"Query result type: {type(result)}")
        print(f"Query result: {result}")
        
        if not result:
            print("❌ Burger recipe not found!")
            return 1
        
        # Check if result is a list or single item
        if isinstance(result, list):
            if len(result) == 0:
                print("❌ No results in list!")
                return 1
            recipe_row = result[0]
        else:
            recipe_row = result
            
        print(f"Recipe row: {recipe_row}")
        
        recipe_data = recipe_row['recipe_data']
        print(f"Recipe title: {recipe_data['title']}")
        
        # Get current steps
        if 'analyzedInstructions' not in recipe_data:
            print("❌ No analyzedInstructions found!")
            return 1
            
        current_steps = recipe_data['analyzedInstructions'][0]['steps']
        print(f"Current number of steps: {len(current_steps)}")
        
        # Show all steps
        for i, step in enumerate(current_steps):
            print(f"Step {step['number']}: {step['step']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())