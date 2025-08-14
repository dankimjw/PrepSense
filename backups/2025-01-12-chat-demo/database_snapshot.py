#!/usr/bin/env python3
"""
Database snapshot for user 111
Date: January 12, 2025
"""
import asyncio
import asyncpg
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def create_snapshot():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database='prepsense',
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    try:
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'user_id': 111,
            'pantry_items': [],
            'saved_recipes': [],
            'user_preferences': {}
        }
        
        # Get pantry items
        pantry_items = await conn.fetch("""
            SELECT pi.* 
            FROM pantry_items pi
            WHERE pi.pantry_id = 1
            AND pi.status = 'available'
            ORDER BY pi.product_name
        """)
        
        for item in pantry_items:
            snapshot['pantry_items'].append({
                'pantry_item_id': item['pantry_item_id'],
                'product_name': item['product_name'],
                'quantity': float(item['quantity']),
                'unit': item['unit_of_measurement'],
                'category': item['category'],
                'expiration_date': item['expiration_date'].isoformat() if item['expiration_date'] else None
            })
        
        # Get saved recipes
        saved_recipes = await conn.fetch("""
            SELECT recipe_id, recipe_title, created_at
            FROM user_recipes
            WHERE user_id = 111
            ORDER BY created_at DESC
        """)
        
        for recipe in saved_recipes:
            snapshot['saved_recipes'].append({
                'recipe_id': recipe['recipe_id'],
                'recipe_title': recipe['recipe_title'],
                'created_at': recipe['created_at'].isoformat() if recipe['created_at'] else None
            })
        
        # Get user preferences
        preferences = await conn.fetchrow("""
            SELECT preferences, household_size
            FROM user_preferences
            WHERE user_id = 111
        """)
        
        if preferences and preferences['preferences']:
            prefs_data = preferences['preferences']
            snapshot['user_preferences'] = {
                'household_size': preferences['household_size'],
                'dietary_preferences': prefs_data.get('dietary_preferences', []),
                'allergens': prefs_data.get('allergens', []),
                'cuisine_preferences': prefs_data.get('cuisine_preferences', [])
            }
        
        # Save snapshot to file
        snapshot_file = 'database_snapshot.json'
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"✅ Database snapshot created: {snapshot_file}")
        print(f"\n📊 Summary:")
        print(f"  - Pantry items: {len(snapshot['pantry_items'])}")
        print(f"  - Saved recipes: {len(snapshot['saved_recipes'])}")
        print(f"  - Has preferences: {'Yes' if snapshot['user_preferences'] else 'No'}")
        
        return snapshot
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_snapshot())