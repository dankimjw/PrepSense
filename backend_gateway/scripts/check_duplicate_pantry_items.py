"""Script to check for duplicate pantry items in the database"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from collections import defaultdict

from backend_gateway.config.database import get_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_duplicate_pantry_items():
    """Check for duplicate pantry items by product name and user"""

    db_service = get_database_service()

    # Get all pantry items grouped by user
    query = """
    SELECT 
        p.user_id,
        pi.pantry_item_id,
        pi.product_name,
        pi.brand_name,
        pi.quantity,
        pi.unit_of_measurement,
        pi.status,
        pi.created_at
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE pi.status = 'available'
    ORDER BY p.user_id, pi.product_name, pi.created_at
    """

    items = db_service.execute_query(query)
    logger.info(f"Found {len(items)} total pantry items")

    # Group by user and product name
    user_products = defaultdict(lambda: defaultdict(list))

    for item in items:
        user_id = item["user_id"]
        product_key = f"{item['product_name']}|{item.get('brand_name', '')}"
        user_products[user_id][product_key].append(item)

    # Find duplicates
    duplicate_count = 0
    duplicate_examples = []

    for user_id, products in user_products.items():
        for product_key, items_list in products.items():
            if len(items_list) > 1:
                duplicate_count += 1
                product_name, brand_name = product_key.split("|")

                duplicate_info = {
                    "user_id": user_id,
                    "product_name": product_name,
                    "brand_name": brand_name,
                    "count": len(items_list),
                    "items": [],
                }

                for item in items_list:
                    duplicate_info["items"].append(
                        {
                            "pantry_item_id": item["pantry_item_id"],
                            "quantity": item["quantity"],
                            "unit": item["unit_of_measurement"],
                            "created_at": str(item["created_at"]),
                        }
                    )

                duplicate_examples.append(duplicate_info)

    # Print results
    print("\n=== Duplicate Pantry Items Analysis ===")
    print(f"Total users checked: {len(user_products)}")
    print(f"Total duplicate product groups: {duplicate_count}")

    if duplicate_examples:
        print("\n=== Duplicate Examples (First 10) ===")
        for dup in duplicate_examples[:10]:
            print(f"\nUser {dup['user_id']}: {dup['product_name']} ({dup['brand_name']})")
            print(f"  Found {dup['count']} duplicate items:")
            for item in dup["items"]:
                print(
                    f"    - ID: {item['pantry_item_id']}, Qty: {item['quantity']} {item['unit']}, Created: {item['created_at']}"
                )

    # Check specific case mentioned in the issue
    print("\n=== Checking 'Pacific Organic Low Sodium Chicken Broth' ===")
    pacific_query = """
    SELECT 
        p.user_id,
        pi.pantry_item_id,
        pi.product_name,
        pi.quantity,
        pi.unit_of_measurement,
        pi.created_at
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE LOWER(pi.product_name) LIKE '%pacific%chicken%broth%'
    AND pi.status = 'available'
    ORDER BY p.user_id, pi.created_at
    """

    pacific_items = db_service.execute_query(pacific_query)
    print(f"Found {len(pacific_items)} Pacific Chicken Broth items")

    for item in pacific_items:
        print(
            f"  User {item['user_id']}: ID {item['pantry_item_id']}, {item['quantity']} {item['unit_of_measurement']}"
        )

    return duplicate_examples


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    check_duplicate_pantry_items()
