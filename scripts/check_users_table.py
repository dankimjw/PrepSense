#!/usr/bin/env python3
"""Check the structure of the users table"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add parent directory to path to access backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create a database connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def check_users_table():
    """Check the structure of the users table"""
    conn = get_db_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # List all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print("Tables in database:")
            for table in tables:
                print(f"  - {table['table_name']}")
            
            # Check if users table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            has_users_table = cursor.fetchone()['exists']
            
            if has_users_table:
                # Get columns of users table
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                print("\nColumns in 'users' table:")
                for col in columns:
                    print(f"  - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
                
                # Get sample data
                cursor.execute("SELECT * FROM users LIMIT 5;")
                users = cursor.fetchall()
                print(f"\nSample users (found {len(users)} users):")
                for user in users:
                    print(f"  - {user}")
            else:
                # Check for user table (singular)
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = 'user'
                    );
                """)
                has_user_table = cursor.fetchone()['exists']
                
                if has_user_table:
                    print("\nFound 'user' table (singular). Getting structure:")
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'user'
                        ORDER BY ordinal_position;
                    """)
                    
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"  - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
                    
                    # Get sample data
                    cursor.execute("SELECT * FROM \"user\" LIMIT 5;")
                    users = cursor.fetchall()
                    print(f"\nSample users from 'user' table (found {len(users)} users):")
                    for user in users:
                        print(f"  - {user}")
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_users_table()