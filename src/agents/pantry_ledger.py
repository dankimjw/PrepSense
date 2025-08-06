import logging
import os
from decimal import Decimal

import asyncpg

from src.tools.ingredient_matcher import match_and_score
from src.tools.pantry_update import deduct

logger = logging.getLogger(__name__)


class PantryLedger:
    name = "pantry_ledger"

    async def run(
        self,
        final_recipes: list[dict],
        user_id: str,
        selected_recipe_id: int = None,
        commit_deduction: bool = False,
    ):
        """
        Input: [{'recipe_id': 123, 'title': 'Chicken Stir Fry', 'ingredients': [...], 'final_score': 0.85}...]
        Output: Recipe ingredient matching results and optionally perform pantry deductions
        """
        if not final_recipes:
            return []

        if not user_id:
            logger.error("User ID required for pantry operations")
            return final_recipes

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return final_recipes

        try:
            conn = await asyncpg.connect(db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return final_recipes

        try:
            # Get user's current pantry inventory
            pantry_items = await self._get_pantry_inventory(conn, user_id)

            if not pantry_items:
                logger.warning(f"No pantry items found for user {user_id}")
                # Return recipes with empty matching results
                return [
                    {
                        **recipe,
                        "pantry_match": {
                            "matches": [],
                            "coverage": 0,
                            "missing_ingredients": recipe.get("ingredients", []),
                        },
                    }
                    for recipe in final_recipes
                ]

            enriched_recipes = []

            for recipe in final_recipes:
                try:
                    # Match recipe ingredients against pantry
                    matching_result = await self._match_recipe_ingredients(recipe, pantry_items)

                    enriched_recipe = {**recipe, "pantry_match": matching_result}

                    # If this is the selected recipe and commit is requested, perform deduction
                    if (
                        selected_recipe_id
                        and recipe.get("recipe_id") == selected_recipe_id
                        and commit_deduction
                    ):

                        deduction_result = await self._perform_pantry_deduction(
                            conn, user_id, matching_result["matches"]
                        )
                        enriched_recipe["pantry_deduction"] = deduction_result

                    enriched_recipes.append(enriched_recipe)

                except Exception as e:
                    logger.error(f"Error processing recipe {recipe.get('recipe_id')}: {e}")
                    enriched_recipes.append(
                        {**recipe, "pantry_match": {"error": str(e), "matches": [], "coverage": 0}}
                    )

            logger.info(f"Processed pantry matching for {len(enriched_recipes)} recipes")
            return enriched_recipes

        finally:
            await conn.close()

    async def _get_pantry_inventory(self, conn, user_id: str) -> list[dict]:
        """Get user's current pantry inventory with canonical units"""
        try:
            # Get pantry items with their canonical units and quantities
            rows = await conn.fetch(
                """
                SELECT 
                    pi.pantry_item_id as item_id,
                    pi.product_name,
                    pi.category,
                    pi.quantity,
                    pi.unit_of_measurement,
                    pi.expiration_date,
                    pi.brand_name,
                    -- Map to canonical name via USDA foods if possible
                    uf.description as canonical_name,
                    uf.fdc_id,
                    -- For now, assume canonical quantities match raw quantities
                    pi.quantity as qty_canon,
                    pi.unit_of_measurement as canon_unit
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.pantry_id
                LEFT JOIN usda_foods uf ON LOWER(uf.description) LIKE LOWER('%' || pi.product_name || '%')
                WHERE p.user_id = $1
                  AND pi.quantity > 0
                ORDER BY pi.expiration_date ASC NULLS LAST
            """,
                int(user_id),
            )

            pantry_items = []
            for row in rows:
                pantry_items.append(
                    {
                        "item_id": row["item_id"],
                        "product_name": row["product_name"],
                        "canonical_name": row["canonical_name"] or row["product_name"],
                        "category": row["category"],
                        "quantity": row["quantity"],
                        "unit_of_measurement": row["unit_of_measurement"],
                        "qty_canon": Decimal(str(row["qty_canon"] or 0)),
                        "canon_unit": row["canon_unit"] or "each",
                        "expiration_date": row["expiration_date"],
                        "brand_name": row["brand_name"],
                        "fdc_id": row["fdc_id"],
                    }
                )

            logger.info(f"Retrieved {len(pantry_items)} pantry items for user {user_id}")
            return pantry_items

        except Exception as e:
            logger.error(f"Error retrieving pantry inventory: {e}")
            return []

    async def _match_recipe_ingredients(self, recipe: dict, pantry_items: list[dict]) -> dict:
        """Match recipe ingredients against pantry inventory"""
        recipe_ingredients = recipe.get("ingredients", [])

        if not recipe_ingredients:
            return {
                "matches": [],
                "coverage": 0,
                "missing_ingredients": [],
                "partial_matches": [],
                "exact_matches": [],
            }

        # Convert recipe ingredients to the format expected by ingredient_matcher
        normalized_recipe_ingredients = []
        for ing in recipe_ingredients:
            # Try to extract canonical units (simplified for now)
            normalized_ing = {
                "name": ing.get("name", ""),
                "amount": ing.get("amount", 1),
                "unit": ing.get("unit", "each"),
                "qty_canon": Decimal(str(ing.get("amount", 1))),
                "canon_unit": ing.get("unit", "each"),
                "original": ing.get("original", ""),
            }
            normalized_recipe_ingredients.append(normalized_ing)

        try:
            # Use the existing ingredient matcher
            matches = match_and_score(normalized_recipe_ingredients, pantry_items)

            # Categorize matches
            exact_matches = [m for m in matches if m["score"] >= 1.0]
            partial_matches = [m for m in matches if 0.5 <= m["score"] < 1.0]

            # Find missing ingredients
            matched_ingredient_names = {
                match["need"] for match in matches
            }  # This might need adjustment based on match_and_score output
            missing_ingredients = [
                ing
                for ing in normalized_recipe_ingredients
                if ing["name"] not in matched_ingredient_names
            ]

            # Calculate coverage
            total_ingredients = len(normalized_recipe_ingredients)
            coverage = len(matches) / total_ingredients if total_ingredients > 0 else 0

            return {
                "matches": matches,
                "coverage": round(coverage, 3),
                "missing_ingredients": missing_ingredients,
                "partial_matches": partial_matches,
                "exact_matches": exact_matches,
                "total_recipe_ingredients": total_ingredients,
                "matched_count": len(matches),
            }

        except Exception as e:
            logger.error(f"Error in ingredient matching: {e}")
            return {
                "matches": [],
                "coverage": 0,
                "missing_ingredients": normalized_recipe_ingredients,
                "error": str(e),
            }

    async def _perform_pantry_deduction(self, conn, user_id: str, matches: list[dict]) -> dict:
        """Perform actual pantry deductions for selected recipe"""
        if not matches:
            return {"status": "no_deductions", "message": "No ingredients to deduct"}

        try:
            # Filter to only deductions where we have enough quantity
            valid_deductions = []
            insufficient_items = []

            for match in matches:
                if match["score"] >= 0.75 and match["have"] >= match["need"]:
                    valid_deductions.append({"item_id": match["item_id"], "need": match["need"]})
                elif match["have"] < match["need"]:
                    insufficient_items.append(
                        {
                            "item_id": match["item_id"],
                            "needed": match["need"],
                            "available": match["have"],
                        }
                    )

            if not valid_deductions:
                return {
                    "status": "insufficient_ingredients",
                    "message": "Not enough ingredients available for deduction",
                    "insufficient_items": insufficient_items,
                }

            # Perform the deductions
            await deduct(conn, user_id, valid_deductions)

            # Log the transaction
            await self._log_pantry_transaction(conn, user_id, valid_deductions, "recipe_completion")

            return {
                "status": "success",
                "message": f"Deducted {len(valid_deductions)} ingredients from pantry",
                "deducted_items": valid_deductions,
                "insufficient_items": insufficient_items,
                "total_deductions": len(valid_deductions),
            }

        except Exception as e:
            logger.error(f"Error performing pantry deduction: {e}")
            return {"status": "error", "message": f"Failed to deduct ingredients: {str(e)}"}

    async def _log_pantry_transaction(
        self, conn, user_id: str, deductions: list[dict], transaction_type: str
    ):
        """Log pantry transactions for audit trail"""
        try:
            for deduction in deductions:
                await conn.execute(
                    """
                    INSERT INTO pantry_history (
                        pantry_item_id, user_id, action_type, quantity_changed, 
                        action_timestamp, notes
                    ) VALUES ($1, $2, $3, $4, NOW(), $5)
                """,
                    deduction["item_id"],
                    int(user_id),
                    transaction_type,
                    -float(deduction["need"]),  # Negative for deduction
                    f"Recipe ingredient deduction: {deduction['need']} units",
                )

            logger.info(f"Logged {len(deductions)} pantry transactions for user {user_id}")

        except Exception as e:
            logger.error(f"Error logging pantry transactions: {e}")
            # Don't fail the whole operation if logging fails

    async def get_pantry_summary(self, user_id: str) -> dict:
        """Get summary of user's pantry for external use"""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return {"error": "Database not configured"}

        try:
            conn = await asyncpg.connect(db_url)
            pantry_items = await self._get_pantry_inventory(conn, user_id)
            await conn.close()

            # Summarize pantry
            summary = {
                "total_items": len(pantry_items),
                "categories": {},
                "expiring_soon": [],
                "low_stock": [],
            }

            for item in pantry_items:
                category = item.get("category", "Unknown")
                summary["categories"][category] = summary["categories"].get(category, 0) + 1

                # Check for items expiring soon (within 3 days)
                if item.get("expiration_date"):
                    from datetime import datetime, timedelta

                    exp_date = item["expiration_date"]
                    if isinstance(exp_date, str):
                        exp_date = datetime.fromisoformat(exp_date)
                    if exp_date <= datetime.now() + timedelta(days=3):
                        summary["expiring_soon"].append(item["product_name"])

                # Check for low stock (less than 1 unit)
                if item.get("quantity", 0) < 1:
                    summary["low_stock"].append(item["product_name"])

            return summary

        except Exception as e:
            logger.error(f"Error getting pantry summary: {e}")
            return {"error": str(e)}
