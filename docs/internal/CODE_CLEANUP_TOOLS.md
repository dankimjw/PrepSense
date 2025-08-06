# Code Cleanup Tools Documentation

## 🎯 For Lightbulb-Recommender Agent & All Claude Instances

This document provides comprehensive guidance on using code cleanup tools in the PrepSense project. These tools are essential for maintaining code quality while implementing the lightbulb recommendation system and other features.

## 📋 Tool Overview

### 🛠 React Native/Expo Tools (Frontend)
- **depcheck** - Scans for unused dependencies & files
- **madge** - Builds dependency graphs and finds orphaned files  
- **ts-prune** - Finds unused TypeScript exports (zero config)
- **unimported** - Detects unused files and dependencies
- **react-native-unused-styles** - Finds unused StyleSheet entries
- **eslint-plugin-react-native** - ESLint plugin with `no-unused-styles` rule

### 🐍 Python Tools (Backend)
- **vulture** - Finds unused Python code
- **pytest-vulture** - Pytest integration for vulture

## 🚀 Quick Start Commands

### Frontend Cleanup (React Native/Expo)
```bash
cd ios-app

# Individual cleanup commands
npm run cleanup:deps      # Check unused dependencies
npm run cleanup:orphans   # Find orphaned files
npm run cleanup:exports   # Find unused TypeScript exports
npm run cleanup:unused    # Detect unused files/deps
npm run cleanup:styles    # Find unused React Native styles

# Run all cleanup tools at once
npm run cleanup:all
```

### Backend Cleanup (FastAPI/Python)
```bash
# From project root (ensure venv is activated)
source venv/bin/activate

# Find unused Python code
vulture backend_gateway/ tests/

# Run with pytest integration
pytest --vulture

# Generate coverage and find unused code
coverage run -m pytest
coverage report
```

## 🎯 Lightbulb-Recommender Agent Workflow

### Before Implementation
```bash
# 1. Analyze current codebase
cd ios-app
npm run cleanup:all

# 2. Check backend for unused code
cd ..
vulture backend_gateway/services/crewai_service.py
vulture backend_gateway/routers/chat_router.py
```

### During Development
```bash
# After adding new components/services
npm run cleanup:exports  # Check for unused exports
npm run cleanup:styles   # Verify StyleSheet usage

# Before committing changes
npm run cleanup:all      # Full cleanup scan
vulture backend_gateway/ # Check backend
```

### After Implementation
```bash
# Final cleanup before PR
npm run cleanup:all
vulture backend_gateway/ tests/
npm run lint
npm run test:ci
```

## 🔧 Tool-Specific Usage

### Depcheck (Unused Dependencies)
```bash
# Basic scan
npx depcheck

# With custom configuration
npx depcheck --ignores="expo-*,@expo/*"

# JSON output for CI
npx depcheck --json
```

**Common Expo Whitelist:**
```json
{
  "ignores": [
    "expo-*",
    "@expo/*",
    "react-native-*",
    "@react-native-*"
  ]
}
```

### Madge (Dependency Graph & Orphans)
```bash
# Find orphaned files
npx madge --orphans .

# Generate dependency graph
npx madge --image graph.png .

# Circular dependencies
npx madge --circular .
```

### TS-Prune (Unused TypeScript Exports)
```bash
# Basic scan
npx ts-prune

# Exclude test files
npx ts-prune --ignore "*.test.ts|*.spec.ts"

# JSON output
npx ts-prune --json
```

### React Native Unused Styles
```bash
# Scan for unused styles
npx react-native-unused-styles .

# With specific directories
npx react-native-unused-styles components/ screens/

# Delete unused styles (use with caution)
npx react-native-unused-styles . --delete
```

### Vulture (Python Unused Code)
```bash
# Basic scan
vulture backend_gateway/

# With confidence levels
vulture backend_gateway/ --min-confidence 80

# Exclude test files
vulture backend_gateway/ --exclude "*/test_*.py,*/tests/*"

# Generate whitelist for false positives
vulture backend_gateway/ --make-whitelist > vulture_whitelist.py
```

## 🎨 ESLint Integration

The project now includes React Native ESLint rules:

```javascript
// .eslintrc.js
{
  "plugins": ["react-native"],
  "rules": {
    "react-native/no-unused-styles": "warn"
  }
}
```

## 🔍 Lightbulb System Specific Checks

### Key Files to Monitor
```bash
# Check these files specifically during lightbulb development
npx ts-prune | grep -E "(AddButton|chat-modal|crewai_service|chat_router)"

# Check for unused styles in chat components
npx react-native-unused-styles components/ | grep -i chat

# Backend unused code in recommendation services
vulture backend_gateway/services/ --min-confidence 60
```

### Common Cleanup Tasks
1. **After adding new suggestion types:**
   ```bash
   npm run cleanup:exports  # Check for unused enum exports
   ```

2. **After CrewAI service changes:**
   ```bash
   vulture backend_gateway/services/crewai_service.py --min-confidence 70
   ```

3. **After chat modal updates:**
   ```bash
   npm run cleanup:styles   # Check for unused modal styles
   ```

## 📊 CI/CD Integration

### Pre-commit Hooks
```bash
# Add to pre-commit configuration
- repo: local
  hooks:
    - id: cleanup-check
      name: Code Cleanup Check
      entry: bash -c 'cd ios-app && npm run cleanup:all'
      language: system
      pass_filenames: false
```

### GitHub Actions
```yaml
- name: Code Cleanup Check
  run: |
    cd ios-app
    npm run cleanup:all
    cd ..
    vulture backend_gateway/ --min-confidence 80
```

## 🚨 Important Notes for Claude Instances

### Expo-Specific Considerations
- **Metro bundler** uses dynamic requires - may cause false positives
- **Expo plugins** are often loaded dynamically - add to ignore lists
- **Native modules** may appear unused but are required for compilation

### False Positive Management
```bash
# Create depcheck ignore file
echo '{"ignores": ["expo-*", "@expo/*"]}' > .depcheckrc

# Create vulture whitelist
vulture backend_gateway/ --make-whitelist > vulture_whitelist.py
```

### Before Removing Code
1. **Always verify with tests:** `npm run test:ci`
2. **Check runtime behavior:** Test in simulator
3. **Review git history:** Ensure code isn't seasonally used
4. **Ask user confirmation:** For significant deletions

## 🎯 Integration with Health Checks

Add to existing health check scripts:
```bash
# In quick_check.sh
echo "Running code cleanup checks..."
cd ios-app && npm run cleanup:deps --silent
cd .. && vulture backend_gateway/ --min-confidence 90 --quiet

# In check_app_health.py
subprocess.run(["npm", "run", "cleanup:all"], cwd="ios-app", check=True)
```

## 📈 Monitoring & Reports

### Generate Cleanup Reports
```bash
# Frontend report
cd ios-app
npm run cleanup:all > ../cleanup-report-frontend.txt 2>&1

# Backend report
cd ..
vulture backend_gateway/ --min-confidence 60 > cleanup-report-backend.txt
```

### Regular Maintenance Schedule
- **Weekly:** Run `cleanup:all` and review results
- **Before releases:** Full cleanup + manual verification
- **After major features:** Check for orphaned code from old implementations

This documentation ensures all Claude instances can effectively maintain code quality while implementing the lightbulb recommendation system and other PrepSense features.