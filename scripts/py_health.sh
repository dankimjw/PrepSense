#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "======================================"
echo "Python Health Check for PrepSense"
echo "======================================"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt -r requirements-dev.txt

# Run ruff for unused imports/variables
echo ""
echo "Checking for unused imports and variables with ruff..."
cd backend_gateway
ruff . --select F401,F841 --quiet || echo "Some unused imports/variables found"

# Run vulture for dead code
echo ""
echo "Checking for dead code with vulture..."
vulture . --min-confidence 80 --exclude="*/tests/*,*/test_*" || echo "Some potentially dead code found"

# Run pytest
echo ""
echo "Running tests..."
pytest -q || echo "Some tests failed"

# Check dependency tree
echo ""
echo "Checking dependency tree..."
pipdeptree --warn silence

# Run bandit for security issues
echo ""
echo "Checking for security issues with bandit..."
bandit -q -r . -f json -o ../bandit-report.json || echo "Security scan complete - check bandit-report.json"

echo ""
echo "Python health check complete!"