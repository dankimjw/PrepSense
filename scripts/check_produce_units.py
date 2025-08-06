import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_produce_units():
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    # Check for produce items with liquid units
    result = await conn.fetch("""
        SELECT 
            pi.pantry_item_id,
            pi.product_name,
            pi.quantity,
            pi.unit_of_measurement,
            pi.category
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = 111
        AND (pi.status IS NULL OR pi.status != 'consumed')
        AND (
            (LOWER(pi.product_name) LIKE '%strawberr%' OR
             LOWER(pi.product_name) LIKE '%blueberr%' OR
             LOWER(pi.product_name) LIKE '%raspberr%' OR
             LOWER(pi.product_name) LIKE '%blackberr%' OR
             LOWER(pi.product_name) LIKE '%apple%' OR
             LOWER(pi.product_name) LIKE '%banana%' OR
             LOWER(pi.product_name) LIKE '%orange%' OR
             LOWER(pi.product_name) LIKE '%carrot%' OR
             LOWER(pi.product_name) LIKE '%celery%' OR
             LOWER(pi.product_name) LIKE '%lettuce%' OR
             LOWER(pi.product_name) LIKE '%spinach%' OR
             LOWER(pi.product_name) LIKE '%broccoli%')
            AND 
            (LOWER(pi.unit_of_measurement) IN ('ml', 'l', 'fl oz', 'cup', 'gallon', 'liter', 'milliliter', 'fluid ounce'))
        )
        ORDER BY pi.product_name
    """)
    
    if result:
        print(f"Found {len(result)} produce items with liquid units that need fixing:")
        for row in result:
            print(f"  - {row['product_name']}: {row['quantity']} {row['unit_of_measurement']} (Category: {row['category']})")
    else:
        print("No produce items found with liquid units.")
    
    # Also check for any items with 'ml' as unit
    ml_items = await conn.fetch("""
        SELECT 
            pi.product_name,
            pi.quantity,
            pi.unit_of_measurement,
            pi.category
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = 111
        AND (pi.status IS NULL OR pi.status != 'consumed')
        AND LOWER(pi.unit_of_measurement) = 'ml'
        ORDER BY pi.product_name
    """)
    
    if ml_items:
        print(f"\nAll items using 'ml' as unit:")
        for row in ml_items:
            print(f"  - {row['product_name']}: {row['quantity']} {row['unit_of_measurement']}")
    
    await conn.close()

asyncio.run(check_produce_units())