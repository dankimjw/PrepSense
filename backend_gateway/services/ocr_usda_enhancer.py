"""
OCR Enhancement Service using USDA Food Database
Improves OCR results by matching extracted text to known food products.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import asyncpg

from backend_gateway.services.usda_food_service import USDAFoodService

logger = logging.getLogger(__name__)


class OCRUSDAEnhancer:
    """Enhances OCR results using USDA food database."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.usda_service = USDAFoodService(db_pool)
        
        # Common OCR mistakes and corrections
        self.ocr_corrections = {
            'MLKWHL': 'MILK WHOLE',
            'CHKN': 'CHICKEN',
            'BF': 'BEEF',
            'ORG': 'ORGANIC',
            'BNLS': 'BONELESS',
            'SKNLS': 'SKINLESS',
            'GRND': 'GROUND',
            'RST': 'ROAST',
            'STK': 'STEAK',
            'LB': 'POUND',
            'OZ': 'OUNCE',
            'EA': 'EACH',
            'PCT': 'PERCENT',
            'WHL': 'WHOLE',
            'RDCD': 'REDUCED',
            'LOWFT': 'LOW FAT',
            'NONFAT': 'NON FAT',
        }
    
    async def enhance_ocr_results(
        self, 
        ocr_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance OCR extracted items with USDA data.
        
        Args:
            ocr_items: List of items extracted by OCR with fields:
                - item_name: Raw text from receipt
                - quantity: Extracted quantity (optional)
                - unit: Extracted unit (optional)
                - price: Extracted price (optional)
                - barcode: Barcode if available (optional)
        
        Returns:
            Enhanced items with additional fields:
                - matched_name: Standardized name from USDA
                - brand: Brand information if found
                - category: Food category
                - confidence: Match confidence score
                - nutritional_available: Boolean
                - serving_size: Standard serving size
                - fdc_id: USDA FoodData Central ID
        """
        enhanced_items = []
        
        for item in ocr_items:
            try:
                enhanced = await self._enhance_single_item(item)
                enhanced_items.append(enhanced)
            except Exception as e:
                logger.error(f"Failed to enhance item {item.get('item_name')}: {e}")
                # Return original item with error flag
                enhanced_items.append({
                    **item,
                    'enhancement_error': str(e),
                    'enhanced': False
                })
        
        return enhanced_items
    
    async def _enhance_single_item(
        self, 
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance a single OCR item."""
        
        raw_name = item.get('item_name', '')
        barcode = item.get('barcode')
        
        # Clean and expand abbreviated text
        cleaned_name = self._clean_ocr_text(raw_name)
        
        # Try barcode lookup first (most accurate)
        if barcode:
            barcode_results = await self.usda_service.search_foods(
                barcode=barcode,
                limit=1
            )
            
            if barcode_results:
                return self._build_enhanced_item(
                    item, 
                    barcode_results[0], 
                    confidence=1.0,
                    match_type='barcode'
                )
        
        # Fall back to text search
        search_results = await self.usda_service.search_foods(
            query=cleaned_name,
            limit=5
        )
        
        if search_results:
            # Find best match
            best_match, confidence = self._find_best_match(
                cleaned_name, 
                search_results
            )
            
            if best_match and confidence > 0.6:  # Threshold for acceptance
                return self._build_enhanced_item(
                    item,
                    best_match,
                    confidence=confidence,
                    match_type='text'
                )
        
        # No good match found
        return {
            **item,
            'cleaned_name': cleaned_name,
            'enhanced': False,
            'no_match_found': True
        }
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean and expand OCR text."""
        # Convert to uppercase for consistency
        text = text.upper().strip()
        
        # Remove special characters except spaces
        text = re.sub(r'[^A-Z0-9\s%]', ' ', text)
        
        # Apply known corrections
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Check if word needs correction
            if word in self.ocr_corrections:
                corrected_words.append(self.ocr_corrections[word])
            else:
                corrected_words.append(word)
        
        # Join and clean up extra spaces
        cleaned = ' '.join(corrected_words)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _find_best_match(
        self, 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Find the best matching result based on string similarity."""
        
        best_match = None
        best_score = 0.0
        
        for result in results:
            # Compare with description
            desc_score = SequenceMatcher(
                None, 
                query.lower(), 
                result['description'].lower()
            ).ratio()
            
            # Bonus for brand match if present
            if result.get('brand_info'):
                brand_score = SequenceMatcher(
                    None,
                    query.lower(),
                    result['brand_info'].lower()
                ).ratio() * 0.3  # Weight brand less
                
                score = max(desc_score, desc_score * 0.7 + brand_score)
            else:
                score = desc_score
            
            # Additional bonus for exact word matches
            query_words = set(query.lower().split())
            desc_words = set(result['description'].lower().split())
            word_overlap = len(query_words & desc_words) / len(query_words)
            score = score * 0.8 + word_overlap * 0.2
            
            if score > best_score:
                best_score = score
                best_match = result
        
        return best_match, best_score
    
    def _build_enhanced_item(
        self,
        original: Dict[str, Any],
        usda_match: Dict[str, Any],
        confidence: float,
        match_type: str
    ) -> Dict[str, Any]:
        """Build the enhanced item dictionary."""
        
        # Get detailed food info
        enhanced = {
            **original,
            'enhanced': True,
            'match_type': match_type,
            'confidence': round(confidence, 2),
            'matched_name': usda_match['description'],
            'fdc_id': usda_match['fdc_id'],
            'category': usda_match.get('category', 'Unknown'),
        }
        
        # Add brand info if available
        if usda_match.get('brand_info'):
            enhanced['brand'] = usda_match['brand_info']
        
        # Add barcode if found via search
        if usda_match.get('barcode') and not original.get('barcode'):
            enhanced['barcode'] = usda_match['barcode']
        
        # Note that nutritional info is available
        enhanced['nutritional_available'] = True
        
        return enhanced
    
    async def get_nutrition_for_item(
        self,
        fdc_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get nutritional information for an enhanced item.
        
        Args:
            fdc_id: USDA FoodData Central ID
            
        Returns:
            Nutritional information if available
        """
        return await self.usda_service.get_food_details(fdc_id)