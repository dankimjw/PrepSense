#!/usr/bin/env python3
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from backend_gateway.config.database import get_database_service, get_pantry_service

async def get_pantry_items_for_user(user_id: int):
    """Retrieve all pantry items for a specific user"""
    
    # Initialize services using the proper configuration
    db_service = get_database_service()
    pantry_service = get_pantry_service()
    
    try:
        # Get pantry items
        items = await pantry_service.get_user_pantry_items(user_id)
        
        print(f"\n=== Pantry Items for User {user_id} ===")
        print(f"Total items: {len(items)}\n")
        
        if items:
            # Display items in a formatted way
            for i, item in enumerate(items, 1):
                print(f"Item #{i}:")
                print(f"  Name: {item.get('product_name', 'N/A')}")
                print(f"  Brand: {item.get('brand_name', 'N/A')}")
                print(f"  Category: {item.get('category', 'N/A')}")
                print(f"  Quantity: {item.get('quantity', 0)} {item.get('unit_of_measurement', '')}")
                print(f"  Status: {item.get('status', 'N/A')}")
                print(f"  Expiration: {item.get('expiration_date', 'N/A')}")
                print(f"  Pantry Item ID: {item.get('pantry_item_id')}")
                print(f"  Created: {item.get('pantry_item_created_at', 'N/A')}")
                print("-" * 50)
        else:
            print("No pantry items found for this user.")
            
    except Exception as e:
        print(f"Error retrieving pantry items: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        db_service.close()

if __name__ == "__main__":
    asyncio.run(get_pantry_items_for_user(111))