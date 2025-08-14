#!/usr/bin/env python3
"""
Script to split step 3 of the burger recipe at "Flatten" using API calls
"""

import requests
import json

API_BASE = "http://localhost:8002/api/v1"
USER_ID = 111

def main():
    """Main function to split burger recipe step 3 via API."""
    
    try:
        # First, let's try to get all user recipes to find the burger recipe
        print("🔍 Searching for burger recipe...")
        
        # Try different endpoints to find the recipes
        endpoints = [
            f"{API_BASE}/user-recipes?user_id={USER_ID}&page=1&per_page=50"
        ]
        
        recipes_data = None
        working_endpoint = None
        
        for endpoint in endpoints:
            print(f"  Trying: {endpoint}")
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    recipes_data = response.json()
                    working_endpoint = endpoint
                    print(f"  ✅ Success! Found {len(recipes_data) if isinstance(recipes_data, list) else 'unknown number of'} recipes")
                    break
                else:
                    print(f"  ❌ Status: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        if not recipes_data:
            print("❌ Could not find recipes via API!")
            return 1
        
        # Show all available recipes first
        print(f"\\nAvailable recipes:")
        all_recipes = recipes_data if isinstance(recipes_data, list) else recipes_data.get('recipes', [])
        for i, recipe in enumerate(all_recipes, 1):
            title = recipe.get('recipe_title', recipe.get('title', 'Unknown'))
            print(f"  {i}. {title}")
        
        # Look for burger recipe - prioritize the one with "Chipotle" or "Cheesy"
        burger_recipes = []
        if isinstance(recipes_data, list):
            for recipe in recipes_data:
                title = recipe.get('recipe_title', recipe.get('title', ''))
                if 'burger' in title.lower() or 'Burger' in title:
                    burger_recipes.append(recipe)
        elif isinstance(recipes_data, dict) and 'recipes' in recipes_data:
            for recipe in recipes_data['recipes']:
                title = recipe.get('recipe_title', recipe.get('title', ''))
                if 'burger' in title.lower() or 'Burger' in title:
                    burger_recipes.append(recipe)
        
        if not burger_recipes:
            print("❌ No burger recipes found!")
            return 1
        
        # Prioritize the one with "Chipotle" or "Cheesy" in the name
        burger_recipe = None
        for recipe in burger_recipes:
            title = recipe.get('recipe_title', recipe.get('title', ''))
            if 'chipotle' in title.lower() or 'cheesy' in title.lower():
                burger_recipe = recipe
                break
        
        # If no Chipotle/Cheesy recipe, use the first burger recipe
        if not burger_recipe:
            burger_recipe = burger_recipes[0]
        
        print(f"✅ Found burger recipe: {burger_recipe.get('recipe_title', burger_recipe.get('title'))}")
        
        # Get the recipe data
        recipe_data = burger_recipe.get('recipe_data')
        if not recipe_data:
            print("❌ No recipe_data found in burger recipe!")
            return 1
        
        # Check if it's a string that needs parsing
        if isinstance(recipe_data, str):
            recipe_data = json.loads(recipe_data)
        
        # Get current steps - check for different instruction formats
        current_steps = []
        
        if 'analyzedInstructions' in recipe_data and recipe_data['analyzedInstructions']:
            current_steps = recipe_data['analyzedInstructions'][0]['steps']
        elif 'instructions' in recipe_data and recipe_data['instructions']:
            # Convert instructions array to steps format
            instructions = recipe_data['instructions']
            if isinstance(instructions, list):
                for i, instruction in enumerate(instructions, 1):
                    current_steps.append({
                        'number': i,
                        'step': instruction
                    })
            elif isinstance(instructions, str):
                # Split string instructions by common patterns
                import re
                # Split on numbered steps or sentences
                step_parts = re.split(r'(?:\d+\.\s*|\n)', instructions.strip())
                step_parts = [part.strip() for part in step_parts if part.strip()]
                for i, step_text in enumerate(step_parts, 1):
                    current_steps.append({
                        'number': i,
                        'step': step_text
                    })
        
        if not current_steps:
            print("❌ No instructions found!")
            print(f"Recipe data keys: {list(recipe_data.keys())}")
            if 'instructions' in recipe_data:
                print(f"Instructions type: {type(recipe_data['instructions'])}")
                print(f"Instructions: {recipe_data['instructions'][:500]}...")
            return 1
        print(f"Current number of steps: {len(current_steps)}")
        
        # Show all current steps to find the one with "Flatten"
        flatten_step = None
        for step in current_steps:
            print(f"Step {step['number']}: {step['step']}")
            if 'Flatten' in step['step'] or 'flatten' in step['step']:
                flatten_step = step
        
        if not flatten_step:
            print("❌ No step contains 'Flatten'!")
            return 1
        
        print(f"\\n🎯 Found step with 'Flatten': Step {flatten_step['number']}")
        print(f"Current text: {flatten_step['step']}")
        
        # Find the split point
        step_text = flatten_step['step']
        flatten_index = step_text.find('Flatten')
        if flatten_index == -1:
            flatten_index = step_text.find('flatten')
        
        if flatten_index == -1:
            print("❌ 'Flatten' not found in step text!")
            return 1
        
        # Split the text
        new_step_text = step_text[:flatten_index].rstrip(". ")
        new_next_step_text = step_text[flatten_index:]
        
        print(f"\\nProposed split:")
        print(f"  Step {flatten_step['number']}: {new_step_text}")
        print(f"  Step {flatten_step['number'] + 1}: {new_next_step_text}")
        
        # Auto-proceed since we found the correct step
        print("\\nProceeding with the split...")
        
        # Create new steps list
        new_steps = []
        
        # Add steps before the flatten step unchanged
        for step in current_steps:
            if step['number'] < flatten_step['number']:
                new_steps.append(step)
        
        # Add the split flatten step
        new_steps.append({
            "number": flatten_step['number'],
            "step": new_step_text
        })
        
        # Add the new step (second part of original flatten step)
        new_steps.append({
            "number": flatten_step['number'] + 1,
            "step": new_next_step_text
        })
        
        # Add remaining steps with incremented numbers
        for step in current_steps:
            if step['number'] > flatten_step['number']:
                new_steps.append({
                    "number": step['number'] + 1,
                    "step": step['step']
                })
        
        # Update the recipe data
        recipe_data['analyzedInstructions'][0]['steps'] = new_steps
        
        # Also update the instructions array for consistency
        recipe_data['instructions'] = [step['step'] for step in new_steps]
        
        print(f"\\nNew recipe will have {len(new_steps)} steps (was {len(current_steps)})")
        
        # Update via API (this might require a PUT endpoint)
        recipe_id = burger_recipe.get('recipe_id')
        if recipe_id:
            update_data = {
                'recipe_data': recipe_data
            }
            
            # Try to update via API
            try:
                update_response = requests.put(f"{API_BASE}/user-recipes/{recipe_id}", json=update_data, timeout=30)
                if update_response.status_code in [200, 201]:
                    print("✅ Recipe updated via API!")
                else:
                    print(f"❌ Failed to update via API. Status: {update_response.status_code}")
                    print(f"Response: {update_response.text}")
                    return 1
            except Exception as e:
                print(f"❌ Error updating via API: {e}")
                return 1
        
        # Show the final steps
        print("\\n📋 Final Recipe Steps:")
        for i, step in enumerate(new_steps, 1):
            print(f"  Step {i}: {step['step'][:100]}{'...' if len(step['step']) > 100 else ''}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())