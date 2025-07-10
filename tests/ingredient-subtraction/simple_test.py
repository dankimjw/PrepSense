#!/usr/bin/env python3
"""
Simple test runner that uses urllib instead of requests
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
USER_ID = 111

def make_request(endpoint, data):
    """Make POST request using urllib"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Convert data to JSON
    json_data = json.dumps(data).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        # Make request
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_test(test_name, payload):
    """Run a single test"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    result = make_request("/pantry/recipe/complete", payload)
    
    if result:
        print(f"\n📥 Response:")
        print(json.dumps(result, indent=2))
        print("✅ Test completed")
    else:
        print("❌ Test failed")
    
    return result

def main():
    print("PrepSense Ingredient Subtraction Tests")
    print("=====================================")
    
    # Check if server is running
    try:
        response = urllib.request.urlopen(f"{API_BASE_URL}/health")
        print("✅ Backend server is running")
    except:
        print("❌ Backend server is not running!")
        print("Please start it with: python run_app.py")
        sys.exit(1)
    
    # Test 1: Basic Subtraction
    run_test(
        "Test 1: Basic Pasta Subtraction",
        {
            "user_id": USER_ID,
            "recipe_name": "Simple Pasta Test",
            "ingredients": [
                {
                    "ingredient_name": "pasta",
                    "quantity": 200,
                    "unit": "g"
                }
            ]
        }
    )
    
    # Test 2: Unit Conversion
    run_test(
        "Test 2: Milk Cup to ML Conversion",
        {
            "user_id": USER_ID,
            "recipe_name": "Baking Test",
            "ingredients": [
                {
                    "ingredient_name": "milk",
                    "quantity": 1,
                    "unit": "cup"
                }
            ]
        }
    )
    
    # Test 3: Missing Ingredient
    run_test(
        "Test 3: Missing Ingredient (Saffron)",
        {
            "user_id": USER_ID,
            "recipe_name": "Exotic Recipe",
            "ingredients": [
                {
                    "ingredient_name": "saffron",
                    "quantity": 1,
                    "unit": "g"
                }
            ]
        }
    )
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()