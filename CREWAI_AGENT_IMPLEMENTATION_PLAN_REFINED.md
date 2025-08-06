# PrepSense CrewAI Agent Implementation Plan - REFINED & LOW RISK

## 🎯 Executive Summary

After researching CrewAI and FastAPI best practices, this refined plan integrates 8 specialized CrewAI agents with **recipe image fetching** capabilities into your existing PrepSense backend. Uses FastAPI's `BackgroundTasks`, dependency injection, and service composition patterns for zero-risk integration.

## ✅ **Key Refinements from Research**

### 1. **FastAPI BackgroundTasks Integration**
- Use `BackgroundTasks` for heavy pantry processing (normalization crew)
- Real-time crews for user-facing responses (<3 seconds)
- Automatic task orchestration via FastAPI's dependency injection

### 2. **Service Composition Pattern**
- Agents **use** your existing services as tools (not replace them)
- `Depends()` pattern connects agents to database, APIs, services
- Zero duplication - agents add intelligence on top of working infrastructure

### 3. **Enhanced Tool Architecture**
- CrewAI tools call your existing `spoonacular_service.py`, `nutrition_router.py`
- Agents compose multiple services for complex workflows
- **NEW**: Recipe image fetching from multiple sources

## 🏗️ Architecture Overview

### Enhanced Integration (Additive Only)
```
backend_gateway/
├── services/ (unchanged - agents use these as tools)
├── routers/ (unchanged)
├── crewai/
│   ├── foreground_crew.py (existing - enhanced)
│   ├── background_flows.py (existing - enhanced)  
│   ├── models.py (existing)
│   ├── agents/ (NEW - specialized agent classes)
│   │   ├── __init__.py
│   │   ├── food_categorizer_agent.py
│   │   ├── unit_canon_agent.py
│   │   ├── fresh_filter_agent.py
│   │   ├── recipe_search_agent.py  # ← With image fetching!
│   │   ├── nutri_check_agent.py
│   │   ├── user_preferences_agent.py
│   │   ├── judge_thyme_agent.py
│   │   └── pantry_ledger_agent.py
│   ├── crews/ (NEW - orchestrated crews)
│   │   ├── __init__.py
│   │   ├── pantry_normalization_crew.py
│   │   └── recipe_recommendation_crew.py
│   └── tools/ (NEW - intelligent agent tools)
│       ├── __init__.py
│       ├── ingredient_matcher_tool.py
│       ├── unit_converter_tool.py
│       ├── nutrition_calculator_tool.py
│       ├── preference_scorer_tool.py
│       └── recipe_image_fetcher_tool.py  # ← NEW!
```

## 🤖 Enhanced Agent Specifications

### Crew 1: PantryNormalizationCrew (Background)
**Integration**: Uses FastAPI `BackgroundTasks` for async processing

#### Agent 1: Food Categorizer Agent
```python
from crewai import Agent
from backend_gateway.services.food_database_service import FoodDatabaseService
from .tools.ingredient_matcher_tool import IngredientMatcherTool

food_categorizer = Agent(
    role="Food Category Expert",
    goal="Categorize raw food items using existing USDA database",
    backstory="Expert at identifying foods and mapping to nutrition databases",
    tools=[IngredientMatcherTool()],
    verbose=True
)
```

#### Agent 2: Unit Canon Agent
```python
unit_canon = Agent(
    role="Unit Standardization Specialist",
    goal="Convert quantities using existing unit conversion service", 
    backstory="Precision expert ensuring measurement consistency",
    tools=[UnitConverterTool()],
    verbose=True
)
```

#### Agent 3: Fresh Filter Agent
```python
fresh_filter = Agent(
    role="Freshness Analyst",
    goal="Score items for freshness using expiry data",
    backstory="Food safety expert preventing waste",
    tools=[],  # Uses existing pantry data
    verbose=True
)
```

### Crew 2: RecipeRecommendationCrew (Real-time)
**Integration**: Uses existing foreground crew pattern with enhanced agents

#### Agent 4: Recipe Search Agent (WITH IMAGES!)
```python
recipe_search = Agent(
    role="Recipe Discovery Expert",
    goal="Find recipes with beautiful images that maximize pantry utilization",
    backstory="Creative chef who finds perfect recipes with stunning visuals",
    tools=[
        IngredientMatcherTool(),
        RecipeImageFetcherTool()  # ← NEW!
    ],
    verbose=True
)
```

#### Agent 5: Nutri Check Agent
```python
nutri_check = Agent(
    role="Nutrition Analyst", 
    goal="Calculate nutrition using existing nutrition service",
    backstory="Registered dietitian ensuring nutritional goals",
    tools=[NutritionCalculatorTool()],
    verbose=True
)
```

#### Agent 6: User Preferences Agent
```python
user_preferences = Agent(
    role="Preference Specialist",
    goal="Score recipes using existing preference system",
    backstory="Personal taste expert adapting to individual preferences",
    tools=[PreferenceScorerTool()],
    verbose=True
)
```

#### Agent 7: Judge Thyme Agent
```python
judge_thyme = Agent(
    role="Cooking Feasibility Judge",
    goal="Evaluate recipe practicality based on user constraints",
    backstory="Practical cooking expert ensuring recipes are makeable",
    tools=[],  # Uses recipe complexity analysis
    verbose=True
)
```

#### Agent 8: Pantry Ledger Agent
```python
pantry_ledger = Agent(
    role="Inventory Manager",
    goal="Update pantry using existing pantry service",
    backstory="Meticulous accountant tracking ingredient usage",
    tools=[],  # Uses existing pantry_service.py
    verbose=True
)
```

## 🛠️ Enhanced Tool Implementations

### RecipeImageFetcherTool (NEW!)
```python
from crewai_tools import BaseTool
from backend_gateway.services.spoonacular_service import SpoonacularService
import httpx
import os

class RecipeImageFetcherTool(BaseTool):
    name: str = "recipe_image_fetcher"
    description: str = "Fetches high-quality recipe images from multiple sources"
    
    def _run(self, recipe_id: int, recipe_title: str, recipe_url: str = None) -> dict:
        """
        Enhanced multi-source image fetching strategy:
        1. Spoonacular recipe images (high quality, recipe-specific)
        2. Firecrawl web scraping (recipe blogs, cooking sites)
        3. Unsplash food photography (beautiful, generic food images)
        4. Placeholder generation (branded, consistent fallback)
        """
        # Try Spoonacular first (best quality)
        spoon_image = self._get_spoonacular_image(recipe_id)
        if spoon_image:
            return {
                "source": "spoonacular",
                "url": spoon_image["url"],
                "sizes": self._generate_sizes(spoon_image["url"]),
                "alt_text": f"{recipe_title} recipe"
            }
        
        # Try Firecrawl web scraping (recipe blogs/cooking sites)
        if recipe_url:
            firecrawl_image = self._get_firecrawl_image(recipe_url, recipe_title)
            if firecrawl_image:
                return {
                    "source": "firecrawl",
                    "url": firecrawl_image["url"],
                    "sizes": self._generate_sizes(firecrawl_image["url"]),
                    "alt_text": f"{recipe_title} from {firecrawl_image['domain']}",
                    "scraped_from": firecrawl_image["source_url"]
                }
        
        # Fallback to Unsplash (beautiful generic)
        unsplash_image = self._get_unsplash_image(recipe_title)
        if unsplash_image:
            return {
                "source": "unsplash", 
                "url": unsplash_image["url"],
                "sizes": self._generate_sizes(unsplash_image["url"]),
                "alt_text": f"{recipe_title} food photography",
                "photographer": unsplash_image["photographer"]
            }
        
        # Generate branded placeholder
        return {
            "source": "placeholder",
            "url": self._generate_placeholder(recipe_title),
            "sizes": {"thumbnail": "150x150", "card": "300x200", "full": "600x400"},
            "alt_text": f"{recipe_title} recipe"
        }
    
    def _get_spoonacular_image(self, recipe_id: int) -> dict:
        """Get high-quality image from Spoonacular"""
        try:
            # Use existing SpoonacularService
            service = SpoonacularService()
            recipe_data = service.get_recipe_information(recipe_id)
            
            if recipe_data.get("image"):
                return {
                    "url": recipe_data["image"],
                    "quality": "high"
                }
        except Exception as e:
            print(f"Spoonacular image fetch failed: {e}")
        return None
    
    def _get_firecrawl_image(self, recipe_url: str, recipe_title: str) -> dict:
        """Scrape recipe images from cooking websites using Firecrawl"""
        try:
            import httpx
            from urllib.parse import urlparse, urljoin
            
            if not os.getenv("FIRECRAWL_API_KEY"):
                return None
            
            # Use Firecrawl to scrape the recipe page
            response = httpx.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={
                    "Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": recipe_url,
                    "extractorOptions": {
                        "mode": "llm-extraction",
                        "extractionPrompt": f"Extract the main recipe image URL for '{recipe_title}'. Look for hero images, featured images, or primary recipe photos. Return just the image URL."
                    },
                    "pageOptions": {
                        "waitFor": 2000,  # Wait for images to load
                        "screenshot": False
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Try LLM extraction first
                if data.get("llm_extraction"):
                    extracted_url = data["llm_extraction"].strip()
                    if self._is_valid_image_url(extracted_url):
                        return {
                            "url": self._make_absolute_url(extracted_url, recipe_url),
                            "source_url": recipe_url,
                            "domain": urlparse(recipe_url).netloc,
                            "extraction_method": "llm"
                        }
                
                # Fallback to HTML parsing
                if data.get("content"):
                    html_content = data["content"]
                    image_url = self._extract_recipe_image_from_html(html_content, recipe_title)
                    if image_url:
                        return {
                            "url": self._make_absolute_url(image_url, recipe_url),
                            "source_url": recipe_url,
                            "domain": urlparse(recipe_url).netloc,
                            "extraction_method": "html_parsing"
                        }
                        
        except Exception as e:
            print(f"Firecrawl image fetch failed for {recipe_url}: {e}")
        return None
    
    def _extract_recipe_image_from_html(self, html_content: str, recipe_title: str) -> str:
        """Extract recipe image from HTML content using smart heuristics"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Priority-based image search
            image_selectors = [
                # Common recipe image patterns
                'img[class*="recipe-image"]',
                'img[class*="hero-image"]', 
                'img[class*="featured-image"]',
                'img[id*="recipe-image"]',
                '.recipe-card img',
                '.recipe-header img',
                'article img:first-of-type',
                
                # Schema.org structured data
                '[itemtype*="Recipe"] img',
                
                # Open Graph images
                'meta[property="og:image"]',
                
                # Generic content images (larger ones likely to be recipe photos)
                'img[width*="400"], img[height*="300"]'
            ]
            
            for selector in image_selectors:
                if selector.startswith('meta'):
                    # Handle meta tags
                    element = soup.select_one(selector)
                    if element and element.get('content'):
                        return element['content']
                else:
                    # Handle img tags
                    images = soup.select(selector)
                    for img in images:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if src and self._is_valid_image_url(src):
                            # Prefer larger images (likely the main recipe photo)
                            width = self._extract_dimension(img.get('width'))
                            height = self._extract_dimension(img.get('height'))
                            if width >= 300 or height >= 200:
                                return src
            
            # Last resort: find any reasonably sized image
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                if src and self._is_valid_image_url(src):
                    alt = img.get('alt', '').lower()
                    # Prefer images with recipe-related alt text
                    if any(word in alt for word in ['recipe', 'food', 'dish', recipe_title.lower().split()[0]]):
                        return src
                        
        except Exception as e:
            print(f"HTML parsing failed: {e}")
        return None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL"""
        if not url:
            return False
        
        # Check for image file extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        url_lower = url.lower()
        
        # Direct extension check
        if any(ext in url_lower for ext in image_extensions):
            return True
        
        # Check for image-related URL patterns
        image_patterns = ['image', 'img', 'photo', 'pic']
        if any(pattern in url_lower for pattern in image_patterns):
            return True
            
        return False
    
    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        try:
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        except:
            return url
    
    def _extract_dimension(self, dimension_str) -> int:
        """Extract numeric dimension from string"""
        if not dimension_str:
            return 0
        try:
            import re
            numbers = re.findall(r'\d+', str(dimension_str))
            return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    def _get_unsplash_image(self, recipe_title: str) -> dict:
        """Get beautiful food photography from Unsplash"""
        try:
            if not os.getenv("UNSPLASH_ACCESS_KEY"):
                return None
                
            # Extract key food terms from recipe title
            food_terms = self._extract_food_terms(recipe_title)
            search_query = f"{food_terms} food"
            
            response = httpx.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": search_query,
                    "per_page": 1,
                    "orientation": "landscape"
                },
                headers={"Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    result = data["results"][0]
                    return {
                        "url": result["urls"]["regular"],
                        "photographer": result["user"]["name"]
                    }
        except Exception as e:
            print(f"Unsplash image fetch failed: {e}")
        return None
    
    def _generate_placeholder(self, recipe_title: str) -> str:
        """Generate branded placeholder image"""
        # Create placeholder URL with recipe title
        encoded_title = recipe_title.replace(" ", "+")
        return f"https://via.placeholder.com/600x400/4F46E5/FFFFFF?text={encoded_title}"
    
    def _generate_sizes(self, base_url: str) -> dict:
        """Generate multiple image sizes for mobile optimization"""
        # For Spoonacular images, use their size parameters
        if "spoonacular" in base_url:
            return {
                "thumbnail": f"{base_url}?width=150&height=150",
                "card": f"{base_url}?width=300&height=200", 
                "full": f"{base_url}?width=600&height=400"
            }
        
        # For other sources, return original
        return {
            "thumbnail": base_url,
            "card": base_url,
            "full": base_url
        }
    
    def _extract_food_terms(self, recipe_title: str) -> str:
        """Extract main food ingredients from recipe title"""
        # Simple keyword extraction (can be enhanced with NLP)
        food_keywords = [
            "chicken", "beef", "pork", "fish", "salmon", "pasta", "pizza",
            "salad", "soup", "bread", "cake", "cookies", "rice", "noodles"
        ]
        
        title_lower = recipe_title.lower()
        found_terms = [term for term in food_keywords if term in title_lower]
        
        return found_terms[0] if found_terms else "food"
```

### IngredientMatcherTool
```python
from crewai_tools import BaseTool
from backend_gateway.services.ingredient_matcher_service import IngredientMatcherService

class IngredientMatcherTool(BaseTool):
    name: str = "ingredient_matcher"
    description: str = "Match recipe ingredients with pantry items using existing service"
    
    def _run(self, recipe_ingredients: list, pantry_items: list) -> dict:
        """Use existing ingredient matching service"""
        matcher = IngredientMatcherService()
        return matcher.match_ingredients(recipe_ingredients, pantry_items)
```

### UnitConverterTool
```python
from crewai_tools import BaseTool
from backend_gateway.services.unit_conversion_service import UnitConversionService

class UnitConverterTool(BaseTool):
    name: str = "unit_converter"
    description: str = "Convert units using existing unit conversion service"
    
    def _run(self, quantity: float, from_unit: str, to_unit: str) -> dict:
        """Use existing unit conversion service"""
        converter = UnitConversionService()
        return converter.convert_unit(quantity, from_unit, to_unit)
```

### NutritionCalculatorTool  
```python
from crewai_tools import BaseTool
from backend_gateway.services.openai_recipe_service import OpenAIRecipeService

class NutritionCalculatorTool(BaseTool):
    name: str = "nutrition_calculator"
    description: str = "Calculate nutrition using existing nutrition service"
    
    def _run(self, ingredients: list) -> dict:
        """Use existing nutrition calculation service"""
        nutrition_service = OpenAIRecipeService()
        return nutrition_service.calculate_nutrition(ingredients)
```

### PreferenceScorerTool
```python
from crewai_tools import BaseTool
from backend_gateway.services.preference_analyzer_service import PreferenceAnalyzerService

class PreferenceScorerTool(BaseTool):
    name: str = "preference_scorer" 
    description: str = "Score recipes using existing preference analyzer"
    
    def _run(self, recipe: dict, user_preferences: dict) -> dict:
        """Use existing preference scoring service"""
        scorer = PreferenceAnalyzerService()
        return scorer.score_recipe(recipe, user_preferences)
```

## 🔄 Enhanced Agent Interaction Flows

### Flow 1: Background Pantry Processing
```
FastAPI BackgroundTasks
    ↓
PantryNormalizationCrew.kickoff()
    ↓
Food Categorizer → (uses IngredientMatcherTool → existing services)
    ↓  
Unit Canon → (uses UnitConverterTool → existing unit_conversion_service)
    ↓
Fresh Filter → (reads existing pantry data)
    ↓
Cache normalized results → (existing cache_manager)
```

### Flow 2: Real-time Recipe Recommendations
```
User Query (FastAPI endpoint)
    ↓
RecipeRecommendationCrew.kickoff()
    ↓
Recipe Search → Spoonacular API + RecipeImageFetcherTool 📸
    ↓
Nutri Check → (uses NutritionCalculatorTool → existing services)
    ↓  
User Preferences → (uses PreferenceScorerTool → existing services)
    ↓
Judge Thyme → feasibility assessment
    ↓
Return enriched recipes with beautiful images! 🖼️
    ↓
[User selects recipe]
    ↓
Pantry Ledger → (uses existing pantry_service.py)
```

## 📋 FastAPI Integration Pattern

### Enhanced Chat Router with Crews
```python
from fastapi import APIRouter, BackgroundTasks, Depends
from backend_gateway.crewai.crews.pantry_normalization_crew import PantryNormalizationCrew
from backend_gateway.crewai.crews.recipe_recommendation_crew import RecipeRecommendationCrew

@router.post("/chat/message")
async def enhanced_chat_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Enhanced chat with CrewAI agents and recipe images"""
    
    # Background processing for pantry normalization
    if request.includes_pantry_update:
        background_tasks.add_task(
            run_pantry_normalization_crew,
            user_id=current_user["id"],
            pantry_data=request.pantry_items
        )
    
    # Real-time recipe recommendations with images
    recipe_crew = RecipeRecommendationCrew()
    result = await recipe_crew.kickoff({
        "user_message": request.message,
        "user_id": current_user["id"],
        "include_images": True  # ← Enable image fetching!
    })
    
    return {
        "response": result.response_text,
        "recipes": result.recipes,  # Now include beautiful images!
        "processing_time": result.processing_time_ms
    }

async def run_pantry_normalization_crew(user_id: int, pantry_data: list):
    """Background task for heavy pantry processing"""
    crew = PantryNormalizationCrew()
    await crew.kickoff({
        "user_id": user_id,
        "raw_pantry_items": pantry_data
    })
```

## 🎯 Implementation Phases (Refined)

### Phase 1: Enhanced Foundation (Week 1) - ZERO RISK
1. Create enhanced directory structure 
2. Implement agent tools that **call existing services**
3. Add `RecipeImageFetcherTool` with multi-source strategy
4. Write integration tests using existing test patterns
5. **Validation**: All existing functionality unchanged

### Phase 2: Smart Agent Development (Week 2) - LOW RISK
1. Implement agent classes that **use tools**
2. Create crews that **orchestrate agents**
3. Test with mock data and feature flags
4. **Validation**: Agents work with existing services via tools

### Phase 3: FastAPI Integration (Week 3) - CONTROLLED RISK
1. Integrate crews with `BackgroundTasks` pattern
2. Enhance existing chat router with crew calls
3. Add feature flags for gradual rollout
4. **Validation**: Parallel processing (old + new) comparison

### Phase 4: Recipe Image Enhancement (Week 4) - VALUE ADD
1. Deploy `RecipeImageFetcherTool` to production
2. Test multi-source image fallback strategy
3. Monitor image loading performance
4. **Validation**: Recipes now have beautiful images!

### Phase 5: Production Rollout (Week 5) - MANAGED RISK
1. Enable crew processing for 10% of requests
2. Monitor response times and image loading
3. Gradually increase to 100% usage
4. **Validation**: Enhanced UX with AI agents + images

## 🖼️ Recipe Image Strategy

### Multi-Source Approach
1. **Spoonacular Images** (Primary)
   - High quality, recipe-specific
   - Already integrated with your API
   - Best accuracy for actual recipe

2. **Unsplash Food Photography** (Secondary)  
   - Professional, beautiful food images
   - Free with attribution
   - Great for visual appeal

3. **Generated Placeholders** (Fallback)
   - Branded with PrepSense colors
   - Consistent design language
   - Always available, never fails

### Mobile Optimization
- Multiple image sizes (thumbnail, card, full)
- Lazy loading implementation
- CDN optimization for fast delivery
- Cached locally after first load

## ✅ Success Metrics (Enhanced)

### Technical Metrics
- ✅ Response time <3 seconds (maintained)
- ✅ Image load time <2 seconds
- ✅ 95% image availability (multi-source fallback)
- ✅ Zero downtime deployment

### User Experience Metrics  
- ✅ Recipe recommendation quality improved
- ✅ Visual engagement increased (with images)
- ✅ Recipe selection rate improved
- ✅ User satisfaction scores increased

This refined plan leverages FastAPI's strengths, integrates seamlessly with your existing architecture, and adds beautiful recipe images to enhance the user experience! 🚀📸