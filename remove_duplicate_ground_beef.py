#!/usr/bin/env python3
"""
Remove duplicate Ground Beef items, keeping only one with the correct quantity
"""
import requests
import json

def remove_duplicate_ground_beef():
    """Remove one of the duplicate Ground Beef items"""
    
    # Get current Ground Beef items
    print("Checking current Ground Beef items...")
    pantry_response = requests.get("http://localhost:8001/api/v1/pantry/user/111/full")
    if pantry_response.status_code != 200:
        print("Failed to get pantry items")
        return
        
    items = pantry_response.json()
    ground_beef_items = [item for item in items if 'ground beef' in item.get('product_name', '').lower()]
    
    print(f"Found {len(ground_beef_items)} Ground Beef items:")
    for item in ground_beef_items:
        print(f"  ID {item['pantry_item_id']}: {item['quantity']} {item['unit_of_measurement']} (used: {item.get('used_quantity', 0)})")
    
    if len(ground_beef_items) <= 1:
        print("Only one Ground Beef item found, no duplicates to remove")
        return
        
    # Find the item that has been used and keep it
    used_item = None
    unused_items = []
    
    for item in ground_beef_items:
        if float(item.get('used_quantity', 0)) > 0:
            used_item = item
        else:
            unused_items.append(item)
    
    if not unused_items:
        print("No unused items to remove")
        return
        
    # Remove unused duplicates
    for item in unused_items:
        print(f"\nRemoving unused Ground Beef item {item['pantry_item_id']} ({item['quantity']} {item['unit_of_measurement']})")
        
        delete_response = requests.delete(
            f"http://localhost:8001/api/v1/pantry/items/{item['pantry_item_id']}"
        )
        
        if delete_response.status_code == 200:
            print(f"✓ Successfully removed item {item['pantry_item_id']}")
        else:
            print(f"✗ Failed to remove item {item['pantry_item_id']}: {delete_response.status_code} - {delete_response.text}")
    
    # Show final result
    print("\nFinal Ground Beef items:")
    final_response = requests.get("http://localhost:8001/api/v1/pantry/user/111/full")
    if final_response.status_code == 200:
        final_items = final_response.json()
        final_ground_beef = [item for item in final_items if 'ground beef' in item.get('product_name', '').lower()]
        
        for item in final_ground_beef:
            print(f"  ID {item['pantry_item_id']}: {item['quantity']} {item['unit_of_measurement']} (used: {item.get('used_quantity', 0)})")
    
    print("Done!")

if __name__ == "__main__":
    remove_duplicate_ground_beef()