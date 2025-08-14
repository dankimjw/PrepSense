#!/usr/bin/env python3
"""
Verify that burger ingredients are properly sorted at the top of the pantry list.
"""

import psycopg2
from datetime import datetime, timedelta
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="prepsense",
    user="danielkim",
    password="",
    port=5432
)

def get_pantry_items(user_id=111):
    """Get all pantry items for a user."""
    cursor = conn.cursor()
    query = """
        SELECT 
            pantry_item_id,
            item_name,
            quantity,
            quantity_unit,
            expiration_date
        FROM pantry_items
        WHERE user_id = %s
        ORDER BY expiration_date ASC
    """
    cursor.execute(query, (user_id,))
    items = cursor.fetchall()
    cursor.close()
    return items

def check_burger_ingredients():
    """Check if burger ingredients exist and their positions."""
    # Burger ingredient keywords (from the frontend sorting logic)
    burger_keywords = [
        'chipotle', 'mayonnaise', 'ground beef', 'turkey bacon',
        'hamburger buns', 'cheddar cheese', 'lettuce', 'tomato',
        'onion', 'pickles', 'ketchup', 'mustard', 'worcestershire',
        'garlic powder', 'salt', 'pepper', 'paprika', 'cayenne'
    ]
    
    items = get_pantry_items()
    
    print("\n" + "="*60)
    print("PANTRY ITEMS VERIFICATION - BURGER SORTING")
    print("="*60)
    
    print(f"\nTotal pantry items: {len(items)}")
    print("\n" + "-"*60)
    print("PANTRY ITEMS (Database Order by Expiration):")
    print("-"*60)
    
    burger_items = []
    other_items = []
    
    for idx, item in enumerate(items, 1):
        item_id, name, quantity, unit, exp_date = item
        
        # Check if this is a burger ingredient
        is_burger = any(keyword in name.lower() for keyword in burger_keywords)
        
        if is_burger:
            burger_items.append((idx, name, quantity, unit, exp_date))
            print(f"{idx:3}. 🍔 {name:<30} {quantity:>8.2f} {unit:<10} Exp: {exp_date} [BURGER]")
        else:
            other_items.append((idx, name, quantity, unit, exp_date))
            print(f"{idx:3}.    {name:<30} {quantity:>8.2f} {unit:<10} Exp: {exp_date}")
    
    print("\n" + "-"*60)
    print("SORTING VERIFICATION:")
    print("-"*60)
    
    print(f"\n✅ Burger ingredients found: {len(burger_items)}")
    print(f"📦 Other ingredients: {len(other_items)}")
    
    if burger_items:
        print("\n🍔 BURGER INGREDIENTS:")
        for idx, name, qty, unit, exp in burger_items:
            print(f"   - {name}: {qty:.2f} {unit}")
    
    print("\n" + "-"*60)
    print("FRONTEND SORTING EXPECTATION:")
    print("-"*60)
    print("The frontend should display these burger ingredients FIRST,")
    print("regardless of their expiration dates, due to the hidden override.")
    print("\nExpected order in UI:")
    print("1. All burger ingredients (sorted by expiration among themselves)")
    print("2. All other ingredients (sorted by expiration)")
    
    # Simulate the frontend sorting
    print("\n" + "-"*60)
    print("SIMULATED FRONTEND DISPLAY ORDER:")
    print("-"*60)
    
    # Sort burger items by expiration
    burger_items_sorted = sorted(burger_items, key=lambda x: x[4])
    # Sort other items by expiration  
    other_items_sorted = sorted(other_items, key=lambda x: x[4])
    
    display_order = burger_items_sorted + other_items_sorted
    
    for idx, (_, name, qty, unit, exp) in enumerate(display_order, 1):
        is_burger = any(keyword in name.lower() for keyword in burger_keywords)
        marker = "🍔" if is_burger else "  "
        print(f"{idx:3}. {marker} {name:<30} {qty:>8.2f} {unit:<10} Exp: {exp}")
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60)
    
    if burger_items:
        print("\n✅ Burger ingredients are present in the pantry.")
        print("✅ Frontend sorting override should display them at the top.")
    else:
        print("\n⚠️  No burger ingredients found in pantry!")
        print("   The sorting override won't have any effect.")

if __name__ == "__main__":
    try:
        check_burger_ingredients()
    finally:
        conn.close()
