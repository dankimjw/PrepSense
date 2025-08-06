#!/usr/bin/env python3
"""
USDA Database Query Utility
A handy script for querying USDA food data, testing unit validations, and exploring the database.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


# Database connection
async def get_connection():
    """Get database connection."""
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DATABASE")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")

    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return await asyncpg.connect(db_url)


# Query functions
async def search_foods(query: str, limit: int = 20):
    """Search for foods by name."""
    conn = await get_connection()
    try:
        results = await conn.fetch(
            """
            SELECT 
                f.fdc_id,
                f.description,
                f.brand_owner,
                f.brand_name,
                fc.description as category
            FROM usda_foods f
            LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
            WHERE LOWER(f.description) LIKE LOWER($1)
            ORDER BY f.description
            LIMIT $2
        """,
            f"%{query}%",
            limit,
        )

        if results:
            print(f"\n🔍 Found {len(results)} foods matching '{query}':\n")
            data = [
                [
                    r["fdc_id"],
                    r["description"][:50],
                    r["brand_owner"] or "",
                    r["category"] or "Unknown",
                ]
                for r in results
            ]
            print(
                tabulate(
                    data, headers=["FDC ID", "Description", "Brand", "Category"], tablefmt="grid"
                )
            )
        else:
            print(f"\n❌ No foods found matching '{query}'")
    finally:
        await conn.close()


async def validate_unit(food_name: str, unit: str):
    """Validate if a unit is appropriate for a food."""
    conn = await get_connection()
    try:
        result = await conn.fetchrow(
            """
            SELECT * FROM validate_unit_for_food($1, $2)
        """,
            food_name,
            unit,
        )

        print(f"\n🧪 Validating '{unit}' for '{food_name}':")
        print(f"  Valid: {'✅' if result['is_valid'] else '❌'}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Reason: {result['reason']}")
        print(f"  Suggested units: {', '.join(result['suggested_units'])}")
    finally:
        await conn.close()


async def list_categories():
    """List all food categories."""
    conn = await get_connection()
    try:
        categories = await conn.fetch(
            """
            SELECT 
                fc.id,
                fc.code,
                fc.description,
                COUNT(f.fdc_id) as food_count
            FROM usda_food_categories fc
            LEFT JOIN usda_foods f ON f.food_category_id = fc.id
            GROUP BY fc.id, fc.code, fc.description
            ORDER BY fc.id
        """
        )

        print("\n📋 Food Categories:\n")
        data = [[c["id"], c["code"], c["description"], c["food_count"]] for c in categories]
        print(tabulate(data, headers=["ID", "Code", "Description", "Foods"], tablefmt="grid"))
    finally:
        await conn.close()


async def category_units(category_id: int):
    """Show units for a specific category."""
    conn = await get_connection()
    try:
        # Get category name
        category = await conn.fetchrow(
            """
            SELECT description FROM usda_food_categories WHERE id = $1
        """,
            category_id,
        )

        if not category:
            print(f"\n❌ Category {category_id} not found")
            return

        # Get units
        units = await conn.fetch(
            """
            SELECT 
                mu.name as unit,
                cum.usage_percentage,
                cum.is_preferred,
                mu.unit_type
            FROM usda_category_unit_mappings cum
            JOIN usda_measure_units mu ON cum.unit_id = mu.id
            WHERE cum.category_id = $1
            ORDER BY cum.is_preferred DESC, cum.usage_percentage DESC
        """,
            category_id,
        )

        print(f"\n📊 Units for {category['description']}:\n")
        data = [
            [
                u["unit"],
                f"{u['usage_percentage']:.0f}%",
                "⭐" if u["is_preferred"] else "",
                u["unit_type"],
            ]
            for u in units
        ]
        print(tabulate(data, headers=["Unit", "Usage", "Preferred", "Type"], tablefmt="grid"))
    finally:
        await conn.close()


async def food_details(fdc_id: int):
    """Show detailed information about a specific food."""
    conn = await get_connection()
    try:
        food = await conn.fetchrow(
            """
            SELECT 
                f.*,
                fc.description as category_name
            FROM usda_foods f
            LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
            WHERE f.fdc_id = $1
        """,
            fdc_id,
        )

        if not food:
            print(f"\n❌ Food with FDC ID {fdc_id} not found")
            return

        print(f"\n🍽️  Food Details (FDC ID: {fdc_id}):\n")
        print(f"  Description: {food['description']}")
        print(f"  Category: {food['category_name'] or 'Unknown'}")
        print(f"  Data Type: {food['data_type']}")
        if food["brand_owner"]:
            print(f"  Brand Owner: {food['brand_owner']}")
        if food["brand_name"]:
            print(f"  Brand Name: {food['brand_name']}")
        if food["gtin_upc"]:
            print(f"  Barcode: {food['gtin_upc']}")
        if food["serving_size"]:
            print(f"  Serving Size: {food['serving_size']} {food['serving_size_unit']}")

        # Show valid units for this food's category
        if food["food_category_id"]:
            print(f"\n  Valid units for {food['category_name']}:")
            units = await conn.fetch(
                """
                SELECT mu.name 
                FROM usda_category_unit_mappings cum
                JOIN usda_measure_units mu ON cum.unit_id = mu.id
                WHERE cum.category_id = $1 AND cum.is_preferred = TRUE
                ORDER BY cum.usage_percentage DESC
                LIMIT 5
            """,
                food["food_category_id"],
            )

            if units:
                print(f"  {', '.join([u['name'] for u in units])}")
    finally:
        await conn.close()


async def stats():
    """Show database statistics."""
    conn = await get_connection()
    try:
        # Get counts
        food_count = await conn.fetchval("SELECT COUNT(*) FROM usda_foods")
        category_count = await conn.fetchval("SELECT COUNT(*) FROM usda_food_categories")
        unit_count = await conn.fetchval("SELECT COUNT(*) FROM usda_measure_units")
        mapping_count = await conn.fetchval("SELECT COUNT(*) FROM usda_category_unit_mappings")

        print("\n📊 USDA Database Statistics:\n")
        print(f"  Foods: {food_count:,}")
        print(f"  Categories: {category_count}")
        print(f"  Units: {unit_count}")
        print(f"  Category-Unit Mappings: {mapping_count}")

        # Top categories by food count
        print("\n  Top 5 Categories by Food Count:")
        top_cats = await conn.fetch(
            """
            SELECT 
                fc.description,
                COUNT(f.fdc_id) as count
            FROM usda_food_categories fc
            JOIN usda_foods f ON f.food_category_id = fc.id
            GROUP BY fc.id, fc.description
            ORDER BY count DESC
            LIMIT 5
        """
        )

        for cat in top_cats:
            print(f"    - {cat['description']}: {cat['count']:,} foods")
    finally:
        await conn.close()


async def custom_query(sql: str):
    """Run a custom SQL query."""
    conn = await get_connection()
    try:
        # Only allow SELECT queries for safety
        if not sql.strip().upper().startswith("SELECT"):
            print("❌ Only SELECT queries are allowed")
            return

        results = await conn.fetch(sql)

        if results:
            print(f"\n✅ Query returned {len(results)} rows:\n")
            # Convert to list of lists for tabulate
            if len(results) > 0:
                headers = list(results[0].keys())
                data = [[row[col] for col in headers] for row in results]
                print(tabulate(data[:50], headers=headers, tablefmt="grid"))  # Limit to 50 rows
                if len(results) > 50:
                    print(f"\n... and {len(results) - 50} more rows")
        else:
            print("\n✅ Query executed successfully (no results)")
    except Exception as e:
        print(f"\n❌ Query error: {e}")
    finally:
        await conn.close()


# Main CLI
async def main():
    parser = argparse.ArgumentParser(description="USDA Database Query Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Search foods
    search_parser = subparsers.add_parser("search", help="Search for foods")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # Validate unit
    validate_parser = subparsers.add_parser("validate", help="Validate unit for food")
    validate_parser.add_argument("food", help="Food name")
    validate_parser.add_argument("unit", help="Unit to validate")

    # List categories
    subparsers.add_parser("categories", help="List all food categories")

    # Category units
    units_parser = subparsers.add_parser("units", help="Show units for a category")
    units_parser.add_argument("category_id", type=int, help="Category ID")

    # Food details
    details_parser = subparsers.add_parser("details", help="Show food details")
    details_parser.add_argument("fdc_id", type=int, help="FDC ID")

    # Stats
    subparsers.add_parser("stats", help="Show database statistics")

    # Custom query
    query_parser = subparsers.add_parser("query", help="Run custom SQL query")
    query_parser.add_argument("sql", help="SQL query (SELECT only)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == "search":
        await search_foods(args.query, args.limit)
    elif args.command == "validate":
        await validate_unit(args.food, args.unit)
    elif args.command == "categories":
        await list_categories()
    elif args.command == "units":
        await category_units(args.category_id)
    elif args.command == "details":
        await food_details(args.fdc_id)
    elif args.command == "stats":
        await stats()
    elif args.command == "query":
        await custom_query(args.sql)


if __name__ == "__main__":
    print("🗄️  USDA Database Query Utility")
    print("================================\n")

    asyncio.run(main())
