#!/usr/bin/env python3
"""
Script to properly split step 3 of the burger recipe at "Flatten" 
using direct database access with proper HTML handling
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_html_instructions(html_text):
    """Clean HTML from instructions and return proper step structure."""
    if not html_text:
        return []
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Split into logical steps - look for patterns like numbered lists or line breaks
    # First try to split on common step indicators
    steps = []
    
    # Split on line breaks first
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    
    if len(lines) <= 1:
        # If no line breaks, try to split on sentence boundaries that look like step separators
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean_text)
        lines = [s.strip() for s in sentences if s.strip()]
    
    # Combine short lines that seem to belong together
    combined_lines = []
    current_line = ""
    
    for line in lines:
        if len(line) < 50 and current_line and not line.endswith('.'):
            current_line += " " + line
        else:
            if current_line:
                combined_lines.append(current_line)
            current_line = line
    
    if current_line:
        combined_lines.append(current_line)
    
    # Convert to step structure
    for i, line in enumerate(combined_lines, 1):
        steps.append({
            'number': i,
            'step': line
        })
    
    return steps

def main():
    """Main function to fix the burger recipe step splitting."""
    
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
        # Get the burger recipe
        cur.execute("""
        SELECT recipe_title, recipe_data FROM user_recipes 
        WHERE user_id = 111 AND recipe_title LIKE %s
        ORDER BY created_at DESC
        LIMIT 1
        """, ('%Chipotle%',))
        
        result = cur.fetchone()
        
        if not result:
            print("❌ Burger recipe not found!")
            return 1
        
        recipe_data = result['recipe_data']
        print(f"✅ Found recipe: {recipe_data['title']}")
        
        # Check current instructions format
        instructions = recipe_data.get('instructions', [])
        print(f"Current instructions type: {type(instructions)}")
        print(f"Current instructions length: {len(instructions) if isinstance(instructions, (list, str)) else 'Unknown'}")
        
        # If instructions is a string (likely HTML), clean it up
        if isinstance(instructions, str):
            print("🧹 Cleaning HTML instructions...")
            cleaned_steps = clean_html_instructions(instructions)
            print(f"Extracted {len(cleaned_steps)} steps")
            
            for i, step in enumerate(cleaned_steps, 1):
                print(f"Step {i}: {step['step'][:100]}{'...' if len(step['step']) > 100 else ''}")
            
        elif isinstance(instructions, list) and len(instructions) > 900:
            print("❌ Instructions appear to be corrupted (too many steps)")
            print("This needs to be restored from backup or manually fixed")
            return 1
            
        else:
            print(f"Instructions format looks normal: {len(instructions)} steps")
            cleaned_steps = []
            for i, instruction in enumerate(instructions, 1):
                cleaned_steps.append({
                    'number': i,
                    'step': instruction
                })
        
        # Find the step with "Flatten"
        flatten_step = None
        flatten_step_index = -1
        
        for i, step in enumerate(cleaned_steps):
            if 'Flatten' in step['step'] or 'flatten' in step['step']:
                flatten_step = step
                flatten_step_index = i
                break
        
        if not flatten_step:
            print("❌ No step contains 'Flatten'!")
            print("Available steps:")
            for step in cleaned_steps:
                print(f"  Step {step['number']}: {step['step'][:100]}...")
            return 1
        
        print(f"\\n🎯 Found step {flatten_step['number']} with 'Flatten':")
        print(f"Current text: {flatten_step['step']}")
        
        # Split at "Flatten"
        step_text = flatten_step['step']
        flatten_pos = step_text.find('Flatten')
        if flatten_pos == -1:
            flatten_pos = step_text.find('flatten')
        
        if flatten_pos == -1:
            print("❌ 'Flatten' not found in step text!")
            return 1
        
        # Split the text
        before_flatten = step_text[:flatten_pos].rstrip('. ')
        from_flatten = step_text[flatten_pos:]
        
        print(f"\\nProposed split:")
        print(f"  New Step {flatten_step['number']}: {before_flatten}")
        print(f"  New Step {flatten_step['number'] + 1}: {from_flatten}")
        
        # Create new steps list
        new_steps = []
        
        # Add steps before the flatten step
        for i in range(flatten_step_index):
            new_steps.append(cleaned_steps[i])
        
        # Add the split flatten step
        new_steps.append({
            'number': flatten_step['number'],
            'step': before_flatten
        })
        
        # Add the new step (second part)
        new_steps.append({
            'number': flatten_step['number'] + 1,
            'step': from_flatten
        })
        
        # Add remaining steps with incremented numbers
        for i in range(flatten_step_index + 1, len(cleaned_steps)):
            original_step = cleaned_steps[i]
            new_steps.append({
                'number': original_step['number'] + 1,
                'step': original_step['step']
            })
        
        print(f"\\nNew recipe will have {len(new_steps)} steps (was {len(cleaned_steps)})")
        
        # Update the recipe data structure
        recipe_data['instructions'] = [step['step'] for step in new_steps]
        
        # Also create analyzedInstructions format for compatibility
        recipe_data['analyzedInstructions'] = [{
            'name': '',
            'steps': new_steps
        }]
        
        # Update the database
        print("\\n💾 Updating database...")
        cur.execute("""
        UPDATE user_recipes 
        SET recipe_data = %s
        WHERE user_id = 111 AND recipe_title LIKE %s
        """, (json.dumps(recipe_data), '%Chipotle%'))
        
        conn.commit()
        print("✅ Recipe updated successfully!")
        
        # Show final steps
        print("\\n📋 Final Recipe Steps:")
        for i, step in enumerate(new_steps):
            print(f"  Step {step['number']}: {step['step'][:100]}{'...' if len(step['step']) > 100 else ''}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return 1
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    import sys
    sys.exit(main())