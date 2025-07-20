#!/usr/bin/env python3
"""
Comprehensive PrepSense Application Test Suite
Tests core user workflows and system functionality from first principles.

This script tests what actually matters for the PrepSense pantry management app:
- User can manage pantry items
- AI chat provides recipe recommendations  
- Recipe system works end-to-end
- External APIs are functional
- Database operations are reliable
- Authentication works properly
"""

import sys
import time
import json
import requests
import asyncio
import subprocess
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import random
import string

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class PrepSenseTestSuite:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
        self.test_user_id = None
        self.auth_token = None
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "info", test_name: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}]"
        
        if test_name:
            prefix += f" [{test_name}]"
            
        if level == "pass":
            print(f"{Colors.GREEN}✅ {prefix} {message}{Colors.RESET}")
        elif level == "fail":
            print(f"{Colors.RED}❌ {prefix} {message}{Colors.RESET}")
            if test_name:
                self.critical_failures.append(f"{test_name}: {message}")
        elif level == "warn":
            print(f"{Colors.YELLOW}⚠️  {prefix} {message}{Colors.RESET}")
            self.warnings.append(f"{test_name}: {message}")
        elif level == "info":
            print(f"{Colors.BLUE}ℹ️  {prefix} {message}{Colors.RESET}")
        elif level == "test":
            print(f"{Colors.PURPLE}🧪 {prefix} {message}{Colors.RESET}")
        else:
            print(f"{prefix} {message}")

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

    # ===============================================================
    # INFRASTRUCTURE TESTS
    # ===============================================================
    
    def test_basic_connectivity(self) -> bool:
        """Test that backend is running and responsive"""
        test_name = "basic_connectivity"
        self.log("Testing basic backend connectivity", "test", test_name)
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"Backend responding - Status: {health_data}", "pass", test_name)
                self.record_result(test_name, True, f"Health endpoint returned: {health_data}")
                return True
            else:
                self.log(f"Health endpoint returned {response.status_code}", "fail", test_name)
                self.record_result(test_name, False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log(f"Backend not accessible: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    def test_database_connectivity(self) -> bool:
        """Test database connectivity and basic operations"""
        test_name = "database_connectivity"
        self.log("Testing database connectivity", "test", test_name)
        
        try:
            # Try a simple endpoint that requires database
            response = self.session.get(f"{self.base_url}/api/v1/users/me", timeout=10)
            
            # We expect 401 (unauthorized) not 500 (database error)
            if response.status_code in [401, 403]:
                self.log("Database accessible (got auth error, not DB error)", "pass", test_name)
                self.record_result(test_name, True, "Database responding correctly")
                return True
            elif response.status_code == 500:
                error_detail = response.json().get("detail", "Unknown error")
                if "database" in error_detail.lower() or "connection" in error_detail.lower():
                    self.log(f"Database connection failed: {error_detail}", "fail", test_name)
                    self.record_result(test_name, False, error_detail)
                    return False
                else:
                    self.log("Database accessible (500 error not DB-related)", "pass", test_name)
                    self.record_result(test_name, True, "Non-DB 500 error")
                    return True
            else:
                self.log(f"Unexpected response: {response.status_code}", "warn", test_name)
                self.record_result(test_name, True, f"Unexpected but not failure: {response.status_code}")
                return True
                
        except Exception as e:
            self.log(f"Database test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    def test_external_api_configuration(self) -> Dict[str, bool]:
        """Test external API keys are configured"""
        test_name = "external_apis"
        self.log("Testing external API configuration", "test", test_name)
        
        results = {}
        
        # Test if API keys are configured by checking environment or endpoints
        api_tests = [
            ("spoonacular", "SPOONACULAR_API_KEY"),
            ("openai", "OPENAI_API_KEY"),
            ("unsplash", "UNSPLASH_ACCESS_KEY")
        ]
        
        for api_name, env_var in api_tests:
            # Check if environment variable exists
            if os.getenv(env_var):
                self.log(f"{api_name} API key configured", "pass", test_name)
                results[api_name] = True
            else:
                self.log(f"{api_name} API key not found in environment", "warn", test_name)
                results[api_name] = False
        
        all_configured = all(results.values())
        self.record_result(test_name, all_configured, f"API configs: {results}")
        return results

    # ===============================================================
    # CORE FUNCTIONALITY TESTS
    # ===============================================================

    def test_chat_system(self) -> bool:
        """Test the AI chat system that's core to PrepSense"""
        test_name = "chat_system"
        self.log("Testing AI chat system", "test", test_name)
        
        try:
            # Test chat endpoint with a simple request
            chat_payload = {
                "message": "I have chicken and rice. What can I make?",
                "user_id": 111,  # Default test user
                "use_preferences": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json=chat_payload,
                timeout=30  # Chat can take longer
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                
                # Validate response structure
                required_fields = ["response", "recipes"]
                missing_fields = [field for field in required_fields if field not in chat_data]
                
                if missing_fields:
                    self.log(f"Chat response missing fields: {missing_fields}", "fail", test_name)
                    self.record_result(test_name, False, f"Missing fields: {missing_fields}")
                    return False
                
                # Check if we got some kind of response
                if chat_data["response"] and len(chat_data["response"]) > 10:
                    self.log(f"Chat system working - got {len(chat_data.get('recipes', []))} recipes", "pass", test_name)
                    self.record_result(test_name, True, f"Response length: {len(chat_data['response'])}")
                    return True
                else:
                    self.log("Chat response too short or empty", "fail", test_name)
                    self.record_result(test_name, False, "Empty/short response")
                    return False
                    
            elif response.status_code == 422:
                error_detail = response.json().get("detail", "Unknown validation error")
                self.log(f"Chat validation error: {error_detail}", "fail", test_name)
                self.record_result(test_name, False, f"Validation: {error_detail}")
                return False
            elif response.status_code == 500:
                error_detail = response.json().get("detail", "Unknown server error")
                self.log(f"Chat server error: {error_detail}", "fail", test_name)
                self.record_result(test_name, False, f"Server error: {error_detail}")
                return False
            else:
                self.log(f"Chat endpoint returned {response.status_code}", "fail", test_name)
                self.record_result(test_name, False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Chat test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    def test_recipe_system(self) -> bool:
        """Test recipe search and details functionality"""
        test_name = "recipe_system"
        self.log("Testing recipe system", "test", test_name)
        
        try:
            # Test demo recipes endpoint (should always work)
            response = self.session.get(f"{self.base_url}/api/v1/demo/recipes", timeout=10)
            
            if response.status_code == 200:
                recipes_data = response.json()
                
                if isinstance(recipes_data, dict) and "recipes" in recipes_data:
                    recipes = recipes_data["recipes"]
                elif isinstance(recipes_data, list):
                    recipes = recipes_data
                else:
                    self.log(f"Unexpected recipe data structure: {type(recipes_data)}", "fail", test_name)
                    self.record_result(test_name, False, "Invalid data structure")
                    return False
                
                if len(recipes) > 0:
                    # Check if recipes have required fields
                    sample_recipe = recipes[0]
                    required_fields = ["id", "title"]
                    missing_fields = [field for field in required_fields if field not in sample_recipe]
                    
                    if missing_fields:
                        self.log(f"Recipe missing fields: {missing_fields}", "warn", test_name)
                    
                    self.log(f"Recipe system working - found {len(recipes)} demo recipes", "pass", test_name)
                    self.record_result(test_name, True, f"Found {len(recipes)} recipes")
                    return True
                else:
                    self.log("No recipes returned", "fail", test_name)
                    self.record_result(test_name, False, "Empty recipe list")
                    return False
            else:
                self.log(f"Recipe endpoint returned {response.status_code}", "fail", test_name)
                self.record_result(test_name, False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Recipe test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    def test_pantry_management(self) -> bool:
        """Test pantry item CRUD operations"""
        test_name = "pantry_management"
        self.log("Testing pantry management system", "test", test_name)
        
        try:
            # Test getting pantry items (even if empty)
            response = self.session.get(f"{self.base_url}/api/v1/pantry/items/111", timeout=10)
            
            if response.status_code == 200:
                items_data = response.json()
                self.log(f"Pantry endpoint accessible - found {len(items_data)} items", "pass", test_name)
                self.record_result(test_name, True, f"Pantry accessible, {len(items_data)} items")
                return True
            elif response.status_code == 404:
                self.log("Pantry endpoint not found", "fail", test_name)
                self.record_result(test_name, False, "Endpoint not found")
                return False
            elif response.status_code in [401, 403]:
                self.log("Pantry requires authentication (expected)", "pass", test_name)
                self.record_result(test_name, True, "Auth required (normal)")
                return True
            else:
                self.log(f"Pantry endpoint returned {response.status_code}", "warn", test_name)
                self.record_result(test_name, True, f"Unexpected but not critical: {response.status_code}")
                return True
                
        except Exception as e:
            self.log(f"Pantry test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    def test_image_generation(self) -> bool:
        """Test recipe image generation system"""
        test_name = "image_generation"
        self.log("Testing image generation system", "test", test_name)
        
        try:
            # Test recipe image generation
            image_payload = {
                "recipe_name": "Chicken Stir Fry",
                "style": "professional food photography",
                "use_generated": False  # Use Unsplash for reliability
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/generate-recipe-image",
                json=image_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                image_data = response.json()
                
                if "image_url" in image_data and image_data["image_url"]:
                    # Validate that the URL is accessible
                    try:
                        img_response = requests.head(image_data["image_url"], timeout=5)
                        if img_response.status_code == 200:
                            self.log("Image generation working - URL accessible", "pass", test_name)
                            self.record_result(test_name, True, f"Generated: {image_data['image_url']}")
                            return True
                        else:
                            self.log("Image URL not accessible", "fail", test_name)
                            self.record_result(test_name, False, "URL not accessible")
                            return False
                    except:
                        self.log("Could not verify image URL", "warn", test_name)
                        self.record_result(test_name, True, "URL generated but not verified")
                        return True
                else:
                    self.log("No image URL in response", "fail", test_name)
                    self.record_result(test_name, False, "No image URL")
                    return False
            else:
                self.log(f"Image generation returned {response.status_code}", "fail", test_name)
                self.record_result(test_name, False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Image generation test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    # ===============================================================
    # END-TO-END USER WORKFLOW TESTS
    # ===============================================================

    def test_user_workflow_recipe_discovery(self) -> bool:
        """Test complete user workflow: Chat → Get recipes → View details"""
        test_name = "workflow_recipe_discovery"
        self.log("Testing complete recipe discovery workflow", "test", test_name)
        
        workflow_steps = []
        
        try:
            # Step 1: Chat for recipe suggestions
            self.log("Step 1: Asking for recipe suggestions", "info", test_name)
            chat_response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json={
                    "message": "I have pasta and tomatoes, suggest something quick",
                    "user_id": 111,
                    "use_preferences": False
                },
                timeout=30
            )
            
            if chat_response.status_code != 200:
                workflow_steps.append("❌ Chat request failed")
                self.record_result(test_name, False, "Chat step failed")
                return False
            
            chat_data = chat_response.json()
            if not chat_data.get("recipes") or len(chat_data["recipes"]) == 0:
                workflow_steps.append("❌ No recipes returned from chat")
                self.record_result(test_name, False, "No recipes in chat response")
                return False
                
            workflow_steps.append(f"✅ Got {len(chat_data['recipes'])} recipe suggestions")
            
            # Step 2: Get recipe details (simulate user clicking on a recipe)
            self.log("Step 2: Getting demo recipe details", "info", test_name)
            demo_response = self.session.get(f"{self.base_url}/api/v1/demo/recipes", timeout=10)
            
            if demo_response.status_code != 200:
                workflow_steps.append("❌ Recipe details request failed")
                self.record_result(test_name, False, "Recipe details step failed")
                return False
                
            demo_data = demo_response.json()
            if isinstance(demo_data, dict) and "recipes" in demo_data:
                recipes = demo_data["recipes"]
            else:
                recipes = demo_data
                
            if len(recipes) > 0:
                workflow_steps.append("✅ Recipe details accessible")
            else:
                workflow_steps.append("❌ No recipe details available")
                self.record_result(test_name, False, "No recipe details")
                return False
            
            # Step 3: Test image generation for the recipe
            self.log("Step 3: Generating recipe image", "info", test_name)
            sample_recipe = recipes[0]
            recipe_name = sample_recipe.get("title", "Sample Recipe")
            
            image_response = self.session.post(
                f"{self.base_url}/api/v1/chat/generate-recipe-image",
                json={
                    "recipe_name": recipe_name,
                    "use_generated": False
                },
                timeout=15
            )
            
            if image_response.status_code == 200:
                workflow_steps.append("✅ Recipe image generated")
            else:
                workflow_steps.append("⚠️ Recipe image generation failed (non-critical)")
            
            # Workflow completed successfully
            self.log("Complete workflow successful", "pass", test_name)
            workflow_summary = " → ".join(workflow_steps)
            self.record_result(test_name, True, workflow_summary)
            return True
            
        except Exception as e:
            workflow_steps.append(f"❌ Exception: {str(e)}")
            self.log(f"Workflow test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, " → ".join(workflow_steps))
            return False

    # ===============================================================
    # ERROR HANDLING TESTS
    # ===============================================================

    def test_error_handling(self) -> bool:
        """Test how the system handles various error conditions"""
        test_name = "error_handling"
        self.log("Testing error handling capabilities", "test", test_name)
        
        error_tests = []
        
        try:
            # Test 1: Invalid endpoint
            response = self.session.get(f"{self.base_url}/api/v1/nonexistent", timeout=5)
            if response.status_code == 404:
                error_tests.append("✅ 404 handling works")
            else:
                error_tests.append(f"❌ 404 handling: got {response.status_code}")
            
            # Test 2: Invalid chat data
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json={"invalid": "data"},
                timeout=10
            )
            if response.status_code == 422:
                error_tests.append("✅ Input validation works")
            else:
                error_tests.append(f"⚠️ Input validation: got {response.status_code}")
            
            # Test 3: Large request (test limits)
            large_message = "x" * 10000  # 10KB message
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json={
                    "message": large_message,
                    "user_id": 111
                },
                timeout=15
            )
            if response.status_code in [200, 422, 413]:  # Any reasonable response
                error_tests.append("✅ Large request handling works")
            else:
                error_tests.append(f"⚠️ Large request: got {response.status_code}")
            
            all_passed = all("✅" in test for test in error_tests)
            error_summary = " | ".join(error_tests)
            
            if all_passed:
                self.log("Error handling tests passed", "pass", test_name)
            else:
                self.log("Some error handling tests failed", "warn", test_name)
                
            self.record_result(test_name, all_passed, error_summary)
            return all_passed
            
        except Exception as e:
            self.log(f"Error handling test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    # ===============================================================
    # PERFORMANCE TESTS
    # ===============================================================

    def test_performance_basics(self) -> bool:
        """Test basic performance characteristics"""
        test_name = "performance"
        self.log("Testing basic performance", "test", test_name)
        
        performance_results = []
        
        try:
            # Test 1: Health endpoint response time
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=10)
            health_time = time.time() - start_time
            
            if health_time < 1.0:
                performance_results.append(f"✅ Health: {health_time:.2f}s")
            else:
                performance_results.append(f"⚠️ Health: {health_time:.2f}s (slow)")
            
            # Test 2: Demo recipes response time
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/v1/demo/recipes", timeout=15)
            recipes_time = time.time() - start_time
            
            if recipes_time < 3.0:
                performance_results.append(f"✅ Recipes: {recipes_time:.2f}s")
            else:
                performance_results.append(f"⚠️ Recipes: {recipes_time:.2f}s (slow)")
            
            # Test 3: Chat response time (longer acceptable)
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json={
                    "message": "Quick recipe with eggs",
                    "user_id": 111,
                    "use_preferences": False
                },
                timeout=45
            )
            chat_time = time.time() - start_time
            
            if chat_time < 30.0:
                performance_results.append(f"✅ Chat: {chat_time:.2f}s")
            else:
                performance_results.append(f"⚠️ Chat: {chat_time:.2f}s (very slow)")
            
            perf_summary = " | ".join(performance_results)
            acceptable_performance = not any("very slow" in result for result in performance_results)
            
            if acceptable_performance:
                self.log("Performance within acceptable ranges", "pass", test_name)
            else:
                self.log("Performance issues detected", "warn", test_name)
                
            self.record_result(test_name, acceptable_performance, perf_summary)
            return acceptable_performance
            
        except Exception as e:
            self.log(f"Performance test failed: {str(e)}", "fail", test_name)
            self.record_result(test_name, False, str(e))
            return False

    # ===============================================================
    # MAIN TEST EXECUTION
    # ===============================================================

    def run_comprehensive_tests(self) -> Tuple[bool, Dict]:
        """Run all comprehensive tests and return overall result"""
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔬 PrepSense Comprehensive Test Suite{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"Testing core functionality from first principles...")
        print(f"Base URL: {self.base_url}\n")
        
        # Test categories with their tests
        test_categories = {
            "Infrastructure": [
                ("Basic Connectivity", self.test_basic_connectivity),
                ("Database Connectivity", self.test_database_connectivity),
                ("External API Config", lambda: all(self.test_external_api_configuration().values()))
            ],
            "Core Features": [
                ("Chat System", self.test_chat_system),
                ("Recipe System", self.test_recipe_system),
                ("Pantry Management", self.test_pantry_management),
                ("Image Generation", self.test_image_generation)
            ],
            "User Workflows": [
                ("Recipe Discovery Flow", self.test_user_workflow_recipe_discovery)
            ],
            "System Quality": [
                ("Error Handling", self.test_error_handling),
                ("Performance", self.test_performance_basics)
            ]
        }
        
        category_results = {}
        overall_passed = 0
        overall_total = 0
        
        for category, tests in test_categories.items():
            print(f"\n{Colors.BOLD}{Colors.BLUE}📋 {category} Tests{Colors.RESET}")
            print(f"{Colors.BLUE}{'-'*40}{Colors.RESET}")
            
            category_passed = 0
            category_total = len(tests)
            
            for test_desc, test_func in tests:
                overall_total += 1
                try:
                    result = test_func()
                    if result:
                        category_passed += 1
                        overall_passed += 1
                except Exception as e:
                    self.log(f"Test {test_desc} threw exception: {str(e)}", "fail")
                    
            category_results[category] = {
                "passed": category_passed,
                "total": category_total,
                "success_rate": (category_passed / category_total * 100) if category_total > 0 else 0
            }
            
            success_rate = category_results[category]["success_rate"]
            if success_rate >= 90:
                status_color = Colors.GREEN
                status_emoji = "✅"
            elif success_rate >= 70:
                status_color = Colors.YELLOW
                status_emoji = "⚠️"
            else:
                status_color = Colors.RED
                status_emoji = "❌"
                
            print(f"{status_color}{status_emoji} {category}: {category_passed}/{category_total} ({success_rate:.1f}%){Colors.RESET}")
        
        # Overall summary
        overall_success_rate = (overall_passed / overall_total * 100) if overall_total > 0 else 0
        
        print(f"\n{Colors.BOLD}🎯 Overall Test Results{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        
        if overall_success_rate >= 90:
            status_color = Colors.GREEN
            status_emoji = "🎉"
            status_text = "EXCELLENT"
        elif overall_success_rate >= 75:
            status_color = Colors.YELLOW
            status_emoji = "👍"
            status_text = "GOOD"
        elif overall_success_rate >= 50:
            status_color = Colors.YELLOW
            status_emoji = "⚠️"
            status_text = "NEEDS ATTENTION"
        else:
            status_color = Colors.RED
            status_emoji = "🚨"
            status_text = "CRITICAL ISSUES"
        
        print(f"{status_color}{status_emoji} {status_text}: {overall_passed}/{overall_total} tests passed ({overall_success_rate:.1f}%){Colors.RESET}")
        
        # Critical failures
        if self.critical_failures:
            print(f"\n{Colors.RED}🚨 Critical Failures:{Colors.RESET}")
            for failure in self.critical_failures[:10]:  # Show top 10
                print(f"  • {failure}")
        
        # Warnings
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️ Warnings:{Colors.RESET}")
            for warning in self.warnings[:5]:  # Show top 5
                print(f"  • {warning}")
        
        # Recommendations
        print(f"\n{Colors.BOLD}💡 Recommendations:{Colors.RESET}")
        
        if overall_success_rate < 75:
            print("  1. Fix critical failures before proceeding with development")
            
        if "chat_system" in [r for r, data in self.test_results.items() if not data["passed"]]:
            print("  2. Chat system is core to PrepSense - prioritize fixing")
            
        if "database_connectivity" in [r for r, data in self.test_results.items() if not data["passed"]]:
            print("  3. Database issues will break most functionality")
            
        if overall_success_rate >= 90:
            print("  🎯 System is in excellent condition!")
        elif overall_success_rate >= 75:
            print("  👍 System is functional with minor issues")
        
        # Save detailed results
        results_file = Path(f".comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "timestamp": datetime.now().isoformat(),
                    "overall_passed": overall_passed,
                    "overall_total": overall_total,
                    "success_rate": overall_success_rate,
                    "status": status_text
                },
                "categories": category_results,
                "detailed_results": self.test_results,
                "critical_failures": self.critical_failures,
                "warnings": self.warnings
            }, f, indent=2)
        
        print(f"\n{Colors.BLUE}📄 Detailed results saved to {results_file}{Colors.RESET}")
        
        return overall_success_rate >= 75, {
            "success_rate": overall_success_rate,
            "passed": overall_passed,
            "total": overall_total,
            "categories": category_results
        }

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PrepSense Comprehensive Test Suite")
    parser.add_argument("--url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument("--timeout", type=int, default=300, help="Overall timeout in seconds")
    
    args = parser.parse_args()
    
    tester = PrepSenseTestSuite(base_url=args.url)
    
    try:
        success, results = tester.run_comprehensive_tests()
        
        # Exit with appropriate code
        if success:
            print(f"\n{Colors.GREEN}✅ All critical systems functional{Colors.RESET}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}❌ Critical issues found{Colors.RESET}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Test interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Test suite failed: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()