"""Script to fix duplicate pantry items by consolidating them"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from collections import defaultdict
from decimal import Decimal

from backend_gateway.config.database import get_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_duplicate_pantry_items(dry_run=True):
    """
    Fix duplicate pantry items by consolidating them into single items

    Args:
        dry_run: If True, only show what would be done without making changes
    """

    db_service = get_database_service()

    # Get all pantry items grouped by user and product
    query = """
    SELECT 
        p.user_id,
        p.pantry_id,
        pi.pantry_item_id,
        pi.product_name,
        pi.brand_name,
        pi.quantity,
        pi.unit_of_measurement,
        pi.expiration_date,
        pi.status,
        pi.created_at
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE pi.status = 'available'
    ORDER BY p.user_id, pi.product_name, pi.expiration_date, pi.created_at
    """

    items = db_service.execute_query(query)
    logger.info(f"Found {len(items)} total pantry items")

    # Group by user, product name, and unit
    user_products = defaultdict(lambda: defaultdict(list))

    for item in items:
        user_id = item["user_id"]
        # Group by product name, brand, and unit to consolidate properly
        product_key = (
            f"{item['product_name']}|{item.get('brand_name', '')}|{item['unit_of_measurement']}"
        )
        user_products[user_id][product_key].append(item)

    # Plan consolidations
    consolidations = []
    items_to_delete = []

    for user_id, products in user_products.items():
        for product_key, items_list in products.items():
            if len(items_list) > 1:
                product_name, brand_name, unit = product_key.split("|")

                # Keep the item with the earliest expiration date (or oldest if no expiration)
                items_sorted = sorted(
                    items_list,
                    key=lambda x: (x.get("expiration_date") or "9999-12-31", x["created_at"]),
                )

                keep_item = items_sorted[0]
                delete_items = items_sorted[1:]

                # Calculate total quantity
                total_quantity = sum(Decimal(str(item["quantity"])) for item in items_list)

                consolidation = {
                    "user_id": user_id,
                    "product_name": product_name,
                    "brand_name": brand_name,
                    "unit": unit,
                    "keep_item_id": keep_item["pantry_item_id"],
                    "new_quantity": total_quantity,
                    "delete_item_ids": [item["pantry_item_id"] for item in delete_items],
                    "items_consolidated": len(items_list),
                }

                consolidations.append(consolidation)
                items_to_delete.extend(consolidation["delete_item_ids"])

    # Print summary
    print("\n=== Duplicate Consolidation Summary ===")
    print(f"Total consolidations needed: {len(consolidations)}")
    print(f"Total items to delete: {len(items_to_delete)}")

    if consolidations:
        print("\n=== Consolidation Details (First 10) ===")
        for cons in consolidations[:10]:
            print(f"\nUser {cons['user_id']}: {cons['product_name']} ({cons['brand_name']})")
            print(f"  Keep item ID: {cons['keep_item_id']}")
            print(f"  New quantity: {cons['new_quantity']} {cons['unit']}")
            print(f"  Consolidating {cons['items_consolidated']} items")
            print(
                f"  Deleting IDs: {cons['delete_item_ids'][:5]}{'...' if len(cons['delete_item_ids']) > 5 else ''}"
            )

    if not dry_run and consolidations:
        response = input("\nProceed with consolidation? (y/n): ")
        if response.lower() == "y":
            perform_consolidation(db_service, consolidations)
        else:
            print("Consolidation cancelled.")
    else:
        print("\nDry run complete. Use dry_run=False to actually perform consolidation.")

    return consolidations


def perform_consolidation(db_service, consolidations):
    """Actually perform the consolidation in the database"""

    logger.info("Starting consolidation...")

    success_count = 0
    error_count = 0

    for cons in consolidations:
        try:
            # Update the kept item with new total quantity
            update_query = """
            UPDATE pantry_items 
            SET quantity = %(quantity)s
            WHERE pantry_item_id = %(item_id)s
            """

            db_service.execute_query(
                update_query, {"quantity": cons["new_quantity"], "item_id": cons["keep_item_id"]}
            )

            # Delete the duplicate items
            if cons["delete_item_ids"]:
                delete_query = """
                DELETE FROM pantry_items 
                WHERE pantry_item_id = ANY(%(item_ids)s)
                """

                db_service.execute_query(delete_query, {"item_ids": cons["delete_item_ids"]})

            success_count += 1

        except Exception as e:
            logger.error(f"Error consolidating {cons['product_name']}: {e}")
            error_count += 1

    print(f"\n=== Consolidation Complete ===")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    import argparse

    parser = argparse.ArgumentParser(description="Fix duplicate pantry items")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the consolidation (default is dry run)",
    )

    args = parser.parse_args()

    fix_duplicate_pantry_items(dry_run=not args.execute)
