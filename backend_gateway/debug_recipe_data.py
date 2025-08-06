#!/usr/bin/env python3
"""
Debug script to examine recipe data structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_database_service
import json

def debug_recipe_data():
    """Debug recipe data structure"""
    print("Examining recipe data structure...")
    
    db = get_database_service()
    
    # Get a few sample recipes
    recipes = db.execute_query("""
        SELECT recipe_title, recipe_data, source 
        FROM user_recipes 
        WHERE user_id = 111 
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    for i, recipe in enumerate(recipes):
        print(f"\n=== Recipe {i+1} ===")
        print(f"Title: {recipe['recipe_title']}")
        print(f"Source: {recipe['source']}")
        
        recipe_data = recipe['recipe_data']
        if recipe_data:
            print(f"Data keys: {list(recipe_data.keys())}")
            
            # Check for ingredients
            if 'ingredients' in recipe_data:
                ingredients = recipe_data['ingredients']
                print(f"Ingredients count: {len(ingredients) if ingredients else 0}")
                if ingredients and len(ingredients) > 0:
                    print(f"First ingredient type: {type(ingredients[0])}")
                    print(f"First ingredient: {ingredients[0]}")
            else:
                print("No 'ingredients' key found")
                
            # Check for title in data
            if 'title' in recipe_data:
                print(f"Title in data: {recipe_data['title']}")
        else:
            print("recipe_data is None/empty")

if __name__ == "__main__":
    debug_recipe_data()
