# 🚀 PrepSense Comprehensive CI/CD Setup Guide

## Overview

This guide provides complete setup instructions for the PrepSense project's comprehensive CI/CD pipeline, including pre-commit hooks, quality gates, automated testing, and failure recovery mechanisms.

## 📋 Table of Contents

1. [Quick Setup](#-quick-setup)
2. [Pre-commit Hooks](#-pre-commit-hooks-setup)
3. [GitHub Actions CI/CD](#-github-actions-cicd)
4. [Quality Gates](#-quality-gates)
5. [Developer Tools](#-developer-tools)
6. [Failure Recovery](#-failure-recovery)
7. [Monitoring & Analytics](#-monitoring--analytics)
8. [Troubleshooting](#-troubleshooting)

## 🎯 Quick Setup

### Prerequisites

- Python 3.9+
- Node.js 20+
- Git
- Docker (optional)

### One-Command Setup

```bash
# Run the automated setup script
./scripts/setup-dev-environment.sh
```

This script will:
- ✅ Set up Python and Node.js environments
- ✅ Install all development tools
- ✅ Configure pre-commit hooks
- ✅ Set up IDE configuration
- ✅ Create helper scripts

## 🪝 Pre-commit Hooks Setup

### Manual Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install --install-hooks
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg
pre-commit install --hook-type prepare-commit-msg

# Configure custom Git hooks
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### Pre-commit Hook Features

#### 🐍 Python Quality Checks
- **Black**: Code formatting (100 character line length)
- **Ruff**: Fast Python linter with auto-fixes
- **isort**: Import statement sorting
- **MyPy**: Static type checking
- **Flake8**: Additional linting with plugins
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking

#### 📱 React Native Quality Checks
- **ESLint**: TypeScript/JavaScript linting with enterprise rules
- **Prettier**: Code formatting
- **TypeScript**: Type checking

#### 🔒 Security & Quality Assurance
- **Spectral**: OpenAPI contract validation
- **Secret detection**: Prevents committing sensitive data
- **Large file detection**: Prevents committing large binaries
- **License insertion**: Automatic copyright headers

#### 🏗️ Build & Validation
- **FastAPI health check**: Validates backend imports
- **React Native typecheck**: TypeScript compilation
- **Test collection**: Validates test discovery
- **API documentation generation**: Auto-updates OpenAPI specs

### Running Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black

# Run hooks on specific files
pre-commit run --files backend_gateway/app.py

# Skip hooks for emergency commits
git commit --no-verify -m "Emergency fix"
```

## 🏗️ GitHub Actions CI/CD

### Workflow Overview

The CI/CD pipeline consists of multiple parallel jobs for maximum efficiency:

#### 🚀 Setup & Preparation
- **Change detection**: Identifies affected services
- **Cache management**: Optimizes build times
- **Condition evaluation**: Skips unnecessary steps

#### 🔒 Security & Quality
- **Security scanning**: Bandit, Safety, Semgrep
- **Code quality analysis**: Parallel backend/frontend checks
- **Dependency auditing**: Vulnerability detection

#### 🧪 Testing Pipeline
- **Backend tests**: Unit, integration, API tests with PostgreSQL/Redis
- **Frontend tests**: Unit, integration, performance tests
- **Contract testing**: OpenAPI validation with Spectral/Schemathesis
- **Performance testing**: Load testing with Locust

#### 🚪 Quality Gates
- **Coverage thresholds**: Backend 70%, Frontend 70%
- **Security requirements**: Zero high-severity vulnerabilities
- **Code quality metrics**: Complexity, maintainability
- **Test requirements**: Minimum test coverage

#### 🚀 Deployment Readiness
- **Build validation**: Ensures deployability
- **Release tagging**: Automated versioning
- **Deployment preparation**: Production-ready artifacts

### Workflow Configuration

```yaml
# Trigger conditions
on:
  push:
    branches: [ main, develop, experimental-work ]
    paths-ignore: ['**.md', 'docs/**']
  pull_request:
    branches: [ main, develop ]
    paths-ignore: ['**.md', 'docs/**']
  workflow_dispatch:
    inputs:
      skip_tests: { type: boolean, default: false }
      run_performance_tests: { type: boolean, default: true }
```

### Environment Variables

The pipeline uses the following environment variables:

```bash
# Database
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/test_db

# APIs
OPENAI_API_KEY=test-key-123
SPOONACULAR_API_KEY=test-spoon-key

# Configuration
TESTING=true
CI=true
```

## 📊 Quality Gates

### Coverage Requirements

```yaml
backend:
  minimum_line_coverage: 70
  minimum_branch_coverage: 65
  minimum_function_coverage: 75

frontend:
  minimum_line_coverage: 70
  minimum_branch_coverage: 65
  minimum_statement_coverage: 70
```

### Code Quality Metrics

```yaml
backend:
  max_cyclomatic_complexity: 10
  max_cognitive_complexity: 15
  max_function_length: 50
  max_file_length: 500

frontend:
  max_cyclomatic_complexity: 10
  max_function_length: 50
  max_file_length: 300
```

### Security Thresholds

```yaml
security:
  max_high_severity_vulnerabilities: 0
  max_medium_severity_vulnerabilities: 5
  max_low_severity_vulnerabilities: 20
  block_secrets_in_code: true
```

### Performance Requirements

```yaml
api_response_time:
  p50_max: 200ms
  p95_max: 500ms
  p99_max: 1000ms

load_testing:
  min_requests_per_second: 50
  max_error_rate: 5%
```

### Running Quality Gate Validation

```bash
# Run all quality checks
python scripts/validate-quality-gates.py

# Run specific categories
python scripts/validate-quality-gates.py --categories coverage security

# Export results
python scripts/validate-quality-gates.py --export json --output results.json
```

## 🛠️ Developer Tools

### Helper Scripts

#### Start Development Environment
```bash
./scripts/start-dev.sh
```
- Starts FastAPI backend on port 8001
- Starts React Native development server
- Manages process lifecycle

#### Run All Tests
```bash
./scripts/run-all-tests.sh
```
- Backend tests with coverage
- Frontend tests with coverage
- Generates HTML coverage reports

#### Quality Check
```bash
./scripts/quality-check.sh
```
- Pre-commit validation
- Code formatting checks
- Type checking
- Linting

### IDE Configuration (VS Code)

The setup includes optimized VS Code configuration:

#### Settings
- Python interpreter path: `./venv/bin/python`
- Format on save enabled
- Auto-organize imports
- ESLint and Prettier integration

#### Extensions
- Python development tools
- TypeScript/React Native tools
- Git integration
- Testing frameworks

#### Debug Configurations
- FastAPI server debugging
- Python file debugging
- Test debugging

## 🚨 Failure Recovery

### Recovery Toolkit

```bash
# Interactive recovery menu
./scripts/recovery-toolkit.sh

# Specific recovery options
./scripts/recovery-toolkit.sh health        # Health check
./scripts/recovery-toolkit.sh python       # Fix Python environment
./scripts/recovery-toolkit.sh nodejs       # Fix Node.js environment
./scripts/recovery-toolkit.sh git          # Fix Git state
./scripts/recovery-toolkit.sh full         # Complete recovery
```

### CI/CD Failure Analysis

```bash
# Analyze failed CI/CD logs
python scripts/ci-failure-analyzer.py ci_log.txt

# Apply automatic fixes
python scripts/ci-failure-analyzer.py ci_log.txt --apply-fixes

# Generate analysis report
python scripts/ci-failure-analyzer.py ci_log.txt --export md
```

### Common Recovery Scenarios

#### 1. Python Environment Corruption
```bash
./scripts/recovery-toolkit.sh python
```
- Removes corrupted virtual environment
- Creates new virtual environment
- Reinstalls dependencies
- Reconfigures pre-commit hooks

#### 2. Node.js Dependency Issues
```bash
./scripts/recovery-toolkit.sh nodejs
```
- Clears npm cache
- Removes node_modules
- Reinstalls dependencies
- Validates TypeScript compilation

#### 3. Pre-commit Hook Failures
```bash
./scripts/recovery-toolkit.sh precommit
```
- Uninstalls corrupted hooks
- Cleans pre-commit cache
- Reinstalls all hooks
- Tests hook functionality

#### 4. Git State Issues
```bash
./scripts/recovery-toolkit.sh git
```
- Resets Git hooks
- Cleans Git index
- Validates Git configuration
- Restores hook permissions

## 📈 Monitoring & Analytics

### Coverage Tracking

Coverage reports are generated in multiple formats:
- **HTML**: Interactive coverage reports
- **XML**: For external tools (Codecov, SonarQube)
- **JSON**: For programmatic analysis
- **Terminal**: Real-time feedback

### Performance Monitoring

#### Load Testing Results
- Request/response metrics
- Error rate analysis
- Latency percentiles
- Throughput measurements

#### Bundle Analysis
- Frontend bundle size tracking
- Dependency analysis
- Performance impact assessment

### Security Monitoring

#### Vulnerability Scanning
- Python dependency vulnerabilities (pip-audit)
- Node.js dependency vulnerabilities (npm audit)
- Static analysis security testing (Bandit)
- Secret detection in commits

## 🔧 Troubleshooting

### Common Issues

#### 1. Pre-commit Hook Failures

**Issue**: Pre-commit hooks fail to install or run
```bash
# Solution
pre-commit clean
pre-commit install --install-hooks
```

#### 2. Python Import Errors

**Issue**: ModuleNotFoundError in tests
```bash
# Solution
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. TypeScript Compilation Errors

**Issue**: TypeScript type checking fails
```bash
# Solution
cd ios-app
rm -rf node_modules
npm install
npm run typecheck
```

#### 4. Database Connection Issues

**Issue**: Tests fail due to database connection
```bash
# Solution
# Check DATABASE_URL environment variable
# Ensure PostgreSQL is running
# Run migrations: alembic upgrade head
```

#### 5. Coverage Below Threshold

**Issue**: Code coverage below required threshold
```bash
# Solution
# Add more unit tests
# Review excluded files in pyproject.toml
# Update coverage thresholds if appropriate
```

### Debugging CI/CD Issues

#### 1. Check Workflow Logs
- Navigate to GitHub Actions tab
- Click on failed workflow
- Expand failed job steps
- Download logs for detailed analysis

#### 2. Local Reproduction
```bash
# Reproduce CI environment locally
export CI=true
export TESTING=true
./scripts/run-all-tests.sh
```

#### 3. Analyze with Failure Analyzer
```bash
# Download GitHub Actions log
python scripts/ci-failure-analyzer.py downloaded_log.txt --export md
```

### Performance Optimization

#### 1. Cache Optimization
- Pre-commit hooks are cached per revision
- Node.js modules cached by package-lock.json hash
- Python dependencies cached by requirements.txt hash

#### 2. Parallel Execution
- Pre-commit hooks run in parallel where possible
- CI/CD jobs run in parallel matrix builds
- Tests can be parallelized with pytest-xdist

#### 3. Smart Triggering
- Path-based triggers skip unnecessary builds
- Change detection runs only affected tests
- Conditional job execution based on changes

## 🎯 Best Practices

### Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git add .
   git commit  # Pre-commit hooks run automatically
   git push    # Pre-push hooks run
   ```

2. **Quality Assurance**
   ```bash
   ./scripts/quality-check.sh  # Before committing
   ./scripts/run-all-tests.sh  # Validate changes
   ```

3. **Recovery Procedures**
   ```bash
   ./scripts/recovery-toolkit.sh health  # Regular health checks
   ```

### CI/CD Best Practices

1. **Branch Protection**
   - Require status checks
   - Require pull request reviews
   - Enforce up-to-date branches

2. **Quality Gates**
   - Zero tolerance for high-security vulnerabilities
   - Maintain high code coverage
   - Enforce code quality standards

3. **Monitoring**
   - Track build times and success rates
   - Monitor security vulnerabilities
   - Review performance metrics

## 📚 Additional Resources

### Documentation
- [Pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Code Quality Tools](https://docs.python.org/3/library/development.html)
- [React Native Testing](https://reactnative.dev/docs/testing-overview)

### Tools Reference
- [Black](https://black.readthedocs.io/) - Python code formatter
- [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter
- [ESLint](https://eslint.org/) - JavaScript/TypeScript linter
- [Spectral](https://stoplight.io/open-source/spectral) - OpenAPI linter
- [Bandit](https://bandit.readthedocs.io/) - Security linter for Python

## 🎉 Conclusion

This comprehensive CI/CD setup provides:

✅ **Automated Quality Assurance**: Pre-commit hooks ensure code quality before commits
✅ **Comprehensive Testing**: Multi-level testing strategy with coverage tracking
✅ **Security First**: Vulnerability scanning and secret detection
✅ **Performance Monitoring**: Load testing and bundle analysis
✅ **Failure Recovery**: Automated recovery mechanisms and detailed analysis
✅ **Developer Experience**: Rich tooling and IDE integration
✅ **Scalable Architecture**: Parallel execution and intelligent caching

The system is designed to catch issues early, provide actionable feedback, and maintain high code quality standards while maximizing developer productivity.

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Maintainer**: PrepSense Development Team