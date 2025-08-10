#!/usr/bin/env python3
"""Query completed recipes per user from PostgreSQL database"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

# Add parent directory to path to access backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()


def get_db_connection():
    """Create a database connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT", 5432),
            database=os.getenv("POSTGRES_DATABASE"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def query_completed_recipes():
    """Query completed recipes per user"""
    conn = get_db_connection()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First, check if there's a recipe_history table
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'recipe_history'
                );
            """
            )
            has_recipe_history = cursor.fetchone()["exists"]

            print("=" * 80)
            print("COMPLETED RECIPES PER USER")
            print("=" * 80)

            # Query for completed recipes in user_recipes table
            print("\n1. From user_recipes table (status = 'cooked'):")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    COUNT(ur.id) as completed_recipes,
                    COUNT(CASE WHEN ur.is_favorite THEN 1 END) as favorite_cooked,
                    COUNT(CASE WHEN ur.rating = 'thumbs_up' THEN 1 END) as liked_cooked,
                    MIN(ur.cooked_at) as first_cooked,
                    MAX(ur.cooked_at) as last_cooked
                FROM users u
                LEFT JOIN user_recipes ur ON u.user_id = ur.user_id AND ur.status = 'cooked'
                GROUP BY u.user_id, u.first_name, u.last_name, u.email
                ORDER BY completed_recipes DESC, u.first_name, u.last_name
            """
            )

            results = cursor.fetchall()

            # Format results for display
            table_data = []
            for row in results:
                full_name = f"{row['first_name']} {row['last_name']}"
                first_cooked = (
                    row["first_cooked"].strftime("%Y-%m-%d") if row["first_cooked"] else "Never"
                )
                last_cooked = (
                    row["last_cooked"].strftime("%Y-%m-%d") if row["last_cooked"] else "Never"
                )

                table_data.append(
                    [
                        row["user_id"],
                        full_name,
                        row["email"],
                        row["completed_recipes"],
                        row["favorite_cooked"],
                        row["liked_cooked"],
                        first_cooked,
                        last_cooked,
                    ]
                )

            print(
                tabulate(
                    table_data,
                    headers=[
                        "User ID",
                        "Name",
                        "Email",
                        "Completed",
                        "Favorites",
                        "Liked",
                        "First Cooked",
                        "Last Cooked",
                    ],
                    tablefmt="grid",
                )
            )

            # Summary statistics
            total_users = len(results)
            users_with_completed = sum(1 for r in results if r["completed_recipes"] > 0)
            total_completed = sum(r["completed_recipes"] for r in results)

            print("\nSummary:")
            print(f"  Total users: {total_users}")
            print(f"  Users who have cooked recipes: {users_with_completed}")
            print(f"  Total completed recipes: {total_completed}")
            if users_with_completed > 0:
                print(
                    f"  Average recipes per active user: {total_completed / users_with_completed:.1f}"
                )

            # Query for saved vs cooked recipes
            print("\n2. Saved vs Cooked recipes per user:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.first_name,
                    u.last_name,
                    COUNT(CASE WHEN ur.status = 'saved' THEN 1 END) as saved_recipes,
                    COUNT(CASE WHEN ur.status = 'cooked' THEN 1 END) as cooked_recipes,
                    COUNT(ur.id) as total_recipes,
                    CASE
                        WHEN COUNT(CASE WHEN ur.status = 'saved' THEN 1 END) > 0
                        THEN ROUND(COUNT(CASE WHEN ur.status = 'cooked' THEN 1 END)::numeric /
                                  COUNT(ur.id)::numeric * 100, 1)
                        ELSE 0
                    END as completion_rate
                FROM users u
                LEFT JOIN user_recipes ur ON u.user_id = ur.user_id
                GROUP BY u.user_id, u.first_name, u.last_name
                HAVING COUNT(ur.id) > 0
                ORDER BY completion_rate DESC, u.first_name, u.last_name
            """
            )

            results = cursor.fetchall()

            table_data = []
            for row in results:
                full_name = f"{row['first_name']} {row['last_name']}"
                table_data.append(
                    [
                        row["user_id"],
                        full_name,
                        row["saved_recipes"],
                        row["cooked_recipes"],
                        row["total_recipes"],
                        f"{row['completion_rate']}%",
                    ]
                )

            print(
                tabulate(
                    table_data,
                    headers=["User ID", "Name", "Saved", "Cooked", "Total", "Completion Rate"],
                    tablefmt="grid",
                )
            )

            # Check recipe_history table if it exists
            if has_recipe_history:
                print("\n3. Recipe history table analysis:")
                print("-" * 60)

                cursor.execute(
                    """
                    SELECT
                        u.user_id,
                        u.first_name,
                        u.last_name,
                        COUNT(rh.id) as history_entries
                    FROM users u
                    LEFT JOIN recipe_history rh ON u.user_id = rh.user_id
                    GROUP BY u.user_id, u.first_name, u.last_name
                    ORDER BY history_entries DESC
                """
                )

                results = cursor.fetchall()

                table_data = []
                for row in results:
                    full_name = f"{row['first_name']} {row['last_name']}"
                    table_data.append([row["user_id"], full_name, row["history_entries"]])

                print(
                    tabulate(
                        table_data, headers=["User ID", "Name", "History Entries"], tablefmt="grid"
                    )
                )
            else:
                print("\n3. No recipe_history table found in the database.")

            # Recent cooking activity
            print("\n4. Recent cooking activity (last 30 days):")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    u.first_name || ' ' || u.last_name as user_name,
                    ur.recipe_title,
                    ur.source,
                    ur.rating,
                    ur.cooked_at
                FROM user_recipes ur
                JOIN users u ON u.user_id = ur.user_id
                WHERE ur.status = 'cooked'
                AND ur.cooked_at IS NOT NULL
                AND ur.cooked_at >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY ur.cooked_at DESC
                LIMIT 10
            """
            )

            results = cursor.fetchall()

            if results:
                table_data = []
                for row in results:
                    cooked_date = row["cooked_at"].strftime("%Y-%m-%d %H:%M")
                    table_data.append(
                        [
                            row["user_name"],
                            (
                                row["recipe_title"][:40] + "..."
                                if len(row["recipe_title"]) > 40
                                else row["recipe_title"]
                            ),
                            row["source"],
                            row["rating"],
                            cooked_date,
                        ]
                    )

                print(
                    tabulate(
                        table_data,
                        headers=["User", "Recipe", "Source", "Rating", "Cooked At"],
                        tablefmt="grid",
                    )
                )
            else:
                print("No recipes cooked in the last 30 days.")

    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    query_completed_recipes()
