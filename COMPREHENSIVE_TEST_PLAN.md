# Comprehensive Test Suite Implementation Plan

## 🎯 Overview
Implement robust tests for all external integrations:
- Spoonacular API
- OpenAI API
- CrewAI library
- Google Cloud SQL PostgreSQL database
- FastAPI endpoints

Following strict TDD: Write tests first → Confirm they fail → Implement until passing

## 📋 Service Wrapper Modules Needed

### 1. `spoonacular_client.py`
- Encapsulate all Spoonacular API calls
- Handle authentication and error responses
- Parse JSON into domain objects

### 2. `openai_client.py`
- Wrap OpenAI API interactions
- Handle completions and error scenarios
- Manage rate limiting

### 3. `crewai_client.py`
- Thin wrapper around CrewAI library
- Standardize agent execution
- Handle CrewAI exceptions

### 4. `db_client.py`
- Encapsulate Cloud SQL connection logic
- Use SQLAlchemy or psycopg2
- Parameterized for test/prod environments

## 🧪 Test Structure

### Unit Tests
```
tests/
├── test_spoonacular.py      # Spoonacular client tests
├── test_openai.py          # OpenAI client tests
├── test_crewai.py          # CrewAI integration tests
├── test_db.py              # Database client tests
├── test_api.py             # FastAPI endpoint tests
└── conftest.py             # Fixtures and configuration
```

### Test Categories

#### Spoonacular Tests
- ✅ URL construction with parameters
- ✅ API key inclusion
- ✅ JSON parsing to domain objects
- ✅ Error status handling
- ✅ Rate limit handling

#### OpenAI Tests
- ✅ Correct endpoint and payload
- ✅ Headers and authentication
- ✅ Completion response parsing
- ✅ Rate limit errors
- ✅ Invalid key handling

#### CrewAI Tests
- ✅ Library function invocation
- ✅ Proper argument passing
- ✅ Exception handling
- ✅ Mock verification (not reimplementation)

#### Database Tests
- ✅ CRUD operations
- ✅ Constraint violations
- ✅ Transaction rollbacks
- ✅ Connection handling
- ✅ Schema validation

#### FastAPI Tests
- ✅ Valid request handling
- ✅ Edge cases (missing params, invalid IDs)
- ✅ Error responses
- ✅ Dependency injection
- ✅ Service client integration

## 🔧 Implementation Steps

### Phase 1: Environment Setup
```bash
# Install test dependencies
pip install pytest pytest-mock pytest-asyncio pytest-cov

# Configure test database
export TEST_DB_HOST=localhost
export TEST_DB_NAME=prepsense_test
export TEST_DB_USER=test_user
export TEST_DB_PASSWORD=test_pass
```

### Phase 2: Mock Strategy
```python
# HTTP mocking for APIs
@patch('requests.get')
def test_spoonacular_search(mock_get):
    mock_get.return_value.json.return_value = {...}

# CrewAI mocking
@patch('crewai.Agent.execute')
def test_crew_execution(mock_execute):
    mock_execute.return_value = "AI response"

# Database fixture
@pytest.fixture
def test_db():
    # Setup test tables
    yield db_session
    # Teardown
```

### Phase 3: Test Implementation Order
1. Database client tests (foundation)
2. Service wrapper tests (isolated)
3. FastAPI endpoint tests (integration)
4. Cloud SQL connectivity (optional)

## 📊 Edge Cases to Test

### Network Failures
- Connection timeouts
- DNS resolution failures
- SSL certificate errors

### API Errors
- 401 Unauthorized
- 403 Forbidden
- 429 Rate Limited
- 500 Server Error

### Data Validation
- Missing required fields
- Invalid data types
- Constraint violations
- Malformed JSON

### Concurrency
- Race conditions
- Deadlocks
- Connection pool exhaustion

## 🚀 Execution Plan

### Day 1: Planning & Setup
- [ ] Survey existing code
- [ ] Design wrapper interfaces
- [ ] Set up test environment
- [ ] Configure mocking strategy

### Day 2: Service Tests
- [ ] Implement spoonacular_client.py + tests
- [ ] Implement openai_client.py + tests
- [ ] Implement crewai_client.py + tests
- [ ] Implement db_client.py + tests

### Day 3: API Tests
- [ ] FastAPI route tests
- [ ] Integration tests
- [ ] Cloud SQL connectivity test
- [ ] Documentation

## 📝 Deliverables

1. **Service Wrappers**: Clean interfaces for all external services
2. **Test Suite**: 100% coverage of service interactions
3. **Documentation**: `docs/test_report.md` with findings
4. **CI Configuration**: GitHub Actions for automated testing

## 🎯 Success Criteria

- All tests pass locally
- Mocks prevent external API calls
- Tests are deterministic
- Coverage > 90%
- Clear documentation
- Easy to run in CI/CD

---

This plan ensures comprehensive testing while maintaining clean separation of concerns and following TDD principles.