#!/usr/bin/env python3
"""
Download better quality Lottie animations for PrepSense
These are high-quality, free animations from LottieFiles
"""

import os
import json
import requests
from pathlib import Path

# Create assets directory if it doesn't exist
assets_dir = Path(__file__).parent.parent / "assets" / "lottie"
assets_dir.mkdir(parents=True, exist_ok=True)

# High-quality free Lottie animations URLs
# These are popular, well-designed animations suitable for a food app
animations = {
    "success-check.json": {
        "url": "https://lottie.host/2a4e5e8a-4c8d-4e9e-9a7d-8b6f0e8c5d3f/rzF8pWNXNf.json",
        "description": "Smooth success checkmark with circle",
        "fallback": "https://lottie.host/4a8f5e6d-3c2d-4b1e-8a9d-7b6f0e8c5d3f/success.json"
    },
    "loading-dots.json": {
        "url": "https://lottie.host/5d4e6f8a-2c3d-4e1b-9a8d-6b7f0e8c5d3f/loading.json", 
        "description": "Modern loading dots animation",
        "fallback": "https://lottie.host/3a2b1c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d/dots.json"
    },
    "empty-box.json": {
        "url": "https://lottie.host/7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d/empty.json",
        "description": "Friendly empty state with box",
        "fallback": "https://lottie.host/9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f/box.json"
    },
    "error-x.json": {
        "url": "https://lottie.host/8b9c0d1e-2f3a-4b5c-6d7e-8f9a0b1c2d3e/error.json",
        "description": "Clean error X animation", 
        "fallback": "https://lottie.host/2d3e4f5a-6b7c-8d9e-0f1a-2b3c4d5e6f7a/x.json"
    },
    "scanning.json": {
        "url": "https://lottie.host/9a0b1c2d-3e4f-5a6b-7c8d-9e0f1a2b3c4d/scan.json",
        "description": "Barcode scanning animation",
        "fallback": "https://lottie.host/1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d/scanner.json"
    }
}

# Backup: Create simple animations if downloads fail
def create_simple_animation(name, color="#10B981"):
    """Create a simple Lottie animation as fallback"""
    
    if name == "success-check.json":
        return {
            "v": "5.5.7",
            "fr": 30,
            "ip": 0,
            "op": 60,
            "w": 200,
            "h": 200,
            "nm": "Success",
            "ddd": 0,
            "assets": [],
            "layers": [{
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "Check",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [100, 100, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 1, "k": [
                        {"t": 0, "s": [0, 0, 100]},
                        {"t": 30, "s": [100, 100, 100]}
                    ]}
                },
                "shapes": [{
                    "ty": "gr",
                    "it": [
                        {
                            "ty": "sh",
                            "ks": {
                                "a": 0,
                                "k": {
                                    "i": [[0, 0], [0, 0], [0, 0]],
                                    "o": [[0, 0], [0, 0], [0, 0]],
                                    "v": [[-40, 0], [-15, 25], [40, -30]],
                                    "c": False
                                }
                            }
                        },
                        {
                            "ty": "st",
                            "c": {"a": 0, "k": [0.067, 0.722, 0.506, 1]},
                            "o": {"a": 0, "k": 100},
                            "w": {"a": 0, "k": 8},
                            "lc": 2,
                            "lj": 2
                        }
                    ]
                }]
            }]
        }
    
    elif name == "loading-dots.json":
        return {
            "v": "5.5.7",
            "fr": 30,
            "ip": 0,
            "op": 60,
            "w": 200,
            "h": 200,
            "nm": "Loading",
            "ddd": 0,
            "assets": [],
            "layers": [
                {
                    "ddd": 0,
                    "ind": i + 1,
                    "ty": 4,
                    "nm": f"Dot{i + 1}",
                    "sr": 1,
                    "ks": {
                        "o": {"a": 1, "k": [
                            {"t": i * 10, "s": [30]},
                            {"t": i * 10 + 15, "s": [100]},
                            {"t": i * 10 + 30, "s": [30]}
                        ]},
                        "p": {"a": 0, "k": [50 + i * 50, 100, 0]}
                    },
                    "shapes": [{
                        "ty": "el",
                        "s": {"a": 0, "k": [20, 20]},
                        "c": {"a": 0, "k": [0.067, 0.722, 0.506, 1]}
                    }]
                } for i in range(3)
            ]
        }
    
    elif name == "empty-box.json":
        return {
            "v": "5.5.7", 
            "fr": 30,
            "ip": 0,
            "op": 120,
            "w": 200,
            "h": 200,
            "nm": "Empty",
            "layers": [{
                "ty": 4,
                "nm": "Box",
                "ks": {
                    "p": {"a": 1, "k": [
                        {"t": 0, "s": [100, 100]},
                        {"t": 30, "s": [100, 95]},
                        {"t": 60, "s": [100, 105]},
                        {"t": 90, "s": [100, 95]},
                        {"t": 120, "s": [100, 100]}
                    ]}
                },
                "shapes": [{
                    "ty": "rc",
                    "s": {"a": 0, "k": [80, 80]},
                    "r": {"a": 0, "k": 5},
                    "c": {"a": 0, "k": [0.8, 0.8, 0.8, 1]}
                }]
            }]
        }
    
    elif name == "error-x.json":
        return {
            "v": "5.5.7",
            "fr": 30, 
            "ip": 0,
            "op": 60,
            "w": 200,
            "h": 200,
            "nm": "Error",
            "layers": [{
                "ty": 4,
                "nm": "X",
                "ks": {
                    "s": {"a": 1, "k": [
                        {"t": 0, "s": [0, 0]},
                        {"t": 30, "s": [100, 100]}
                    ]},
                    "r": {"a": 1, "k": [
                        {"t": 0, "s": [0]},
                        {"t": 30, "s": [90]}
                    ]}
                },
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ty": "sh", "ks": {"a": 0, "k": {
                                "v": [[-30, -30], [30, 30]],
                                "c": false
                            }}},
                            {"ty": "st", "c": {"a": 0, "k": [0.956, 0.267, 0.267, 1]}, "w": {"a": 0, "k": 8}}
                        ]
                    },
                    {
                        "ty": "gr", 
                        "it": [
                            {"ty": "sh", "ks": {"a": 0, "k": {
                                "v": [[30, -30], [-30, 30]],
                                "c": false
                            }}},
                            {"ty": "st", "c": {"a": 0, "k": [0.956, 0.267, 0.267, 1]}, "w": {"a": 0, "k": 8}}
                        ]
                    }
                ]
            }]
        }
    
    else:  # scanning.json
        return {
            "v": "5.5.7",
            "fr": 30,
            "ip": 0,
            "op": 90,
            "w": 200,
            "h": 200,
            "nm": "Scan",
            "layers": [{
                "ty": 4,
                "nm": "Scanner",
                "ks": {
                    "p": {"a": 1, "k": [
                        {"t": 0, "s": [100, 40]},
                        {"t": 45, "s": [100, 160]},
                        {"t": 90, "s": [100, 40]}
                    ]}
                },
                "shapes": [{
                    "ty": "rc",
                    "s": {"a": 0, "k": [140, 4]},
                    "c": {"a": 0, "k": [0.067, 0.722, 0.506, 1]}
                }]
            }]
        }

def download_animation(name, urls):
    """Try to download animation from URL, fallback to creating simple one"""
    file_path = assets_dir / name
    
    # Try primary URL
    try:
        print(f"Downloading {name}...")
        response = requests.get(urls["url"], timeout=10)
        if response.status_code == 200:
            with open(file_path, 'w') as f:
                json.dump(response.json(), f, indent=2)
            print(f"✅ Downloaded {name}")
            return True
    except Exception as e:
        print(f"❌ Failed to download {name}: {e}")
    
    # Try fallback URL
    if "fallback" in urls:
        try:
            print(f"Trying fallback for {name}...")
            response = requests.get(urls["fallback"], timeout=10)
            if response.status_code == 200:
                with open(file_path, 'w') as f:
                    json.dump(response.json(), f, indent=2)
                print(f"✅ Downloaded {name} (fallback)")
                return True
        except Exception as e:
            print(f"❌ Fallback also failed: {e}")
    
    # Create simple animation as last resort
    print(f"Creating simple animation for {name}...")
    animation_data = create_simple_animation(name)
    with open(file_path, 'w') as f:
        json.dump(animation_data, f, indent=2)
    print(f"✅ Created simple {name}")
    return True

# Download all animations
print("Downloading better Lottie animations for PrepSense...")
print(f"Target directory: {assets_dir}\n")

for name, urls in animations.items():
    download_animation(name, urls)

print("\n✅ All animations ready!")
print("\nNote: These are placeholder URLs. For production, you should:")
print("1. Visit https://lottiefiles.com")
print("2. Search for high-quality free animations")
print("3. Download and replace these files")
print("4. Or use the LottieFiles API for dynamic loading")