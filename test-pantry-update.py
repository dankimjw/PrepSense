#!/usr/bin/env python3
"""
Test script to verify pantry item updates are working correctly
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
USER_ID = 111

def test_pantry_update():
    # First, get all pantry items
    print("1. Fetching all pantry items...")
    response = requests.get(f"{BASE_URL}/pantry/user/{USER_ID}/full")
    
    if response.status_code != 200:
        print(f"Failed to fetch pantry items: {response.status_code}")
        return
    
    items = response.json()
    print(f"Found {len(items)} items")
    
    if not items:
        print("No items found. Please add some items first.")
        return
    
    # Take the first item
    test_item = items[0]
    item_id = test_item.get('pantry_item_id')
    
    print(f"\n2. Testing update on item: {test_item.get('product_name')} (ID: {item_id})")
    print(f"   Current values:")
    print(f"   - Name: {test_item.get('product_name')}")
    print(f"   - Quantity: {test_item.get('quantity')} {test_item.get('unit_of_measurement')}")
    print(f"   - Category: {test_item.get('category')}")
    print(f"   - Expiration: {test_item.get('expiration_date')}")
    
    # Update the item
    quantity_str = test_item.get('quantity', '1')
    quantity_value = float(quantity_str.replace(',', ''))
    
    update_data = {
        "product_name": f"{test_item.get('product_name')} - UPDATED",
        "quantity": quantity_value + 1,
        "unit_of_measurement": test_item.get('unit_of_measurement', 'unit'),
        "category": "Test",
        "expiration_date": "2025-12-31"
    }
    
    print(f"\n3. Updating item with new values...")
    print(f"   - Name: {update_data['product_name']}")
    print(f"   - Quantity: {update_data['quantity']} {update_data['unit_of_measurement']}")
    print(f"   - Category: {update_data['category']}")
    print(f"   - Expiration: {update_data['expiration_date']}")
    
    # Send update request
    response = requests.put(
        f"{BASE_URL}/pantry/items/{item_id}",
        json=update_data
    )
    
    if response.status_code != 200:
        print(f"Failed to update item: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    updated_item = response.json()
    print("\n4. Update response received:")
    print(json.dumps(updated_item, indent=2))
    
    # Verify the update by fetching again
    time.sleep(1)  # Small delay
    print("\n5. Fetching item again to verify update...")
    response = requests.get(f"{BASE_URL}/pantry/user/{USER_ID}/full")
    
    if response.status_code == 200:
        items = response.json()
        for item in items:
            if item.get('pantry_item_id') == item_id:
                print("   Updated item found:")
                print(f"   - Name: {item.get('product_name')}")
                print(f"   - Quantity: {item.get('quantity')} {item.get('unit_of_measurement')}")
                print(f"   - Category: {item.get('category')}")
                print(f"   - Expiration: {item.get('expiration_date')}")
                
                # Check if updates were applied
                if item.get('product_name') == update_data['product_name']:
                    print("\n✅ Name update: SUCCESS")
                else:
                    print("\n❌ Name update: FAILED")
                
                item_quantity = float(item.get('quantity', '0').replace(',', ''))
                if item_quantity == update_data['quantity']:
                    print("✅ Quantity update: SUCCESS")
                else:
                    print(f"❌ Quantity update: FAILED (expected {update_data['quantity']}, got {item_quantity})")
                    
                if item.get('category') == update_data['category']:
                    print("✅ Category update: SUCCESS")
                else:
                    print("❌ Category update: FAILED")
                    
                if item.get('expiration_date') == update_data['expiration_date']:
                    print("✅ Expiration date update: SUCCESS")
                else:
                    print("❌ Expiration date update: FAILED")
                
                break
    
    print("\n6. Testing field name mapping...")
    print("   API returns these field names:")
    print("   - pantry_item_id (should map to 'id' in UI)")
    print("   - product_name (should map to 'item_name' in UI)")
    print("   - quantity (should map to 'quantity_amount' in UI)")
    print("   - unit_of_measurement (should map to 'quantity_unit' in UI)")
    print("   - expiration_date (should map to 'expected_expiration' in UI)")

if __name__ == "__main__":
    test_pantry_update()