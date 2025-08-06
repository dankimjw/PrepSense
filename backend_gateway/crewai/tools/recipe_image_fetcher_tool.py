"""Recipe Image Fetcher Tool for CrewAI

Multi-source image fetching strategy:
1. Spoonacular recipe images (high quality, recipe-specific)
2. Firecrawl web scraping (recipe blogs, cooking sites)  
3. Unsplash food photography (beautiful, generic food images)
4. Placeholder generation (branded, consistent fallback)
"""

from crewai.tools import BaseTool
from backend_gateway.services.spoonacular_service import SpoonacularService
import httpx
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


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
    
    def _get_spoonacular_image(self, recipe_id: int) -> Optional[Dict[str, Any]]:
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
            logger.warning(f"Spoonacular image fetch failed for recipe {recipe_id}: {e}")
        return None
    
    def _get_firecrawl_image(self, recipe_url: str, recipe_title: str) -> Optional[Dict[str, Any]]:
        """Scrape recipe images from cooking websites using Firecrawl"""
        try:
            from urllib.parse import urlparse, urljoin
            
            if not os.getenv("FIRECRAWL_API_KEY"):
                logger.info("Firecrawl API key not found, skipping web scraping")
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
            logger.warning(f"Firecrawl image fetch failed for {recipe_url}: {e}")
        return None
    
    def _extract_recipe_image_from_html(self, html_content: str, recipe_title: str) -> Optional[str]:
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
            logger.warning(f"HTML parsing failed: {e}")
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
    
    def _get_unsplash_image(self, recipe_title: str) -> Optional[Dict[str, Any]]:
        """Get beautiful food photography from Unsplash"""
        try:
            if not os.getenv("UNSPLASH_ACCESS_KEY"):
                logger.info("Unsplash access key not found, skipping Unsplash search")
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
            logger.warning(f"Unsplash image fetch failed: {e}")
        return None
    
    def _generate_placeholder(self, recipe_title: str) -> str:
        """Generate branded placeholder image"""
        # Create placeholder URL with recipe title
        encoded_title = recipe_title.replace(" ", "+")
        return f"https://via.placeholder.com/600x400/4F46E5/FFFFFF?text={encoded_title}"
    
    def _generate_sizes(self, base_url: str) -> Dict[str, str]:
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