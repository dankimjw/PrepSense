#!/usr/bin/env python3
"""
Script to query and analyze chat-generated recipes from the user_recipes table.
Displays key information and statistics about recipes created through the chat interface.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from the project root
project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / '.env')


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return dt_str


def display_recipe_summary(recipe: Dict[str, Any]) -> None:
    """Display a formatted summary of a recipe"""
    print(f"\n{'='*60}")
    print(f"Recipe: {recipe.get('recipe_title', 'Untitled')}")
    print(f"{'='*60}")
    print(f"User ID: {recipe.get('user_id')}")
    print(f"Recipe ID: {recipe.get('id')}")
    print(f"Source: {recipe.get('source')}")
    print(f"Rating: {recipe.get('rating', 'neutral')}")
    print(f"Favorite: {'Yes' if recipe.get('is_favorite') else 'No'}")
    print(f"Times Cooked: {recipe.get('times_cooked', 0)}")
    print(f"Created: {format_datetime(recipe.get('created_at'))}")
    print(f"Last Modified: {format_datetime(recipe.get('updated_at'))}")
    
    # Display tags if available
    tags = recipe.get('tags', [])
    if tags:
        print(f"Tags: {', '.join(tags)}")
    
    # Display notes if available
    notes = recipe.get('notes')
    if notes:
        print(f"Notes: {notes}")


def query_chat_recipes(client: bigquery.Client) -> List[Dict[str, Any]]:
    """Query all recipes from chat source"""
    query = """
    SELECT 
        id,
        user_id,
        recipe_id,
        recipe_title,
        recipe_image,
        source,
        rating,
        is_favorite,
        times_cooked,
        notes,
        tags,
        created_at,
        updated_at,
        last_cooked_at
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat'
    ORDER BY created_at DESC
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def query_favorite_chat_recipes(client: bigquery.Client) -> List[Dict[str, Any]]:
    """Query favorite chat recipes"""
    query = """
    SELECT 
        id,
        user_id,
        recipe_title,
        rating,
        times_cooked,
        created_at
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat' AND is_favorite = TRUE
    ORDER BY created_at DESC
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_chat_recipe_stats(client: bigquery.Client) -> Dict[str, Any]:
    """Get statistics about chat recipes"""
    query = """
    SELECT 
        COUNT(*) as total_recipes,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(CASE WHEN is_favorite THEN 1 ELSE 0 END) as favorite_count,
        SUM(CASE WHEN rating = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up_count,
        SUM(CASE WHEN rating = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down_count,
        SUM(times_cooked) as total_times_cooked,
        AVG(times_cooked) as avg_times_cooked,
        MAX(times_cooked) as max_times_cooked
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat'
    """
    
    results = list(client.query(query).result())
    return dict(results[0]) if results else {}


def get_top_users(client: bigquery.Client, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top users by number of chat recipes saved"""
    query = f"""
    SELECT 
        user_id,
        COUNT(*) as recipe_count,
        SUM(CASE WHEN is_favorite THEN 1 ELSE 0 END) as favorites,
        SUM(times_cooked) as total_times_cooked
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat'
    GROUP BY user_id
    ORDER BY recipe_count DESC
    LIMIT {limit}
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def main():
    """Main function to run the chat recipe queries"""
    print("Chat Recipe Query Tool")
    print("======================\n")
    
    try:
        # Set up credentials
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path:
            # If it's a relative path, make it absolute relative to project root
            if not os.path.isabs(credentials_path):
                credentials_path = str(project_root / credentials_path)
        else:
            # Fallback to default location
            credentials_path = str(project_root / "config" / "adsp-34002-on02-prep-sense-ef1111b0833b.json")
            
        # Ensure path exists
        if not os.path.exists(credentials_path):
            print(f"Error: Credentials file not found at {credentials_path}")
            sys.exit(1)
            
        print(f"Using credentials from: {credentials_path}")
        
        # Initialize BigQuery client
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        client = bigquery.Client(credentials=credentials, project='adsp-34002-on02-prep-sense')
        print("✓ Connected to BigQuery\n")
        
        # Get overall statistics
        print("📊 Chat Recipe Statistics")
        print("-" * 30)
        stats = get_chat_recipe_stats(client)
        if stats:
            print(f"Total Chat Recipes: {stats.get('total_recipes', 0)}")
            print(f"Unique Users: {stats.get('unique_users', 0)}")
            print(f"Favorite Recipes: {stats.get('favorite_count', 0)}")
            print(f"Thumbs Up: {stats.get('thumbs_up_count', 0)}")
            print(f"Thumbs Down: {stats.get('thumbs_down_count', 0)}")
            print(f"Total Times Cooked: {stats.get('total_times_cooked', 0)}")
            avg_cooked = stats.get('avg_times_cooked', 0)
            print(f"Average Times Cooked: {float(avg_cooked) if avg_cooked else 0:.2f}")
            print(f"Max Times Cooked: {stats.get('max_times_cooked', 0)}")
        else:
            print("No chat recipes found in the database.")
            return
        
        # Get top users
        print("\n\n🏆 Top Users by Chat Recipes")
        print("-" * 30)
        top_users = get_top_users(client)
        for i, user in enumerate(top_users, 1):
            print(f"{i}. User {user['user_id']}: {user['recipe_count']} recipes "
                  f"({user['favorites']} favorites, cooked {user['total_times_cooked']} times)")
        
        # Query all chat recipes
        print("\n\n📝 All Chat Recipes")
        print("-" * 30)
        recipes = query_chat_recipes(client)
        
        if recipes:
            print(f"Found {len(recipes)} chat recipes.\n")
            
            # Display first 5 recipes in detail
            display_count = min(5, len(recipes))
            print(f"Showing first {display_count} recipes:")
            
            for recipe in recipes[:display_count]:
                display_recipe_summary(recipe)
            
            if len(recipes) > display_count:
                print(f"\n... and {len(recipes) - display_count} more recipes.")
        else:
            print("No chat recipes found.")
        
        # Show favorite chat recipes
        print("\n\n⭐ Favorite Chat Recipes")
        print("-" * 30)
        favorites = query_favorite_chat_recipes(client)
        
        if favorites:
            print(f"Found {len(favorites)} favorite chat recipes:\n")
            for recipe in favorites:
                print(f"- {recipe['recipe_title']} (User: {recipe['user_id']}, "
                      f"Cooked: {recipe['times_cooked']} times)")
        else:
            print("No favorite chat recipes found.")
        
        print("\n\n✓ Query completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()