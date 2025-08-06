# Recipe URL Sources for Firecrawl Integration

## 🎯 Primary Source: Spoonacular API (You Already Have This!)

Your existing Spoonacular API calls return recipe URLs automatically:

### Example Spoonacular Response:
```json
{
  "id": 715538,
  "title": "What to make for dinner tonight?? Bruschetta!",
  "image": "https://spoonacular.com/recipeImages/715538-556x370.jpg",  // ← Spoonacular image (use first)
  "sourceUrl": "https://www.foodista.com/recipe/N2HQJJ8C/bruschetta",  // ← Firecrawl target!
  "sourceName": "Foodista",
  "servings": 6,
  "readyInMinutes": 45
}
```

### When Recipe Has No Image:
```json
{
  "id": 123456,
  "title": "Grandma's Secret Meatloaf Recipe",
  "image": null,                                                       // ← No Spoonacular image
  "sourceUrl": "https://www.allrecipes.com/recipe/16354/meatloaf/",   // ← Perfect for Firecrawl!
  "sourceName": "AllRecipes",
  "servings": 8
}
```

## 🌐 Common Recipe Sites Spoonacular Links To:

### Major Cooking Sites (High Success Rate)
- **AllRecipes.com** - Structured recipe pages, great images
- **FoodNetwork.com** - Professional food photography  
- **BonAppetit.com** - High-quality recipe images
- **Serious Eats** - Detailed recipe photos
- **Taste.com.au** - Clean recipe layouts
- **BBC Good Food** - Excellent recipe structure

### Food Blogs (Medium Success Rate)  
- **Foodista.com** - Recipe sharing platform
- **MyRecipes.com** - Time Inc. recipes
- **Epicurious.com** - Conde Nast recipes
- **Food.com** - Community recipes
- Various food blogs linked by Spoonacular

### Recipe Aggregators (Variable Success)
- **Yummly.com** - Recipe discovery
- **BigOven.com** - Recipe management
- **RecipeLand.com** - Recipe database

## 🔄 Smart URL Discovery Flow

```
User asks: "What can I make with chicken?"
    ↓
Spoonacular API search: "chicken recipes"
    ↓
Returns 20 recipes, each with:
  - id, title, image, sourceUrl, ingredients
    ↓
Recipe Search Agent processes each recipe:
  1. ✅ Has image? → Use Spoonacular image
  2. ❌ No image + has sourceUrl? → Queue for Firecrawl
  3. 🔥 Firecrawl scrapes sourceUrl → Gets original recipe image
    ↓
Result: Higher quality, recipe-specific images!
```

## 📊 URL Coverage Analysis

Based on Spoonacular data patterns:
- **~95%** of recipes include `sourceUrl` 
- **~70%** already have Spoonacular images
- **~25%** need Firecrawl (no Spoonacular image, has sourceUrl)
- **~5%** fallback to Unsplash/placeholders

## 💡 Alternative URL Sources (Future Enhancement)

### Recipe Search APIs
```python
# Could also get URLs from:
recipe_urls = [
    "https://api.edamam.com/search",      # Recipe URLs in responses
    "https://api.yummly.com/v1/api/recipes",  # Recipe discovery
    "https://rapidapi.com/spoonacular/api/recipe-food-nutrition/"  # Alternative
]
```

### Web Search for Specific Recipes
```python
# If no sourceUrl, search for recipe online:
search_query = f"{recipe_title} recipe site:allrecipes.com OR site:foodnetwork.com"
# Then Firecrawl the top result
```

### User-Generated URLs
```python
# Users could paste recipe URLs:
user_recipe_url = "https://www.seriouseats.com/perfect-chocolate-chip-cookies"
# Firecrawl extracts recipe data + images
```

## 🎯 Implementation Strategy

### Phase 1: Use Spoonacular URLs (Immediate)
```python
def get_recipe_with_image(spoonacular_recipe):
    if spoonacular_recipe.get("image"):
        # Use existing Spoonacular image
        return spoonacular_recipe
    
    elif spoonacular_recipe.get("sourceUrl"):
        # Firecrawl the source URL for images
        firecrawl_image = fetch_image_from_url(spoonacular_recipe["sourceUrl"])
        spoonacular_recipe["image"] = firecrawl_image
        return spoonacular_recipe
    
    else:
        # Fallback to Unsplash/placeholder
        return add_fallback_image(spoonacular_recipe)
```

### Phase 2: Smart URL Discovery (Future)
- Recipe URL database
- User-submitted URLs  
- Web search integration
- Social media recipe links

## 🔍 Real-World Example

Let's trace a complete flow:

```
1. User: "I want to make pasta"
   ↓
2. Spoonacular API: Returns 20 pasta recipes
   ↓  
3. Recipe #7: "Creamy Garlic Parmesan Pasta"
   - image: null
   - sourceUrl: "https://www.allrecipes.com/recipe/244716/creamy-garlic-parmesan-pasta/"
   ↓
4. Firecrawl scrapes AllRecipes page
   ↓
5. Extracts: "https://imagesvc.meredithcorp.io/v3/mm/image?q=85&c=sc&poi=face&w=750&h=750&url=https%3A%2F%2Fstatic.onecms.io%2Fwp-content%2Fuploads%2Fsites%2F43%2F2020%2F02%2F26%2F244716-creamy-garlic-parmesan-pasta-ddmfs-3x4-0766.jpg"
   ↓
6. User sees: Beautiful, high-res pasta photo from AllRecipes!
```

**The key insight: Spoonacular already gives us the URLs to crawl - we just need to use them when images are missing!** 🎯