#!/usr/bin/env python3
"""
Simple script to download Spoonacular recipe images locally
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

# Configuration
IMAGES_DIR = Path("Recipe Images")
IMAGES_DIR.mkdir(exist_ok=True)

# Priority recipes to download
PRIORITY_RECIPES = [
    {"id": 638071, "title": "Chicken En Papillote With Basil and Cherry Tomatoes"},
    {"id": 633212, "title": "Baba Ganoush"},
    {"id": 632835, "title": "Asian Green Pea Soup"},
    {"id": 1512847, "title": "Avocado Egg Salad"},
    {"id": 639411, "title": "Cilantro Lime Chicken"},
    {"id": 632252, "title": "Alouette Stuffed Mushrooms"},
    {"id": 633344, "title": "Bacon Wrapped Pork Tenderloin"},
    {"id": 645710, "title": "Grilled Fish Tacos"},
    {"id": 649931, "title": "Lentil Soup"},
    {"id": 660109, "title": "Simple Spaghetti Fra Diavolo"},
    {"id": 665527, "title": "Yogurt Parfait"},
    {"id": 715594, "title": "Homemade Garlic and Basil French Fries"},
    {"id": 642129, "title": "Easy to Make Spring Rolls"},
    {"id": 636728, "title": "Butterscotch Pudding"},
    {"id": 649495, "title": "Lemon Chicken Orzo Soup"},
]

# Additional common recipes (add IDs you see in your app)
COMMON_RECIPES = [
    {"id": 716429, "title": "Pasta with Garlic, Scallions, Cauliflower & Breadcrumbs"},
    {"id": 782585, "title": "Cannellini Bean and Asparagus Salad with Mushrooms"},
    {"id": 663559, "title": "Tomato and lentil soup"},
    {"id": 664680, "title": "Vegetarian Mushroom Shepherd's Pie"},
    {"id": 640062, "title": "Corn Avocado Salsa"},
]


def sanitize_filename(text: str) -> str:
    """Create safe filename from text"""
    safe_text = "".join(c for c in text if c.isalnum() or c in " -_")
    safe_text = safe_text.replace(" ", "_").lower()
    return safe_text[:80]


def download_image(recipe_id: int, title: str) -> dict:
    """Download a single recipe image"""
    # Construct Spoonacular image URL
    image_url = f"https://img.spoonacular.com/recipes/{recipe_id}-556x370.jpg"

    # Generate local filename
    safe_title = sanitize_filename(title)
    filename = f"recipe_{recipe_id}_{safe_title}.jpg"
    filepath = IMAGES_DIR / filename

    # Skip if already exists
    if filepath.exists():
        print(f"✅ Already exists: {filename}")
        return {
            "recipe_id": recipe_id,
            "title": title,
            "filename": filename,
            "status": "exists",
            "size": filepath.stat().st_size,
        }

    try:
        # Download image
        response = requests.get(image_url, timeout=30, headers={"User-Agent": "PrepSense/1.0"})
        response.raise_for_status()

        # Save to file
        with open(filepath, "wb") as f:
            f.write(response.content)

        size = filepath.stat().st_size
        print(f"✅ Downloaded: {filename} ({size:,} bytes)")

        return {
            "recipe_id": recipe_id,
            "title": title,
            "filename": filename,
            "status": "downloaded",
            "size": size,
            "url": image_url,
        }

    except Exception as e:
        print(f"❌ Failed {recipe_id}: {e}")
        return {"recipe_id": recipe_id, "title": title, "status": "failed", "error": str(e)}


def main():
    """Download all recipe images"""
    print("\n🖼️  Spoonacular Recipe Image Downloader")
    print("=" * 50)
    print(f"📁 Saving to: {IMAGES_DIR.absolute()}\n")

    results = []
    all_recipes = PRIORITY_RECIPES + COMMON_RECIPES

    # Download each recipe
    for i, recipe in enumerate(all_recipes, 1):
        print(f"[{i}/{len(all_recipes)}] Recipe {recipe['id']}: {recipe['title']}")
        result = download_image(recipe["id"], recipe["title"])
        results.append(result)

        # Small delay to be polite to Spoonacular
        if result["status"] == "downloaded":
            time.sleep(0.5)

    # Summary
    downloaded = len([r for r in results if r["status"] == "downloaded"])
    exists = len([r for r in results if r["status"] == "exists"])
    failed = len([r for r in results if r["status"] == "failed"])

    print(f"\n📊 Summary:")
    print(f"   • Total: {len(results)}")
    print(f"   • Downloaded: {downloaded}")
    print(f"   • Already existed: {exists}")
    print(f"   • Failed: {failed}")

    # Calculate total size
    total_size = sum(r.get("size", 0) for r in results if r.get("size"))
    print(f"   • Total size: {total_size / 1024 / 1024:.1f} MB")

    # Save manifest
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_recipes": len(results),
        "downloaded": downloaded,
        "exists": exists,
        "failed": failed,
        "total_size_bytes": total_size,
        "recipes": results,
    }

    manifest_path = IMAGES_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n📝 Manifest saved: {manifest_path}")
    print(f"✅ Done! Images saved to: {IMAGES_DIR.absolute()}")


if __name__ == "__main__":
    main()
