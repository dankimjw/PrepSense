#!/usr/bin/env python3
"""
Check the status of embeddings in the database
"""

import psycopg2
import os
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

def check_embedding_status():
    """Check how many items have/need embeddings"""
    
    # Get database credentials
    db_config = {
        'host': os.getenv('POSTGRES_HOST'),
        'database': os.getenv('POSTGRES_DATABASE'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    print("📊 PrepSense Embedding Status")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check recipes
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(embedding) as with_embedding,
                COUNT(*) - COUNT(embedding) as need_embedding
            FROM recipes
        """)
        recipes = cursor.fetchone()
        
        # Check products
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(embedding) as with_embedding,
                COUNT(*) - COUNT(embedding) as need_embedding
            FROM products
        """)
        products = cursor.fetchone()
        
        # Check pantry items
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(embedding) as with_embedding,
                COUNT(*) - COUNT(embedding) as need_embedding
            FROM pantry_items
        """)
        pantry_items = cursor.fetchone()
        
        # Display results
        data = [
            ["Recipes", recipes[0], recipes[1], recipes[2]],
            ["Products", products[0], products[1], products[2]],
            ["Pantry Items", pantry_items[0], pantry_items[1], pantry_items[2]],
            ["─" * 12, "─" * 8, "─" * 12, "─" * 12],
            ["Total", 
             recipes[0] + products[0] + pantry_items[0],
             recipes[1] + products[1] + pantry_items[1],
             recipes[2] + products[2] + pantry_items[2]]
        ]
        
        headers = ["Entity Type", "Total", "Has Embedding", "Needs Embedding"]
        print(tabulate(data, headers=headers, tablefmt="simple"))
        
        # Get sample items without embeddings
        print("\n📝 Sample items needing embeddings:")
        
        # Sample recipes
        cursor.execute("""
            SELECT id, name 
            FROM recipes 
            WHERE embedding IS NULL 
            LIMIT 5
        """)
        sample_recipes = cursor.fetchall()
        if sample_recipes:
            print("\nRecipes:")
            for id, name in sample_recipes:
                print(f"  - [{id}] {name}")
        
        # Sample products
        cursor.execute("""
            SELECT id, name, brand 
            FROM products 
            WHERE embedding IS NULL 
            LIMIT 5
        """)
        sample_products = cursor.fetchall()
        if sample_products:
            print("\nProducts:")
            for id, name, brand in sample_products:
                print(f"  - [{id}] {name} ({brand or 'No brand'})")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    check_embedding_status()