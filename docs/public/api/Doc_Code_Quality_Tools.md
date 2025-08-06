# 6. Code Quality Tools Documentation

## 🚨 CRITICAL INSTRUCTIONS FOR CLAUDE INSTANCES 🚨

This documentation covers code cleanup and quality tools essential for maintaining the PrepSense codebase. **ALL Claude instances MUST use these tools during development.**

**BEFORE and AFTER any code changes:**
1. Run appropriate cleanup tools for your area (frontend/backend)
2. Verify no unused code or dependencies are introduced
3. Check for orphaned files and exports
4. Update this documentation if you discover new patterns

---

## 📋 Tool Matrix Overview

### 🛠 React Native/Expo Tools (Frontend - ios-app/)
| Tool | Purpose | Command | Focus Area |
|------|---------|---------|------------|
| **depcheck** | Unused dependencies & files | `npm run cleanup:deps` | package.json dependencies |
| **madge** | Dependency graphs & orphans | `npm run cleanup:orphans` | File relationships |
| **ts-prune** | Unused TypeScript exports | `npm run cleanup:exports` | TypeScript interfaces/exports |
| **unimported** | Unused files & dependencies | `npm run cleanup:unused` | Overall project cleanup |
| **react-native-unused-styles** | Unused StyleSheet entries | `npm run cleanup:styles` | React Native StyleSheet |
| **eslint-plugin-react-native** | Style linting | `npm run lint` | ESLint integration |

### 🐍 Python Tools (Backend - backend_gateway/)
| Tool | Purpose | Command | Focus Area |
|------|---------|---------|------------|
| **vulture** | Unused Python code | `vulture backend_gateway/` | Functions, classes, imports |
| **pytest-vulture** | Pytest integration | `pytest --vulture` | Testing integration |

---

## 🚀 Quick Start Commands

### Frontend Cleanup (React Native/Expo)
```bash
cd ios-app

# All cleanup tools at once
npm run cleanup:all

# Individual tools
npm run cleanup:deps      # Unused dependencies
npm run cleanup:orphans   # Orphaned files  
npm run cleanup:exports   # Unused TypeScript exports
npm run cleanup:unused    # Unused files & dependencies
npm run cleanup:styles    # Unused React Native styles
```

### Backend Cleanup (FastAPI/Python)
```bash
# From project root (ensure venv is activated)
source venv/bin/activate

# Basic unused code scan
vulture backend_gateway/

# Specific services (for lightbulb development)
vulture backend_gateway/services/crewai_service.py
vulture backend_gateway/routers/chat_router.py

# With confidence threshold
vulture backend_gateway/ --min-confidence 80

# Pytest integration
pytest --vulture
```

---

## 🎯 Lightbulb-Recommender Agent Workflow

### Before Implementation
```bash
# 1. Analyze current codebase state
cd ios-app
npm run cleanup:all > ../cleanup-report-before.txt

# 2. Check backend services
cd ..
vulture backend_gateway/services/crewai_service.py --min-confidence 60
vulture backend_gateway/routers/chat_router.py --min-confidence 60
```

### During Development
```bash
# After adding new suggestion types or components
npm run cleanup:exports    # Check for unused enum exports
npm run cleanup:styles     # Verify StyleSheet usage

# After CrewAI service modifications
vulture backend_gateway/services/ --min-confidence 70
```

### After Implementation
```bash
# Final cleanup before commit
cd ios-app
npm run cleanup:all

cd ..
vulture backend_gateway/ --min-confidence 80

# Run full health checks
npm run lint
npm run test:ci
./quick_check.sh
```

---

## 🔧 Detailed Tool Usage

### Depcheck - Dependency Analysis
```bash
# Basic scan
npx depcheck

# Expo-specific ignore patterns
npx depcheck --ignores="expo-*,@expo/*,@react-native-*"

# JSON output for automation
npx depcheck --json > depcheck-report.json
```

**Common Expo False Positives to Ignore:**
- `expo-*` packages (loaded dynamically)
- `@expo/*` packages (Metro bundler handling)
- `react-native-*` native modules
- Platform-specific dependencies

### Madge - Dependency Graphs
```bash
# Find orphaned files
npx madge --orphans .

# Generate visual dependency graph
npx madge --image dependency-graph.png .

# Find circular dependencies
npx madge --circular .

# Specific directory analysis
npx madge --orphans components/ screens/
```

### TS-Prune - TypeScript Exports
```bash
# Basic scan
npx ts-prune

# Exclude test files
npx ts-prune --ignore "*.test.ts|*.spec.ts"

# Filter by specific patterns
npx ts-prune | grep -E "(AddButton|chat-modal|recipe)"
```

### React Native Unused Styles
```bash
# Scan specific directories
npx react-native-unused-styles components/
npx react-native-unused-styles screens/

# Generate report
npx react-native-unused-styles . --reporter json > unused-styles.json

# Delete unused styles (use with extreme caution)
# npx react-native-unused-styles . --delete
```

### Vulture - Python Dead Code
```bash
# Basic service scan
vulture backend_gateway/services/

# Specific files for lightbulb development
vulture backend_gateway/services/crewai_service.py
vulture backend_gateway/routers/chat_router.py

# With confidence levels (0-100)
vulture backend_gateway/ --min-confidence 90  # Very confident
vulture backend_gateway/ --min-confidence 60  # More permissive

# Generate whitelist for false positives
vulture backend_gateway/ --make-whitelist > vulture_whitelist.py

# Exclude patterns
vulture backend_gateway/ --exclude "*/test_*,*/tests/*"
```

---

## 🎨 ESLint Integration

### Configuration
The project includes React Native ESLint rules in `.eslintrc.js`:

```javascript
{
  "plugins": ["react-native"],
  "rules": {
    "react-native/no-unused-styles": "warn"
  }
}
```

### Usage
```bash
cd ios-app
npm run lint              # Check all files
npm run lint:fix          # Auto-fix issues
npm run lint -- --quiet  # Show only errors
```

---

## 🔍 Lightbulb System Specific Monitoring

### Key Files to Watch
```bash
# Monitor specific files during lightbulb development
npx ts-prune | grep -E "(AddButton|chat-modal|crewai_service|chat_router)"

# Check chat-related components for unused styles
npx react-native-unused-styles components/ screens/ | grep -i chat

# Backend service analysis
vulture backend_gateway/services/crewai_service.py --min-confidence 60
vulture backend_gateway/routers/chat_router.py --min-confidence 60
```

### Development Phase Checks
1. **After adding suggestion types:**
   ```bash
   npm run cleanup:exports | grep -E "(suggestion|lightbulb|fab)"
   ```

2. **After CrewAI service enhancement:**
   ```bash
   vulture backend_gateway/services/ --min-confidence 70
   ```

3. **After chat modal improvements:**
   ```bash
   npm run cleanup:styles | grep -E "(modal|chat|overlay)"
   ```

---

## 📊 Automation & CI/CD Integration

### Package.json Scripts
All tools are integrated as npm scripts:
```json
{
  "scripts": {
    "cleanup:deps": "depcheck",
    "cleanup:orphans": "madge --orphans .",
    "cleanup:exports": "ts-prune", 
    "cleanup:unused": "unimported",
    "cleanup:styles": "react-native-unused-styles .",
    "cleanup:all": "npm run cleanup:deps && npm run cleanup:orphans && npm run cleanup:exports && npm run cleanup:unused && npm run cleanup:styles"
  }
}
```

### Pre-commit Hooks
```bash
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: cleanup-frontend
      name: Frontend Cleanup Check
      entry: bash -c 'cd ios-app && npm run cleanup:all'
      language: system
      pass_filenames: false
    
    - id: cleanup-backend  
      name: Backend Cleanup Check
      entry: bash -c 'vulture backend_gateway/ --min-confidence 80'
      language: system
      pass_filenames: false
```

### GitHub Actions Integration
```yaml
- name: Code Quality Checks
  run: |
    cd ios-app
    npm run cleanup:all
    npm run lint
    cd ..
    vulture backend_gateway/ --min-confidence 80
    ./quick_check.sh
```

---

## 🚨 Important Considerations

### Expo-Specific Gotchas
- **Metro bundler** uses dynamic requires that may appear as unused
- **Expo plugins** are loaded at runtime and may trigger false positives
- **Platform-specific imports** (iOS/Android) may appear unused on single platform
- **Native modules** required for compilation but not directly imported

### False Positive Management
```bash
# Create depcheck configuration
echo '{
  "ignores": [
    "expo-*",
    "@expo/*", 
    "react-native-*",
    "@react-native-*",
    "@types/*"
  ]
}' > .depcheckrc

# Create vulture whitelist
vulture backend_gateway/ --make-whitelist > vulture_whitelist.py
```

### Safety Guidelines
1. **Always test after cleanup** - run full test suite
2. **Check runtime behavior** - test in iOS simulator  
3. **Review git diff carefully** - ensure no critical code removed
4. **Start with high confidence** - use `--min-confidence 90` first
5. **Get user confirmation** - for removing significant code sections

---

## 📈 Monitoring & Reporting

### Generate Cleanup Reports
```bash
# Frontend comprehensive report
cd ios-app
{
  echo "=== DEPENDENCY CHECK ==="
  npm run cleanup:deps
  echo -e "\n=== ORPHANED FILES ==="
  npm run cleanup:orphans  
  echo -e "\n=== UNUSED EXPORTS ==="
  npm run cleanup:exports
  echo -e "\n=== UNUSED STYLES ==="
  npm run cleanup:styles
} > ../cleanup-report-frontend-$(date +%Y%m%d).txt

# Backend report
vulture backend_gateway/ --min-confidence 60 > cleanup-report-backend-$(date +%Y%m%d).txt
```

### Regular Maintenance Schedule
- **Before major features:** Full cleanup scan
- **Weekly:** `cleanup:all` + `vulture` scan
- **Before releases:** Manual verification of flagged items
- **After refactoring:** Verify no orphaned code remains

---

## 🤝 Integration with Health Checks

### Quick Check Integration
Add to `quick_check.sh`:
```bash
echo "🧹 Running code cleanup checks..."
cd ios-app
npm run cleanup:deps --silent > /dev/null || echo "⚠️ Unused dependencies detected"
cd ..
vulture backend_gateway/ --min-confidence 90 --quiet > /dev/null || echo "⚠️ Unused code detected"
```

### Health Check Integration  
Add to `check_app_health.py`:
```python
def check_code_quality():
    """Run code cleanup tools and report results"""
    try:
        # Frontend cleanup
        subprocess.run(["npm", "run", "cleanup:all"], 
                      cwd="ios-app", check=True, capture_output=True)
        
        # Backend cleanup  
        result = subprocess.run(["vulture", "backend_gateway/", "--min-confidence", "80"],
                               capture_output=True, text=True)
        
        return {"status": "success", "warnings": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "issues_found", "details": e.stdout}
```

---

## 📝 Documentation Maintenance

### When to Update This Document
- New cleanup tools added
- Configuration changes made
- New ignore patterns discovered
- Integration patterns updated
- False positive solutions found

### Change Log
- **2025-08-06**: Initial documentation created
- **2025-08-06**: Added lightbulb-recommender agent integration
- **2025-08-06**: Configured ESLint React Native plugin

---

## 🎯 Summary for Claude Instances

**Essential Commands:**
```bash
# Before starting work
cd ios-app && npm run cleanup:all
cd .. && vulture backend_gateway/ --min-confidence 80

# During development
npm run cleanup:exports  # After adding components
npm run cleanup:styles   # After style changes

# Before committing  
npm run cleanup:all && vulture backend_gateway/
npm run lint && npm run test:ci
```

**Key Principles:**
1. **Run cleanup tools before AND after changes**
2. **Use high confidence levels initially (80-90%)**
3. **Test thoroughly after any cleanup**
4. **Document new ignore patterns**
5. **Integrate with existing health checks**

This toolset ensures the PrepSense codebase remains lean and maintainable while implementing complex features like the lightbulb recommendation system.

---

**Last Updated:** 2025-08-06  
**Maintainer:** Lightbulb-Recommender Agent & All Claude Instances