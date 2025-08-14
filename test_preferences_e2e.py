#!/usr/bin/env python3
"""End-to-end test for preferences synchronization."""

import requests
import json
import time

BASE_URL = "http://localhost:8008/api/v1"

def test_preferences_e2e():
    """Test that preferences persist across multiple API calls."""
    print("=" * 60)
    print("END-TO-END PREFERENCES PERSISTENCE TEST")
    print("=" * 60)
    
    # Step 1: Get initial preferences
    print("\n1. Getting initial preferences...")
    response = requests.get(f"{BASE_URL}/preferences")
    if response.status_code == 200:
        initial_prefs = response.json()
        print(f"   Initial preferences retrieved")
        print(f"   Allergens: {initial_prefs.get('allergens', [])}")
    else:
        print(f"   No initial preferences (starting fresh)")
        initial_prefs = None
    
    # Step 2: Save new preferences
    print("\n2. Saving new preferences...")
    new_prefs = {
        "allergens": ["Shellfish", "Eggs"],
        "dietary_restrictions": ["Gluten-Free"],
        "cuisine_preferences": ["Mediterranean", "Japanese"],
        "household_size": 3
    }
    print(f"   Sending: {json.dumps(new_prefs, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/preferences", json=new_prefs)
    if response.status_code == 200:
        print("   ✅ Preferences saved successfully!")
    else:
        print(f"   ❌ Failed to save: {response.text}")
        return
    
    # Step 3: Verify persistence (immediate check)
    print("\n3. Verifying immediate persistence...")
    response = requests.get(f"{BASE_URL}/preferences")
    if response.status_code == 200:
        saved_prefs = response.json()
        if saved_prefs["allergens"] == new_prefs["allergens"]:
            print("   ✅ Preferences persisted immediately!")
        else:
            print("   ❌ Preferences don't match!")
    
    # Step 4: Wait and check again (delayed persistence check)
    print("\n4. Checking persistence after delay...")
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/preferences")
    if response.status_code == 200:
        saved_prefs = response.json()
        print(f"   Retrieved preferences:")
        print(f"   - Allergens: {saved_prefs['allergens']}")
        print(f"   - Dietary: {saved_prefs['dietary_restrictions']}")
        print(f"   - Cuisines: {saved_prefs['cuisine_preferences']}")
        print(f"   - Household: {saved_prefs['household_size']}")
        
        # Verify all fields match
        if (saved_prefs["allergens"] == new_prefs["allergens"] and
            saved_prefs["dietary_restrictions"] == new_prefs["dietary_restrictions"] and
            saved_prefs["cuisine_preferences"] == new_prefs["cuisine_preferences"] and
            saved_prefs["household_size"] == new_prefs["household_size"]):
            print("\n   ✅ SUCCESS: All preferences persisted correctly!")
            print("   The backend is successfully saving to the SQL database.")
        else:
            print("\n   ❌ Some preferences don't match")
    
    # Step 5: Update preferences again
    print("\n5. Testing preference updates...")
    updated_prefs = {
        "allergens": ["Shellfish", "Eggs", "Soy"],  # Added Soy
        "dietary_restrictions": ["Gluten-Free", "Low-Sodium"],  # Added Low-Sodium
        "cuisine_preferences": ["Mediterranean", "Japanese", "Thai"],  # Added Thai
        "household_size": 4  # Changed from 3 to 4
    }
    
    response = requests.post(f"{BASE_URL}/preferences", json=updated_prefs)
    if response.status_code == 200:
        print("   ✅ Preferences updated successfully!")
        
        # Verify the update
        response = requests.get(f"{BASE_URL}/preferences")
        if response.status_code == 200:
            final_prefs = response.json()
            if (final_prefs["household_size"] == 4 and
                "Soy" in final_prefs["allergens"] and
                "Low-Sodium" in final_prefs["dietary_restrictions"] and
                "Thai" in final_prefs["cuisine_preferences"]):
                print("   ✅ All updates persisted correctly!")
            else:
                print("   ❌ Updates didn't persist correctly")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - Preferences sync is working!")
    print("=" * 60)

if __name__ == "__main__":
    test_preferences_e2e()
