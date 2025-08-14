#!/usr/bin/env python3
"""
Add new pantry items for user 111
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Items to add with their quantities and units
new_items = [
    {"product_name": "Sliced almonds", "quantity": 1, "unit": "cup", "category": "Nuts"},
    {"product_name": "Butter", "quantity": 1, "unit": "cup", "category": "Dairy"},
    {"product_name": "Eggs", "quantity": 1, "unit": "each", "category": "Protein"},
    {"product_name": "All-purpose flour", "quantity": 2, "unit": "cups", "category": "Grains"},  # Rounded up from 1.75
    {"product_name": "Potatoes", "quantity": 500, "unit": "grams", "category": "Vegetables"},
    {"product_name": "Salt", "quantity": 1, "unit": "container", "category": "Seasonings"},
    {"product_name": "Black pepper", "quantity": 1, "unit": "container", "category": "Seasonings"},
    {"product_name": "Salmon", "quantity": 1, "unit": "can", "category": "Protein"},
    {"product_name": "Tuna flakes", "quantity": 1, "unit": "can", "category": "Protein"}
]

async def add_pantry_items():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database='prepsense',
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    try:
        print("🔄 Adding new pantry items for user 111...")
        print("=" * 70)
        
        # Get the pantry_id for user 111 - it should be 1 based on previous queries
        pantry_id = 1  # User 111 uses pantry_id 1
        print(f"Using pantry_id: {pantry_id} for user 111")
        
        added_count = 0
        updated_count = 0
        
        for item in new_items:
            # Check if item already exists - need to join with users table
            existing = await conn.fetchrow("""
                SELECT pi.pantry_item_id, pi.product_name, pi.quantity, pi.unit_of_measurement
                FROM pantry_items pi
                WHERE pi.pantry_id = $1
                AND LOWER(pi.product_name) = LOWER($2)
                AND pi.status = 'available'
            """, pantry_id, item['product_name'])
            
            if existing:
                # Update quantity if item exists
                if item['product_name'].lower() in ['salt', 'black pepper']:
                    # Don't update salt and pepper as they already exist
                    print(f"⏭️  Skipping {item['product_name']} (already exists)")
                    continue
                else:
                    # Update quantity for other items
                    new_qty = float(existing['quantity']) + item['quantity']
                    await conn.execute("""
                        UPDATE pantry_items
                        SET quantity = $1, updated_at = $2
                        WHERE pantry_item_id = $3
                    """, new_qty, datetime.now(), existing['pantry_item_id'])
                    updated_count += 1
                    print(f"📝 Updated {item['product_name']}: {existing['quantity']} → {new_qty} {item['unit']}")
            else:
                # Calculate expiration date based on category
                if item['category'] == 'Dairy':
                    exp_days = 14
                elif item['category'] == 'Protein':
                    if 'can' in item['unit']:
                        exp_days = 365  # Canned goods
                    else:
                        exp_days = 7  # Fresh eggs
                elif item['category'] == 'Vegetables':
                    exp_days = 14
                elif item['category'] == 'Nuts':
                    exp_days = 180
                elif item['category'] in ['Grains', 'Seasonings']:
                    exp_days = 365
                else:
                    exp_days = 30
                
                expiration_date = datetime.now() + timedelta(days=exp_days)
                
                # Insert new item into pantry_items table
                result = await conn.fetchrow("""
                    INSERT INTO pantry_items 
                    (pantry_id, product_name, quantity, unit_of_measurement, 
                     category, expiration_date, created_at, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING pantry_item_id
                """, pantry_id, item['product_name'], item['quantity'], 
                    item['unit'], item['category'], expiration_date, 
                    datetime.now(), 'available')
                
                added_count += 1
                print(f"✅ Added {item['product_name']}: {item['quantity']} {item['unit']} (expires in {exp_days} days)")
        
        print("-" * 70)
        print(f"\n📊 Summary:")
        print(f"  Added: {added_count} new items")
        print(f"  Updated: {updated_count} existing items")
        print(f"  Skipped: {len(new_items) - added_count - updated_count} items")
        
        # Show updated pantry summary
        total_items = await conn.fetchval("""
            SELECT COUNT(*) FROM user_pantry_full 
            WHERE user_id = 111 AND quantity > 0
        """)
        
        print(f"\n📈 Total pantry items for user 111: {total_items}")
        
        # Show the newly added items
        print("\n🆕 Current pantry snapshot (newest items):")
        print("-" * 70)
        
        recent_items = await conn.fetch("""
            SELECT product_name, quantity, unit_of_measurement, category
            FROM user_pantry_full
            WHERE user_id = 111 AND quantity > 0
            ORDER BY created_at DESC, product_name
            LIMIT 15
        """)
        
        for item in recent_items:
            qty = int(item['quantity']) if item['quantity'] == int(item['quantity']) else item['quantity']
            print(f"  {item['product_name'][:30]:<30} {qty:>6} {item['unit_of_measurement']:<12} [{item['category']}]")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_pantry_items())
    print("\n✨ Done!")