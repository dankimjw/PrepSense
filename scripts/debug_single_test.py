#!/usr/bin/env python3
"""
Single OCR Test - Debug the 500 error issue
"""

import io
import tempfile

import requests
from PIL import Image, ImageDraw


def create_test_image():
    """Create a simple test image"""
    img = Image.new("RGB", (400, 300), color="white")
    draw = ImageDraw.Draw(img)

    # Draw some basic text
    draw.text((50, 100), "BANANA", fill="black")
    draw.text((50, 150), "DOLE", fill="blue")

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    return img_bytes.getvalue()


def test_ocr():
    """Test OCR with detailed error logging"""
    base_url = "http://127.0.0.1:8001/api/v1"

    print("🧪 Testing OCR with single image...")

    # First disable mock data
    print("1. Disabling mock data...")
    response = requests.post(f"{base_url}/ocr/configure-mock-data", json={"use_mock_data": False})
    print(f"   Mock data response: {response.status_code}")

    # Clear cache
    print("2. Clearing cache...")
    response = requests.post(f"{base_url}/ocr/debug/clear-cache")
    print(f"   Cache clear response: {response.status_code}")

    # Create test image
    print("3. Creating test image...")
    test_image = create_test_image()
    print(f"   Image size: {len(test_image)} bytes")

    # Make OCR request
    print("4. Making OCR request...")
    files = {"file": ("test.jpg", test_image, "image/jpeg")}

    try:
        response = requests.post(f"{base_url}/ocr/scan-items", files=files)
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Items: {len(data.get('items', []))}")
            print(f"   Debug info: {data.get('debug_info', {})}")
        else:
            print(f"   Error response: {response.text}")

            # Try to get more detailed error info
            try:
                error_data = response.json()
                print(f"   Error JSON: {error_data}")
            except:
                print("   Could not parse error as JSON")

    except Exception as e:
        print(f"   Exception: {str(e)}")


if __name__ == "__main__":
    test_ocr()
