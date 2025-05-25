import asyncio
import httpx
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

async def test_user_flow():
    # Create a test client
    async with httpx.AsyncClient() as client:
        # Test creating a new user
        print("Testing user creation...")
        user_data = {
            "email": "samantha.smith@example.com",
            "first_name": "Samantha",
            "last_name": "Smith",
            "password": "testpassword123",
            "is_admin": True
        }
        
        # Create user
        response = await client.post(
            f"{BASE_URL}/users/",
            json=user_data
        )
        print(f"Create user response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        # Get token
        print("\nTesting login...")
        login_data = {
            "username": "samantha.smith@example.com",
            "password": "testpassword123"
        }
        
        # Get token
        response = await client.post(
            f"{BASE_URL}/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login response: {response.status_code}")
        token = response.json().get("access_token")
        
        # Get current user
        print("\nTesting get current user...")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"{BASE_URL}/users/me",
            headers=headers
        )
        print(f"Get current user response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        # Get user by ID
        user_id = response.json().get("id")
        print(f"\nTesting get user by ID: {user_id}")
        response = await client.get(
            f"{BASE_URL}/users/{user_id}",
            headers=headers
        )
        print(f"Get user by ID response: {response.status_code}")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(test_user_flow())
