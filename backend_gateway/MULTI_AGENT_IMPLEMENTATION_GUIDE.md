# Multi-Agent CrewAI Implementation Guide

## Current vs. Original Architecture Comparison

### Current Implementation (Single Agent)
```
User Message → CrewAIService → RecipeAdvisor → Response
                    ↓
              External APIs
              (Spoonacular)
```

### Original Multi-Agent Design
```
User Message → Crew Orchestrator
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
Pantry Scan Agent          User Preference Agent
    ↓                               ↓
Ingredient Filter Agent ←───────────┘
    ↓
Recipe Search Agent
    ↓
Nutritional Agent
    ↓
Recipe Scoring Agent
    ↓
Recipe Evaluator Agent
    ↓
Response Formatting Agent
    ↓
Final Response
```

## Detailed Agent Specifications

### 1. Pantry Scan Agent 🖨️
**Purpose**: Database interaction specialist
```python
Input: {
    "user_id": 111
}

Process:
- Connects to PostgreSQL database
- Executes query: SELECT * FROM user_pantry_full
- Retrieves all pantry items

Output: {
    "pantry_items": [
        {
            "pantry_item_id": 1,
            "product_name": "Chicken Breast",
            "quantity": 2,
            "unit": "lbs",
            "expiration_date": "2024-07-20",
            "category": "protein"
        },
        ...
    ]
}
```

### 2. Ingredient Filter Agent 🚫
**Purpose**: Quality control for ingredients
```python
Input: {
    "pantry_items": [...] # From Pantry Scan Agent
}

Process:
- Check expiration dates
- Remove expired items
- Filter out unusable items (e.g., empty quantities)

Output: {
    "valid_ingredients": [...],
    "expired_items": [...],
    "filtered_count": 3
}
```

### 3. User Preference Agent 🍴
**Purpose**: User profile specialist
```python
Input: {
    "user_id": 111
}

Process:
- Query user_preferences table
- Extract dietary restrictions
- Get allergen information
- Retrieve cuisine preferences

Output: {
    "dietary_restrictions": ["vegetarian"],
    "allergens": ["nuts", "shellfish"],
    "cuisine_preferences": ["italian", "asian"],
    "cooking_skill": "intermediate",
    "max_cooking_time": 45
}
```

### 4. Recipe Search Agent 🔍
**Purpose**: Recipe discovery specialist
```python
Input: {
    "valid_ingredients": [...],
    "user_preferences": {...},
    "user_query": "What can I make for dinner?"
}

Process:
- Search saved recipes database
- Query Spoonacular API
- Apply preference filters
- Consider user's query context

Output: {
    "potential_recipes": [
        {
            "id": 12345,
            "name": "Chicken Stir Fry",
            "source": "spoonacular",
            "ingredients": [...],
            "missing_ingredients": ["soy sauce"],
            "match_percentage": 85
        },
        ...
    ]
}
```

### 5. Nutritional Agent 🥗
**Purpose**: Health and nutrition analyst
```python
Input: {
    "recipes": [...] # From Recipe Search Agent
}

Process:
- Calculate calories, protein, carbs, fat
- Evaluate nutritional balance
- Check for dietary compliance
- Add health scores

Output: {
    "recipes_with_nutrition": [
        {
            ...recipe_data,
            "nutrition": {
                "calories": 450,
                "protein": 35,
                "carbs": 45,
                "fat": 15,
                "fiber": 8,
                "sugar": 12,
                "sodium": 800
            },
            "health_score": 8.5,
            "nutritional_balance": "good"
        }
    ]
}
```

### 6. Recipe Scoring Agent ⭐
**Purpose**: Ranking and prioritization specialist
```python
Input: {
    "recipes_with_nutrition": [...],
    "user_preferences": {...},
    "context": {
        "meal_type": "dinner",
        "has_expiring_items": true
    }
}

Process:
- Score based on:
  * Ingredient match (0-40 points)
  * Nutritional value (0-30 points)
  * User preference match (0-20 points)
  * Uses expiring items (0-10 points)
- Apply weighted scoring
- Sort by total score

Output: {
    "ranked_recipes": [
        {
            ...recipe_data,
            "total_score": 85,
            "score_breakdown": {
                "ingredient_match": 35,
                "nutrition": 25,
                "preference": 20,
                "expiring_bonus": 5
            }
        }
    ]
}
```

### 7. Recipe Evaluator Agent ✅
**Purpose**: Quality assurance specialist
```python
Input: {
    "ranked_recipes": [...] # Top 10 from Scoring Agent
}

Process:
- Verify recipe completeness
- Check instruction clarity
- Validate cooking times
- Ensure ingredient availability
- Remove impractical recipes

Output: {
    "validated_recipes": [...], # Top 5-7 recipes
    "rejected_recipes": [
        {
            "recipe": {...},
            "reason": "Instructions unclear"
        }
    ]
}
```

### 8. Response Formatting Agent 💬
**Purpose**: Communication specialist
```python
Input: {
    "validated_recipes": [...],
    "user_query": "What can I make for dinner?",
    "context": {
        "expiring_items": ["milk", "chicken"],
        "preferences_applied": true
    }
}

Process:
- Generate natural language response
- Format recipe cards
- Add contextual advice
- Include shopping list for missing items

Output: {
    "response": "I found 5 great dinner options for you! I've prioritized recipes that use your expiring milk and chicken. All recipes respect your vegetarian preferences.",
    "formatted_recipes": [
        {
            "title": "🍜 Creamy Mushroom Pasta",
            "time": "25 min",
            "difficulty": "Easy",
            "uses_expiring": ["milk"],
            "missing": ["mushrooms"],
            "preview": "A rich, creamy pasta perfect for dinner..."
        }
    ],
    "quick_tips": [
        "Your milk expires in 2 days - I've prioritized recipes using it",
        "All recipes can be made in under 45 minutes"
    ]
}
```

## Implementation Steps

### 1. Install CrewAI with proper version
```bash
pip install crewai==0.1.32
```

### 2. Create Agent Classes
Each agent needs:
- Specific tools (database access, API calls)
- Clear role and goal
- Defined input/output format

### 3. Define Task Chain
Tasks must be ordered correctly:
1. Parallel: Pantry Scan + User Preferences
2. Sequential: Filter → Search → Nutrition → Score → Evaluate → Format

### 4. Configure Crew
```python
crew = Crew(
    agents=[...all_8_agents],
    tasks=[...all_8_tasks],
    process=Process.sequential,
    memory=True,  # Agents can reference previous results
    cache=True,   # Cache results for efficiency
    max_rpm=10,   # Rate limiting
    share_crew=True  # Agents can communicate
)
```

### 5. Integration Points
- Database connections in tools
- Async API calls for Spoonacular
- Error handling at each agent level
- Timeout management (30s max)

## Benefits of Multi-Agent Approach

1. **Separation of Concerns**: Each agent has one job
2. **Scalability**: Easy to add new agents (e.g., Cost Calculator Agent)
3. **Debugging**: Can test each agent independently
4. **Flexibility**: Can reorder or parallelize tasks
5. **Specialization**: Each agent can be optimized for its task

## Challenges to Consider

1. **Complexity**: More moving parts than single agent
2. **Latency**: Sequential processing adds time
3. **Coordination**: Agents must communicate effectively
4. **Error Propagation**: One agent failure affects chain
5. **Resource Usage**: Multiple agents = more memory/CPU

## Testing Strategy

### Unit Tests per Agent
```python
def test_pantry_scan_agent():
    agent = create_pantry_scan_agent()
    result = agent.execute(user_id=111)
    assert len(result['pantry_items']) > 0

def test_filter_agent():
    agent = create_filter_agent()
    result = agent.execute(pantry_items=mock_items)
    assert len(result['expired_items']) == 1
```

### Integration Tests
```python
def test_full_crew_flow():
    crew = create_recipe_crew()
    result = crew.kickoff(user_id=111, message="Quick dinner")
    assert 'recipes' in result
    assert len(result['recipes']) <= 5
```

## Migration Path

1. **Phase 1**: Keep current system running
2. **Phase 2**: Implement agents one by one
3. **Phase 3**: Test multi-agent system in parallel
4. **Phase 4**: Gradual rollout (10% → 50% → 100%)
5. **Phase 5**: Deprecate old system

This architecture provides better modularity and follows the original design vision while adding complexity that needs to be managed carefully.