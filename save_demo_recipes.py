#!/usr/bin/env python3
import json
import subprocess

# Get AI-generated recipes first
print("Fetching AI-generated recipes...")
result = subprocess.run(
    ["curl", "-s", "http://localhost:8001/recipes/enhanced-openai?user_id=111&num_recipes=5"],
    capture_output=True,
    text=True
)

try:
    data = json.loads(result.stdout)
    recipes = data.get('recipes', [])
    print(f"Found {len(recipes)} AI-generated recipes")
    
    if recipes:
        saved_count = 0
        for i, recipe in enumerate(recipes[:5], 1):
            # Prepare recipe data
            recipe_data = {
                'recipe_title': recipe.get('title', recipe.get('name', f'Recipe {i}')),
                'ingredients': json.dumps(recipe.get('ingredients', [])),
                'instructions': json.dumps(recipe.get('instructions', [])),
                'nutrition_info': json.dumps(recipe.get('nutrition', {})),
                'cooking_time': recipe.get('time', 30),
                'servings': recipe.get('servings', 4),
                'image_url': recipe.get('image_url', 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400')
            }
            
            # Save using curl
            curl_cmd = [
                "curl", "-X", "POST",
                "http://localhost:8001/user-recipes/add?user_id=111",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(recipe_data),
                "-s"
            ]
            
            save_result = subprocess.run(curl_cmd, capture_output=True, text=True)
            
            if save_result.returncode == 0:
                try:
                    response = json.loads(save_result.stdout)
                    if 'recipe_id' in response or 'id' in response:
                        saved_count += 1
                        print(f"✓ Saved: {recipe_data['recipe_title'][:50]}")
                    else:
                        print(f"✗ Failed: {recipe_data['recipe_title'][:30]}")
                except:
                    print(f"✗ Failed: {recipe_data['recipe_title'][:30]} - Invalid response")
            else:
                print(f"✗ Failed: {recipe_data['recipe_title'][:30]} - Request error")
        
        print(f"\nTotal saved: {saved_count}/{min(5, len(recipes))}")
        
        # Verify saved recipes
        verify_result = subprocess.run(
            ["curl", "-s", "http://localhost:8001/user-recipes/111"],
            capture_output=True,
            text=True
        )
        
        if verify_result.returncode == 0:
            saved_recipes = json.loads(verify_result.stdout)
            print(f"\nVerification: User 111 now has {len(saved_recipes)} saved recipes:")
            for r in saved_recipes[:10]:
                print(f"  - {r.get('recipe_title', 'Unknown')[:50]}")
    else:
        print("No recipes generated. Check if OpenAI API is configured.")
        
except Exception as e:
    print(f"Error: {e}")