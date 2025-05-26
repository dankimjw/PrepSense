"""Creates small in-memory images used across tests."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # Create a simple image with some text
    img = Image.new('RGB', (200, 100), color='white')
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Test Food Image", fill='black')
    
    # Save the image
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    img.save(os.path.join(os.path.dirname(__file__), 'test_food.jpg'))

if __name__ == "__main__":
    create_test_image()
