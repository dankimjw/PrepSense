#!/usr/bin/env python3
"""
Script to verify that burger ingredients are correctly subtracted from pantry
after recipe completion.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import sys

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="prepsense",
    user="danielkim",
    password="danielkim",
    cursor_factory=RealDictCursor
)
cur = conn.cursor()

def get_pantry_items(user_id=111):
    """Get all pantry items for a user."""
    cur.execute("""
        SELECT pi.*, p.pantry_name 
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = %s
        ORDER BY pi.ingredient_name
    """, (user_id,))
    return cur.fetchall()

def get_burger_recipe():
    """Get the burger recipe details."""
    cur.execute("""
        SELECT * FROM recipes 
        WHERE title = 'Cheesy Bacon Burger with Spicy Chipotle'
        LIMIT 1
    """)
    return cur.fetchone()

def print_pantry_status(title):
    """Print current pantry status for burger ingredients."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)
    
    items = get_pantry_items()
    
    # Burger ingredient keywords to look for
    burger_keywords = [
        'ground beef', 'beef', 'hamburger buns', 'buns', 
        'cheddar cheese', 'cheese', 'bacon', 'lettuce', 
        'tomato', 'red onion', 'onion', 'pickles', 
        'chipotle', 'mayonnaise', 'salt', 'pepper', 'olive oil'
    ]
    
    burger_items = []
    for item in items:
        item_name_lower = item['ingredient_name'].lower()
        for keyword in burger_keywords:
            if keyword in item_name_lower:
                burger_items.append(item)
                break
    
    if burger_items:
        print(f"\nBurger Ingredients in Pantry ({len(burger_items)} items):")
        print("-" * 40)
        for item in burger_items:
            print(f"  • {item['ingredient_name']}: {item['quantity']} {item['unit']}")
            print(f"    (Expires: {item['expiration_date']})")
    else:
        print("\n❌ No burger ingredients found in pantry!")
    
    print(f"\nTotal pantry items: {len(items)}")
    return burger_items

def simulate_recipe_completion():
    """Simulate what should happen when recipe is completed."""
    print("\n" + "="*60)
    print("SIMULATING RECIPE COMPLETION")
    print("="*60)
    
    recipe = get_burger_recipe()
    if not recipe:
        print("❌ Burger recipe not found in database!")
        return
    
    print(f"\nRecipe: {recipe['title']}")
    print(f"Recipe ID: {recipe['id']}")
    
    # Parse ingredients from recipe
    ingredients_data = recipe.get('extendedIngredients') or recipe.get('ingredients')
    if isinstance(ingredients_data, str):
        try:
            ingredients_data = json.loads(ingredients_data)
        except:
            print("❌ Could not parse recipe ingredients!")
            return
    
    print(f"\nRecipe requires {len(ingredients_data)} ingredients:")
    print("-" * 40)
    for ing in ingredients_data:
        if isinstance(ing, dict):
            name = ing.get('name') or ing.get('nameClean') or ing.get('original', '')
            amount = ing.get('amount', 0)
            unit = ing.get('unit', '')
            print(f"  • {name}: {amount} {unit}")
    
    print("\n⚠️  When recipe is completed, these amounts should be")
    print("   subtracted from the pantry (or a percentage based on slider).")

def main():
    print("\n" + "="*60)
    print("PANTRY CONSUMPTION VERIFICATION")
    print("="*60)
    
    # Check initial pantry state
    initial_items = print_pantry_status("CURRENT PANTRY STATE")
    
    if not initial_items:
        print("\n⚠️  No burger ingredients in pantry!")
        print("   Run add_burger_recipe.py first to add ingredients.")
        sys.exit(1)
    
    # Show what should happen on recipe completion
    simulate_recipe_completion()
    
    print("\n" + "="*60)
    print("VERIFICATION STEPS")
    print("="*60)
    print("""
To verify pantry consumption is working:

1. Open the PrepSense app
2. Navigate to 'My Recipes' or 'Chat' section
3. Select 'Cheesy Bacon Burger with Spicy Chipotle'
4. Start cooking mode and complete the recipe
5. In the completion modal, adjust ingredient sliders as needed
6. Confirm recipe completion
7. Check that success modal shows updated quantities
8. Run this script again to verify database changes

Expected behavior:
- Pantry items should be reduced by the amounts used
- Success modal should show before/after quantities
- Database should reflect the updated quantities
""")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
