#!/usr/bin/env python3
"""
Dynamic script to update ingredient expiration dates and quantities
Creates a mix of near-expiration, close-to-expiration, and okay ingredients
Runs automatically when the app starts to provide realistic test scenarios
"""

import os
import random
import sys
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
load_dotenv(os.path.join(parent_dir, ".env"))

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# User ID for demo user
USER_ID = 111  # samantha-1
PANTRY_ID = 1011  # pantry_id for user 111


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def update_ingredient_expirations():
    """Update ingredient expiration dates to create realistic test scenarios"""

    # Define ingredients to update with specific expiration patterns
    expiration_updates = [
        # 1 day from now (critical - red)
        {
            "ingredients": ["avocado", "spinach", "cilantro", "fresh basil"],
            "days_until_expiry": 1,
            "quantity_multiplier": 0.3,  # Low quantity
        },
        # 2 days from now (warning - orange)
        {
            "ingredients": ["ground turkey", "ground lamb", "milk", "cottage cheese"],
            "days_until_expiry": 2,
            "quantity_multiplier": 0.5,  # Medium quantity
        },
        # 3 days from now (warning - orange)
        {
            "ingredients": ["chicken breast", "flank steak", "turkey sausage"],
            "days_until_expiry": 3,
            "quantity_multiplier": 0.6,
        },
        # 7 days from now (caution - yellow)
        {
            "ingredients": [
                "eggs",
                "Greek yogurt",
                "mozzarella cheese",
                "tomatoes",
                "cucumber",
                "lemon",
                "lime",
            ],
            "days_until_expiry": 7,
            "quantity_multiplier": 0.8,
        },
        # 14 days from now (okay - green)
        {
            "ingredients": [
                "chicken thighs",
                "chicken drumsticks",
                "butter",
                "heavy cream",
                "ricotta cheese",
            ],
            "days_until_expiry": 14,
            "quantity_multiplier": 1.0,
        },
        # 21 days from now (good)
        {
            "ingredients": ["onion", "garlic", "ginger", "red onion", "green onions"],
            "days_until_expiry": 21,
            "quantity_multiplier": 1.2,
        },
    ]

    conn = get_connection()
    cur = conn.cursor()

    try:
        # First, get all current ingredients to reset quantities
        cur.execute(
            """
            SELECT pantry_item_id, product_name, quantity, unit_of_measurement 
            FROM pantry_items 
            WHERE pantry_id = %s
        """,
            (PANTRY_ID,),
        )

        all_items = {item["product_name"]: item for item in cur.fetchall()}

        updated_count = 0

        for update_group in expiration_updates:
            days = update_group["days_until_expiry"]
            multiplier = update_group["quantity_multiplier"]
            expiration_date = datetime.now() + timedelta(days=days)

            for ingredient_name in update_group["ingredients"]:
                if ingredient_name in all_items:
                    item = all_items[ingredient_name]

                    # Calculate new quantity based on original
                    # Extract numeric value from the database
                    original_qty = float(item["quantity"])

                    # Define base quantities with proper units for different ingredient types
                    # Format: (quantity, unit)
                    base_quantities = {
                        "avocado": (4, "unit"),
                        "spinach": (500, "g"),
                        "cilantro": (3, "bunches"),
                        "fresh basil": (2, "bunches"),
                        "ground turkey": (1000, "g"),
                        "ground lamb": (800, "g"),
                        "milk": (500, "ml"),
                        "cottage cheese": (400, "g"),
                        "chicken breast": (1600, "g"),
                        "flank steak": (800, "g"),
                        "turkey sausage": (400, "g"),
                        "eggs": (2, "dozen"),
                        "Greek yogurt": (1, "kg"),
                        "mozzarella cheese": (600, "g"),
                        "tomatoes": (8, "unit"),
                        "cucumber": (3, "unit"),
                        "lemon": (4, "unit"),
                        "lime": (8, "unit"),
                        "chicken thighs": (1200, "g"),
                        "chicken drumsticks": (1600, "g"),
                        "butter": (300, "g"),
                        "heavy cream": (600, "ml"),
                        "ricotta cheese": (500, "g"),
                        "onion": (8, "unit"),
                        "garlic": (10, "cloves"),
                        "ginger": (4, "inch piece"),
                        "red onion": (3, "unit"),
                        "green onions": (1, "bunch"),
                    }

                    # Get base quantity and unit or use current if not defined
                    if ingredient_name in base_quantities:
                        base_qty, expected_unit = base_quantities[ingredient_name]
                        new_quantity = base_qty * multiplier

                        # Add some randomness (±10%)
                        new_quantity = new_quantity * random.uniform(0.9, 1.1)

                        # Update the item with correct unit
                        cur.execute(
                            """
                            UPDATE pantry_items 
                            SET quantity = %s,
                                unit_of_measurement = %s,
                                expiration_date = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE pantry_item_id = %s
                        """,
                            (
                                round(new_quantity, 2),
                                expected_unit,
                                expiration_date,
                                item["pantry_item_id"],
                            ),
                        )
                    else:
                        # For items not in our list, just update quantity with existing unit
                        new_quantity = original_qty * multiplier * random.uniform(0.9, 1.1)
                        cur.execute(
                            """
                            UPDATE pantry_items 
                            SET quantity = %s,
                                expiration_date = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE pantry_item_id = %s
                        """,
                            (round(new_quantity, 2), expiration_date, item["pantry_item_id"]),
                        )

                    updated_count += 1
                    # Show the unit that was actually set
                    display_unit = (
                        expected_unit
                        if ingredient_name in base_quantities
                        else item["unit_of_measurement"]
                    )
                    print(
                        f"Updated {ingredient_name}: {new_quantity:.2f} {display_unit} - expires in {days} days"
                    )

        conn.commit()
        print(
            f"\n✅ Successfully updated {updated_count} ingredients with dynamic expiration dates"
        )

        # Show summary
        print("\nExpiration Summary:")
        print("- 1 day (critical): avocado, spinach, cilantro, fresh basil")
        print("- 2 days (warning): ground turkey, ground lamb, milk, cottage cheese")
        print("- 3 days (warning): chicken breast, flank steak, turkey sausage")
        print("- 7 days (caution): eggs, Greek yogurt, mozzarella, produce items")
        print("- 14+ days (good): remaining proteins and pantry items")

    except Exception as e:
        conn.rollback()
        print(f"Error updating ingredients: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_updates():
    """Show current expiration status"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get items by expiration date
        cur.execute(
            """
            SELECT product_name, quantity, unit_of_measurement, expiration_date
            FROM pantry_items 
            WHERE pantry_id = %s
            ORDER BY expiration_date ASC
            LIMIT 20
        """,
            (PANTRY_ID,),
        )

        print("\n📊 Current Expiration Status (Top 20):")
        print("-" * 70)

        for item in cur.fetchall():
            # Calculate days until expiry
            days_diff = item["expiration_date"] - datetime.now().date()
            days = days_diff.days
            status = (
                "🔴 CRITICAL"
                if days <= 1
                else "🟠 WARNING" if days <= 3 else "🟡 CAUTION" if days <= 7 else "🟢 GOOD"
            )
            print(
                f"{item['product_name']:25} {item['quantity']:6.2f} {item['unit_of_measurement']:10} | {days:2d} days | {status}"
            )

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("🔄 Updating ingredient expiration dates and quantities...")
    print(f"Database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
    print(f"User ID: {USER_ID}, Pantry ID: {PANTRY_ID}\n")

    try:
        update_ingredient_expirations()
        verify_updates()
        print("\n✅ Dynamic expiration updates completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
