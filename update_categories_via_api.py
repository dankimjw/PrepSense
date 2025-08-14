#!/usr/bin/env python3
"""
Script to update pantry items that have "Other" or "Uncategorized" categories
using the API endpoints.
"""

import json
import requests
from typing import Dict, List


# Category mapping based on ingredient names
INGREDIENT_CATEGORY_MAPPING = {
    # Meat & Poultry
    'ground beef': 'Meat & Poultry',
    'lean ground beef': 'Meat & Poultry', 
    'ground turkey': 'Meat & Poultry',
    'chicken breast': 'Meat & Poultry',
    'turkey bacon': 'Meat & Poultry',
    'slices turkey bacon': 'Meat & Poultry',
    
    # Dairy & Eggs
    'greek yogurt': 'Dairy',
    'paneer': 'Dairy',
    'milk': 'Dairy',
    'almond milk': 'Dairy',
    'eggs': 'Dairy',
    'wedges laughing cow swiss cheese': 'Dairy',
    
    # Fresh Produce
    'green bell pepper': 'Fresh Produce',
    'bell peppers': 'Fresh Produce', 
    'orange bell pepper': 'Fresh Produce',
    'yellow bell pepper': 'Fresh Produce',
    'poblano pepper': 'Fresh Produce',
    'onions': 'Fresh Produce',
    'garlic': 'Fresh Produce',
    'tomatoes': 'Fresh Produce',
    'onion, sliced into strips': 'Fresh Produce',
    'finely diced celery': 'Fresh Produce',
    'fresh chopped parsley': 'Fresh Herbs',
    'kale': 'Fresh Produce',
    'avocados': 'Fresh Produce',
    'sweet potatoes': 'Fresh Produce',
    'cremini mushrooms': 'Fresh Produce',
    'strawberries': 'Fresh Produce',
    'raspberries': 'Fresh Produce',
    
    # Pantry Staples
    'pasta': 'Pantry Staples',
    'rice': 'Rice & Grains',
    'quinoa': 'Rice & Grains',
    'oats': 'Rice & Grains',
    
    # Spices & Condiments
    'chopped chipotle chiles in adobo': 'Condiments',
    'fat free mayonnaise': 'Condiments',
    'garlic powder': 'Spices',
    'ground cumin': 'Spices',
    'ground black pepper': 'Spices',
    'salt': 'Spices',
    'lime juice': 'Condiments',
    'olive oil': 'Condiments',
    'balsamic vinegar': 'Condiments',
    '1/2- 2 tbsp pesto': 'Condiments',
    
    # Bakery & Breads
    'wheat hamburger buns': 'Bakery & Pastries',
    'whole grain sandwich thins': 'Bakery & Pastries',
    
    # Snacks & Treats
    'walnuts': 'Snacks & Treats',
    'pine nuts': 'Snacks & Treats',
    'chia seeds': 'Snacks & Treats',
    'dark chocolate': 'Snacks & Treats',
    'honey': 'Condiments',
    'sun dried tomatoes': 'Condiments',
    
    # Other items
    'guacamole': 'Condiments',
}


def get_category_for_item(product_name: str) -> str:
    """
    Determine the appropriate category for a pantry item based on its name.
    """
    if not product_name:
        return 'Other'
    
    # Convert to lowercase for matching
    name_lower = product_name.lower().strip()
    
    # Check for exact matches first
    if name_lower in INGREDIENT_CATEGORY_MAPPING:
        return INGREDIENT_CATEGORY_MAPPING[name_lower]
    
    # Check for partial matches
    for ingredient, category in INGREDIENT_CATEGORY_MAPPING.items():
        if ingredient in name_lower or name_lower in ingredient:
            return category
    
    # Check for common patterns
    if any(word in name_lower for word in ['pepper', 'bell']):
        return 'Fresh Produce'
    elif any(word in name_lower for word in ['cheese', 'yogurt', 'milk']):
        return 'Dairy'
    elif any(word in name_lower for word in ['chicken', 'beef', 'turkey', 'bacon', 'meat']):
        return 'Meat & Poultry'
    elif any(word in name_lower for word in ['powder', 'spice', 'seasoning']):
        return 'Spices'
    elif any(word in name_lower for word in ['sauce', 'oil', 'vinegar', 'mayo']):
        return 'Condiments'
    elif any(word in name_lower for word in ['bread', 'bun', 'roll', 'bagel']):
        return 'Bakery & Pastries'
    elif any(word in name_lower for word in ['nut', 'seed', 'almond', 'walnut']):
        return 'Snacks & Treats'
    elif any(word in name_lower for word in ['pasta', 'rice', 'grain', 'cereal', 'oat']):
        return 'Pantry Staples'
    elif any(word in name_lower for word in ['herb', 'parsley', 'basil', 'cilantro']):
        return 'Fresh Herbs'
    
    # Keep as uncategorized if we can't determine
    return 'Uncategorized'


def main():
    """Main function to update pantry categories via API."""
    
    BASE_URL = "http://localhost:8001"
    USER_ID = 111
    
    try:
        # Get all pantry items
        response = requests.get(f"{BASE_URL}/api/v1/pantry/user/{USER_ID}/items")
        response.raise_for_status()
        items = response.json()
        
        print(f"Found {len(items)} total pantry items")
        
        # Filter items that need category updates
        items_to_update = [
            item for item in items 
            if item['food_category'] in ['Other', 'Uncategorized']
        ]
        
        print(f"Found {len(items_to_update)} items with 'Other' or 'Uncategorized' category")
        
        if not items_to_update:
            print("No items to update!")
            return 0
        
        # Analyze and prepare updates
        updates = []
        print("\\nAnalyzing items:")
        for item in items_to_update:
            product_name = item['product_name']
            current_category = item['food_category']
            new_category = get_category_for_item(product_name)
            
            if new_category != 'Uncategorized' and new_category != current_category:
                updates.append({
                    'pantry_item_id': item['pantry_item_id'],
                    'product_name': product_name,
                    'old_category': current_category,
                    'new_category': new_category,
                    'item_data': item
                })
                print(f"  {product_name}: {current_category} → {new_category}")
            else:
                print(f"  {product_name}: keeping '{current_category}'")
        
        if not updates:
            print("\\nNo updates needed!")
            return 0
        
        print(f"\\nPreparing to update {len(updates)} items...")
        
        # Show category summary
        category_counts = {}
        for update in updates:
            category = update['new_category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\\nCategory changes:")
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count} items")
        
        print("\\nProceeding with updates...")
        
        # Note: Since there's no direct category update API endpoint, 
        # we would need to implement this through the database or add a new API endpoint.
        # For now, let's create the SQL statements that can be run manually.
        
        print("\\nGenerating SQL update statements...")
        print("\\n-- SQL statements to update categories --")
        
        for update in updates:
            sql = f"UPDATE pantry_items SET category = '{update['new_category']}' WHERE pantry_item_id = {update['pantry_item_id']}; -- {update['product_name']}"
            print(sql)
        
        # Also create a summary
        print(f"\\n-- Summary: {len(updates)} items to be updated --")
        for category, count in sorted(category_counts.items()):
            print(f"-- {category}: {count} items")
        
        print("\\n✅ SQL statements generated successfully!")
        print("\\n📝 To apply these changes:")
        print("1. Copy the SQL statements above")
        print("2. Run them against your PostgreSQL database")
        print("3. Or implement a category update API endpoint")
        
        return 0
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())