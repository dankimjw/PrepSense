"""
Recipe Deduplication Service - Fixed version

🟡 IMPLEMENTATION STATUS: PARTIAL - WORKING WITH FIXES
This service provides recipe fingerprinting and deduplication functionality
for the Spoonacular API tracking system.

Features implemented:
- ✅ Recipe fingerprint generation
- ✅ Similarity scoring (fixed algorithm)
- ✅ Batch deduplication
- ✅ Fuzzy ingredient matching
"""
import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple, Set
from difflib import SequenceMatcher
from dataclasses import dataclass
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class RecipeFingerprint:
    """Recipe fingerprint data structure."""
    recipe_id: int
    fingerprint: str
    title_normalized: str
    ingredient_hash: str
    timing_category: str
    serving_category: str


class RecipeDeduplicationService:
    """
    Service for detecting and handling duplicate recipes from Spoonacular API calls.
    
    🟡 IMPLEMENTATION STATUS: PARTIAL - WORKING WITH FIXES
    - ✅ Recipe fingerprinting with ingredient normalization (fixed)
    - ✅ Title-based similarity matching with fuzzy logic (improved)
    - ✅ Ingredient-based matching with quantity tolerance (fixed normalization)
    - ✅ Batch deduplication with configurable threshold
    - 🟡 Database integration (requires API tracker)
    - 🔴 Analytics integration not yet implemented
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the deduplication service.
        
        Args:
            similarity_threshold: Minimum similarity score to consider recipes as duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.common_words = {
            'with', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'for', 'to', 'of',
            'recipe', 'dish', 'easy', 'quick', 'simple', 'best', 'homemade'
        }
        
        # Timing categories for comparison
        self.timing_categories = {
            'very_quick': (0, 15),      # 0-15 minutes
            'quick': (16, 30),          # 16-30 minutes  
            'medium': (31, 60),         # 31-60 minutes
            'slow': (61, 120),          # 1-2 hours
            'very_slow': (121, 999)     # 2+ hours
        }
        
        # Serving categories
        self.serving_categories = {
            'single': (1, 1),
            'couple': (2, 2), 
            'small': (3, 4),
            'medium': (5, 6),
            'large': (7, 10),
            'very_large': (11, 999)
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent comparison.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
        
        # Convert to lowercase and remove accents
        text = unicodedata.normalize('NFD', text.lower())
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common words that don't add semantic value
        words = text.split()
        words = [w for w in words if w not in self.common_words and len(w) > 2]
        
        # Keep original order for title matching, but normalize spacing
        return ' '.join(words)
    
    def normalize_ingredient_name(self, ingredient: str) -> str:
        """
        Normalize ingredient names for comparison - FIXED VERSION.
        
        Args:
            ingredient: Raw ingredient name
            
        Returns:
            Normalized ingredient name
        """
        if not ingredient:
            return ""
        
        # Convert to lowercase first
        ingredient = ingredient.lower()
        
        # Remove measurements and descriptors
        ingredient = re.sub(r'\b\d+.*?(oz|lb|g|kg|ml|l|cup|tbsp|tsp|pound|ounce|gram|kilogram|liter|milliliter)\b', '', ingredient, flags=re.IGNORECASE)
        ingredient = re.sub(r'\b(organic|fresh|frozen|dried|chopped|minced|sliced|diced|crushed|ground)\b', '', ingredient, flags=re.IGNORECASE)
        
        # Apply specific ingredient mappings BEFORE general normalization
        ingredient_map = {
            'chicken breast': 'chicken',
            'chicken thigh': 'chicken', 
            'chicken thighs': 'chicken',
            'chicken drumstick': 'chicken',
            'chicken drumsticks': 'chicken',
            'ground beef': 'beef',
            'beef steak': 'beef',
            'olive oil': 'oil',
            'vegetable oil': 'oil',
            'canola oil': 'oil',
            'red onion': 'onion',
            'yellow onion': 'onion',
            'white onion': 'onion',
            'green onions': 'onion',
            'pasta noodles': 'pasta',
            'spaghetti noodles': 'pasta'
        }
        
        # Apply mappings
        for variant, canonical in ingredient_map.items():
            if variant in ingredient:
                ingredient = ingredient.replace(variant, canonical)
        
        # General text normalization
        normalized = self.normalize_text(ingredient)
        
        # If normalization resulted in empty string, try to extract main ingredient
        if not normalized and ingredient.strip():
            # Take the first significant word
            words = ingredient.strip().split()
            for word in words:
                if len(word) > 2 and word not in self.common_words:
                    return word
        
        return normalized if normalized else ingredient.strip()
    
    def get_timing_category(self, ready_in_minutes: int) -> str:
        """Categorize recipe timing."""
        if ready_in_minutes is None:
            return 'unknown'
        
        for category, (min_time, max_time) in self.timing_categories.items():
            if min_time <= ready_in_minutes <= max_time:
                return category
        return 'unknown'
    
    def get_serving_category(self, servings: int) -> str:
        """Categorize recipe serving size."""
        if servings is None:
            return 'unknown'
        
        for category, (min_serv, max_serv) in self.serving_categories.items():
            if min_serv <= servings <= max_serv:
                return category
        return 'unknown'
    
    def extract_ingredients_hash(self, recipe: Dict[str, Any]) -> str:
        """
        Extract and hash recipe ingredients for comparison.
        
        Args:
            recipe: Recipe dictionary from Spoonacular
            
        Returns:
            Hash string representing the ingredient profile
        """
        ingredients = []
        
        # Extract ingredients from different possible formats
        if 'extendedIngredients' in recipe:
            for ing in recipe['extendedIngredients']:
                name = ing.get('name', '') or ing.get('original', '')
                if name:
                    normalized = self.normalize_ingredient_name(name)
                    if normalized:  # Only add non-empty normalized ingredients
                        ingredients.append(normalized)
        elif 'ingredients' in recipe:
            for ing in recipe['ingredients']:
                if isinstance(ing, str):
                    normalized = self.normalize_ingredient_name(ing)
                    if normalized:
                        ingredients.append(normalized)
                elif isinstance(ing, dict):
                    name = ing.get('name', '') or ing.get('original', '')
                    if name:
                        normalized = self.normalize_ingredient_name(name)
                        if normalized:
                            ingredients.append(normalized)
        
        # Sort ingredients for consistent hashing and remove duplicates
        ingredients = sorted(set(ingredients))
        ingredient_string = '|'.join(ingredients)
        
        return hashlib.md5(ingredient_string.encode()).hexdigest()[:12]
    
    def generate_recipe_fingerprint(self, recipe: Dict[str, Any]) -> str:
        """
        Generate a unique fingerprint for a recipe based on key characteristics.
        
        Args:
            recipe: Recipe dictionary from Spoonacular API
            
        Returns:
            Fingerprint string for the recipe
        """
        try:
            # Extract key recipe characteristics
            title = recipe.get('title', '')
            ready_time = recipe.get('readyInMinutes', 0)
            servings = recipe.get('servings', 0)
            
            # Normalize title
            normalized_title = self.normalize_text(title)
            
            # Get category classifications
            timing_cat = self.get_timing_category(ready_time)
            serving_cat = self.get_serving_category(servings)
            
            # Extract ingredient signature
            ingredient_hash = self.extract_ingredients_hash(recipe)
            
            # Create fingerprint components
            components = [
                f"title:{normalized_title[:30]}",  # First 30 chars of normalized title
                f"time:{timing_cat}",
                f"serv:{serving_cat}",
                f"ing:{ingredient_hash}"
            ]
            
            # Generate final fingerprint
            fingerprint = '|'.join(components)
            return hashlib.md5(fingerprint.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.warning(f"Error generating fingerprint for recipe {recipe.get('id', 'unknown')}: {str(e)}")
            # Fallback fingerprint based on recipe ID
            recipe_id = recipe.get('id', 0)
            return hashlib.md5(f"fallback:{recipe_id}".encode()).hexdigest()[:16]
    
    def calculate_similarity(self, recipe1: Dict[str, Any], recipe2: Dict[str, Any]) -> float:
        """
        Calculate similarity score between two recipes - IMPROVED VERSION.
        
        Args:
            recipe1: First recipe dictionary
            recipe2: Second recipe dictionary
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            scores = []
            
            # Title similarity (50% weight) - More important for recipe matching
            title1 = self.normalize_text(recipe1.get('title', ''))
            title2 = self.normalize_text(recipe2.get('title', ''))
            if title1 and title2:
                # Use sequence matching for word order flexibility
                title_sim = SequenceMatcher(None, title1, title2).ratio()
                
                # Also check for common words between titles
                words1 = set(title1.split())
                words2 = set(title2.split())
                if words1 and words2:
                    word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                    # Take the maximum of sequence similarity and word overlap
                    title_sim = max(title_sim, word_overlap)
                
                scores.append(('title', title_sim, 0.5))
            
            # Ingredient similarity (30% weight)
            ing_sim = self._calculate_ingredient_overlap(recipe1, recipe2)
            if ing_sim >= 0:  # Only add if calculation was successful
                scores.append(('ingredients', ing_sim, 0.3))
            
            # Timing similarity (10% weight)
            time1 = recipe1.get('readyInMinutes', 0)
            time2 = recipe2.get('readyInMinutes', 0)
            if time1 and time2:
                time_diff = abs(time1 - time2)
                # More generous time tolerance (45 minutes)
                time_sim = max(0, 1 - (time_diff / 45))
                scores.append(('timing', time_sim, 0.1))
            
            # Serving similarity (10% weight)
            serv1 = recipe1.get('servings', 0)
            serv2 = recipe2.get('servings', 0)
            if serv1 and serv2:
                serv_diff = abs(serv1 - serv2)
                # More generous serving tolerance (up to 3 servings difference)
                serv_sim = max(0, 1 - (serv_diff / 6))
                scores.append(('servings', serv_sim, 0.1))
            
            # Calculate weighted average
            if scores:
                total_weight = sum(weight for _, _, weight in scores)
                weighted_sum = sum(score * weight for _, score, weight in scores)
                final_score = weighted_sum / total_weight
                
                logger.debug(f"Similarity calculation: {scores} -> {final_score:.3f}")
                return final_score
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def _calculate_ingredient_overlap(self, recipe1: Dict[str, Any], recipe2: Dict[str, Any]) -> float:
        """Calculate ingredient list overlap between two recipes - IMPROVED VERSION."""
        try:
            # Extract normalized ingredient sets
            ing1 = set()
            ing2 = set()
            
            # Recipe 1 ingredients
            if 'extendedIngredients' in recipe1:
                for ing in recipe1['extendedIngredients']:
                    name = ing.get('name', '')
                    if name:
                        normalized = self.normalize_ingredient_name(name)
                        if normalized:
                            ing1.add(normalized)
            
            # Recipe 2 ingredients
            if 'extendedIngredients' in recipe2:
                for ing in recipe2['extendedIngredients']:
                    name = ing.get('name', '')
                    if name:
                        normalized = self.normalize_ingredient_name(name)
                        if normalized:
                            ing2.add(normalized)
            
            if not ing1 or not ing2:
                return 0.0
            
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(ing1.intersection(ing2))
            union = len(ing1.union(ing2))
            
            jaccard_sim = intersection / union if union > 0 else 0.0
            
            logger.debug(f"Ingredient comparison: {ing1} vs {ing2} -> {jaccard_sim:.3f}")
            return jaccard_sim
            
        except Exception as e:
            logger.warning(f"Error calculating ingredient overlap: {str(e)}")
            return -1  # Return -1 to indicate calculation failed
    
    def is_duplicate(self, recipe1: Dict[str, Any], recipe2: Dict[str, Any], threshold: float = None) -> bool:
        """
        Determine if two recipes are duplicates.
        
        Args:
            recipe1: First recipe dictionary
            recipe2: Second recipe dictionary
            threshold: Custom similarity threshold (uses instance default if None)
            
        Returns:
            True if recipes are considered duplicates
        """
        threshold = threshold or self.similarity_threshold
        similarity = self.calculate_similarity(recipe1, recipe2)
        
        logger.debug(f"Duplicate check: '{recipe1.get('title', '')}' vs '{recipe2.get('title', '')}' "
                    f"= {similarity:.3f} (threshold: {threshold})")
        
        return similarity >= threshold
    
    def deduplicate_recipes(
        self, 
        recipes: List[Dict[str, Any]], 
        threshold: float = None
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Remove duplicate recipes from a list.
        
        Args:
            recipes: List of recipe dictionaries
            threshold: Custom similarity threshold
            
        Returns:
            Tuple of (deduplicated_recipes, duplicate_recipe_ids)
        """
        threshold = threshold or self.similarity_threshold
        unique_recipes = []
        duplicate_ids = []
        
        logger.info(f"Starting deduplication of {len(recipes)} recipes with threshold {threshold}")
        
        for i, recipe in enumerate(recipes):
            is_duplicate = False
            
            # Compare with all previously accepted unique recipes
            for unique_recipe in unique_recipes:
                if self.is_duplicate(recipe, unique_recipe, threshold):
                    is_duplicate = True
                    recipe_id = recipe.get('id', f'recipe_{i}')
                    duplicate_ids.append(recipe_id)
                    
                    logger.debug(f"Recipe {recipe_id} '{recipe.get('title', '')}' "
                               f"is duplicate of {unique_recipe.get('id', '')} "
                               f"'{unique_recipe.get('title', '')}'")
                    break
            
            if not is_duplicate:
                unique_recipes.append(recipe)
        
        reduction_percent = (len(duplicate_ids) / len(recipes)) * 100 if recipes else 0
        logger.info(f"Deduplication complete: {len(unique_recipes)} unique recipes, "
                   f"{len(duplicate_ids)} duplicates removed ({reduction_percent:.1f}% reduction)")
        
        return unique_recipes, duplicate_ids
    
    def analyze_recipe_batch(self, recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a batch of recipes for deduplication insights.
        
        Args:
            recipes: List of recipe dictionaries
            
        Returns:
            Analysis results dictionary
        """
        if not recipes:
            return {
                'total_recipes': 0,
                'fingerprints': [],
                'duplicate_analysis': {'estimated_duplicates': 0, 'similarity_scores': []}
            }
        
        fingerprints = []
        similarity_scores = []
        
        # Generate fingerprints
        for recipe in recipes:
            fingerprint = self.generate_recipe_fingerprint(recipe)
            fingerprints.append({
                'recipe_id': recipe.get('id'),
                'title': recipe.get('title'),
                'fingerprint': fingerprint
            })
        
        # Sample similarity analysis (compare first 10 recipes with each other)
        sample_recipes = recipes[:10]
        for i in range(len(sample_recipes)):
            for j in range(i + 1, len(sample_recipes)):
                similarity = self.calculate_similarity(sample_recipes[i], sample_recipes[j])
                similarity_scores.append(similarity)
        
        # Estimate duplicates
        high_similarity_count = sum(1 for score in similarity_scores if score >= self.similarity_threshold)
        
        return {
            'total_recipes': len(recipes),
            'fingerprints': fingerprints,
            'duplicate_analysis': {
                'estimated_duplicates': high_similarity_count,
                'similarity_scores': similarity_scores,
                'avg_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
                'max_similarity': max(similarity_scores) if similarity_scores else 0
            }
        }