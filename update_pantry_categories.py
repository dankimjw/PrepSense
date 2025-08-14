#!/usr/bin/env python3
"""
Script to update pantry items that have "Other" or "Uncategorized" categories
to more specific categories based on ingredient names.
"""

import os
import sys
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend_gateway'))

from backend_gateway.services.postgres_service import PostgresService


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
    'greek yogurt': 'Dairy & Eggs',
    'paneer': 'Dairy & Eggs',
    'milk': 'Dairy & Eggs',
    'almond milk': 'Dairy & Eggs',
    'eggs': 'Dairy & Eggs',
    'wedges laughing cow swiss cheese': 'Dairy & Eggs',
    
    # Produce & Vegetables
    'green bell pepper': 'Produce',
    'bell peppers': 'Produce',
    'orange bell pepper': 'Produce',
    'yellow bell pepper': 'Produce',
    'poblano pepper': 'Produce',
    'onions': 'Produce',
    'garlic': 'Produce',
    'tomatoes': 'Produce',
    'onion, sliced into strips': 'Produce',
    'finely diced celery': 'Produce',
    'fresh chopped parsley': 'Produce',
    'kale': 'Produce',
    'avocados': 'Produce',
    'sweet potatoes': 'Produce',
    'cremini mushrooms': 'Produce',
    'strawberries': 'Produce',
    'raspberries': 'Produce',
    
    # Pantry & Grains
    'pasta': 'Pantry & Grains',
    'rice': 'Pantry & Grains',
    'quinoa': 'Pantry & Grains',
    'oats': 'Pantry & Grains',
    
    # Condiments & Spices
    'chopped chipotle chiles in adobo': 'Condiments & Spices',
    'fat free mayonnaise': 'Condiments & Spices',
    'garlic powder': 'Condiments & Spices',
    'ground cumin': 'Condiments & Spices',
    'ground black pepper': 'Condiments & Spices',
    'salt': 'Condiments & Spices',
    'lime juice': 'Condiments & Spices',
    'olive oil': 'Condiments & Spices',
    'balsamic vinegar': 'Condiments & Spices',
    '1/2- 2 tbsp pesto': 'Condiments & Spices',
    
    # Bakery & Breads
    'wheat hamburger buns': 'Bakery & Breads',
    'whole grain sandwich thins': 'Bakery & Breads',
    
    # Nuts & Seeds
    'walnuts': 'Nuts & Seeds',
    'pine nuts': 'Nuts & Seeds',
    'chia seeds': 'Nuts & Seeds',
    
    # Snacks & Sweets
    'dark chocolate': 'Snacks & Sweets',
    'honey': 'Snacks & Sweets',
    
    # Beverages (if needed)
    'guacamole': 'Condiments & Spices',
    
    # Specialty items
    'sun dried tomatoes': 'Condiments & Spices',
}


def get_category_for_item(product_name: str) -> str:
    """
    Determine the appropriate category for a pantry item based on its name.
    
    Args:
        product_name: The name of the product
    
    Returns:
        The appropriate category name
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
        return 'Produce'
    elif any(word in name_lower for word in ['cheese', 'yogurt', 'milk']):
        return 'Dairy & Eggs'
    elif any(word in name_lower for word in ['chicken', 'beef', 'turkey', 'bacon', 'meat']):
        return 'Meat & Poultry'
    elif any(word in name_lower for word in ['powder', 'spice', 'seasoning', 'sauce', 'oil', 'vinegar']):
        return 'Condiments & Spices'
    elif any(word in name_lower for word in ['bread', 'bun', 'roll', 'bagel']):
        return 'Bakery & Breads'
    elif any(word in name_lower for word in ['nut', 'seed', 'almond', 'walnut']):
        return 'Nuts & Seeds'
    elif any(word in name_lower for word in ['pasta', 'rice', 'grain', 'cereal', 'oat']):
        return 'Pantry & Grains'
    
    # Default to keeping existing category if we can't determine a better one
    return 'Other'


def main():
    """Main function to update pantry categories."""
    
    # Initialize database connection
    connection_params = {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT', 5432),
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
    }
    
    db_service = PostgresService(connection_params)
    
    try:
        # Get all items with "Other" or "Uncategorized" categories
        query = """
        SELECT pi.pantry_item_id, pi.product_name, pi.category as food_category
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        JOIN users u ON p.user_id = u.user_id
        WHERE u.user_id = 111 
        AND (pi.category = 'Other' OR pi.category = 'Uncategorized')
        ORDER BY pi.product_name;
        """
        
        items = db_service.execute_query(query)
        print(f"Found {len(items)} items with 'Other' or 'Uncategorized' category")
        
        if not items:
            print("No items to update!")
            return
        
        # Analyze and prepare updates
        updates = []
        for item in items:
            pantry_item_id = item['pantry_item_id']
            product_name = item['product_name']
            current_category = item['food_category']
            
            new_category = get_category_for_item(product_name)
            
            if new_category != 'Other' and new_category != current_category:
                updates.append({
                    'pantry_item_id': pantry_item_id,
                    'product_name': product_name,
                    'old_category': current_category,
                    'new_category': new_category
                })
                print(f"  {product_name}: {current_category} → {new_category}")
            else:
                print(f"  {product_name}: keeping '{current_category}'")
        
        if not updates:
            print("\nNo updates needed!")
            return
        
        print(f"\nPreparing to update {len(updates)} items...")
        
        # Confirm with user
        response = input("Do you want to proceed with these updates? (y/N): ").strip().lower()
        if response != 'y':
            print("Updates cancelled.")
            return
        
        # Perform updates
        print("\nUpdating categories...")
        update_query = """
        UPDATE pantry_items 
        SET category = %(new_category)s 
        WHERE pantry_item_id = %(pantry_item_id)s
        """
        
        updated_count = 0
        for update in updates:
            try:
                db_service.execute_query(update_query, {
                    'new_category': update['new_category'],
                    'pantry_item_id': update['pantry_item_id']
                })
                updated_count += 1
                print(f"  ✅ Updated: {update['product_name']}")
            except Exception as e:
                print(f"  ❌ Failed to update {update['product_name']}: {e}")
        
        print(f"\n🎉 Successfully updated {updated_count} out of {len(updates)} items!")
        
        # Show summary of new categories
        print("\nCategory summary:")
        category_counts = {}
        for update in updates:
            category = update['new_category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count} items")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())