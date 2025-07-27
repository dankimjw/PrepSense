#!/usr/bin/env python3
"""
Check user preferences for user ID 111
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'database': os.getenv('POSTGRES_DATABASE'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def check_preferences(user_id=111):
    """Check all preferences for a user"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print(f"\n=== Checking preferences for user ID {user_id} ===\n")
        
        # Check user_preferences table
        cur.execute("""
            SELECT * FROM user_preferences WHERE user_id = %s
        """, (user_id,))
        prefs = cur.fetchone()
        
        if prefs:
            print("General Preferences:")
            print(f"  - Household size: {prefs['household_size']}")
            print(f"  - Preferences JSON: {prefs['preferences']}")
            print(f"  - Created: {prefs['created_at']}")
            print(f"  - Updated: {prefs['updated_at']}")
        else:
            print("No general preferences found")
        
        # Check dietary preferences
        cur.execute("""
            SELECT preference FROM user_dietary_preferences WHERE user_id = %s
        """, (user_id,))
        dietary = cur.fetchall()
        
        if dietary:
            print("\nDietary Preferences:")
            for d in dietary:
                print(f"  - {d['preference']}")
        else:
            print("\nNo dietary preferences found")
        
        # Check allergens
        cur.execute("""
            SELECT allergen FROM user_allergens WHERE user_id = %s
        """, (user_id,))
        allergens = cur.fetchall()
        
        if allergens:
            print("\nAllergens:")
            for a in allergens:
                print(f"  - {a['allergen']}")
        else:
            print("\nNo allergens found")
        
        # Check cuisine preferences
        cur.execute("""
            SELECT cuisine FROM user_cuisine_preferences WHERE user_id = %s
        """, (user_id,))
        cuisines = cur.fetchall()
        
        if cuisines:
            print("\nCuisine Preferences:")
            for c in cuisines:
                print(f"  - {c['cuisine']}")
        else:
            print("\nNo cuisine preferences found")
        
        # Check user info
        cur.execute("""
            SELECT username, email, first_name, last_name FROM users WHERE user_id = %s
        """, (user_id,))
        user = cur.fetchone()
        
        if user:
            print(f"\nUser Info:")
            print(f"  - Username: {user['username']}")
            print(f"  - Email: {user['email']}")
            print(f"  - Name: {user['first_name']} {user['last_name']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 111
    check_preferences(user_id)