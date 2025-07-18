"""Load testing for PrepSense API with Locust"""
from locust import HttpUser, task, between
import json
import random


class PrepSenseUser(HttpUser):
    """Simulated user for load testing PrepSense API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize test data for each user"""
        self.user_id = random.randint(1, 1000)
        self.conversation_id = f"load-test-{self.user_id}-{random.randint(1000, 9999)}"
        
        # Common test messages
        self.test_messages = [
            "What can I make for dinner?",
            "I need a quick lunch recipe",
            "What's good for breakfast?",
            "I want to use my chicken and rice",
            "Show me vegetarian options",
            "I need something healthy",
            "What can I make with what I have?",
            "I'm craving something spicy",
            "Quick snack ideas?",
            "Family dinner suggestions"
        ]
    
    @task(10)
    def get_recipe_recommendations(self):
        """Main task: Get recipe recommendations via chat"""
        message = random.choice(self.test_messages)
        
        payload = {
            "user_id": self.user_id,
            "message": message,
            "conversation_id": self.conversation_id
        }
        
        with self.client.post("/chat/", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "message" in data and "recipes" in data:
                        response.success()
                    else:
                        response.failure("Response missing required fields")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(5)
    def get_pantry_items(self):
        """Secondary task: Get user's pantry items"""
        with self.client.get(f"/pantry/?user_id={self.user_id}", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Pantry response should be a list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def get_recipes(self):
        """Tertiary task: Get recipes"""
        with self.client.get(f"/recipes/?user_id={self.user_id}", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Recipes response should be a list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def add_pantry_item(self):
        """Occasional task: Add a pantry item"""
        test_items = [
            {"product_name": "Chicken Breast", "quantity": 2, "unit": "lbs"},
            {"product_name": "Rice", "quantity": 3, "unit": "cups"},
            {"product_name": "Milk", "quantity": 1, "unit": "gallon"},
            {"product_name": "Eggs", "quantity": 12, "unit": "count"},
            {"product_name": "Bread", "quantity": 1, "unit": "loaf"},
        ]
        
        item = random.choice(test_items)
        item["user_id"] = self.user_id
        item["expiration_date"] = "2024-12-31"
        
        with self.client.post("/pantry/", json=item, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Light task: Health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class CrewAIIntensiveUser(HttpUser):
    """User focused on testing CrewAI-intensive operations"""
    
    wait_time = between(2, 5)  # Longer wait time for AI operations
    
    def on_start(self):
        self.user_id = random.randint(2000, 3000)
        self.conversation_id = f"ai-test-{self.user_id}"
        
        # Complex messages that require more AI processing
        self.complex_messages = [
            "I have chicken, rice, and vegetables. What's a healthy dinner recipe that my kids will like?",
            "I'm diabetic and need a low-carb meal using ingredients that expire soon",
            "Plan a week of vegetarian meals for a family of 4 with a $50 budget",
            "I need a high-protein breakfast that takes less than 10 minutes to make",
            "What can I make with leftover ingredients from last night's dinner?",
            "I'm having guests over and need an impressive meal using pantry staples",
            "Suggest meals for someone with gluten intolerance and nut allergies",
            "I want to meal prep for the week - what are good batch cooking recipes?",
        ]
    
    @task(8)
    def complex_recipe_request(self):
        """Test complex recipe recommendations that stress the AI system"""
        message = random.choice(self.complex_messages)
        
        payload = {
            "user_id": self.user_id,
            "message": message,
            "conversation_id": self.conversation_id
        }
        
        # Set longer timeout for AI-intensive operations
        with self.client.post("/chat/", json=payload, catch_response=True, timeout=30) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "message" in data and "recipes" in data and len(data["recipes"]) > 0:
                        response.success()
                    else:
                        response.failure("AI response incomplete")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 408:
                response.failure("AI processing timeout")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def followup_questions(self):
        """Test follow-up questions in the same conversation"""
        followup_messages = [
            "Can you make that recipe vegetarian?",
            "What if I don't have that ingredient?",
            "How can I make this healthier?",
            "Can you suggest a side dish?",
            "What's a good dessert to go with this?",
        ]
        
        message = random.choice(followup_messages)
        
        payload = {
            "user_id": self.user_id,
            "message": message,
            "conversation_id": self.conversation_id
        }
        
        with self.client.post("/chat/", json=payload, catch_response=True, timeout=20) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


# Custom test scenarios
class StressTestUser(HttpUser):
    """User for stress testing edge cases"""
    
    wait_time = between(0.5, 1.5)  # Faster requests for stress testing
    
    def on_start(self):
        self.user_id = random.randint(5000, 6000)
        self.request_count = 0
    
    @task(5)
    def rapid_chat_requests(self):
        """Send rapid chat requests to test system under load"""
        self.request_count += 1
        
        payload = {
            "user_id": self.user_id,
            "message": f"Quick test request #{self.request_count}",
            "conversation_id": f"stress-{self.user_id}-{self.request_count}"
        }
        
        with self.client.post("/chat/", json=payload, catch_response=True, timeout=10) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def concurrent_pantry_operations(self):
        """Test concurrent pantry operations"""
        # Random pantry operation
        operations = [
            ("GET", f"/pantry/?user_id={self.user_id}"),
            ("POST", "/pantry/", {
                "user_id": self.user_id,
                "product_name": f"Test Item {random.randint(1, 100)}",
                "quantity": random.randint(1, 5),
                "unit": "units"
            })
        ]
        
        method, url, *data = random.choice(operations)
        
        if method == "GET":
            with self.client.get(url, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"HTTP {response.status_code}")
        else:
            with self.client.post(url, json=data[0], catch_response=True) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"HTTP {response.status_code}")


# Running instructions:
# 
# Basic load test:
# locust -H http://localhost:8000 -u 50 -r 10 --run-time 1m
# 
# AI-intensive test:
# locust -H http://localhost:8000 -u 20 -r 5 --run-time 2m --locustfile locustfile.py CrewAIIntensiveUser
# 
# Stress test:
# locust -H http://localhost:8000 -u 100 -r 20 --run-time 30s --locustfile locustfile.py StressTestUser
# 
# Performance criteria:
# - Mean response time < 1.5s for normal requests
# - Mean response time < 5s for AI-intensive requests  
# - P95 response time < 3s for normal requests
# - P95 response time < 10s for AI-intensive requests
# - Error rate < 1% under normal load
# - Error rate < 5% under stress load