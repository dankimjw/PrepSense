#!/usr/bin/env python3
"""Test script to verify user preferences sync between frontend and backend."""

import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1"
USER_ID = 111

def test_preferences_sync():
    """Test the preferences sync functionality."""
    
    print("=" * 60)
    print("TESTING USER PREFERENCES SYNC")
    print("=" * 60)
    
    # Step 1: Get current preferences
    print("\n1. Getting current preferences from backend...")
    try:
        response = requests.get(
            f"{BASE_URL}/preferences",
            headers={"X-User-Id": str(USER_ID)}
        )
        
        if response.status_code == 200:
            current_prefs = response.json()
            print(f"   Current preferences: {json.dumps(current_prefs, indent=2)}")
        else:
            print(f"   No existing preferences (status: {response.status_code})")
            current_prefs = {}
    except Exception as e:
        print(f"   Error getting preferences: {e}")
        current_prefs = {}
    
    # Step 2: Simulate adding "Peanuts" as an allergen
    print("\n2. Simulating adding 'Peanuts' as an allergen...")
    
    # Get existing allergens or start with empty list
    existing_allergens = current_prefs.get("allergens", [])
    
    # Add Peanuts if not already present
    if "Peanuts" not in existing_allergens:
        existing_allergens.append("Peanuts")
    
    # Prepare the payload (matching frontend structure)
    payload = {
        "allergens": existing_allergens,
        "dietary_restrictions": current_prefs.get("dietary_restrictions", []),
        "cuisine_preferences": current_prefs.get("cuisine_preferences", []),
        "household_size": current_prefs.get("household_size", 1)
    }
    
    print(f"   Sending payload: {json.dumps(payload, indent=2)}")
    
    # Step 3: Send POST request to save preferences
    try:
        response = requests.post(
            f"{BASE_URL}/preferences",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-User-Id": str(USER_ID)
            }
        )
        
        print(f"\n3. Save response:")
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            print("   ✅ Preferences saved successfully!")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error saving preferences: {e}")
    
    # Step 4: Verify the preferences were saved
    print("\n4. Verifying preferences were saved...")
    time.sleep(1)  # Small delay to ensure save is complete
    
    try:
        response = requests.get(
            f"{BASE_URL}/preferences",
            headers={"X-User-Id": str(USER_ID)}
        )
        
        if response.status_code == 200:
            saved_prefs = response.json()
            print(f"   Saved preferences: {json.dumps(saved_prefs, indent=2)}")
            
            # Check if Peanuts is in allergens
            if "allergens" in saved_prefs and "Peanuts" in saved_prefs["allergens"]:
                print("\n   ✅ SUCCESS: 'Peanuts' allergen was saved to backend!")
            else:
                print("\n   ❌ FAILED: 'Peanuts' allergen was not found in saved preferences")
        else:
            print(f"   ❌ Error getting saved preferences: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error verifying preferences: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_preferences_sync()
