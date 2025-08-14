#!/usr/bin/env python3
"""
Debug script to test recipe completion calculation with Ground Beef
"""
import requests
import json

def test_ground_beef_subtraction():
    """Test the recipe completion with Ground Beef to see the math"""
    
    # First, let's see the current Ground Beef quantity
    print("Checking current Ground Beef quantity...")
    pantry_response = requests.get("http://localhost:8001/api/v1/pantry/user/111/full")
    if pantry_response.status_code == 200:
        items = pantry_response.json()
        ground_beef_items = [item for item in items if 'ground beef' in item.get('product_name', '').lower()]
        
        for item in ground_beef_items:
            print(f"Found: {item['product_name']}")
            print(f"  Current quantity: {item['quantity']} {item['unit_of_measurement']}")
            print(f"  Pantry Item ID: {item['pantry_item_id']}")
    
    # Now test recipe completion
    print("\nTesting recipe completion with 2 lbs Ground Beef...")
    
    recipe_data = {
        "user_id": 111,
        "recipe_name": "Test Ground Beef Recipe",
        "ingredients": [
            {
                "ingredient_name": "Ground Beef", 
                "quantity": 2.0,
                "unit": "lb"
            }
        ]
    }
    
    print(f"Sending to API: {json.dumps(recipe_data, indent=2)}")
    
    # Complete the recipe using the correct endpoint
    completion_response = requests.post(
        "http://localhost:8001/api/v1/pantry/recipe/complete",
        json=recipe_data,
        headers={"Content-Type": "application/json"}
    )
    
    if completion_response.status_code == 200:
        result = completion_response.json()
        print(f"\nResponse: {json.dumps(result, indent=2)}")
        
        # Check updated quantities
        print("\nChecking updated Ground Beef quantities...")
        updated_response = requests.get("http://localhost:8001/api/v1/pantry/user/111/full")
        if updated_response.status_code == 200:
            updated_items = updated_response.json()
            updated_ground_beef = [item for item in updated_items if 'ground beef' in item.get('product_name', '').lower()]
            
            for item in updated_ground_beef:
                print(f"After cooking: {item['product_name']}")
                print(f"  New quantity: {item['quantity']} {item['unit_of_measurement']}")
                print(f"  Used quantity: {item.get('used_quantity', 0)}")
    else:
        print(f"Error: {completion_response.status_code} - {completion_response.text}")

if __name__ == "__main__":
    test_ground_beef_subtraction()