#!/usr/bin/env python3
"""
Fix the last remaining invalid unit in pantry items
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables from the correct path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


def fix_remaining_unit():
    """Find and fix the last invalid unit"""

    # Get database connection info from .env
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")

    print(f"Connecting to {host}:{port}/{database}...")

    try:
        conn = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password, sslmode="require"
        )

        # Find the invalid unit
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pi.pantry_item_id, pi.product_name, pi.unit_of_measurement, pi.quantity
                FROM pantry_items pi
                LEFT JOIN units u ON pi.unit_of_measurement = u.id
                WHERE pi.unit_of_measurement IS NOT NULL 
                AND u.id IS NULL
            """
            )
            invalid_items = cursor.fetchall()

            if not invalid_items:
                print("✅ All units are now valid!")
                return

            print(f"Found {len(invalid_items)} items with invalid units:")
            for item_id, product_name, unit, quantity in invalid_items:
                print(f"  - ID {item_id}: '{product_name}' - {quantity} '{unit}'")

                # Fix the unit - 'package' should map to 'ea' (each)
                if unit == "package":
                    cursor.execute(
                        """
                        UPDATE pantry_items 
                        SET unit_of_measurement = 'ea' 
                        WHERE pantry_item_id = %s
                    """,
                        (item_id,),
                    )
                    print(f"    → Fixed: 'package' → 'ea'")
                else:
                    # Default to 'ea' for any other invalid unit
                    cursor.execute(
                        """
                        UPDATE pantry_items 
                        SET unit_of_measurement = 'ea' 
                        WHERE pantry_item_id = %s
                    """,
                        (item_id,),
                    )
                    print(f"    → Fixed: '{unit}' → 'ea'")

        conn.commit()

        # Final verification
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) as invalid_count
                FROM pantry_items pi
                LEFT JOIN units u ON pi.unit_of_measurement = u.id
                WHERE pi.unit_of_measurement IS NOT NULL 
                AND u.id IS NULL
            """
            )
            invalid_count = cursor.fetchone()[0]

            if invalid_count == 0:
                print("\n🎉 All pantry items now have valid units!")
            else:
                print(f"\n⚠️  Still {invalid_count} items with invalid units")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    fix_remaining_unit()
