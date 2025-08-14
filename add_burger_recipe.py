#!/usr/bin/env python3
"""
Script to add Cheesy Bacon Burger with Spicy Chipotle recipe and its ingredients to the database
"""
import psycopg2
from datetime import datetime, timedelta
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="prepsense",
    user="danielkim",
    password=""
)
cur = conn.cursor()

# Recipe data for Cheesy Bacon Burger with Spicy Chipotle
recipe_data = {
    "id": 2011,
    "title": "Cheesy Bacon Burger with Spicy Chipotle",
    "readyInMinutes": 25,
    "servings": 4,
    "sourceUrl": "",
    "image": "cheesy-bacon-burger.jpg",
    "summary": "A juicy beef burger topped with melted cheese, crispy bacon, and spicy chipotle mayo",
    "cuisines": ["American"],
    "dishTypes": ["lunch", "main course", "dinner"],
    "diets": [],
    "instructions": [
        "Form ground beef into 4 patties and season with salt and pepper",
        "Cook bacon until crispy and set aside",
        "Mix chipotle peppers with mayonnaise for the sauce",
        "Grill or pan-fry burger patties for 4-5 minutes per side",
        "Add cheese slices in the last minute of cooking",
        "Toast burger buns lightly",
        "Assemble burgers with lettuce, tomato, patty, bacon, and chipotle mayo"
    ],
    "analyzedInstructions": [{
        "name": "",
        "steps": [
            {"number": 1, "step": "Form ground beef into 4 patties and season with salt and pepper"},
            {"number": 2, "step": "Cook bacon until crispy and set aside"},
            {"number": 3, "step": "Mix chipotle peppers with mayonnaise for the sauce"},
            {"number": 4, "step": "Grill or pan-fry burger patties for 4-5 minutes per side"},
            {"number": 5, "step": "Add cheese slices in the last minute of cooking"},
            {"number": 6, "step": "Toast burger buns lightly"},
            {"number": 7, "step": "Assemble burgers with lettuce, tomato, patty, bacon, and chipotle mayo"}
        ]
    }],
    "extendedIngredients": [
        {"id": 1, "name": "ground beef", "amount": 1.5, "unit": "lb", "original": "1.5 lb ground beef"},
        {"id": 2, "name": "bacon", "amount": 8, "unit": "slices", "original": "8 slices bacon"},
        {"id": 3, "name": "cheddar cheese", "amount": 4, "unit": "slices", "original": "4 slices cheddar cheese"},
        {"id": 4, "name": "burger buns", "amount": 4, "unit": "buns", "original": "4 burger buns"},
        {"id": 5, "name": "lettuce", "amount": 4, "unit": "leaves", "original": "4 lettuce leaves"},
        {"id": 6, "name": "tomato", "amount": 1, "unit": "large", "original": "1 large tomato, sliced"},
        {"id": 7, "name": "red onion", "amount": 1, "unit": "medium", "original": "1 medium red onion, sliced"},
        {"id": 8, "name": "mayonnaise", "amount": 0.5, "unit": "cup", "original": "1/2 cup mayonnaise"},
        {"id": 9, "name": "chipotle peppers in adobo", "amount": 2, "unit": "tbsp", "original": "2 tbsp chipotle peppers in adobo, minced"},
        {"id": 10, "name": "salt", "amount": 1, "unit": "tsp", "original": "1 tsp salt"},
        {"id": 11, "name": "black pepper", "amount": 0.5, "unit": "tsp", "original": "1/2 tsp black pepper"},
        {"id": 12, "name": "pickles", "amount": 8, "unit": "slices", "original": "8 pickle slices (optional)"}
    ],
    "nutrition": {
        "nutrients": [
            {"name": "Calories", "amount": 680, "unit": "kcal"},
            {"name": "Protein", "amount": 42, "unit": "g"},
            {"name": "Fat", "amount": 45, "unit": "g"},
            {"name": "Carbohydrates", "amount": 28, "unit": "g"}
        ]
    }
}

try:
    # First, check if recipe already exists
    cur.execute("SELECT recipe_id FROM recipes WHERE recipe_id = 2011")
    if cur.fetchone():
        print("Recipe 2011 already exists, updating...")
        cur.execute("""
            UPDATE recipes 
            SET recipe_name = %s, recipe_data = %s, cuisine_type = %s, prep_time = %s
            WHERE recipe_id = %s
        """, (
            recipe_data['title'],
            json.dumps(recipe_data),
            'American',
            recipe_data['readyInMinutes'],
            2011
        ))
    else:
        print("Creating new recipe...")
        cur.execute("""
            INSERT INTO recipes (recipe_id, recipe_name, recipe_data, cuisine_type, prep_time, servings)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            2011,
            recipe_data['title'],
            json.dumps(recipe_data),
            'American',
            recipe_data['readyInMinutes'],
            recipe_data['servings']
        ))
    
    # Add to user_recipes for user 111
    # First check if it exists
    cur.execute("SELECT * FROM user_recipes WHERE user_id = 111 AND recipe_id = 2011")
    if cur.fetchone():
        cur.execute("""
            UPDATE user_recipes 
            SET is_favorite = true, source = 'saved', recipe_title = %s, recipe_image = %s, recipe_data = %s
            WHERE user_id = 111 AND recipe_id = 2011
        """, (recipe_data['title'], recipe_data['image'], json.dumps(recipe_data)))
    else:
        cur.execute("""
            INSERT INTO user_recipes (user_id, recipe_id, recipe_title, recipe_image, recipe_data, source, is_favorite, status)
            VALUES (111, 2011, %s, %s, %s, 'saved', true, 'saved')
        """, (recipe_data['title'], recipe_data['image'], json.dumps(recipe_data)))
    
    print(f"✅ Recipe '{recipe_data['title']}' added/updated successfully!")
    
    # First get the pantry_id for user 111
    cur.execute("SELECT pantry_id FROM pantries WHERE user_id = 111")
    pantry_result = cur.fetchone()
    if not pantry_result:
        # Create pantry if it doesn't exist
        cur.execute("""
            INSERT INTO pantries (user_id, pantry_name)
            VALUES (111, 'My Pantry')
            RETURNING pantry_id
        """)
        pantry_id = cur.fetchone()[0]
        print(f"Created pantry with ID {pantry_id} for user 111")
    else:
        pantry_id = pantry_result[0]
        print(f"Using existing pantry ID {pantry_id} for user 111")
    
    # Now add all ingredients to pantry for user 111
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    
    ingredients_to_add = [
        ("ground beef", 10, "lb", tomorrow_str),
        ("bacon", 10, "package", tomorrow_str),
        ("cheddar cheese", 10, "package", tomorrow_str),
        ("burger buns", 10, "package", tomorrow_str),
        ("lettuce", 10, "head", tomorrow_str),
        ("tomato", 10, "each", tomorrow_str),
        ("red onion", 10, "each", tomorrow_str),
        ("mayonnaise", 10, "jar", tomorrow_str),
        ("chipotle peppers in adobo", 10, "can", tomorrow_str),
        ("salt", 10, "container", tomorrow_str),
        ("black pepper", 10, "container", tomorrow_str),
        ("pickles", 10, "jar", tomorrow_str)
    ]
    
    for name, quantity, unit, exp_date in ingredients_to_add:
        # Check if item already exists
        cur.execute("""
            SELECT pantry_item_id FROM pantry_items 
            WHERE pantry_id = %s AND LOWER(product_name) = LOWER(%s)
        """, (pantry_id, name))
        
        existing = cur.fetchone()
        
        if existing:
            # Update existing item
            cur.execute("""
                UPDATE pantry_items 
                SET quantity = %s, unit_of_measurement = %s, expiration_date = %s
                WHERE pantry_item_id = %s
            """, (quantity, unit, exp_date, existing[0]))
            print(f"  ✓ Updated {name}: {quantity} {unit} (expires {exp_date})")
        else:
            # Insert new item
            cur.execute("""
                INSERT INTO pantry_items (pantry_id, product_name, quantity, unit_of_measurement, expiration_date, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pantry_id, name, quantity, unit, exp_date, 'Other'))
            print(f"  ✓ Added {name}: {quantity} {unit} (expires {exp_date})")
    
    conn.commit()
    print("\n✅ All ingredients added to pantry successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
