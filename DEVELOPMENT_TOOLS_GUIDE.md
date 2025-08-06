# PrepSense Backend Development Tools Guide

This guide covers the comprehensive development tooling setup for the PrepSense FastAPI backend, including linting, formatting, type checking, error monitoring, and structured logging.

## 🛠️ Tools Overview

### Code Quality Tools
- **Black**: Code formatting with consistent style
- **isort**: Import statement organization
- **Ruff**: Fast, modern Python linter (primary)
- **Flake8**: Additional linting with plugins
- **MyPy**: Static type checking with Pydantic support

### Monitoring & Observability
- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection and monitoring
- **Structured Logging**: JSON-formatted logs with context
- **OpenTelemetry**: Distributed tracing and observability

### Development Automation
- **dev.py**: Python-based task runner (like npm scripts)
- **pyproject.toml**: Centralized tool configuration
- **Pre-configured workflows**: Format, lint, test, and serve

## 🚀 Quick Start

### 1. Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Development Commands
```bash
# Format code (Black + isort)
python dev.py format

# Lint code (Ruff + Flake8)
python dev.py lint

# Type check (MyPy)
python dev.py typecheck

# Run fast tests
python dev.py test --type=fast

# Comprehensive quality check
python dev.py quality

# Start development server
python dev.py serve --port=8002 --mock
```

### 3. Health Check
```bash
python test_backend_health.py
```

## 📖 Detailed Usage

### Code Formatting

#### Black
Automatic code formatting with consistent style:
```bash
black backend_gateway/ src/ tests/
```

Configuration in `pyproject.toml`:
- Line length: 100 characters
- Target Python 3.9+
- Excludes migrations and auto-generated files

#### isort
Import statement organization:
```bash
isort backend_gateway/ src/ tests/
```

Features:
- Groups imports by type (stdlib, third-party, first-party)
- Compatible with Black formatting
- Consistent trailing commas

### Linting

#### Ruff (Primary Linter)
Fast, modern Python linter:
```bash
ruff check backend_gateway/ src/ tests/ --fix
```

Enabled checks:
- pycodestyle (E, W)
- pyflakes (F)  
- isort (I)
- flake8-bugbear (B)
- flake8-comprehensions (C4)
- pyupgrade (UP)
- flake8-simplify (SIM)

#### Flake8 (Additional Checks)
Comprehensive linting with plugins:
```bash
flake8 backend_gateway/ src/ tests/
```

Plugins included:
- flake8-annotations: Type hint enforcement
- flake8-docstrings: Docstring quality
- flake8-fastapi: FastAPI-specific checks

### Type Checking

#### MyPy
Static type analysis:
```bash
mypy backend_gateway/ src/
```

Configuration:
- Strict mode enabled
- Pydantic plugin support
- FastAPI compatibility
- Third-party library stubs

Common type issues and fixes:
```python
# Before
def get_user(user_id):
    return {"id": user_id}

# After
def get_user(user_id: int) -> Dict[str, Any]:
    return {"id": user_id}
```

### Testing

#### Test Types
```bash
# All tests
python dev.py test

# Unit tests only
python dev.py test --type=unit

# Integration tests
python dev.py test --type=integration

# API tests
python dev.py test --type=api

# Fast tests (exclude slow ones)
python dev.py test --type=fast
```

#### Test Configuration
- Framework: pytest
- Coverage reporting enabled
- Markers for different test types
- Mock data fixtures included

### Development Server

#### Local Development
```bash
# Standard server
python dev.py serve

# With mock data
python dev.py serve --mock

# Custom port
python dev.py serve --port=8002

# No auto-reload
python dev.py serve --no-reload
```

#### Smart Port Detection
The development tools automatically detect port conflicts:
```python
# Automatically finds available ports
python run_backend_test.py  # Uses ports 8002+
python run_app_smart.py     # Full smart detection
```

## 🔧 Configuration Files

### pyproject.toml
Central configuration for all tools:

```toml
[tool.black]
line-length = 100
target-version = ['py39']

[tool.isort]  
profile = "black"
known_first_party = ["backend_gateway"]

[tool.mypy]
python_version = "3.9"
strict = true
plugins = ["pydantic.mypy"]

[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "unit: unit tests", 
    "integration: integration tests",
    "api: API tests"
]
```

### .flake8
Flake8-specific configuration:
```ini
[flake8]
max-line-length = 100
max-complexity = 10
ignore = E203,E501,W503
per-file-ignores = 
    tests/*:D,E501
    __init__.py:F401
```

## 📊 Monitoring & Observability

### Error Tracking (Sentry)

#### Setup
Set environment variable:
```bash
export SENTRY_DSN="https://your-dsn@sentry.io/project"
```

#### Usage
Automatic error capture for:
- Unhandled exceptions
- FastAPI request errors
- CrewAI agent failures
- Database query errors

#### Manual Error Reporting
```python
from backend_gateway.core.monitoring import report_error

try:
    risky_operation()
except Exception as e:
    report_error(e, {"context": "user_action", "user_id": "123"})
```

### Metrics (Prometheus)

#### Available Metrics
- `http_requests_total`: HTTP request count by method/endpoint/status
- `http_request_duration_seconds`: Request duration histogram  
- `crewai_requests_total`: CrewAI agent execution count
- `database_queries_total`: Database query count by type

#### Endpoints
- `/metrics`: Prometheus metrics
- `/monitoring/health`: Monitoring status

#### Agent Monitoring
```python
from backend_gateway.core.monitoring import monitor_crewai_agent

@monitor_crewai_agent("recipe_search")
async def search_recipes(query: str):
    # Agent implementation
    pass
```

### Structured Logging

#### Setup
Automatically configured in `app.py`:
- JSON format for production (`LOG_FORMAT=json`)
- Human-readable for development
- File rotation (10MB app log, 5MB error log)

#### Usage
```python
from backend_gateway.core.logging_config import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info(
    "Recipe search completed",
    user_id="123",
    query="pasta recipes",
    results_count=15,
    duration_ms=234.5
)

# API request logging
from backend_gateway.core.logging_config import log_api_request
log_api_request(logger, "POST", "/api/v1/recipes", 201, 456.7, "user123")
```

#### Log Files
- `logs/prepsense.log`: Main application log
- `logs/errors.log`: Error-level logs only
- `logs/crewai.log`: CrewAI-specific logs

### Distributed Tracing (OpenTelemetry)

#### Setup
```bash
export JAEGER_ENDPOINT="http://localhost:14268"
```

#### Automatic Tracing
- FastAPI requests
- Database queries
- External API calls

#### Manual Tracing
```python
from backend_gateway.core.observability import trace_function

@trace_function("recipe_processing")
async def process_recipe(recipe_data):
    # Processing logic
    pass
```

## 🚦 Quality Checks

### Pre-commit Workflow
```bash
# 1. Format code
python dev.py format

# 2. Run linting
python dev.py lint

# 3. Type check (optional for rapid development)
python dev.py typecheck

# 4. Run tests
python dev.py test --type=fast

# 5. Comprehensive check (all of the above)
python dev.py quality
```

### Continuous Integration
The tools are configured for CI/CD:

```yaml
# GitHub Actions example
- name: Quality Check
  run: |
    source venv/bin/activate
    python dev.py format --check
    python dev.py lint
    python dev.py test
```

### Code Quality Standards

#### Type Hints
All new code should include type hints:
```python
# Good
async def create_recipe(
    recipe_data: RecipeCreate,
    user_id: int,
    db: Session = Depends(get_db)
) -> Recipe:
    pass

# Avoid
async def create_recipe(recipe_data, user_id, db=Depends(get_db)):
    pass
```

#### Error Handling
Use structured error handling:
```python
from backend_gateway.core.monitoring import report_error

async def risky_operation():
    try:
        result = await external_api_call()
        return result
    except ExternalAPIError as e:
        report_error(e, {"operation": "external_api_call"})
        raise HTTPException(status_code=503, detail="Service unavailable")
```

#### Documentation
Use Google-style docstrings:
```python
async def search_recipes(
    query: str,
    filters: Optional[RecipeFilters] = None
) -> List[Recipe]:
    """Search for recipes matching the given criteria.
    
    Args:
        query: Search terms for recipe matching
        filters: Optional filters for dietary restrictions, etc.
        
    Returns:
        List of matching recipes
        
    Raises:
        ValidationError: If search parameters are invalid
        ServiceUnavailable: If search service is down
    """
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Error: Port 8001 already in use
# Solution: Use smart scripts
python run_backend_test.py  # Finds available port
```

#### 2. Import Errors
```bash
# Error: Module not found
# Solution: Check Python path and virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Type Checking Failures
```bash
# Error: Missing type annotations
# Solution: Add type hints incrementally
# Focus on new code first, then legacy code
```

#### 4. Linting Conflicts
```bash
# Error: Black and Flake8 disagree
# Solution: Configuration is aligned, but check for:
# - Custom .flake8 overrides
# - Line length mismatches
```

#### 5. Test Failures Due to Missing Config
```bash
# Error: Database connection failed
# Solution: Use mock data for testing
python dev.py serve --mock
python dev.py test --type=unit  # Uses mocked services
```

### Performance Tips

#### 1. Use Fast Tests During Development
```bash
python dev.py test --type=fast
```

#### 2. Run Quality Checks in Parallel
The `dev.py quality` command runs multiple tools in parallel for speed.

#### 3. Skip Heavy Type Checking for Rapid Iteration
```bash
# Quick check without MyPy
python dev.py format && python dev.py lint
```

#### 4. Use File Watching for Auto-formatting
```bash
# Set up your IDE to run Black on save
# VS Code: "python.formatting.provider": "black"
```

## 📚 Further Reading

- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Sentry FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)

## 🤝 Contributing

When contributing to the backend:

1. **Run quality checks**: `python dev.py quality`
2. **Add type hints** to new functions
3. **Write tests** for new features
4. **Update documentation** as needed
5. **Check monitoring** works with new code

The development tools are designed to maintain code quality while not slowing down development. Use them as part of your workflow for the best experience.