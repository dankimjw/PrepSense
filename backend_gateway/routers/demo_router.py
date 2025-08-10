"""Demo router for testing recipe completion"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/demo",
    tags=["Demo"],
    responses={404: {"description": "Not found"}},
)

# Demo recipes for chat to suggest
DEMO_RECIPES = [
    {
        "name": "Classic Spaghetti Carbonara",
        "ingredients": [
            "400g pasta (spaghetti)",
            "4 large eggs",
            "2 tablespoons olive oil",
            "1 teaspoon salt",
            "1/2 teaspoon black pepper",
        ],
        "instructions": [
            "Bring a large pot of salted water to boil and cook pasta according to package directions.",
            "While pasta cooks, whisk eggs with salt and pepper in a bowl.",
            "Cook bacon until crispy, reserve fat.",
            "Toss hot pasta with egg mixture and bacon fat to create creamy sauce.",
        ],
        "time": 30,
        "match_score": 0.95,
        "available_ingredients": ["pasta", "eggs", "olive oil", "salt", "black pepper"],
        "missing_ingredients": [],
        "missing_count": 0,
        "available_count": 5,
        "nutrition": {"calories": 420, "protein": 18},
        "expected_joy": 0.9,
        "cuisine_type": "Italian",
        "dietary_tags": [],
        "demo_notes": "Tests weight conversion (g to lb) and count items",
    },
    {
        "name": "Chocolate Chip Cookies",
        "ingredients": [
            "2 1/4 cups all-purpose flour",
            "1 cup butter, softened",
            "3/4 cup granulated sugar",
            "2 large eggs",
            "1 teaspoon vanilla extract",
            "1 teaspoon salt",
        ],
        "instructions": [
            "Preheat oven to 375°F (190°C).",
            "Cream butter and sugars until fluffy.",
            "Beat in eggs and vanilla.",
            "Mix in flour, baking soda, and salt.",
            "Fold in chocolate chips.",
            "Drop dough on baking sheets and bake 9-11 minutes.",
        ],
        "time": 45,
        "match_score": 0.92,
        "available_ingredients": ["flour", "butter", "sugar", "eggs", "vanilla extract", "salt"],
        "missing_ingredients": [],
        "missing_count": 0,
        "available_count": 6,
        "nutrition": {"calories": 280, "protein": 3},
        "expected_joy": 0.95,
        "cuisine_type": "American",
        "dietary_tags": ["vegetarian"],
        "demo_notes": "Tests volume conversions (cups to ml/g) and baking measurements",
    },
    {
        "name": "Lemon Herb Roasted Chicken",
        "ingredients": [
            "1.5 pounds chicken breast",
            "1/4 cup olive oil",
            "2 teaspoons salt",
            "1 teaspoon black pepper",
        ],
        "instructions": [
            "Preheat oven to 425°F (220°C).",
            "Season chicken with salt and pepper.",
            "Drizzle with olive oil and lemon juice.",
            "Roast for 45-50 minutes until golden.",
        ],
        "time": 60,
        "match_score": 0.88,
        "available_ingredients": ["chicken breast", "olive oil", "salt", "black pepper"],
        "missing_ingredients": [],
        "missing_count": 0,
        "available_count": 4,
        "nutrition": {"calories": 320, "protein": 42},
        "expected_joy": 0.85,
        "cuisine_type": "Mediterranean",
        "dietary_tags": ["gluten-free", "low-carb"],
        "demo_notes": "Tests direct pound matching and mixed units",
    },
]


@router.get("/recipes", summary="Get demo recipes for testing")
async def get_demo_recipes() -> dict[str, Any]:
    """
    Returns demo recipes formatted for the chat interface.
    These recipes are designed to test various unit conversion scenarios.
    """
    return {
        "recipes": DEMO_RECIPES,
        "message": "Here are some demo recipes perfect for testing ingredient subtraction:",
        "notes": {
            "carbonara": "Tests weight conversions (pasta: g to lb) and count items (eggs)",
            "cookies": "Tests volume conversions (flour/butter: cups to weight) and baking units",
            "chicken": "Tests direct pound matching and mixed measurement units",
        },
    }


@router.get("/pantry-status", summary="Get current pantry quantities for demo")
async def get_pantry_status(
    user_id: int = 111, db_service=Depends(get_database_service)
) -> dict[str, Any]:
    """
    Get current pantry quantities to verify ingredient subtraction
    """
    query = """
    SELECT
        product_name,
        quantity,
        unit_of_measurement,
        used_quantity,
        category
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE p.user_id = %(user_id)s
    ORDER BY category, product_name
    """

    items = db_service.execute_query(query, {"user_id": user_id})

    # Group by category for better display
    categorized = {}
    for item in items:
        category = item["category"] or "Other"
        if category not in categorized:
            categorized[category] = []

        categorized[category].append(
            {
                "name": item["product_name"],
                "quantity": float(item["quantity"]),
                "unit": item["unit_of_measurement"],
                "used": float(item.get("used_quantity", 0) or 0),
            }
        )

    return {
        "pantry_items": categorized,
        "total_items": len(items),
        "message": "Current pantry quantities by category",
    }


@router.post("/reset-demo", summary="Reset demo data to original values")
async def reset_demo_data_old(db_service=Depends(get_database_service)) -> dict[str, Any]:
    """
    Reset all demo pantry items to their original quantities (legacy endpoint)
    """
    try:
        # Import here to avoid circular imports
        from backend_gateway.scripts.setup_demo_data import reset_demo_data as reset_func

        # This will reset the demo data
        reset_func()

        return {
            "success": True,
            "message": "Demo data has been reset to original values",
            "next_steps": [
                "Pantry items restored to full quantities",
                "Demo recipes are available in My Recipes",
                "Ready for testing ingredient subtraction",
            ],
        }
    except Exception as e:
        logger.error(f"Error resetting demo data: {str(e)}")
        return {"success": False, "message": f"Error resetting demo data: {str(e)}"}


@router.post("/reset-data", summary="Reset demo data (new endpoint)")
async def reset_demo_data(db_service=Depends(get_database_service)) -> dict[str, Any]:
    """
    Reset demo pantry items and recipes to default state
    """
    try:
        # Import and run setup script
        import os
        import subprocess
        import sys

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "setup_demo_data.py",
        )

        result = subprocess.run(
            [sys.executable, script_path], check=False, capture_output=True, text=True
        )

        if result.returncode == 0:
            # Parse output to get counts
            lines = result.stdout.split("\n")
            pantry_count = 0
            recipe_count = 0

            for line in lines:
                if "Added:" in line or "Updated:" in line:
                    pantry_count += 1
                elif "Saved recipe:" in line:
                    recipe_count += 1

            return {
                "success": True,
                "pantry_items_count": pantry_count,
                "recipes_count": recipe_count,
                "message": "Demo data reset successfully",
            }
        else:
            raise Exception(result.stderr or "Failed to run setup script")

    except Exception as e:
        logger.error(f"Error resetting demo data: {str(e)}")
        return {
            "success": False,
            "pantry_items_count": 0,
            "recipes_count": 0,
            "message": f"Error: {str(e)}",
        }


@router.post("/test-subtraction", summary="Run ingredient subtraction tests")
async def run_subtraction_tests(db_service=Depends(get_database_service)) -> dict[str, Any]:
    """
    Run automated tests for ingredient subtraction
    """
    try:
        # Import and run test script
        import os
        import subprocess
        import sys

        test_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "tests",
            "ingredient-subtraction",
            "run_tests.py",
        )

        if not os.path.exists(test_script):
            # Try simple test
            test_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "tests",
                "ingredient-subtraction",
                "simple_test.py",
            )

        result = subprocess.run(
            [sys.executable, test_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )

        # Parse test results
        output_lines = result.stdout.split("\n")
        passed = 0
        failed = 0
        total = 0

        for line in output_lines:
            if "PASSED" in line:
                passed += 1
                total += 1
            elif "FAILED" in line:
                failed += 1
                total += 1

        summary = []
        if passed > 0:
            summary.append(f"✅ {passed} tests passed")
        if failed > 0:
            summary.append(f"❌ {failed} tests failed")

        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "total": total,
            "summary": "\n".join(summary) if summary else "Test results logged to console",
            "output": result.stdout if failed > 0 else None,
        }

    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return {
            "success": False,
            "passed": 0,
            "failed": 0,
            "total": 0,
            "summary": f"Error running tests: {str(e)}",
        }
