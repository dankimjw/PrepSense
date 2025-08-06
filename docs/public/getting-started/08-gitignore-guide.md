# 🚫 Understanding .gitignore

[← Previous: Helpful Resources](./07-resources.md) | [Back to Main Guide](../README.md)

## 🎯 What is .gitignore?

The `.gitignore` file tells Git which files and folders to ignore. This is crucial for:
- Keeping sensitive information out of the repository
- Avoiding large or unnecessary files
- Preventing conflicts from personal settings

**Important:** The `.gitignore` file itself SHOULD be committed to the repository so all team members ignore the same files!

## 📋 What Should Be in .gitignore?

### 🔐 Security - ALWAYS Ignore These:
```gitignore
# API keys and credentials
.env
.env.*
*.key
*credentials*
*secret*
service-account-key.json

# Configuration with sensitive data
config/
local.settings.json
```

### 💻 Development Files:
```gitignore
# IDE/Editor settings (personal preferences)
.vscode/
.idea/
*.swp
.cursor/

# OS-specific files
.DS_Store        # macOS
Thumbs.db        # Windows
Desktop.ini      # Windows

# Personal notes
my_notes/
TODO.txt
CLAUDE.md        # AI assistant instructions
```

### 🐍 Python-Specific:
```gitignore
# Virtual environment
venv/
env/
.venv/

# Python cache
__pycache__/
*.py[cod]
*.pyc

# Distribution/build files
build/
dist/
*.egg-info/
```

### 📱 Node.js/React Native:
```gitignore
# Dependencies (reinstalled via npm install)
node_modules/

# Expo
.expo/
expo-env.d.ts

# Build files
*.apk
*.ipa
build/
dist/

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
```

### 📊 Data & Large Files:
```gitignore
# Large data files
*.csv
*.xlsx
data/

# Database files
*.db
*.sqlite

# Backups
*.backup
*.bak
```

## ✅ PrepSense .gitignore Best Practices

### Must Include:
1. **Environment files** (.env) - Contains API keys
2. **Service account keys** - Google Cloud credentials
3. **Virtual environment** (venv/) - Can be recreated
4. **Node modules** (node_modules/) - Can be reinstalled
5. **Cache files** (__pycache__, .expo)

### Project-Specific Additions:
```gitignore
# PrepSense specific
CLAUDE.md              # AI configuration
config/               # Contains credentials
test_assets/          # Test images/data
*.json               # Credential files
!package.json        # Exception: needed for npm
!tsconfig.json       # Exception: TypeScript config
```

## 🔍 How to Use .gitignore

### Check What's Being Ignored:
```bash
# See which files are ignored
git status --ignored

# Check if a specific file is ignored
git check-ignore -v filename.txt
```

### Adding New Patterns:
```bash
# Edit .gitignore
nano .gitignore

# Add your pattern, save, then:
git add .gitignore
git commit -m "chore: update .gitignore"
```

### If You Accidentally Committed a File:
```bash
# Remove from Git but keep locally
git rm --cached filename.txt

# Add to .gitignore
echo "filename.txt" >> .gitignore

# Commit the changes
git add .gitignore
git commit -m "chore: remove and ignore filename.txt"
```

## ⚠️ Common Mistakes

### 1. Committing Before Adding to .gitignore
**Problem:** Sensitive file already in Git history
**Solution:** 
- Remove with `git rm --cached`
- Consider rewriting history if sensitive
- Alert team if credentials were exposed

### 2. Ignoring Too Much
**Problem:** Needed files not in repository
**Solution:** Use exceptions:
```gitignore
# Ignore all JSON files
*.json
# Except these important ones
!package.json
!tsconfig.json
```

### 3. Personal vs Team Ignores
**Problem:** Your personal preferences affecting team
**Solution:** 
- Team ignores → `.gitignore`
- Personal ignores → `.git/info/exclude` (local only)

## 📝 .gitignore Syntax

### Basic Patterns:
```gitignore
# Comments start with #

file.txt         # Ignore specific file
*.log           # Ignore all .log files
folder/         # Ignore entire folder
!important.log  # Exception: don't ignore this

# Paths
/root-file.txt  # Only root directory
**/any-folder/  # Any folder named "any-folder"
```

### Advanced Patterns:
```gitignore
# Multiple extensions
*.{log,tmp,cache}

# Nested patterns
logs/**/*.log

# Character ranges
file[0-9].txt   # file0.txt, file1.txt, etc.
```

## 🆘 Quick Reference

### Essential .gitignore for PrepSense:
```gitignore
# Security
.env
*.key
*credentials*
service-account-key.json

# Python
venv/
__pycache__/
*.pyc

# Node.js
node_modules/
.expo/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Project specific
CLAUDE.md
config/
```

## 💡 Pro Tips

1. **Start with a template**: GitHub provides .gitignore templates for different languages
2. **Review regularly**: Update .gitignore as project evolves
3. **Commit early**: Add .gitignore before adding files
4. **Use global gitignore**: For personal preferences across all projects:
   ```bash
   git config --global core.excludesfile ~/.gitignore_global
   ```

## 🔗 Helpful Resources

- [GitHub's .gitignore templates](https://github.com/github/gitignore)
- [gitignore.io](https://www.toptal.com/developers/gitignore) - Generate .gitignore files
- [Git documentation on .gitignore](https://git-scm.com/docs/gitignore)

---

[← Previous: Helpful Resources](./07-resources.md) | [Back to Main Guide](../README.md)