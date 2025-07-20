# CrewAI Recipe Recommendation System

A Test-Driven Development (TDD) implementation of a real CrewAI-based recipe recommendation system to replace the fake "CrewAI" service currently in use.

## Overview

This system implements the background/foreground architecture pattern recommended for CrewAI mobile applications:

- **Background Flows**: Pre-process data when pantry/preferences change
- **Foreground Crew**: Real-time recipe recommendations in <3 seconds
- **Redis Caching**: High-performance artifact storage with TTL management

## Architecture

```
User Request → Foreground Crew → Cached Artifacts → Response (<3s)
                      ↑
Background Flows → Cache Artifacts → (Triggered by data changes)
```

## Components Implemented

### 1. Data Models (`models.py`)
- `PantryArtifact` - Cached pantry analysis with expiry detection
- `PreferenceArtifact` - User preference vectors with ML learning
- `RecipeArtifact` - Ranked recipes with embeddings
- `CrewInput/CrewOutput` - Crew communication with performance validation

### 2. Cache Manager (`cache_manager.py`)
- `ArtifactCacheManager` - Redis-based caching with automatic TTL
- Cache invalidation and warming strategies
- Performance monitoring and health checks

### 3. Test Suite (`tests/crewai/`)
- `test_models.py` - Complete data model testing (17 tests ✅)
- `test_cache_manager.py` - Redis cache testing (15 tests)
- `test_background_flows.py` - Flow testing (12 tests)
- `test_foreground_crew.py` - Crew testing (20 tests)

## TDD Implementation Status

✅ **Phase 1 Complete**: Foundation Components
- Data models with serialization, validation, freshness checking
- Cache manager with Redis integration ready
- Comprehensive test coverage for all components

⏳ **Phase 2 Next**: Background Flows
- PantryAnalysisFlow - Process pantry changes
- PreferenceLearningFlow - Update user preferences
- RecipeIntelligenceFlow - Nightly recipe updates

⏳ **Phase 3 Future**: Foreground Crew
- Real-time agents (PantryAnalyst, RecipeRanker, Nutritionist, Copywriter)
- <3 second response time with cached artifacts
- Streaming responses to mobile app

⏳ **Phase 4 Future**: Integration
- Replace fake CrewAIService with real implementation
- Hybrid Spoonacular + AI approach
- Feature flags and gradual rollout

## Performance Targets

- **Response Time**: <3 seconds for recipe recommendations
- **Cache Hit Rate**: >85% for repeat queries
- **Cache TTL**: Pantry (1h), Preferences (24h), Recipes (2h)
- **Relevance Improvement**: 40% better recipe matching

## Usage Example

```python
from backend_gateway.crewai.models import CrewInput, PantryArtifact
from backend_gateway.crewai.cache_manager import ArtifactCacheManager

# Initialize cache manager
cache = ArtifactCacheManager()

# Check for cached artifacts
pantry_artifact = cache.get_pantry_artifact(user_id=123)
preference_artifact = cache.get_preference_artifact(user_id=123)

if pantry_artifact and preference_artifact:
    # Use foreground crew with cached data
    crew_input = CrewInput(
        user_message="What can I make for dinner?",
        user_id=123,
        pantry_artifact=pantry_artifact,
        preference_artifact=preference_artifact
    )
    # Process with real-time crew...
else:
    # Fallback to current Spoonacular system
    # Trigger background flows to warm cache
```

## Testing

Run the comprehensive test suite:

```bash
# Test data models
PYTHONPATH=. python backend_gateway/tests/crewai/test_models.py

# Test cache manager (requires Redis mock)
PYTHONPATH=. python backend_gateway/tests/crewai/test_cache_manager.py
```

## Dependencies

- `redis` - For caching artifacts
- `crewai` - For background flows and foreground crew (Phase 2+)
- Standard Python libraries: `json`, `datetime`, `dataclasses`

## Next Steps

1. Install CrewAI library: `pip install crewai`
2. Implement background flows with failing tests
3. Create real-time foreground crew
4. Replace fake CrewAIService with real implementation

This TDD approach ensures reliable, tested components that meet performance requirements from day one.