#!/usr/bin/env python3
"""
Script to query and analyze chat-generated recipes from the user_recipes table with detailed information.
Displays comprehensive recipe data including ingredients, instructions, and metadata.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
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


def display_recipe_detailed(recipe: Dict[str, Any]) -> None:
    """Display a comprehensive view of a recipe including all details"""
    print(f"\n{'='*80}")
    print(f"Recipe: {recipe.get('recipe_title', 'Untitled')}")
    print(f"{'='*80}")
    
    # Basic Information
    print(f"\n📋 Basic Information:")
    print(f"  User ID: {recipe.get('user_id')}")
    print(f"  Recipe ID: {recipe.get('id')}")
    print(f"  Source: {recipe.get('source')}")
    print(f"  Rating: {recipe.get('rating', 'neutral')}")
    print(f"  Favorite: {'Yes' if recipe.get('is_favorite') else 'No'}")
    print(f"  Times Cooked: {recipe.get('times_cooked', 0)}")
    
    # Time Information
    print(f"\n⏰ Time Information:")
    prep_time = recipe.get('prep_time')
    cook_time = recipe.get('cook_time')
    total_time = recipe.get('total_time')
    
    if prep_time:
        print(f"  Prep Time: {prep_time} minutes")
    if cook_time:
        print(f"  Cook Time: {cook_time} minutes")
    if total_time:
        print(f"  Total Time: {total_time} minutes")
    
    # Servings
    servings = recipe.get('servings')
    if servings:
        print(f"  Servings: {servings}")
    
    # Dietary Information
    print(f"\n🥗 Dietary Information:")
    cuisine = recipe.get('cuisine', [])
    dish_type = recipe.get('dish_type', [])
    diet_labels = recipe.get('diet_labels', [])
    
    if cuisine:
        print(f"  Cuisine: {', '.join(cuisine)}")
    if dish_type:
        print(f"  Dish Type: {', '.join(dish_type)}")
    if diet_labels:
        print(f"  Diet Labels: {', '.join(diet_labels)}")
    
    # Tags
    tags = recipe.get('tags', [])
    if tags:
        print(f"  Tags: {', '.join(tags)}")
    
    # Recipe Data (ingredients, instructions, etc.)
    recipe_data = recipe.get('recipe_data')
    if recipe_data:
        try:
            # Parse JSON if it's a string
            if isinstance(recipe_data, str):
                recipe_data = json.loads(recipe_data)
            
            # Display ingredients
            ingredients = recipe_data.get('ingredients', [])
            if ingredients:
                print(f"\n🥘 Ingredients ({len(ingredients)} items):")
                for ing in ingredients:
                    amount = ing.get('amount', '')
                    unit = ing.get('unit', '')
                    name = ing.get('name', ing.get('item', ''))
                    if amount and unit:
                        print(f"  - {amount} {unit} {name}")
                    elif amount:
                        print(f"  - {amount} {name}")
                    else:
                        print(f"  - {name}")
            
            # Display instructions
            instructions = recipe_data.get('instructions', '')
            if instructions:
                print(f"\n📝 Instructions:")
                if isinstance(instructions, list):
                    for i, step in enumerate(instructions, 1):
                        print(f"  {i}. {step}")
                else:
                    # Handle multi-line instructions
                    lines = instructions.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            print(f"  {line.strip()}")
            
            # Display nutritional info if available
            nutrition = recipe_data.get('nutrition', {})
            if nutrition:
                print(f"\n🍎 Nutrition (per serving):")
                for key, value in nutrition.items():
                    if value:
                        print(f"  - {key.replace('_', ' ').title()}: {value}")
        
        except json.JSONDecodeError:
            print(f"\n  [Unable to parse recipe data]")
    
    # Notes
    notes = recipe.get('notes')
    if notes:
        print(f"\n📌 Notes: {notes}")
    
    # Timestamps
    print(f"\n🕐 Timestamps:")
    print(f"  Created: {format_datetime(recipe.get('created_at'))}")
    print(f"  Last Modified: {format_datetime(recipe.get('updated_at'))}")
    last_cooked = recipe.get('last_cooked_at')
    if last_cooked:
        print(f"  Last Cooked: {format_datetime(last_cooked)}")
    
    # Recipe Image
    image = recipe.get('recipe_image')
    if image:
        print(f"\n🖼️  Recipe Image: {image}")


def query_all_chat_recipe_details(client: bigquery.Client) -> List[Dict[str, Any]]:
    """Query all chat recipes with full details"""
    query = """
    SELECT 
        *
    FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
    WHERE source = 'chat'
    ORDER BY created_at DESC
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def export_recipes_to_json(recipes: List[Dict[str, Any]], filename: str) -> None:
    """Export recipes to a JSON file for backup or analysis"""
    # Convert datetime objects to strings
    for recipe in recipes:
        for key, value in recipe.items():
            if isinstance(value, datetime):
                recipe[key] = value.isoformat()
    
    output_path = Path(__file__).parent / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Recipes exported to: {output_path}")


def main():
    """Main function to run detailed chat recipe queries"""
    print("Chat Recipe Detailed Query Tool")
    print("===============================\n")
    
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
        
        # Query all chat recipes with full details
        print("📊 Querying all chat recipes with full details...")
        recipes = query_all_chat_recipe_details(client)
        
        if recipes:
            print(f"\nFound {len(recipes)} chat recipes.\n")
            
            # Display each recipe in detail
            for i, recipe in enumerate(recipes, 1):
                print(f"\n{'='*80}")
                print(f"RECIPE {i} OF {len(recipes)}")
                display_recipe_detailed(recipe)
            
            # Ask if user wants to export
            print(f"\n\n{'='*80}")
            response = input("\nWould you like to export these recipes to JSON? (y/n): ")
            if response.lower() == 'y':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_recipes_export_{timestamp}.json"
                export_recipes_to_json(recipes, filename)
        else:
            print("No chat recipes found in the database.")
        
        print("\n\n✓ Query completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()