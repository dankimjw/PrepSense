#!/usr/bin/env python3
"""
Script to split step 3 of the burger recipe at "Flatten" to create two separate steps
using direct psycopg2 connection (like add_burger_recipe.py)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main function to split burger recipe step 3."""
    
    # Database connection
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', 5432),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get the current burger recipe
        cur.execute("""
        SELECT recipe_title, recipe_data FROM user_recipes 
        WHERE user_id = 111 AND recipe_title LIKE %s
        ORDER BY created_at DESC
        LIMIT 1
        """, ('%Burger%',))
        
        result = cur.fetchone()
        
        if not result:
            print("❌ Burger recipe not found!")
            return 1
        
        recipe_data = result['recipe_data']
        print(f"✅ Found recipe: {recipe_data['title']}")
        
        # Get current steps
        current_steps = recipe_data['analyzedInstructions'][0]['steps']
        print(f"Current number of steps: {len(current_steps)}")
        
        # Find step 3 and split it
        step_3 = None
        for step in current_steps:
            if step['number'] == 3:
                step_3 = step
                break
        
        if not step_3:
            print("❌ Step 3 not found!")
            return 1
        
        current_step_3_text = step_3['step']
        print(f"\\nCurrent Step 3: {current_step_3_text}")
        
        # Split at "Flatten"
        if "Flatten" not in current_step_3_text:
            print("❌ 'Flatten' not found in step 3!")
            return 1
        
        # Find the split point
        flatten_index = current_step_3_text.find("Flatten")
        
        # Split the text - everything before "Flatten" becomes new step 3
        # Everything from "Flatten" onwards becomes new step 4
        new_step_3_text = current_step_3_text[:flatten_index].rstrip(". ")
        new_step_4_text = current_step_3_text[flatten_index:]
        
        print(f"\\nNew Step 3: {new_step_3_text}")
        print(f"New Step 4: {new_step_4_text}")
        
        # Confirm with user
        response = input("\\nDo you want to proceed with splitting step 3? (y/N): ").strip().lower()
        if response != 'y':
            print("Operation cancelled.")
            return 0
        
        # Create new steps list
        new_steps = []
        
        # Add steps 1 and 2 unchanged
        for step in current_steps:
            if step['number'] < 3:
                new_steps.append(step)
        
        # Add new step 3
        new_steps.append({
            "number": 3, 
            "step": new_step_3_text
        })
        
        # Add new step 4 (split from original step 3)
        new_steps.append({
            "number": 4, 
            "step": new_step_4_text
        })
        
        # Add remaining steps with incremented numbers
        for step in current_steps:
            if step['number'] > 3:
                new_steps.append({
                    "number": step['number'] + 1, 
                    "step": step['step']
                })
        
        # Update the recipe data
        recipe_data['analyzedInstructions'][0]['steps'] = new_steps
        
        # Also update the instructions array for consistency
        recipe_data['instructions'] = [step['step'] for step in new_steps]
        
        print(f"\\nNew recipe will have {len(new_steps)} steps (was {len(current_steps)})")
        
        # Update the database
        cur.execute("""
        UPDATE user_recipes 
        SET recipe_data = %s
        WHERE user_id = 111 AND recipe_title LIKE %s
        """, (json.dumps(recipe_data), '%Burger%'))
        
        conn.commit()
        print("✅ Recipe updated successfully!")
        
        # Show the final steps
        print("\\n📋 Final Recipe Steps:")
        for i, step in enumerate(new_steps, 1):
            print(f"  Step {i}: {step['step']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return 1
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    import sys
    sys.exit(main())