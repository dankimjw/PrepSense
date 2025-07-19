# PrepSense Comprehensive Test Implementation Guide

## 🎯 Overview

This is a **batteries-included test bundle** for the PrepSense FastAPI + PostgreSQL + CrewAI stack. Every test is designed to be **executable and fail-fast**, preventing hallucinated "all done!" responses.

## 📁 Directory Structure

```
backend_gateway/
├── tests/                          # Main test directory
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures & test config
│   ├── api/                        # API endpoint tests
│   │   ├── __init__.py
│   │   └── test_chat_recommend.py  # Chat/CrewAI integration tests
│   ├── domain/                     # Domain logic tests
│   │   ├── __init__.py
│   │   └── test_crew_ai_service.py # CrewAI service logic tests
│   ├── db/                         # Database tests
│   │   ├── __init__.py
│   │   └── test_migrations.py      # Migration & schema tests
│   ├── contracts/                  # OpenAPI contract tests
│   │   ├── __init__.py
│   │   └── test_openapi.py         # Schemathesis fuzzing tests
│   └── perf/                       # Performance tests
│       ├── __init__.py
│       └── test_performance.py     # Response time & throughput tests
├── requirements-dev.txt            # Test dependencies
├── pytest.ini                     # Pytest configuration
├── locustfile.py                  # Load testing with Locust
├── run_tests.py                   # Test runner script
└── test_ingredient_matching_simple.py  # Ingredient matching tests
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend_gateway
pip install -r requirements-dev.txt
```

### 2. Run All Tests

```bash
# Run comprehensive test suite
python run_tests.py

# Run with load testing
python run_tests.py --load

# Run specific test categories
pytest tests/domain/ -v           # Unit tests
pytest tests/api/ -v              # Integration tests  
pytest tests/contracts/ -v        # Contract tests
pytest tests/perf/ -v -m performance  # Performance tests
```

### 3. Run Load Testing

```bash
# Basic load test
locust -H http://localhost:8000 -u 50 -r 10 --run-time 1m

# AI-intensive test
locust -H http://localhost:8000 -u 20 -r 5 --run-time 2m --locustfile locustfile.py CrewAIIntensiveUser

# Stress test
locust -H http://localhost:8000 -u 100 -r 20 --run-time 30s --locustfile locustfile.py StressTestUser
```

## 🧪 Test Categories

### 1. API Tests (`tests/api/`)
- **Chat endpoint integration** with CrewAI
- **Ingredient matching consistency** between cards and details
- **Error handling** for AI service failures
- **Response format validation**
- **Dietary restrictions** handling

### 2. Domain Tests (`tests/domain/`)
- **RecipeAdvisor agent** pantry analysis
- **Ingredient name cleaning** (fixes the "lbs" bug)
- **Ingredient similarity matching**
- **Recipe scoring** and ranking logic
- **Meal type detection**

### 3. Database Tests (`tests/db/`)
- **Migration application** and rollback
- **Schema integrity** checks
- **Foreign key constraints**
- **Index performance** validation
- **Data consistency** tests

### 4. Contract Tests (`tests/contracts/`)
- **OpenAPI schema compliance** with Schemathesis
- **Request/response validation**
- **Edge case fuzzing**
- **Performance contract** verification

### 5. Performance Tests (`tests/perf/`)
- **Response time** benchmarks (< 2s normal, < 5s AI-intensive)
- **Concurrent request** handling
- **Memory usage** monitoring
- **Throughput** measurement
- **Ingredient matching** performance

## 📊 Performance Criteria

### Response Time Targets
- **Normal requests**: < 1.5s mean, < 3s P95
- **AI-intensive requests**: < 5s mean, < 10s P95
- **Database queries**: < 500ms
- **Ingredient matching**: < 100ms

### Throughput Targets
- **Normal load**: > 50 requests/second
- **Stress load**: > 20 requests/second
- **Error rate**: < 1% normal, < 5% stress

## 🔧 Key Features

### CrewAI Testing
- **Mocked AI responses** for deterministic tests
- **Conversation continuity** testing
- **Complex query handling**
- **Ingredient matching accuracy**

### Ingredient Matching Bug Testing
- **Unit cleaning** (fixed "lbs" → "lb" bug)
- **Modifier removal** (fixed "whole milk" → "milk")
- **Consistency validation** between card counts and details
- **Edge case handling** (case sensitivity, duplicates)

### Contract Validation
- **OpenAPI compliance** with auto-generated test cases
- **Schema validation** for all endpoints
- **Error response format** consistency
- **Performance contract** enforcement

## 🚨 Failure Modes

Tests are designed to **fail fast** and provide actionable feedback:

1. **Import errors** → Missing dependencies or broken imports
2. **Contract violations** → API doesn't match OpenAPI spec
3. **Performance degradation** → Response times exceed thresholds
4. **Data inconsistency** → Ingredient counts don't match
5. **AI service failures** → Graceful error handling verification

## 🔄 CI/CD Integration

The `.github/workflows/ci.yml` runs:
- **Backend tests** with PostgreSQL
- **Contract tests** with Schemathesis
- **Code quality** checks (Black, Ruff, Bandit)
- **Performance tests** on PRs
- **Mobile tests** (when implemented)
- **E2E tests** (when implemented)

## 📝 Test Data

### Fixtures Provided
- **Sample pantry data** with expiration dates
- **Mock CrewAI responses** for deterministic testing
- **Recipe data** with ingredient lists
- **User preferences** for dietary restrictions

### Environment Variables
```bash
TESTING=true
DATABASE_URL=postgresql://test:test@localhost/test_db
OPENAI_API_KEY=test-key-123
SPOONACULAR_API_KEY=test-spoon-key
```

## 🎯 How to Use with Claude

1. **Commit this test structure** to your repo
2. **Ask Claude to implement** the missing production code
3. **Run tests** to verify implementation
4. **Iterate** until all tests pass

Example prompt:
> "Here's my test structure. Implement the FastAPI chat endpoint and CrewAI service so all tests pass. The tests show exactly what the API should do."

## 🏆 Success Metrics

When all tests pass, you'll have:
- ✅ **Working CrewAI integration** with recipe recommendations
- ✅ **Fixed ingredient matching** bug (card counts = details)
- ✅ **API contract compliance** with OpenAPI schema
- ✅ **Performance within** acceptable limits
- ✅ **Database integrity** with proper migrations
- ✅ **Error handling** that gracefully handles failures

## 🔍 Debugging Failed Tests

### Common Issues
1. **Missing dependencies** → Install from requirements-dev.txt
2. **Database connection** → Check PostgreSQL container
3. **Import errors** → Verify Python path in conftest.py
4. **AI service mocks** → Check mock patches in tests
5. **Performance failures** → Reduce load or increase thresholds

### Debug Commands
```bash
# Run with verbose output
pytest -v -s tests/

# Run specific test with pdb
pytest --pdb tests/domain/test_crew_ai_service.py::test_ingredient_matching

# Check test coverage
pytest --cov=services tests/

# Profile performance
pytest --profile tests/perf/
```

This test bundle ensures that **every feature works as expected** and **prevents regression** as the codebase evolves. The tests are the **source of truth** for how the system should behave.