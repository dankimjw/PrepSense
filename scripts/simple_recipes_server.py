#!/usr/bin/env python3
"""
Simple Recipes API Server using Python's built-in HTTP server.
This provides the exact endpoints needed for testing the iOS app's recipes tab.
"""

import http.server
import json
import socketserver
import urllib.parse

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
print("Successfully loaded .env file.")

# Mock recipe data
MOCK_RECIPES = [
    {
        "id": 1,
        "title": "Spaghetti Carbonara",
        "ingredients": ["spaghetti", "eggs", "bacon", "parmesan cheese", "black pepper"],
        "instructions": ["Cook spaghetti", "Fry bacon", "Mix eggs and cheese", "Combine all"],
        "readyInMinutes": 20,
        "servings": 4,
        "image": "https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?w=400",
        "summary": "Classic Italian pasta dish with eggs, cheese, and bacon",
    },
    {
        "id": 2,
        "title": "Chicken Stir Fry",
        "ingredients": ["chicken breast", "bell peppers", "onion", "soy sauce", "garlic"],
        "instructions": ["Cut chicken", "Heat oil", "Stir fry vegetables", "Add chicken and sauce"],
        "readyInMinutes": 15,
        "servings": 2,
        "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400",
        "summary": "Quick and healthy stir fry with fresh vegetables",
    },
    {
        "id": 3,
        "title": "Vegetable Soup",
        "ingredients": ["carrots", "celery", "onion", "vegetable broth", "tomatoes"],
        "instructions": ["Chop vegetables", "Sauté onions", "Add broth", "Simmer 30 minutes"],
        "readyInMinutes": 45,
        "servings": 6,
        "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
        "summary": "Hearty vegetable soup perfect for cold days",
    },
    {
        "id": 4,
        "title": "Grilled Salmon",
        "ingredients": ["salmon fillet", "lemon", "olive oil", "herbs", "salt"],
        "instructions": [
            "Season salmon",
            "Heat grill",
            "Cook 6 minutes per side",
            "Serve with lemon",
        ],
        "readyInMinutes": 25,
        "servings": 2,
        "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
        "summary": "Perfectly grilled salmon with herbs and lemon",
    },
    {
        "id": 5,
        "title": "Caesar Salad",
        "ingredients": ["romaine lettuce", "croutons", "parmesan", "caesar dressing", "anchovies"],
        "instructions": ["Wash lettuce", "Make dressing", "Toss ingredients", "Add croutons"],
        "readyInMinutes": 10,
        "servings": 4,
        "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400",
        "summary": "Classic Caesar salad with homemade dressing",
    },
]


class RecipesAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)

        print(f"GET {path}")

        if path == "/health":
            self.send_json_response(
                {"status": "healthy", "service": "Simple Recipes API Server", "port": 8001}
            )

        elif path == "/api/v1/recipes/random":
            number = int(query_params.get("number", [10])[0])
            recipes = MOCK_RECIPES[:number]
            self.send_json_response(
                {"recipes": recipes, "message": f"Random selection of {len(recipes)} recipes"}
            )

        elif path == "/api/v1/user-recipes":
            user_id = int(query_params.get("user_id", [111])[0])
            # Return first 2 recipes as "saved" recipes
            saved_recipes = [
                {**recipe, "isFavorite": True, "userRating": 5, "dateAdded": "2024-01-15"}
                for recipe in MOCK_RECIPES[:2]
            ]
            self.send_json_response(
                {
                    "recipes": saved_recipes,
                    "totalCount": len(saved_recipes),
                    "message": f"Found {len(saved_recipes)} saved recipes for user {user_id}",
                }
            )

        elif path == "/api/v1/test/recipes-endpoints":
            self.send_json_response(
                {
                    "endpoints": [
                        "POST /api/v1/recipes/search/from-pantry",
                        "POST /api/v1/recipes/search/complex",
                        "GET /api/v1/recipes/random",
                        "GET /api/v1/user-recipes",
                    ],
                    "status": "All recipes endpoints are available",
                    "mock_data_count": len(MOCK_RECIPES),
                    "server_type": "Simple HTTP Server",
                }
            )

        else:
            self.send_json_response(
                {
                    "error": "Not found",
                    "path": path,
                    "available_endpoints": [
                        "GET /health",
                        "GET /api/v1/recipes/random",
                        "GET /api/v1/user-recipes",
                        "POST /api/v1/recipes/search/from-pantry",
                        "POST /api/v1/recipes/search/complex",
                    ],
                },
                404,
            )

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            request_data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            request_data = {}

        print(f"POST {path} with data: {request_data}")

        if path == "/api/v1/recipes/search/from-pantry":
            user_id = request_data.get("user_id", 111)
            self.send_json_response(
                {
                    "results": MOCK_RECIPES,
                    "totalResults": len(MOCK_RECIPES),
                    "message": f"Recipes based on pantry items for user {user_id}",
                    "user_id": user_id,
                }
            )

        elif path == "/api/v1/recipes/search/complex":
            query = request_data.get("query", "")
            diet = request_data.get("diet", "")
            cuisine = request_data.get("cuisine", "")
            number = request_data.get("number", 10)

            # Simple filtering based on query
            filtered_recipes = MOCK_RECIPES
            if query:
                filtered_recipes = [
                    recipe
                    for recipe in MOCK_RECIPES
                    if query.lower() in recipe["title"].lower()
                    or any(
                        query.lower() in ingredient.lower() for ingredient in recipe["ingredients"]
                    )
                ]

            results = filtered_recipes[:number]
            self.send_json_response(
                {
                    "results": results,
                    "totalResults": len(filtered_recipes),
                    "message": f"Found {len(filtered_recipes)} recipes matching '{query}'",
                    "query": query,
                    "diet": diet,
                    "cuisine": cuisine,
                }
            )

        else:
            self.send_json_response({"error": "Not found", "path": path, "method": "POST"}, 404)


def start_server(port=8001):
    """Start the simple recipes API server"""
    print(f"Starting Simple Recipes API Server on port {port}...")
    print("Available endpoints:")
    print("  GET  /health")
    print("  GET  /api/v1/recipes/random")
    print("  GET  /api/v1/user-recipes")
    print("  POST /api/v1/recipes/search/from-pantry")
    print("  POST /api/v1/recipes/search/complex")
    print("  GET  /api/v1/test/recipes-endpoints")
    print()

    with socketserver.TCPServer(("", port), RecipesAPIHandler) as httpd:
        print(f"✅ Server running on http://0.0.0.0:{port}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")


if __name__ == "__main__":
    start_server(8001)
