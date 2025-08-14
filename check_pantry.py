import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_quantities():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database='prepsense',
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    # Get all pantry items
    items = await conn.fetch('''
        SELECT pantry_item_id, product_name, quantity, unit_of_measurement 
        FROM user_pantry_full 
        WHERE user_id = 111 
        AND quantity > 0
        ORDER BY quantity DESC, product_name
    ''')
    
    print(f'Found {len(items)} pantry items for user 111')
    print('\nItems with quantities:')
    print('-' * 70)
    
    fractional_count = 0
    whole_items = []
    fractional_items = []
    
    for item in items:
        qty = float(item['quantity'])
        if qty != int(qty):
            fractional_count += 1
            fractional_items.append(item)
        else:
            whole_items.append(item)
    
    # Show fractional items first
    if fractional_items:
        print('\n🔴 Items with FRACTIONAL quantities (need updating):')
        print('-' * 70)
        for item in fractional_items:
            qty = float(item['quantity'])
            print(f"{item['product_name'][:35]:<35} {qty:>10.2f} {item['unit_of_measurement']}")
    
    # Show some whole number items
    print('\n✅ Items with WHOLE number quantities (first 20):')
    print('-' * 70)
    for item in whole_items[:20]:
        qty = int(item['quantity'])
        print(f"{item['product_name'][:35]:<35} {qty:>10} {item['unit_of_measurement']}")
    
    print('-' * 70)
    print(f'\nSummary:')
    print(f'  Total items: {len(items)}')
    print(f'  Fractional quantities: {fractional_count}')
    print(f'  Whole quantities: {len(whole_items)}')
    
    await conn.close()

asyncio.run(check_quantities())