# Recipe Image Fetching Flow

## Decision Tree

```
Recipe Search Agent gets recipe from Spoonacular
    ↓
🔍 Check: Does recipe.image exist in Spoonacular response?
    ↓
✅ YES → Use Spoonacular image (BEST quality)
    ↓
❌ NO → Check: Does recipe have source URL?
    ↓
✅ YES → Try Firecrawl web scraping
    ↓
🤖 Firecrawl scrapes recipe blog/cooking site
    ↓ (Looks for hero images, recipe photos, featured images)
✅ Found image → Use scraped image (HIGH quality, recipe-specific)
    ↓
❌ No image found → Try Unsplash food photography  
    ↓
🔍 Extract food keywords from recipe title
    ↓ (e.g., "Chicken Parmesan" → "chicken")
Search Unsplash: "{keyword} food"
    ↓
✅ Found image → Use Unsplash photo + photographer credit
    ↓
❌ No results → Generate branded placeholder
    ↓
✅ ALWAYS SUCCESS → Recipe has beautiful image!
```

## Real Examples

### Example 1: Spoonacular Success
```json
{
  "recipe_id": 715538,
  "title": "Bruschetta with Tomato and Basil",
  "image": {
    "source": "spoonacular",
    "url": "https://spoonacular.com/recipeImages/715538-556x370.jpg",
    "sizes": {
      "thumbnail": "https://spoonacular.com/recipeImages/715538-240x150.jpg",
      "card": "https://spoonacular.com/recipeImages/715538-312x231.jpg", 
      "full": "https://spoonacular.com/recipeImages/715538-636x393.jpg"
    },
    "alt_text": "Bruschetta with Tomato and Basil recipe"
  }
}
```

### Example 2: Unsplash Fallback
```json
{
  "recipe_id": 123456,
  "title": "Homemade Chocolate Chip Cookies",
  "image": {
    "source": "unsplash",
    "url": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35",
    "photographer": "Keenan Loo",
    "sizes": {
      "thumbnail": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=150&h=150&fit=crop",
      "card": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=300&h=200&fit=crop",
      "full": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&h=400&fit=crop"
    },
    "alt_text": "Chocolate chip cookies food photography",
    "attribution_required": true
  }
}
```

### Example 3: Branded Placeholder
```json
{
  "recipe_id": 789012,
  "title": "Grandma's Secret Meatloaf",
  "image": {
    "source": "placeholder",
    "url": "https://via.placeholder.com/600x400/4F46E5/FFFFFF?text=Grandma's+Secret+Meatloaf",
    "sizes": {
      "thumbnail": "https://via.placeholder.com/150x150/4F46E5/FFFFFF?text=GSM",
      "card": "https://via.placeholder.com/300x200/4F46E5/FFFFFF?text=Grandma's+Meatloaf",
      "full": "https://via.placeholder.com/600x400/4F46E5/FFFFFF?text=Grandma's+Secret+Meatloaf"
    },
    "alt_text": "Grandma's Secret Meatloaf recipe"
  }
}
```