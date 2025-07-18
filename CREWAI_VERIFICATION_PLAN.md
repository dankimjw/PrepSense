# CrewAI Implementation Verification & Test Plan

## Current State Analysis

### 1. **No Actual CrewAI Implementation**
- The `CrewAIService` class is misnamed - it doesn't use CrewAI at all
- Uses a simple `RecipeAdvisor` class instead of CrewAI agents
- No crews, agents, or tasks are defined
- Direct API calls to Spoonacular and database queries

### 2. **Version Mismatch**
- `requirements.txt` has `crewai==0.1.32` (very old version)
- Code in `nutrient_auditor_agent.py` tries to use `crewai.flow` (from newer versions)
- This causes import errors and prevents the backend from starting

### 3. **Current Architecture**
```
User Message → CrewAIService (fake) → RecipeAdvisor (simple class)
                    ↓
            Database queries for pantry
                    ↓
            Spoonacular API for recipes
                    ↓
            Custom ranking/scoring
                    ↓
            Response to user
```

## Verification Steps

### Step 1: Fix Immediate Issues
```bash
# 1. Comment out the problematic import
sed -i '' 's/from crewai.flow import Flow, listen, start/# from crewai.flow import Flow, listen, start/' backend_gateway/agents/nutrient_auditor_agent.py

# 2. Start the backend
source venv/bin/activate && python run_app.py

# 3. Test the health endpoint
curl http://localhost:8001/api/v1/health
```

### Step 2: Test Current Functionality
```python
# Test script: test_chat_endpoint.py
import requests
import json

# Test the chat endpoint
url = "http://localhost:8001/api/v1/chat/message"
payload = {
    "message": "What can I make for dinner with chicken?",
    "user_id": 111,
    "use_preferences": True
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

### Step 3: Verify Recipe Recommendation Flow
1. **Check Pantry Retrieval**
   - Verify database connection
   - Confirm pantry items are fetched for user
   
2. **Test Recipe Sources**
   - Saved recipes from database
   - Spoonacular API integration
   
3. **Validate Ranking Logic**
   - Preference scoring
   - Ingredient matching
   - Nutritional analysis

## Implementation Plan for Real CrewAI

### Option 1: Update to Modern CrewAI
```python
# requirements.txt
crewai==0.41.1  # Latest stable version
langchain==0.1.0
openai>=1.7.1

# New implementation structure
from crewai import Agent, Task, Crew

class PantryAnalystAgent(Agent):
    """Analyzes user's pantry items"""
    
class RecipeSearchAgent(Agent):
    """Searches for recipes from multiple sources"""
    
class NutritionExpertAgent(Agent):
    """Evaluates nutritional value"""
    
class RecipeRecommenderCrew(Crew):
    """Orchestrates the agents"""
```

### Option 2: Keep Current Implementation
1. Rename `CrewAIService` to `RecipeRecommendationService`
2. Remove CrewAI from requirements
3. Document that it's a custom implementation
4. Fix the import errors

## Test Cases

### 1. Basic Recipe Request
```json
{
  "message": "What can I make for dinner?",
  "user_id": 111,
  "use_preferences": true
}
```
Expected: Returns 5 recipes based on pantry items

### 2. Expiring Items Priority
```json
{
  "message": "What should I cook with expiring items?",
  "user_id": 111,
  "use_preferences": true
}
```
Expected: Prioritizes recipes using soon-to-expire ingredients

### 3. Dietary Preferences
```json
{
  "message": "Show me vegetarian recipes",
  "user_id": 111,
  "use_preferences": true
}
```
Expected: Filters recipes based on user's dietary preferences

### 4. Nutritional Awareness
```json
{
  "message": "I need high protein meals",
  "user_id": 111,
  "use_preferences": true,
  "include_nutrition": true
}
```
Expected: Returns recipes with nutritional analysis

## Performance Metrics

1. **Response Time**: < 3 seconds for recipe recommendations
2. **Accuracy**: 80%+ ingredient match rate
3. **Relevance**: User preferences properly applied
4. **Availability**: All endpoints respond correctly

## Recommendations

1. **Immediate Action**: Fix the import error to get the backend running
2. **Short Term**: Test and document the current implementation
3. **Long Term**: Either:
   - Implement real CrewAI with proper agents
   - Remove CrewAI references and rename services appropriately

## Commands for Testing

```bash
# Fix imports and start backend
python fix_crewai_imports.py
source venv/bin/activate && python run_app.py

# Run health checks
./quick_check.sh
python check_app_health.py

# Test chat endpoint
python test_chat_endpoint.py

# Monitor logs
tail -f logs/app.log
```