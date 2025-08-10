#!/usr/bin/env python3
"""List all FastAPI routes with their methods and handlers."""

import importlib
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Print all FastAPI routes in a formatted table."""
    try:
        # Import the app
        from backend_gateway.app import app
        from fastapi.routing import APIRoute
        
        print("\n" + "=" * 80)
        print("FastAPI Routes Inventory")
        print("=" * 80)
        print(f"{'Method':<10} {'Path':<50} {'Handler'}")
        print("-" * 80)
        
        routes = []
        for route in app.routes:
            if isinstance(route, APIRoute):
                methods = ", ".join(sorted(m for m in route.methods if m != "HEAD"))
                endpoint = f"{route.endpoint.__module__}.{route.endpoint.__name__}"
                routes.append((methods, route.path, endpoint))
        
        # Sort by path
        routes.sort(key=lambda x: x[1])
        
        for methods, path, endpoint in routes:
            # Truncate long paths and endpoints for readability
            if len(path) > 48:
                path = path[:45] + "..."
            if len(endpoint) > 50:
                endpoint = "..." + endpoint[-47:]
            print(f"{methods:<10} {path:<50} {endpoint}")
        
        print("-" * 80)
        print(f"Total routes: {len(routes)}")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error loading FastAPI app: {e}")
        print("Make sure environment variables are configured properly.")
        sys.exit(1)

if __name__ == "__main__":
    main()