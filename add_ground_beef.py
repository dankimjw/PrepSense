#!/usr/bin/env python3
"""
Add ground beef item to user 111's pantry at the top of the list
"""
import json
import subprocess
from datetime import datetime, timedelta

def add_ground_beef():
    """Add ground beef via API call with early expiration to appear at top"""
    
    # Create ground beef with tomorrow's date so it appears at the top (expires soon)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    pantry_item = {
        "product_name": "Ground Beef",
        "quantity": 1.0,
        "unit_of_measurement": "lb",
        "expiration_date": tomorrow,
        "category": "Proteins"
    }
    
    curl_cmd = [
        "curl", "-X", "POST",
        "http://localhost:8001/api/v1/pantry/user/111/items",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(pantry_item),
        "-s"
    ]
    
    print("Adding Ground Beef to pantry...")
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            print(f"✓ Successfully added Ground Beef")
            print(f"Response: {response}")
            return True
        except json.JSONDecodeError:
            print(f"✓ Added Ground Beef (response: {result.stdout})")
            return True
    else:
        print(f"✗ Failed to add Ground Beef")
        print(f"Error: {result.stderr}")
        print(f"Response: {result.stdout}")
        return False

def main():
    success = add_ground_beef()
    
    if success:
        print("\n🎉 Ground Beef has been added to your pantry!")
        print("It will appear at the top due to its early expiration date.")
    else:
        print("\n❌ Failed to add Ground Beef. Please check the backend is running.")

if __name__ == "__main__":
    main()