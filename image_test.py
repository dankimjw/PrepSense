"""Utility for manual image generation in tests."""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from backend_gateway.app import app
from backend_gateway.services.vision_service import VisionService
from backend_gateway.routers.images_router import get_vision_service

@pytest.fixture
def mock_vision_service_instance():
    mock_service = AsyncMock(spec=VisionService)
    mock_service.process_image.return_value = ("mock_base64_image", "image/jpeg")
    mock_service.classify_food_items.return_value = '[{"item_name": "Milk", "quantity": "1 L", "expiration_date": "2025-05-15"}]'
    mock_service.parse_openai_response.return_value = [
        {"item_name": "Milk", "quantity_amount": 1, "quantity_unit": "L", "expected_expiration": "2025-05-15"}
    ]
    return mock_service

@pytest.fixture
def client_with_mock_vision(mock_vision_service_instance):
    app.dependency_overrides[get_vision_service] = lambda: mock_vision_service_instance
    client = TestClient(app)
    yield client  # Use yield for setup/teardown if needed, or just return
    app.dependency_overrides.clear() # Clean up overrides after test

def test_upload_image(client_with_mock_vision):
    url = "/v1/images/upload"
    # Use relative path as suggested above
    image_path = "path/to/your/test_assets/Pantry-Foods.png"

    with open(image_path, "rb") as img_file:
        files = {"file": ("image.jpg", img_file, "image/jpeg")}
        response = client_with_mock_vision.post(url, files=files)

    assert response.status_code == 200
    assert response.json() == [
        {"item_name": "Milk", "quantity_amount": 1, "quantity_unit": "L", "expected_expiration": "2025-05-15"}
    ]