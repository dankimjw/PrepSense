import os
import base64
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import pytest
import pytest_asyncio
from fastapi import UploadFile
from io import BytesIO
from PIL import Image
import numpy as np

from backend_gateway.services.vision_service import VisionService

# Test data
SAMPLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test_images", "test_food.jpg")
SAMPLE_OPENAI_RESPONSE = """
[
    {
        "item_name": "Banana",
        "quantity": "5",
        "count": 5,
        "expiration_date": "2023-06-15"
    },
    {
        "item_name": "Milk",
        "quantity": "1 L",
        "count": 1,
        "expiration_date": "2023-06-10"
    }
]
"""

# Fixtures
@pytest.fixture
def vision_service():
    return VisionService(api_key="test_api_key")

@pytest.fixture
def mock_openai_response():
    return {
        "choices": [
            {
                "message": {
                    "content": SAMPLE_OPENAI_RESPONSE,
                    "role": "assistant"
                }
            }
        ]
    }

@pytest.fixture
def sample_image():
    # Create a simple 1x1 pixel image
    img = Image.new('RGB', (1, 1), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

# Tests
class TestVisionService:
    @pytest.mark.asyncio
    async def test_process_image(self, vision_service, sample_image):
        # Create a mock UploadFile
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=sample_image.getvalue())
        
        # Call the method
        base64_image, content_type = await vision_service.process_image(mock_file)
        
        # Verify the results
        assert content_type == "image/jpeg"
        assert isinstance(base64_image, str)
        # Verify it's valid base64
        try:
            base64.b64decode(base64_image)
        except Exception:
            pytest.fail("Returned string is not valid base64")

    @pytest.mark.asyncio
    @patch('backend_gateway.services.vision_service.openai.OpenAI')
    async def test_classify_food_items(self, mock_openai_client, vision_service, sample_image):
        # Setup mock
        mock_client = MagicMock()
        mock_openai_client.return_value = mock_client
        
        # Mock the chat completions response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = SAMPLE_OPENAI_RESPONSE
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Set the return value for chat.completions.create
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the method with a base64 encoded image
        base64_image = base64.b64encode(sample_image.getvalue()).decode('utf-8')
        result = await vision_service.classify_food_items(base64_image, "image/jpeg")
        
        # Verify the result
        assert result == SAMPLE_OPENAI_RESPONSE.strip()
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify the API call was made with the correct parameters
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args['model'] == 'gpt-4.1-mini'
        assert len(call_args['messages']) == 1
        assert call_args['messages'][0]['role'] == 'user'
        assert 'image_url' in call_args['messages'][0]['content'][1]

    def test_parse_openai_response(self, vision_service):
        # Test with valid response
        result = vision_service.parse_openai_response(SAMPLE_OPENAI_RESPONSE)
        
        # Verify the results
        assert len(result) == 2
        
        # Check banana item
        banana = next(item for item in result if item['item_name'] == 'Banana')
        assert banana['quantity_amount'] == 5.0
        assert banana['quantity_unit'] == 'unit'
        assert banana['count'] == 5
        assert banana['expected_expiration'] == '2023-06-15'
        
        # Check milk item
        milk = next(item for item in result if item['item_name'] == 'Milk')
        assert milk['quantity_amount'] == 1.0
        assert milk['quantity_unit'] == 'L'
        assert milk['count'] == 1
        assert milk['expected_expiration'] == '2023-06-10'
    
    def test_parse_openai_response_with_markdown(self, vision_service):
        # Test with markdown code blocks
        markdown_response = f"""```json
{SAMPLE_OPENAI_RESPONSE}
```"""
        result = vision_service.parse_openai_response(markdown_response)
        assert len(result) == 2  # Should still parse correctly
    
    def test_parse_openai_response_with_invalid_json(self, vision_service):
        # Test with invalid JSON
        with pytest.raises(ValueError):
            vision_service.parse_openai_response("Not a JSON")
    
    def test_parse_openai_response_with_missing_fields(self, vision_service):
        # Test with missing fields
        response = """
        [
            {
                "item_name": "Apple",
                "quantity": "3",
                "expiration_date": "2023-06-20"
            }
        ]
        """
        result = vision_service.parse_openai_response(response)
        assert len(result) == 1
        assert result[0]['count'] == 1  # Default count should be 1
        assert result[0]['quantity_amount'] == 3.0
        assert result[0]['quantity_unit'] == 'unit'  # Default unit
    
    def test_parse_openai_response_combine_duplicates(self, vision_service):
        # Test combining duplicate items
        response = """
        [
            {"item_name": "Apple", "quantity": "3", "count": 2, "expiration_date": "2023-06-20"},
            {"item_name": "Apple", "quantity": "2", "count": 1, "expiration_date": "2023-06-25"}
        ]
        """
        result = vision_service.parse_openai_response(response)
        assert len(result) == 1
        assert result[0]['item_name'] == 'Apple'
        assert result[0]['quantity_amount'] == 5.0  # 3 + 2
        assert result[0]['count'] == 3  # 2 + 1
        assert result[0]['expected_expiration'] == '2023-06-20'  # Earlier date is kept

    @pytest.mark.asyncio
    async def test_classify_food_items_api_error(self, vision_service, sample_image):
        # Test error handling when API call fails
        with patch('backend_gateway.services.vision_service.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Make the API call raise an exception
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            base64_image = base64.b64encode(sample_image.getvalue()).decode('utf-8')
            
            with pytest.raises(RuntimeError) as exc_info:
                await vision_service.classify_food_items(base64_image, "image/jpeg")
            
            assert "Error communicating with OpenAI API" in str(exc_info.value)
