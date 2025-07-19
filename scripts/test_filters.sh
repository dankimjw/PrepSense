#!/bin/bash

# Test Recipe Filters
echo "Testing Recipe Filters..."

# Test Discover tab with dietary filter
echo -e "\n1. Testing Discover tab with vegetarian filter:"
curl -X POST http://localhost:8001/api/v1/recipes/search/complex \
  -H "Content-Type: application/json" \
  -d '{
    "query": "pasta",
    "diet": "vegetarian",
    "number": 5
  }' | jq '.results | length'

# Test random recipes with tags
echo -e "\n2. Testing random recipes with tags:"
curl "http://localhost:8001/api/v1/recipes/random?number=5&tags=vegetarian,italian" | jq '.recipes | length'

# Test pantry recipes with intolerances
echo -e "\n3. Testing pantry recipes with intolerances:"
curl -X POST http://localhost:8001/api/v1/recipes/search/from-pantry \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111,
    "max_missing_ingredients": 5,
    "use_expiring_first": true,
    "intolerances": ["dairy", "gluten"]
  }' | jq '.recipes | length'

# Test Chat Endpoint
echo -e "\n\nTesting Chat Endpoint..."

# Test simple greeting
echo -e "\n4. Testing simple greeting (should be fast):"
time curl -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello",
    "user_id": 111
  }' | jq '.response'

# Test pantry query
echo -e "\n5. Testing pantry query (should be fast):"
time curl -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what items do I have in my pantry?",
    "user_id": 111
  }' | jq '.response'

# Test Stats Endpoint
echo -e "\n\nTesting Stats Endpoint..."

echo -e "\n6. Testing comprehensive stats:"
curl "http://localhost:8001/api/v1/stats/comprehensive?user_id=111&timeframe=week" | jq '{
  expired: .pantry.summary.expired_items,
  expiring_soon: .pantry.summary.expiring_soon,
  recently_added: .pantry.summary.recently_added
}'