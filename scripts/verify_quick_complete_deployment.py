#!/usr/bin/env python3
"""
Deployment verification script for Quick Complete feature
Tests all endpoints and integration points to ensure production readiness
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

class QuickCompleteVerifier:
    """Comprehensive verification of Quick Complete implementation"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "performance_metrics": {},
            "started_at": datetime.now().isoformat(),
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """Log test result"""
        self.results["tests_run"] += 1
        
        if passed:
            self.results["tests_passed"] += 1
            status = "✅ PASS"
        else:
            self.results["tests_failed"] += 1
            status = "❌ FAIL"
            self.results["errors"].append(f"{test_name}: {details}")
        
        print(f"{status} | {test_name:<40} | {duration:>6.2f}s | {details}")
        
        if duration > 0:
            self.results["performance_metrics"][test_name] = duration
    
    async def test_health_check(self) -> bool:
        """Test basic API health"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test("API Health Check", True, f"Status: {data.get('status', 'unknown')}", duration)
                    return True
                else:
                    self.log_test("API Health Check", False, f"HTTP {response.status}", duration)
                    return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {e}")
            return False
    
    async def test_check_ingredients_endpoint(self) -> bool:
        """Test /recipe-consumption/check-ingredients endpoint"""
        try:
            start_time = time.time()
            
            payload = {
                "user_id": 111,
                "recipe_id": 716429,  # Real Spoonacular recipe
                "servings": 1
            }
            
            async with self.session.post(
                f"{self.base_url}/recipe-consumption/check-ingredients",
                json=payload
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    if "ingredients" in data and isinstance(data["ingredients"], list):
                        
                        # Check first ingredient structure if available
                        if data["ingredients"]:
                            ingredient = data["ingredients"][0]
                            required_fields = [
                                "ingredient_name", "required_quantity", "required_unit",
                                "pantry_matches", "status"
                            ]
                            
                            missing_fields = [field for field in required_fields if field not in ingredient]
                            
                            if not missing_fields:
                                self.log_test(
                                    "Check Ingredients Endpoint",
                                    True,
                                    f"Found {len(data['ingredients'])} ingredients",
                                    duration
                                )
                                return True
                            else:
                                self.log_test(
                                    "Check Ingredients Endpoint",
                                    False,
                                    f"Missing fields: {missing_fields}",
                                    duration
                                )
                                return False
                        else:
                            self.log_test(
                                "Check Ingredients Endpoint",
                                True,
                                "No ingredients found (expected for some recipes)",
                                duration
                            )
                            return True
                    else:
                        self.log_test(
                            "Check Ingredients Endpoint",
                            False,
                            "Invalid response structure",
                            duration
                        )
                        return False
                else:
                    self.log_test(
                        "Check Ingredients Endpoint",
                        False,
                        f"HTTP {response.status}",
                        duration
                    )
                    return False
        except Exception as e:
            self.log_test("Check Ingredients Endpoint", False, f"Error: {e}")
            return False
    
    async def test_quick_complete_endpoint(self) -> bool:
        """Test /recipe-consumption/quick-complete endpoint"""
        try:
            start_time = time.time()
            
            payload = {
                "user_id": 111,
                "recipe_id": 716429,
                "servings": 1,
                "ingredient_selections": [
                    {
                        "ingredient_name": "test_ingredient",
                        "pantry_item_id": 999999,  # Non-existent item
                        "quantity_to_use": 1.0,
                        "unit": "count"
                    }
                ]
            }
            
            async with self.session.post(
                f"{self.base_url}/recipe-consumption/quick-complete",
                json=payload
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = [
                        "success", "message", "completion_record",
                        "updated_items", "depleted_items", "errors"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        # Should fail because item doesn't exist, but endpoint should work
                        if data["success"] is False and data["errors"]:
                            self.log_test(
                                "Quick Complete Endpoint",
                                True,
                                f"Correctly handled missing item error",
                                duration
                            )
                            return True
                        else:
                            self.log_test(
                                "Quick Complete Endpoint",
                                False,
                                "Should have failed with missing item error",
                                duration
                            )
                            return False
                    else:
                        self.log_test(
                            "Quick Complete Endpoint",
                            False,
                            f"Missing fields: {missing_fields}",
                            duration
                        )
                        return False
                else:
                    self.log_test(
                        "Quick Complete Endpoint",
                        False,
                        f"HTTP {response.status}",
                        duration
                    )
                    return False
        except Exception as e:
            self.log_test("Quick Complete Endpoint", False, f"Error: {e}")
            return False
    
    async def test_endpoint_performance(self) -> bool:
        """Test endpoint performance under multiple requests"""
        try:
            payload = {
                "user_id": 111,
                "recipe_id": 716429,
                "servings": 1
            }
            
            # Run 5 concurrent requests
            start_time = time.time()
            tasks = [
                self.session.post(
                    f"{self.base_url}/recipe-consumption/check-ingredients",
                    json=payload
                ) for _ in range(5)
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            successful_responses = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
            
            # Close responses
            for response in responses:
                if hasattr(response, 'close'):
                    response.close()
            
            if successful_responses >= 4:  # Allow 1 failure
                avg_time = duration / 5
                self.log_test(
                    "Performance Test (5 concurrent)",
                    True,
                    f"{successful_responses}/5 successful, avg {avg_time:.2f}s",
                    duration
                )
                return True
            else:
                self.log_test(
                    "Performance Test (5 concurrent)",
                    False,
                    f"Only {successful_responses}/5 successful",
                    duration
                )
                return False
        except Exception as e:
            self.log_test("Performance Test", False, f"Error: {e}")
            return False
    
    async def test_pantry_service_integration(self) -> bool:
        """Test pantry service availability"""
        try:
            start_time = time.time()
            
            # Test basic pantry endpoint
            async with self.session.get(f"{self.base_url}/pantry/user/111/items") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Pantry Service Integration",
                        True,
                        f"Retrieved {len(data) if isinstance(data, list) else 'unknown'} items",
                        duration
                    )
                    return True
                else:
                    self.log_test(
                        "Pantry Service Integration",
                        False,
                        f"HTTP {response.status}",
                        duration
                    )
                    return False
        except Exception as e:
            self.log_test("Pantry Service Integration", False, f"Error: {e}")
            return False
    
    async def test_spoonacular_service_integration(self) -> bool:
        """Test Spoonacular service availability"""
        try:
            start_time = time.time()
            
            # Test recipe information endpoint
            async with self.session.get(f"{self.base_url}/recipes/716429/information") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Spoonacular Service Integration",
                        True,
                        f"Recipe: {data.get('title', 'Unknown')}",
                        duration
                    )
                    return True
                else:
                    self.log_test(
                        "Spoonacular Service Integration",
                        False,
                        f"HTTP {response.status}",
                        duration
                    )
                    return False
        except Exception as e:
            self.log_test("Spoonacular Service Integration", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive verification suite"""
        print("=" * 80)
        print("🧪 QUICK COMPLETE DEPLOYMENT VERIFICATION")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Started: {self.results['started_at']}")
        print("=" * 80)
        print(f"{'STATUS':<6} | {'TEST NAME':<40} | {'TIME':<6} | DETAILS")
        print("-" * 80)
        
        # Core API tests
        await self.test_health_check()
        await self.test_pantry_service_integration()
        await self.test_spoonacular_service_integration()
        
        # Quick Complete specific tests
        await self.test_check_ingredients_endpoint()
        await self.test_quick_complete_endpoint()
        
        # Performance tests
        await self.test_endpoint_performance()
        
        # Calculate results
        self.results["completed_at"] = datetime.now().isoformat()
        self.results["success_rate"] = (
            self.results["tests_passed"] / self.results["tests_run"] * 100
            if self.results["tests_run"] > 0 else 0
        )
        
        print("-" * 80)
        print(f"📊 RESULTS: {self.results['tests_passed']}/{self.results['tests_run']} tests passed "
              f"({self.results['success_rate']:.1f}%)")
        
        if self.results["errors"]:
            print("\n❌ ERRORS:")
            for error in self.results["errors"]:
                print(f"   {error}")
        
        if self.results["performance_metrics"]:
            print("\n⚡ PERFORMANCE:")
            for test, duration in self.results["performance_metrics"].items():
                print(f"   {test}: {duration:.2f}s")
        
        print("=" * 80)
        
        if self.results["success_rate"] >= 80:
            print("✅ DEPLOYMENT VERIFICATION: PASSED")
            print("🚀 Quick Complete feature is ready for production!")
        else:
            print("❌ DEPLOYMENT VERIFICATION: FAILED")
            print("🔧 Issues must be resolved before deployment")
        
        print("=" * 80)
        
        return self.results


async def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify Quick Complete deployment")
    parser.add_argument("--url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument("--output", help="Output results to JSON file")
    
    args = parser.parse_args()
    
    async with QuickCompleteVerifier(args.url) as verifier:
        results = await verifier.run_all_tests()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📁 Results saved to: {args.output}")
        
        return results["success_rate"] >= 80


if __name__ == "__main__":
    import sys
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        sys.exit(1)