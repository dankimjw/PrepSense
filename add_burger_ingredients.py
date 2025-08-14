#!/usr/bin/env python3
"""
Add burger ingredients to user 111's pantry for testing the sorting feature.
"""

import psycopg2
from datetime import datetime, timedelta
import random

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="prepsense",
    user="danielkim"
)

cursor = conn.cursor()

# Get user 111's pantry_id
cursor.execute("SELECT pantry_id FROM pantries WHERE user_id = 111")
result = cursor.fetchone()
if not result:
    print("Error: No pantry found for user 111")
    conn.close()
    exit(1)

pantry_id = result[0]
print(f"Found pantry_id {pantry_id} for user 111")

# Burger ingredients to add
tomorrow = datetime.now() + timedelta(days=1)
expiration_date = tomorrow.strftime('%Y-%m-%d')

burger_ingredients = [
    ("Ground Beef", "Proteins", 10, "lb"),
    ("Hamburger Buns", "Grains", 10, "package"),
    ("Chipotle Peppers in Adobo", "Condiments", 10, "can"),
    ("Mayonnaise", "Condiments", 10, "jar"),
    ("Turkey Bacon", "Proteins", 10, "package"),
    ("Cheddar Cheese", "Dairy", 10, "lb"),
    ("Lettuce", "Fresh Produce", 10, "head"),
    ("Tomatoes", "Fresh Produce", 10, "each"),
    ("Onions", "Fresh Produce", 10, "each"),
]

# Insert each ingredient
for product_name, category, quantity, unit in burger_ingredients:
    # Generate a random product_id
    product_id = random.randint(100000000, 999999999)
    
    # Insert into pantry_items table (without user_id column)
    insert_query = """
    INSERT INTO pantry_items (
        id,
        pantry_id,
        ingredient_name,
        quantity,
        unit,
        expiration_date,
        created_at,
        updated_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    values = (
        product_id,  # id
        pantry_id,   # pantry_id
        product_name,  # ingredient_name
        quantity,    # quantity
        unit,        # unit
        expiration_date,  # expiration_date
        datetime.now(),  # created_at
        datetime.now()   # updated_at
    )
    
    try:
        cursor.execute(insert_query, values)
        print(f"✅ Added {product_name} ({quantity} {unit}) - expires {expiration_date}")
    except psycopg2.IntegrityError as e:
        # If the product_id already exists, try with a different one
        product_id = random.randint(100000000, 999999999)
        values = (product_id,) + values[1:-1] + (product_id,) + values[-1:]
        cursor.execute(insert_query, values)
        print(f"✅ Added {product_name} ({quantity} {unit}) - expires {expiration_date} (retry)")

# Commit the changes
conn.commit()
print(f"\n✅ Successfully added {len(burger_ingredients)} burger ingredients to user 111's pantry!")

# Verify the additions
cursor.execute("""
    SELECT pi.ingredient_name, pi.quantity, pi.unit, pi.expiration_date 
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.id
    WHERE p.user_id = 111 
    AND pi.ingredient_name IN ('Ground Beef', 'Hamburger Buns', 'Chipotle Peppers in Adobo', 
                               'Mayonnaise', 'Turkey Bacon', 'Cheddar Cheese', 
                               'Lettuce', 'Tomatoes', 'Onions')
    ORDER BY pi.ingredient_name
""")

print("\nVerification - Burger ingredients in pantry:")
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]} {row[2]}, expires {row[3]}")

cursor.close()
conn.close()
