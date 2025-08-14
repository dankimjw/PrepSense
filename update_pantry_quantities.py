#!/usr/bin/env python3
"""
Update pantry items for user 111 to have whole number quantities
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import math

load_dotenv()

async def update_pantry_quantities():
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database='prepsense',  # Fixed database name
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    try:
        # Get all pantry items for user 111
        items = await conn.fetch("""
            SELECT pantry_item_id, product_name, quantity, unit_of_measurement 
            FROM user_pantry_full 
            WHERE user_id = 111 AND quantity > 0
            ORDER BY product_name
        """)
        
        print(f"Found {len(items)} pantry items for user 111")
        print("\nUpdating quantities to whole numbers...")
        print("-" * 70)
        
        updated_count = 0
        for item in items:
            old_qty = float(item['quantity'])
            
            # Round up to nearest whole number (so we don't lose items)
            new_qty = math.ceil(old_qty)
            
            # Only update if quantity changed
            if new_qty != old_qty:
                await conn.execute("""
                    UPDATE user_pantry_full 
                    SET quantity = $1 
                    WHERE pantry_item_id = $2
                """, new_qty, item['pantry_item_id'])
                
                updated_count += 1
                print(f"✓ {item['product_name'][:30]:<30} {old_qty:>8.2f} → {new_qty:>3.0f} {item['unit_of_measurement']}")
        
        print("-" * 70)
        print(f"\n✅ Updated {updated_count} items to whole number quantities")
        
        # Show some examples of the updated items
        print("\n📊 Sample of updated pantry (first 20 items):")
        print("-" * 70)
        
        updated_items = await conn.fetch("""
            SELECT product_name, quantity, unit_of_measurement 
            FROM user_pantry_full 
            WHERE user_id = 111 AND quantity > 0
            ORDER BY product_name
            LIMIT 20
        """)
        
        for item in updated_items:
            qty = int(item['quantity'])
            print(f"  {item['product_name'][:35]:<35} {qty:>3} {item['unit_of_measurement']}")
        
        # Show totals
        total_items = await conn.fetchval("""
            SELECT COUNT(*) FROM user_pantry_full 
            WHERE user_id = 111 AND quantity > 0
        """)
        
        print("-" * 70)
        print(f"\n📈 Total active pantry items: {total_items}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🔄 Updating User 111's pantry quantities to whole numbers...")
    print("=" * 70)
    asyncio.run(update_pantry_quantities())
    print("\n✨ Done!")