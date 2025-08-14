#!/usr/bin/env python3
"""Test script to verify user preferences sync with proper authentication."""

import requests
import json
import time

BASE_URL = "http://localhost:8008/api/v1"

def test_preferences_sync_with_auth():
    """Test the preferences sync functionality with authentication."""
    
    print("=" * 60)
    print("TESTING USER PREFERENCES SYNC WITH AUTHENTICATION")
    print("=" * 60)
    
    # Step 1: Login to get auth token
    print("\n1. Logging in to get authentication token...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        if login_response.status_code == 200:
            auth_data = login_response.json()
            token = auth_data.get("access_token")
            user_id = auth_data.get("user", {}).get("numeric_user_id", 111)
            print(f"   ✅ Logged in successfully")
            print(f"   User ID: {user_id}")
            print(f"   Token: {token[:20]}..." if token else "   No token received")
        else:
            print(f"   ⚠️  Login failed with status {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            # Use mock token for testing
            token = "mock-admin-token-for-prototype"
            user_id = 111
            print(f"   Using mock token for testing")
    except Exception as e:
        print(f"   ⚠️  Login error: {e}")
        # Use mock token for testing
        token = "mock-admin-token-for-prototype"
        user_id = 111
        print(f"   Using mock token for testing")
    
    # Prepare headers with authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Step 2: Get current preferences
    print("\n2. Getting current preferences from backend...")
    try:
        response = requests.get(
            f"{BASE_URL}/preferences",
            headers=headers
        )
        
        if response.status_code == 200:
            current_prefs = response.json()
            print(f"   Current preferences: {json.dumps(current_prefs, indent=2)}")
        else:
            print(f"   No existing preferences (status: {response.status_code})")
            print(f"   Response: {response.text}")
            current_prefs = {}
    except Exception as e:
        print(f"   Error getting preferences: {e}")
        current_prefs = {}
    
    # Step 3: Simulate adding "Peanuts" as an allergen
    print("\n3. Simulating adding 'Peanuts' as an allergen...")
    
    # Get existing allergens or start with empty list
    existing_allergens = current_prefs.get("allergens", [])
    
    # Add Peanuts if not already present
    if "Peanuts" not in existing_allergens:
        existing_allergens.append("Peanuts")
        print("   Adding 'Peanuts' to allergens list")
    else:
        print("   'Peanuts' already in allergens list")
    
    # Prepare the payload (matching frontend structure)
    payload = {
        "allergens": existing_allergens,
        "dietary_restrictions": current_prefs.get("dietary_restrictions", []),
        "cuisine_preferences": current_prefs.get("cuisine_preferences", []),
        "household_size": current_prefs.get("household_size", 1)
    }
    
    print(f"   Sending payload: {json.dumps(payload, indent=2)}")
    
    # Step 4: Send POST request to save preferences
    print("\n4. Saving preferences to backend...")
    try:
        response = requests.post(
            f"{BASE_URL}/preferences",
            json=payload,
            headers=headers
        )
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            print("   ✅ Preferences saved successfully!")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error saving preferences: {e}")
    
    # Step 5: Verify the preferences were saved
    print("\n5. Verifying preferences were saved...")
    time.sleep(1)  # Small delay to ensure save is complete
    
    try:
        response = requests.get(
            f"{BASE_URL}/preferences",
            headers=headers
        )
        
        if response.status_code == 200:
            saved_prefs = response.json()
            print(f"   Saved preferences: {json.dumps(saved_prefs, indent=2)}")
            
            # Check if Peanuts is in allergens
            if "allergens" in saved_prefs and "Peanuts" in saved_prefs["allergens"]:
                print("\n   ✅ SUCCESS: 'Peanuts' allergen was saved to backend!")
                print("   The preferences sync is working correctly.")
            else:
                print("\n   ❌ FAILED: 'Peanuts' allergen was not found in saved preferences")
        else:
            print(f"   ❌ Error getting saved preferences: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error verifying preferences: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_preferences_sync_with_auth()
