#!/usr/bin/env python3
"""
Script to populate environmental impact data into the products table
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_environmental_data():
    """Load processed environmental impact data"""
    data_file = Path("data/environmental_impact/processed_impact_data.json")
    if not data_file.exists():
        raise FileNotFoundError(f"Environmental data not found at {data_file}")

    with open(data_file) as f:
        return json.load(f)


def update_products_with_environmental_data(conn, environmental_data):
    """Update products table with environmental impact data"""

    cursor = conn.cursor()

    # Prepare update data
    update_data = []
    for product_name, impact_data in environmental_data.items():
        env = impact_data["environmental"]
        profile = impact_data["sustainability_profile"]

        update_data.append(
            (
                env.get("ghg_kg_co2e_per_kg"),
                env.get("land_m2_per_kg"),
                env.get("water_L_per_kg"),
                env.get("eutrophying_g_per_kg"),
                profile["impact_category"],
                profile["planet_score"],
                profile["ghg_visual"],
                impact_data["owid_product"],
                datetime.now(),
                product_name.lower(),  # Match on lowercase product name
            )
        )

    # Update query
    update_query = """
        UPDATE products
        SET
            ghg_kg_co2e_per_kg = data.ghg,
            land_m2_per_kg = data.land,
            water_l_per_kg = data.water,
            eutrophying_g_per_kg = data.eutrophying,
            impact_category = data.category,
            planet_score = data.score,
            ghg_visual = data.visual,
            owid_product = data.owid,
            environmental_data_updated_at = data.updated_at
        FROM (VALUES %s) AS data(ghg, land, water, eutrophying, category, score, visual, owid, updated_at, name)
        WHERE LOWER(products.product_name) = data.name
           OR LOWER(products.product_name) LIKE '%' || data.name || '%'
    """

    try:
        execute_values(cursor, update_query, update_data)
        updated_count = cursor.rowcount
        conn.commit()
        logger.info(f"Updated {updated_count} products with environmental data")

        # Log some statistics
        cursor.execute(
            """
            SELECT
                impact_category,
                COUNT(*) as count,
                AVG(ghg_kg_co2e_per_kg) as avg_ghg
            FROM products
            WHERE impact_category IS NOT NULL
            GROUP BY impact_category
            ORDER BY
                CASE impact_category
                    WHEN 'very_low' THEN 1
                    WHEN 'low' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'high' THEN 4
                    WHEN 'very_high' THEN 5
                END
        """
        )

        logger.info("\nEnvironmental Impact Distribution:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} products (avg {row[2]:.2f} kg CO2e/kg)")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating products: {str(e)}")
        raise
    finally:
        cursor.close()


def main():
    """Main function"""
    # Load environmental data
    logger.info("Loading environmental impact data...")
    environmental_data = load_environmental_data()
    logger.info(f"Loaded data for {len(environmental_data)} food items")

    # Database connection parameters
    # These should match your .env configuration
    conn_params = {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", 5432),
        "database": os.environ.get("POSTGRES_DATABASE", "prepsense"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
    }

    # Connect to database
    logger.info("Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(**conn_params)
        logger.info("Connected successfully")

        # Update products with environmental data
        update_products_with_environmental_data(conn, environmental_data)

    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        if "conn" in locals():
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    import os
    import sys

    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    main()
