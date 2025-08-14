#!/usr/bin/env python3
"""
Add 2 more saved recipes for user 111 to show in AI chef chat
"""
import json
import subprocess

def add_recipe(recipe_data):
    """Add a recipe via API call"""
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
        except:
            print(f"✗ Failed: {recipe_data['recipe_title']} - Invalid response")
            print(f"Response: {result.stdout}")
            return False
    else:
        print(f"✗ Failed: {recipe_data['recipe_title']} - Request error")
        return False

def main():
    print("Adding 2 more saved recipes for user 111...")
    
    # Recipe 1: Mediterranean Chickpea Salad
    recipe1 = {
        'recipe_title': 'Mediterranean Chickpea Salad',
        'recipe_image': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400',
        'recipe_data': {
            'ingredients': [
                {'name': 'chickpeas', 'amount': 2, 'unit': 'cups', 'category': 'protein'},
                {'name': 'cucumber', 'amount': 1, 'unit': 'large', 'category': 'vegetables'},
                {'name': 'cherry tomatoes', 'amount': 1, 'unit': 'cup', 'category': 'vegetables'},
                {'name': 'red onion', 'amount': 0.25, 'unit': 'cup', 'category': 'vegetables'},
                {'name': 'feta cheese', 'amount': 0.5, 'unit': 'cup', 'category': 'dairy'},
                {'name': 'olive oil', 'amount': 3, 'unit': 'tbsp', 'category': 'oils'},
                {'name': 'lemon juice', 'amount': 2, 'unit': 'tbsp', 'category': 'condiments'},
                {'name': 'oregano', 'amount': 1, 'unit': 'tsp', 'category': 'herbs'}
            ],
            'instructions': [
                'Drain and rinse the chickpeas',
                'Dice cucumber and halve cherry tomatoes',
                'Finely chop red onion',
                'Combine chickpeas, vegetables, and feta in a large bowl',
                'Whisk olive oil, lemon juice, and oregano for dressing',
                'Pour dressing over salad and toss well',
                'Let marinate for 15 minutes before serving'
            ],
            'nutrition': {
                'calories': 285,
                'protein': 12,
                'carbs': 28,
                'fat': 15,
                'fiber': 8
            },
            'tags': ['healthy', 'vegetarian', 'mediterranean', 'no-cook'],
            'difficulty': 'easy',
            'prep_time': 15,
            'total_time': 15
        },
        'source': 'custom',
        'rating': 'neutral',
        'is_favorite': False,
        'is_demo': False
    }
    
    # Recipe 2: Honey Garlic Salmon
    recipe2 = {
        'recipe_title': 'Honey Garlic Salmon',
        'recipe_image': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400',
        'recipe_data': {
            'ingredients': [
                {'name': 'salmon fillets', 'amount': 4, 'unit': 'pieces', 'category': 'protein'},
                {'name': 'honey', 'amount': 3, 'unit': 'tbsp', 'category': 'condiments'},
                {'name': 'soy sauce', 'amount': 2, 'unit': 'tbsp', 'category': 'condiments'},
                {'name': 'garlic', 'amount': 3, 'unit': 'cloves', 'category': 'vegetables'},
                {'name': 'ginger', 'amount': 1, 'unit': 'tsp', 'category': 'spices'},
                {'name': 'sesame oil', 'amount': 1, 'unit': 'tsp', 'category': 'oils'},
                {'name': 'rice vinegar', 'amount': 1, 'unit': 'tbsp', 'category': 'condiments'},
                {'name': 'green onions', 'amount': 2, 'unit': 'stalks', 'category': 'vegetables'},
                {'name': 'sesame seeds', 'amount': 1, 'unit': 'tsp', 'category': 'nuts'}
            ],
            'instructions': [
                'Preheat oven to 425°F (220°C)',
                'Line baking sheet with parchment paper',
                'Mix honey, soy sauce, minced garlic, ginger, sesame oil, and rice vinegar',
                'Place salmon fillets on prepared baking sheet',
                'Brush salmon with half the honey garlic mixture',
                'Bake for 12-15 minutes until salmon flakes easily',
                'Brush with remaining glaze halfway through cooking',
                'Garnish with chopped green onions and sesame seeds'
            ],
            'nutrition': {
                'calories': 320,
                'protein': 35,
                'carbs': 12,
                'fat': 16,
                'omega3': 1.8
            },
            'tags': ['healthy', 'gluten-free', 'high-protein', 'quick'],
            'difficulty': 'easy',
            'prep_time': 10,
            'cook_time': 15,
            'total_time': 25
        },
        'source': 'custom',
        'rating': 'neutral',
        'is_favorite': False,
        'is_demo': False
    }
    
    # Add recipes
    success_count = 0
    recipes = [recipe1, recipe2]
    
    for recipe in recipes:
        if add_recipe(recipe):
            success_count += 1
    
    print(f"\nAdded {success_count}/2 recipes successfully")
    
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
        except:
            print("Could not verify stats")
    
    print("Done!")

if __name__ == "__main__":
    main()