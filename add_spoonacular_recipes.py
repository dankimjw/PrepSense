#!/usr/bin/env python3
"""
Add 2 Spoonacular recipes to user 111's saved recipes for AI chef chat
"""
import json
import subprocess

def fetch_spoonacular_recipes(number=2):
    """Fetch random recipes from Spoonacular API via backend"""
    curl_cmd = [
        "curl", "-s",
        f"http://localhost:8001/api/v1/recipes/random?number={number}"
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            if 'recipes' in response:
                return response['recipes']
            else:
                print(f"No recipes found in response: {response}")
                return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {result.stdout}")
            return []
    else:
        print(f"Failed to fetch recipes. Error: {result.stderr}")
        return []

def save_spoonacular_recipe_as_user_recipe(recipe):
    """Convert Spoonacular recipe to user recipe format and save it"""
    
    # Extract and format ingredients
    ingredients = []
    if 'extendedIngredients' in recipe:
        for ing in recipe['extendedIngredients']:
            ingredients.append({
                'name': ing.get('name', ing.get('originalName', 'Unknown')),
                'amount': ing.get('amount', 1),
                'unit': ing.get('unit', ''),
                'category': ing.get('aisle', 'other').lower()
            })
    
    # Extract and format instructions
    instructions = []
    if 'analyzedInstructions' in recipe and recipe['analyzedInstructions']:
        for instruction_group in recipe['analyzedInstructions']:
            if 'steps' in instruction_group:
                for step in instruction_group['steps']:
                    instructions.append(step.get('step', ''))
    elif 'instructions' in recipe:
        # Fallback if instructions are in a different format
        instructions = [recipe['instructions']]
    
    # Prepare nutrition info
    nutrition = {}
    if 'nutrition' in recipe:
        nutrients = recipe['nutrition'].get('nutrients', [])
        for nutrient in nutrients:
            name = nutrient.get('name', '').lower()
            if 'calorie' in name:
                nutrition['calories'] = nutrient.get('amount', 0)
            elif 'protein' in name:
                nutrition['protein'] = nutrient.get('amount', 0)
            elif 'carbohydrate' in name or 'carbs' in name:
                nutrition['carbs'] = nutrient.get('amount', 0)
            elif 'fat' in name and 'saturated' not in name:
                nutrition['fat'] = nutrient.get('amount', 0)
            elif 'fiber' in name:
                nutrition['fiber'] = nutrient.get('amount', 0)
    
    # Create user recipe data structure
    recipe_data = {
        'recipe_id': recipe.get('id'),
        'recipe_title': recipe.get('title', 'Untitled Recipe'),
        'recipe_image': recipe.get('image'),
        'recipe_data': {
            'ingredients': ingredients,
            'instructions': instructions,
            'nutrition': nutrition,
            'tags': recipe.get('dishTypes', []) + recipe.get('cuisines', []),
            'difficulty': 'medium',
            'prep_time': recipe.get('preparationMinutes', 15),
            'cook_time': recipe.get('cookingMinutes', 30),
            'total_time': recipe.get('readyInMinutes', 45),
            'servings': recipe.get('servings', 4),
            'external_recipe_id': recipe.get('id'),
            'spoonacular_score': recipe.get('spoonacularScore', 0),
            'health_score': recipe.get('healthScore', 0),
            'source_url': recipe.get('sourceUrl'),
            'spoonacular_url': recipe.get('spoonacularSourceUrl')
        },
        'source': 'spoonacular',
        'rating': 'neutral',
        'is_favorite': False,
        'is_demo': False
    }
    
    # Save via API
    curl_cmd = [
        "curl", "-X", "POST",
        "http://localhost:8001/api/v1/user-recipes?user_id=111",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(recipe_data),
        "-s"
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            if response.get('success'):
                print(f"✓ Saved: {recipe_data['recipe_title']}")
                return True
            else:
                print(f"✗ Failed: {recipe_data['recipe_title']} - {response}")
                return False
        except json.JSONDecodeError:
            print(f"✗ Failed: {recipe_data['recipe_title']} - Invalid response")
            print(f"Response: {result.stdout}")
            return False
    else:
        print(f"✗ Failed: {recipe_data['recipe_title']} - Request error")
        return False

def main():
    print("Fetching 2 random Spoonacular recipes...")
    
    recipes = fetch_spoonacular_recipes(2)
    
    if not recipes:
        print("No recipes fetched. Exiting.")
        return
    
    print(f"Fetched {len(recipes)} recipes from Spoonacular")
    
    success_count = 0
    for i, recipe in enumerate(recipes, 1):
        print(f"\nProcessing recipe {i}: {recipe.get('title', 'Untitled')}")
        if save_spoonacular_recipe_as_user_recipe(recipe):
            success_count += 1
    
    print(f"\nSummary: Successfully saved {success_count}/{len(recipes)} Spoonacular recipes")
    
    # Verify results
    print("\nVerifying saved recipes...")
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8001/api/v1/user-recipes/stats"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        try:
            stats = json.loads(result.stdout)
            print(f"Total saved recipes: {stats.get('saved_recipes', 0)}")
            print(f"Total bookmarked external recipes: {stats.get('bookmarked_external_recipes', 0)}")
        except json.JSONDecodeError:
            print("Could not verify stats")
    
    print("Done!")

if __name__ == "__main__":
    main()