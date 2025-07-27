#!/usr/bin/env python3
"""
Import 13k recipe dataset from CSV into PostgreSQL database
"""

import os
import sys
import csv
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import re
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'database': os.getenv('POSTGRES_DATABASE'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'sslmode': 'require'
}

# Data paths
CSV_PATH = '/Users/danielkim/_Capstone/PrepSense/Food Data/recipe-dataset-main/13k-recipes.csv'

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def clean_text(text: str) -> str:
    """Clean recipe text"""
    if not text:
        return ""
    # Remove extra quotes and clean up
    text = text.strip('"\'')
    text = text.replace('\\n', '\n')
    text = text.replace('\\"', '"')
    return text

def parse_ingredients(ingredients_str: str) -> List[str]:
    """Parse ingredients string into list"""
    if not ingredients_str:
        return []
    
    # Clean the string
    ingredients_str = clean_text(ingredients_str)
    
    try:
        # Try to parse as Python list
        if ingredients_str.startswith('[') and ingredients_str.endswith(']'):
            ingredients = eval(ingredients_str)
            if isinstance(ingredients, list):
                return [clean_text(str(ing)) for ing in ingredients]
    except:
        pass
    
    # Fallback: split by newlines or numbered list
    lines = ingredients_str.split('\n')
    ingredients = []
    for line in lines:
        # Remove numbering (1., 2., etc)
        line = re.sub(r'^\d+\.\s*', '', line.strip())
        if line:
            ingredients.append(line)
    
    return ingredients

def parse_instructions(instructions_str: str) -> List[str]:
    """Parse instructions into steps"""
    if not instructions_str:
        return []
    
    instructions_str = clean_text(instructions_str)
    
    # Split by numbered steps or sentences
    steps = []
    
    # Try numbered steps first
    numbered_pattern = r'\d+\.\s*'
    if re.search(numbered_pattern, instructions_str):
        parts = re.split(numbered_pattern, instructions_str)
        steps = [part.strip() for part in parts if part.strip()]
    else:
        # Split by periods but keep some context
        sentences = instructions_str.split('. ')
        current_step = ""
        for sentence in sentences:
            current_step += sentence.strip() + ". "
            # Group every 2-3 sentences into a step
            if len(current_step) > 100 or sentence == sentences[-1]:
                steps.append(current_step.strip())
                current_step = ""
    
    return steps

def estimate_cooking_time(title: str, instructions: str) -> int:
    """Estimate cooking time from recipe content"""
    text = (title + " " + instructions).lower()
    
    # Look for time mentions
    time_patterns = [
        (r'(\d+)\s*hours?', 60),  # hours to minutes
        (r'(\d+)\s*minutes?', 1),  # minutes
        (r'(\d+)\s*mins?', 1),     # mins
    ]
    
    total_minutes = 30  # default
    
    for pattern, multiplier in time_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                time_value = int(match) * multiplier
                if time_value > total_minutes:
                    total_minutes = time_value
            except:
                pass
    
    # Cap at reasonable limits
    return min(total_minutes, 240)  # max 4 hours

def categorize_recipe(title: str, ingredients: List[str]) -> Dict:
    """Categorize recipe by cuisine and difficulty"""
    title_lower = title.lower()
    ingredients_text = ' '.join(ingredients).lower()
    
    # Cuisine detection
    cuisine_keywords = {
        'italian': ['pasta', 'risotto', 'italian', 'marinara', 'pesto', 'parmesan'],
        'mexican': ['taco', 'burrito', 'mexican', 'salsa', 'cilantro', 'lime'],
        'asian': ['soy sauce', 'ginger', 'sesame', 'teriyaki', 'stir fry', 'rice'],
        'indian': ['curry', 'masala', 'naan', 'tandoori', 'tikka', 'turmeric'],
        'american': ['burger', 'bbq', 'mac and cheese', 'fried chicken', 'sandwich'],
        'mediterranean': ['greek', 'hummus', 'feta', 'olive oil', 'tzatziki'],
        'french': ['french', 'croissant', 'baguette', 'crepe', 'ratatouille']
    }
    
    cuisine = 'international'
    for cuisine_type, keywords in cuisine_keywords.items():
        if any(kw in title_lower or kw in ingredients_text for kw in keywords):
            cuisine = cuisine_type
            break
    
    # Difficulty based on number of ingredients and steps
    difficulty = 'easy'
    if len(ingredients) > 15:
        difficulty = 'hard'
    elif len(ingredients) > 8:
        difficulty = 'medium'
    
    return {
        'cuisine_type': cuisine,
        'difficulty': difficulty
    }

def import_recipes():
    """Import recipes from CSV into database"""
    print("Connecting to database...")
    conn = get_connection()
    cur = conn.cursor()
    print("Connected successfully!")
    
    # Track stats
    total_recipes = 0
    imported_recipes = 0
    skipped_recipes = 0
    
    try:
        # Clear existing recipes if needed (optional)
        # cur.execute("DELETE FROM recipe_ingredients")
        # cur.execute("DELETE FROM recipes WHERE recipe_id > 10000")
        
        # Open CSV file
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Start recipe ID from 20001 to avoid conflicts
            recipe_id = 20001
            
            for row in reader:
                total_recipes += 1
                
                # Extract data
                title = clean_text(row.get('Title', ''))
                ingredients_str = row.get('Ingredients', '')
                instructions_str = row.get('Instructions', '')
                image_name = row.get('Image_Name', '')
                
                # Skip if missing essential data
                if not title or not ingredients_str:
                    skipped_recipes += 1
                    continue
                
                # Parse data
                ingredients = parse_ingredients(ingredients_str)
                instructions = parse_instructions(instructions_str)
                
                # Skip if parsing failed
                if not ingredients:
                    skipped_recipes += 1
                    continue
                
                # Estimate metadata
                cook_time = estimate_cooking_time(title, instructions_str)
                categories = categorize_recipe(title, ingredients)
                
                # Prepare recipe data
                recipe_data = {
                    'ingredients': ingredients,
                    'instructions': instructions,
                    'total_time': cook_time,
                    'image_name': image_name
                }
                
                # Insert recipe
                cur.execute("""
                    INSERT INTO recipes (
                        recipe_id, recipe_name, cuisine_type, 
                        prep_time, cook_time, servings, difficulty, 
                        recipe_data, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (recipe_id) DO NOTHING
                """, (
                    recipe_id,
                    title[:200],  # Limit title length
                    categories['cuisine_type'],
                    cook_time // 3,  # Estimate prep as 1/3 of total
                    cook_time,
                    4,  # Default servings
                    categories['difficulty'],
                    json.dumps(recipe_data),
                    datetime.now()
                ))
                
                # Insert ingredients into recipe_ingredients table
                for ingredient in ingredients[:20]:  # Limit to 20 ingredients
                    # Basic parsing to extract quantity and unit
                    match = re.match(r'^([\d\.\/\s]+)?\s*([a-zA-Z]+)?\s*(.+)$', ingredient)
                    if match:
                        quantity_str = match.group(1) or '1'
                        unit = match.group(2) or 'unit'
                        name = match.group(3) or ingredient
                        
                        # Try to convert quantity
                        try:
                            # Handle fractions
                            if '/' in quantity_str:
                                parts = quantity_str.split('/')
                                quantity = float(parts[0]) / float(parts[1])
                            else:
                                quantity = float(quantity_str.strip())
                        except:
                            quantity = 1.0
                        
                        cur.execute("""
                            INSERT INTO recipe_ingredients (
                                recipe_id, ingredient_name, quantity, unit, is_optional
                            ) VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (
                            recipe_id,
                            name[:100],  # Limit name length
                            quantity,
                            unit[:50],   # Limit unit length
                            False
                        ))
                
                imported_recipes += 1
                recipe_id += 1
                
                # Progress update
                if imported_recipes % 100 == 0:
                    conn.commit()
                    print(f"Imported {imported_recipes} recipes...")
                
                # Limit batch to 5000 recipes
                if imported_recipes >= 5000:
                    print(f"\n🛑 Stopping at {imported_recipes} recipes for this batch")
                    break
        
        # Final commit
        conn.commit()
        
        print(f"\n✅ Import complete!")
        print(f"Total recipes in CSV: {total_recipes}")
        print(f"Successfully imported: {imported_recipes}")
        print(f"Skipped (missing data): {skipped_recipes}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during import: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Starting 13k recipe import...")
    import_recipes()