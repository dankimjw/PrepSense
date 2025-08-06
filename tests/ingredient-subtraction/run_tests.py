#!/usr/bin/env python3
"""
Recipe Ingredient Subtraction Test Suite
Run all test cases for the recipe completion feature
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Add backend_gateway to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend_gateway"))

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USER_ID = 111

# Note: To start the backend server, run:
# cd backend_gateway
# python -m uvicorn backend_gateway.app:app --reload --port 8000
# Or if you have a virtual environment:
# source venv/bin/activate  # or venv\Scripts\activate on Windows
# uvicorn backend_gateway.app:app --reload --port 8000


class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def reset_test_data(self):
        """Reset pantry to initial demo state"""
        print("\n🔄 Resetting test data...")
        try:
            # Run setup_demo_data.py
            import subprocess

            result = subprocess.run(
                ["python3", "../../backend_gateway/scripts/setup_demo_data.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
            )
            if result.returncode == 0:
                print("✅ Test data reset successfully")
                time.sleep(2)  # Give DB time to settle
            else:
                print(f"❌ Failed to reset test data: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error resetting test data: {e}")
            return False
        return True

    def run_test(
        self, test_name: str, endpoint: str, payload: Dict[str, Any], validations: List[callable]
    ) -> Dict[str, Any]:
        """Run a single test case"""
        print(f"\n{'='*80}")
        print(f"🧪 {test_name}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")

        # Print request
        print(f"\n📤 Request to {endpoint}:")
        print(json.dumps(payload, indent=2))

        try:
            # Make request
            response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload)
            response_data = response.json()

            # Print response
            print(f"\n📥 Response (Status: {response.status_code}):")
            print(json.dumps(response_data, indent=2))

            # Run validations
            test_passed = True
            validation_results = []

            for validation in validations:
                try:
                    result, message = validation(response_data)
                    validation_results.append((result, message))
                    if result:
                        print(f"✅ {message}")
                    else:
                        print(f"❌ {message}")
                        test_passed = False
                except Exception as e:
                    print(f"❌ Validation error: {e}")
                    test_passed = False
                    validation_results.append((False, f"Validation error: {e}"))

            # Record result
            self.results.append(
                {
                    "test_name": test_name,
                    "passed": test_passed,
                    "response": response_data,
                    "validations": validation_results,
                }
            )

            if test_passed:
                self.passed += 1
                print(f"\n✅ TEST PASSED")
            else:
                self.failed += 1
                print(f"\n❌ TEST FAILED")

            return response_data

        except Exception as e:
            print(f"\n❌ Test execution error: {e}")
            self.failed += 1
            self.results.append({"test_name": test_name, "passed": False, "error": str(e)})
            return {}

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")

        if self.failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result.get("passed", False):
                    print(f"  - {result['test_name']}")


# Validation Functions
def validate_updated_items(expected_count: int):
    def validate(response: Dict) -> tuple[bool, str]:
        count = len(response.get("updated_items", []))
        return (
            count == expected_count,
            f"Updated items count: expected {expected_count}, got {count}",
        )

    return validate


def validate_item_quantity(item_name: str, expected_new_quantity: float):
    def validate(response: Dict) -> tuple[bool, str]:
        for item in response.get("updated_items", []):
            if item_name.lower() in item.get("item_name", "").lower():
                actual = item.get("new_quantity", -1)
                return (
                    abs(actual - expected_new_quantity) < 0.01,
                    f"{item_name} quantity: expected {expected_new_quantity}, got {actual}",
                )
        return False, f"{item_name} not found in updated items"

    return validate


def validate_missing_items(expected_items: List[str]):
    def validate(response: Dict) -> tuple[bool, str]:
        missing = response.get("missing_items", [])
        return (
            set(expected_items) == set(missing),
            f"Missing items: expected {expected_items}, got {missing}",
        )

    return validate


def validate_insufficient_items(expected_count: int):
    def validate(response: Dict) -> tuple[bool, str]:
        count = len(response.get("insufficient_items", []))
        return (
            count == expected_count,
            f"Insufficient items count: expected {expected_count}, got {count}",
        )

    return validate


def validate_conversion_details(ingredient: str, contains: str):
    def validate(response: Dict) -> tuple[bool, str]:
        for item in response.get("updated_items", []):
            if ingredient.lower() in item.get("item_name", "").lower():
                details = item.get("conversion_details", "")
                return (
                    contains in details,
                    f"Conversion details for {ingredient}: expected to contain '{contains}', got '{details}'",
                )
        return False, f"{ingredient} not found in updated items"

    return validate


# Main Test Suite
def main():
    runner = TestRunner()

    # Reset data before starting
    if not runner.reset_test_data():
        print("❌ Failed to reset test data. Exiting.")
        return

    # Test Case 1: Basic Ingredient Subtraction
    runner.run_test(
        "Test Case 1: Basic Ingredient Subtraction with Exact Match",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Simple Pasta Test",
            "ingredients": [{"ingredient_name": "pasta", "quantity": 200, "unit": "g"}],
        },
        [
            validate_updated_items(1),
            validate_item_quantity("Pasta", 253.592),
            validate_conversion_details("pasta", "200 g = 200.00 g"),
        ],
    )

    # Test Case 2: Unit Conversion - Imperial to Metric
    runner.run_test(
        "Test Case 2: Unit Conversion - Cups to Milliliters",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Baking Test",
            "ingredients": [{"ingredient_name": "milk", "quantity": 1, "unit": "cup"}],
        },
        [
            validate_updated_items(1),
            validate_item_quantity("Milk", 709.765),
            validate_conversion_details("milk", "1 cup = 236"),
        ],
    )

    # Test Case 3: Multiple Item Depletion
    # Reset data first
    runner.reset_test_data()

    runner.run_test(
        "Test Case 3: Multiple Item Depletion (FIFO)",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Large Pasta Dish",
            "ingredients": [{"ingredient_name": "pasta", "quantity": 600, "unit": "g"}],
        },
        [
            validate_updated_items(2),  # Should use 2 pasta items
            validate_item_quantity("Spaghetti", 0),  # First should be depleted
        ],
    )

    # Test Case 4: Insufficient Quantity
    runner.run_test(
        "Test Case 4: Insufficient Quantity Handling",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Big Batch Cookies",
            "ingredients": [{"ingredient_name": "flour", "quantity": 1000, "unit": "g"}],
        },
        [
            validate_updated_items(1),
            validate_insufficient_items(1),
            validate_item_quantity("Flour", 0),
        ],
    )

    # Test Case 5: Missing Ingredient
    runner.run_test(
        "Test Case 5: Missing Ingredient",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Exotic Recipe",
            "ingredients": [{"ingredient_name": "saffron", "quantity": 1, "unit": "g"}],
        },
        [validate_updated_items(0), validate_missing_items(["saffron"])],
    )

    # Test Case 6: Count to Count
    runner.run_test(
        "Test Case 6: Count to Count Conversion",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Scrambled Eggs",
            "ingredients": [{"ingredient_name": "eggs", "quantity": 3, "unit": "each"}],
        },
        [validate_updated_items(1), validate_item_quantity("Eggs", 9)],
    )

    # Test Case 7: Smart Matching
    runner.run_test(
        "Test Case 7: Smart Matching with Variations",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Tomato Sauce",
            "ingredients": [{"ingredient_name": "tomatoes", "quantity": 2, "unit": "each"}],
        },
        [validate_updated_items(1), validate_item_quantity("Tomato", 2)],
    )

    # Test Case 8: No Quantity Specified
    runner.run_test(
        "Test Case 8: No Quantity Specified",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Seasoned Dish",
            "ingredients": [{"ingredient_name": "salt"}],
        },
        [validate_updated_items(1), validate_item_quantity("Salt", 0)],  # Should use all available
    )

    # Test Case 9: Complex Recipe
    runner.reset_test_data()

    runner.run_test(
        "Test Case 9: Complex Recipe with Multiple Conversions",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Chocolate Chip Cookies",
            "ingredients": [
                {"ingredient_name": "flour", "quantity": 2.25, "unit": "cups"},
                {"ingredient_name": "butter", "quantity": 1, "unit": "cup"},
                {"ingredient_name": "sugar", "quantity": 0.75, "unit": "cup"},
                {"ingredient_name": "eggs", "quantity": 2, "unit": "each"},
            ],
        },
        [
            lambda r: (
                len(r.get("updated_items", [])) >= 4,
                f"Should update at least 4 items, got {len(r.get('updated_items', []))}",
            )
        ],
    )

    # Test Case 10: Revert Functionality
    # First complete a recipe
    runner.reset_test_data()

    completion_response = runner.run_test(
        "Test Case 10a: Recipe to Revert",
        "/pantry/recipe/complete",
        {
            "user_id": USER_ID,
            "recipe_name": "Simple Pasta Test",
            "ingredients": [{"ingredient_name": "pasta", "quantity": 200, "unit": "g"}],
        },
        [validate_updated_items(1)],
    )

    # Now revert it
    time.sleep(1)  # Ensure some time has passed

    runner.run_test(
        "Test Case 10b: Revert Recipe Completion",
        "/pantry/revert-changes",
        {"user_id": USER_ID, "minutes_ago": 5, "revert_recipe": "Simple Pasta Test"},
        [
            lambda r: (
                "reverted_items" in r and len(r["reverted_items"]) > 0,
                "Should have reverted items",
            )
        ],
    )

    # Print summary
    runner.print_summary()


if __name__ == "__main__":
    main()
