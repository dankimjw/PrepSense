#!/usr/bin/env python3
"""Detailed analysis of recipe completion data"""

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


def analyze_recipe_completions():
    """Analyze recipe completion patterns"""
    conn = get_db_connection()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            print("=" * 80)
            print("RECIPE COMPLETION ANALYSIS")
            print("=" * 80)

            # 1. Overall statistics
            print("\n1. Overall Recipe Statistics:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT user_id) as total_users_with_recipes,
                    COUNT(*) as total_recipes,
                    COUNT(CASE WHEN status = 'saved' THEN 1 END) as saved_recipes,
                    COUNT(CASE WHEN status = 'cooked' THEN 1 END) as cooked_recipes,
                    COUNT(CASE WHEN is_favorite THEN 1 END) as favorite_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_up' THEN 1 END) as liked_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_down' THEN 1 END) as disliked_recipes,
                    COUNT(CASE WHEN source = 'spoonacular' THEN 1 END) as spoonacular_recipes,
                    COUNT(CASE WHEN source = 'chat' THEN 1 END) as ai_generated_recipes,
                    COUNT(CASE WHEN source = 'generated' THEN 1 END) as generated_recipes
                FROM user_recipes
            """
            )

            stats = cursor.fetchone()

            print(f"Total users with recipes: {stats['total_users_with_recipes']}")
            print(f"Total recipes saved: {stats['total_recipes']}")
            print(
                f"  - Saved (not cooked): {stats['saved_recipes']} ({stats['saved_recipes']/stats['total_recipes']*100:.1f}%)"
            )
            print(
                f"  - Cooked: {stats['cooked_recipes']} ({stats['cooked_recipes']/stats['total_recipes']*100:.1f}%)"
            )
            print("\nRecipe ratings:")
            print(f"  - Liked: {stats['liked_recipes']}")
            print(f"  - Disliked: {stats['disliked_recipes']}")
            print(f"  - Favorites: {stats['favorite_recipes']}")
            print("\nRecipe sources:")
            print(f"  - Spoonacular: {stats['spoonacular_recipes']}")
            print(f"  - AI Generated: {stats['ai_generated_recipes']}")
            print(f"  - Generated: {stats['generated_recipes']}")

            # 2. Cooked recipes details
            print("\n2. All Cooked Recipes:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    u.first_name || ' ' || u.last_name as user_name,
                    ur.recipe_title,
                    ur.source,
                    ur.rating,
                    ur.is_favorite,
                    ur.cooked_at,
                    ur.created_at,
                    (ur.cooked_at - ur.created_at) as time_to_cook
                FROM user_recipes ur
                JOIN users u ON u.user_id = ur.user_id
                WHERE ur.status = 'cooked'
                AND ur.cooked_at IS NOT NULL
                ORDER BY ur.cooked_at DESC
            """
            )

            cooked_recipes = cursor.fetchall()

            if cooked_recipes:
                table_data = []
                for recipe in cooked_recipes:
                    cooked_date = recipe["cooked_at"].strftime("%Y-%m-%d %H:%M")
                    saved_date = recipe["created_at"].strftime("%Y-%m-%d")
                    days_to_cook = recipe["time_to_cook"].days if recipe["time_to_cook"] else 0

                    table_data.append(
                        [
                            recipe["user_name"],
                            (
                                recipe["recipe_title"][:40] + "..."
                                if len(recipe["recipe_title"]) > 40
                                else recipe["recipe_title"]
                            ),
                            recipe["source"],
                            recipe["rating"],
                            "★" if recipe["is_favorite"] else "",
                            cooked_date,
                            saved_date,
                            f"{days_to_cook}d",
                        ]
                    )

                print(
                    tabulate(
                        table_data,
                        headers=[
                            "User",
                            "Recipe",
                            "Source",
                            "Rating",
                            "Fav",
                            "Cooked At",
                            "Saved At",
                            "Days",
                        ],
                        tablefmt="grid",
                    )
                )
            else:
                print("No cooked recipes found.")

            # 3. User engagement metrics
            print("\n3. User Engagement Metrics:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.first_name || ' ' || u.last_name as user_name,
                    COUNT(ur.id) as total_recipes,
                    COUNT(CASE WHEN ur.status = 'cooked' THEN 1 END) as cooked_count,
                    COUNT(CASE WHEN ur.is_favorite THEN 1 END) as favorites_count,
                    COUNT(CASE WHEN ur.rating = 'thumbs_up' THEN 1 END) as liked_count,
                    COUNT(CASE WHEN ur.rating = 'thumbs_down' THEN 1 END) as disliked_count,
                    MIN(ur.created_at) as first_recipe_date,
                    MAX(ur.created_at) as last_recipe_date,
                    MAX(ur.cooked_at) as last_cooked_date
                FROM users u
                LEFT JOIN user_recipes ur ON u.user_id = ur.user_id
                GROUP BY u.user_id, u.first_name, u.last_name
                HAVING COUNT(ur.id) > 0
                ORDER BY cooked_count DESC, total_recipes DESC
            """
            )

            users = cursor.fetchall()

            table_data = []
            for user in users:
                engagement_score = (
                    user["cooked_count"] * 3  # Cooking is highest value action
                    + user["favorites_count"] * 2
                    + user["liked_count"] * 1
                )

                days_active = (
                    (user["last_recipe_date"] - user["first_recipe_date"]).days
                    if user["first_recipe_date"]
                    else 0
                )

                table_data.append(
                    [
                        user["user_name"],
                        user["total_recipes"],
                        user["cooked_count"],
                        (
                            f"{user['cooked_count']/user['total_recipes']*100:.0f}%"
                            if user["total_recipes"] > 0
                            else "0%"
                        ),
                        user["favorites_count"],
                        user["liked_count"],
                        user["disliked_count"],
                        engagement_score,
                        f"{days_active}d",
                    ]
                )

            print(
                tabulate(
                    table_data,
                    headers=[
                        "User",
                        "Total",
                        "Cooked",
                        "Cook%",
                        "Favs",
                        "Likes",
                        "Dislikes",
                        "Score",
                        "Active",
                    ],
                    tablefmt="grid",
                )
            )

            print("\n* Engagement Score = (Cooked × 3) + (Favorites × 2) + (Likes × 1)")

            # 4. Recipe popularity (most saved recipes)
            print("\n4. Most Popular Recipes (by saves):")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    recipe_title,
                    COUNT(*) as save_count,
                    COUNT(CASE WHEN status = 'cooked' THEN 1 END) as cook_count,
                    COUNT(CASE WHEN is_favorite THEN 1 END) as favorite_count,
                    COUNT(CASE WHEN rating = 'thumbs_up' THEN 1 END) as like_count,
                    ARRAY_AGG(DISTINCT source) as sources
                FROM user_recipes
                GROUP BY recipe_title
                HAVING COUNT(*) > 1
                ORDER BY save_count DESC
                LIMIT 10
            """
            )

            popular_recipes = cursor.fetchall()

            if popular_recipes:
                table_data = []
                for recipe in popular_recipes:
                    sources = ", ".join(recipe["sources"])
                    table_data.append(
                        [
                            (
                                recipe["recipe_title"][:50] + "..."
                                if len(recipe["recipe_title"]) > 50
                                else recipe["recipe_title"]
                            ),
                            recipe["save_count"],
                            recipe["cook_count"],
                            recipe["favorite_count"],
                            recipe["like_count"],
                            sources,
                        ]
                    )

                print(
                    tabulate(
                        table_data,
                        headers=["Recipe", "Saves", "Cooked", "Favs", "Likes", "Sources"],
                        tablefmt="grid",
                    )
                )
            else:
                print("No recipes saved by multiple users.")

            # 5. Cooking patterns by day of week
            print("\n5. Cooking Patterns:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    TO_CHAR(cooked_at, 'Day') as day_of_week,
                    EXTRACT(DOW FROM cooked_at) as day_num,
                    COUNT(*) as recipes_cooked,
                    COUNT(DISTINCT user_id) as unique_users
                FROM user_recipes
                WHERE status = 'cooked' AND cooked_at IS NOT NULL
                GROUP BY TO_CHAR(cooked_at, 'Day'), EXTRACT(DOW FROM cooked_at)
                ORDER BY day_num
            """
            )

            cooking_patterns = cursor.fetchall()

            if cooking_patterns:
                print("Recipes cooked by day of week:")
                for day in cooking_patterns:
                    print(
                        f"  {day['day_of_week'].strip()}: {day['recipes_cooked']} recipes by {day['unique_users']} users"
                    )

            # 6. Recipe source performance
            print("\n6. Recipe Source Performance:")
            print("-" * 60)

            cursor.execute(
                """
                SELECT
                    source,
                    COUNT(*) as total_saved,
                    COUNT(CASE WHEN status = 'cooked' THEN 1 END) as total_cooked,
                    ROUND(COUNT(CASE WHEN status = 'cooked' THEN 1 END)::numeric / COUNT(*)::numeric * 100, 1) as cook_rate,
                    COUNT(CASE WHEN rating = 'thumbs_up' THEN 1 END) as thumbs_up,
                    COUNT(CASE WHEN rating = 'thumbs_down' THEN 1 END) as thumbs_down,
                    COUNT(CASE WHEN is_favorite THEN 1 END) as favorites
                FROM user_recipes
                GROUP BY source
                ORDER BY total_saved DESC
            """
            )

            sources = cursor.fetchall()

            table_data = []
            for source in sources:
                table_data.append(
                    [
                        source["source"],
                        source["total_saved"],
                        source["total_cooked"],
                        f"{source['cook_rate']}%",
                        source["thumbs_up"],
                        source["thumbs_down"],
                        source["favorites"],
                    ]
                )

            print(
                tabulate(
                    table_data,
                    headers=["Source", "Saved", "Cooked", "Cook Rate", "👍", "👎", "⭐"],
                    tablefmt="grid",
                )
            )

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    analyze_recipe_completions()
