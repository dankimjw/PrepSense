# Backend Gateway Tests

This directory contains comprehensive unit and integration tests for the PrepSense backend gateway, with a focus on the Spoonacular-enhanced agents and hybrid CrewAI services.

## Test Structure

```
tests/
├── conftest.py                           # Shared fixtures and test configuration
├── test_spoonacular_enhanced_agents.py   # Tests for Spoonacular-enhanced CrewAI agents
├── test_hybrid_crew_service.py           # Tests for hybrid generation/evaluation service
├── test_hybrid_chat_router.py            # Tests for hybrid chat API endpoints
└── README.md                             # This file
```

## Running Tests

### Run all tests
```bash
python run_tests.py
```

### Run with coverage report
```bash
python run_tests.py --coverage
```

### Run specific test categories
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# Spoonacular agent tests only
python run_tests.py --spoonacular

# Hybrid service tests only
python run_tests.py --hybrid
```

### Run specific test files
```bash
pytest tests/test_spoonacular_enhanced_agents.py -v
```

### Run with verbose output and stop on first failure
```bash
python run_tests.py -v -x
```

## Test Categories

### 1. Spoonacular-Enhanced Agents Tests
Tests for all CrewAI agents that leverage Spoonacular APIs:
- Recipe validation
- Ingredient verification
- Nutrition calculation
- Cost estimation
- Dietary compliance
- Seasonal availability
- Wine pairing
- Unit conversion

### 2. Hybrid Service Tests
Tests for the hybrid approach combining fast OpenAI generation with quality evaluation:
- Recipe generation
- Quality evaluation
- Performance tracking
- User preference matching
- Context-aware features (authenticity, budget, leftovers)

### 3. API Router Tests
Tests for FastAPI endpoints:
- Request/response validation
- Error handling
- Comparison mode
- Performance metrics

## Key Test Fixtures

### `mock_spoonacular_service`
Mocks all Spoonacular API calls with realistic responses.

### `sample_recipe`
Provides a complete recipe object for testing.

### `sample_user_preferences`
User preferences including dietary restrictions, allergens, and cuisine preferences.

### `mock_crew_ai_service`
Mocks the recipe generation service.

### `mock_database_service`
Mocks database queries for user preferences.

## Test Markers

Tests are marked with the following pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.asyncio` - Asynchronous tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.spoonacular` - Tests requiring Spoonacular mocks
- `@pytest.mark.crewai` - Tests requiring CrewAI mocks

## Coverage Requirements

The project aims for:
- Minimum 70% overall coverage
- 80%+ coverage for critical services
- 90%+ coverage for API endpoints

## Writing New Tests

1. **Use appropriate fixtures** - Check `conftest.py` for available fixtures
2. **Mock external services** - Never make real API calls in tests
3. **Test edge cases** - Include error scenarios and validation
4. **Use descriptive names** - Test names should explain what they test
5. **Keep tests focused** - One test should verify one behavior

## Example Test Structure

```python
class TestMyFeature:
    """Test group for a specific feature"""
    
    @pytest.fixture
    def setup(self):
        """Setup for this test class"""
        return Mock()
    
    def test_success_case(self, setup, mock_spoonacular_service):
        """Test the happy path"""
        # Arrange
        mock_spoonacular_service.some_method.return_value = {...}
        
        # Act
        result = my_function()
        
        # Assert
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async functionality"""
        result = await async_function()
        assert result is not None
```

## Continuous Integration

Tests are run automatically on:
- Every push to main branch
- Every pull request
- Can be triggered manually

## Troubleshooting

### Import Errors
Make sure you're running tests from the `backend_gateway` directory:
```bash
cd backend_gateway
python -m pytest
```

### Async Test Issues
Ensure you're using `@pytest.mark.asyncio` decorator for async tests.

### Mock Not Working
Check that you're patching the correct import path. Use the full module path where the object is used, not where it's defined.

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Update this README if adding new test categories