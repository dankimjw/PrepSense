#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT/ios-app"

echo "======================================"
echo "JavaScript/TypeScript Health Check"
echo "======================================"

# Install dependencies
echo "Installing dependencies..."
npm ci

# Check for unused dependencies
echo ""
echo "Checking for unused dependencies with depcheck..."
npx depcheck || true

# Check for unused exports  
echo ""
echo "Checking for unused exports with ts-prune..."
npx ts-prune --error || true

# Run ESLint
echo ""
echo "Running ESLint..."
npx eslint . --max-warnings 0 || echo "ESLint found some issues"

# Check Expo setup
echo ""
echo "Running Expo doctor..."
npx expo doctor || true

echo ""
echo "JavaScript/TypeScript health check complete!"