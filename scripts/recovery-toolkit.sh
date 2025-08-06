#!/usr/bin/env bash
# PrepSense Recovery Toolkit
# Provides automated recovery mechanisms for common development issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR=".recovery-backups"
LOG_FILE="recovery.log"

echo -e "${BLUE}🛠️ PrepSense Recovery Toolkit${NC}"
echo -e "${BLUE}=============================${NC}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Create backup function
create_backup() {
    local backup_name="$1"
    local backup_path="$BACKUP_DIR/$backup_name-$(date +%Y%m%d-%H%M%S)"
    
    mkdir -p "$backup_path"
    
    # Backup important files
    if [ -f ".env" ]; then
        cp ".env" "$backup_path/"
    fi
    
    if [ -f "requirements.txt" ]; then
        cp "requirements.txt" "$backup_path/"
    fi
    
    if [ -d "ios-app" ] && [ -f "ios-app/package.json" ]; then
        mkdir -p "$backup_path/ios-app"
        cp "ios-app/package.json" "$backup_path/ios-app/"
        cp "ios-app/package-lock.json" "$backup_path/ios-app/" 2>/dev/null || true
    fi
    
    log "${GREEN}✅ Backup created: $backup_path${NC}"
    echo "$backup_path"
}

# Recovery function for Python environment issues
recover_python_environment() {
    log "${YELLOW}🐍 Recovering Python environment...${NC}"
    
    # Create backup
    backup_path=$(create_backup "python-env")
    
    # Remove existing virtual environment
    if [ -d "venv" ]; then
        log "${YELLOW}Removing corrupted virtual environment...${NC}"
        rm -rf venv
    fi
    
    # Create new virtual environment
    log "${YELLOW}Creating new virtual environment...${NC}"
    python3 -m venv venv
    
    # Activate environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Reinstall dependencies
    if [ -f "requirements.txt" ]; then
        log "${YELLOW}Reinstalling Python dependencies...${NC}"
        pip install -r requirements.txt
    fi
    
    # Reinstall development tools
    pip install pre-commit black ruff mypy isort flake8 bandit safety pip-audit pytest pytest-cov
    
    # Reinstall pre-commit hooks
    pre-commit install --install-hooks
    
    log "${GREEN}✅ Python environment recovery completed${NC}"
}

# Recovery function for Node.js environment issues
recover_nodejs_environment() {
    log "${YELLOW}📱 Recovering Node.js environment...${NC}"
    
    # Create backup
    backup_path=$(create_backup "nodejs-env")
    
    cd ios-app
    
    # Clear npm cache
    npm cache clean --force
    
    # Remove node_modules and package-lock.json
    if [ -d "node_modules" ]; then
        log "${YELLOW}Removing corrupted node_modules...${NC}"
        rm -rf node_modules
    fi
    
    if [ -f "package-lock.json" ]; then
        log "${YELLOW}Removing package-lock.json...${NC}"
        rm package-lock.json
    fi
    
    # Reinstall dependencies
    log "${YELLOW}Reinstalling Node.js dependencies...${NC}"
    npm install
    
    cd ..
    
    log "${GREEN}✅ Node.js environment recovery completed${NC}"
}

# Recovery function for Git issues
recover_git_state() {
    log "${YELLOW}📝 Recovering Git state...${NC}"
    
    # Create backup
    backup_path=$(create_backup "git-state")
    
    # Check Git status
    if ! git status >/dev/null 2>&1; then
        log "${RED}❌ Not a Git repository${NC}"
        return 1
    fi
    
    # Reset pre-commit hooks
    log "${YELLOW}Resetting pre-commit hooks...${NC}"
    pre-commit uninstall || true
    pre-commit install --install-hooks
    pre-commit install --hook-type pre-push
    pre-commit install --hook-type commit-msg
    pre-commit install --hook-type prepare-commit-msg
    
    # Configure Git hooks directory
    git config core.hooksPath .githooks
    chmod +x .githooks/*
    
    # Clean up Git index if needed
    if git diff --cached --quiet; then
        log "${GREEN}Git index is clean${NC}"
    else
        log "${YELLOW}Cleaning Git index...${NC}"
        git reset HEAD .
    fi
    
    log "${GREEN}✅ Git state recovery completed${NC}"
}

# Recovery function for pre-commit issues
recover_precommit_hooks() {
    log "${YELLOW}🪝 Recovering pre-commit hooks...${NC}"
    
    # Create backup
    backup_path=$(create_backup "precommit-hooks")
    
    # Uninstall existing hooks
    pre-commit uninstall --hook-type pre-commit
    pre-commit uninstall --hook-type pre-push
    pre-commit uninstall --hook-type commit-msg
    pre-commit uninstall --hook-type prepare-commit-msg
    
    # Clean pre-commit cache
    pre-commit clean
    
    # Reinstall hooks
    pre-commit install --install-hooks
    pre-commit install --hook-type pre-push
    pre-commit install --hook-type commit-msg
    pre-commit install --hook-type prepare-commit-msg
    
    # Run a test to ensure hooks work
    log "${YELLOW}Testing pre-commit hooks...${NC}"
    pre-commit run --all-files --show-diff-on-failure || {
        log "${YELLOW}⚠️ Some pre-commit checks failed, but hooks are installed${NC}"
    }
    
    log "${GREEN}✅ Pre-commit hooks recovery completed${NC}"
}

# Recovery function for database issues
recover_database_state() {
    log "${YELLOW}🗄️ Recovering database state...${NC}"
    
    # Create backup
    backup_path=$(create_backup "database-state")
    
    cd backend_gateway
    
    # Check if Alembic is configured
    if [ -f "alembic.ini" ]; then
        log "${YELLOW}Checking Alembic configuration...${NC}"
        
        # Check current migration state
        alembic current || {
            log "${YELLOW}⚠️ Cannot determine current migration state${NC}"
        }
        
        # Try to upgrade to head
        log "${YELLOW}Attempting to upgrade database to head...${NC}"
        alembic upgrade head || {
            log "${YELLOW}⚠️ Database upgrade failed - manual intervention may be needed${NC}"
        }
    else
        log "${YELLOW}⚠️ Alembic not configured${NC}"
    fi
    
    cd ..
    
    log "${GREEN}✅ Database state recovery completed${NC}"
}

# Recovery function for IDE configuration
recover_ide_config() {
    log "${YELLOW}💻 Recovering IDE configuration...${NC}"
    
    # Create backup
    backup_path=$(create_backup "ide-config")
    
    # Recreate VS Code settings
    mkdir -p .vscode
    
    cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "python.sortImports.args": ["--profile=black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["ios-app"],
  "eslint.format.enable": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.git": false,
    "**/venv": true
  }
}
EOF
    
    log "${GREEN}✅ IDE configuration recovery completed${NC}"
}

# Recovery function for build issues
recover_build_state() {
    log "${YELLOW}🏗️ Recovering build state...${NC}"
    
    # Create backup
    backup_path=$(create_backup "build-state")
    
    # Clean Python build artifacts
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Clean Node.js build artifacts
    if [ -d "ios-app" ]; then
        cd ios-app
        
        # Remove build directories
        rm -rf .expo 2>/dev/null || true
        rm -rf dist 2>/dev/null || true
        rm -rf build 2>/dev/null || true
        
        # Clear Metro cache
        npx expo r -c 2>/dev/null || true
        
        cd ..
    fi
    
    log "${GREEN}✅ Build state recovery completed${NC}"
}

# Complete system recovery
full_recovery() {
    log "${YELLOW}🔄 Starting full system recovery...${NC}"
    
    # Create comprehensive backup
    backup_path=$(create_backup "full-system")
    
    # Recover all components
    recover_python_environment
    recover_nodejs_environment
    recover_git_state
    recover_precommit_hooks
    recover_database_state
    recover_ide_config
    recover_build_state
    
    # Final validation
    log "${YELLOW}🔍 Running final validation...${NC}"
    
    # Test Python environment
    if source venv/bin/activate && python -c "import fastapi" 2>/dev/null; then
        log "${GREEN}✅ Python environment validated${NC}"
    else
        log "${RED}❌ Python environment validation failed${NC}"
    fi
    
    # Test Node.js environment
    if cd ios-app && npm run typecheck >/dev/null 2>&1; then
        log "${GREEN}✅ Node.js environment validated${NC}"
        cd ..
    else
        log "${RED}❌ Node.js environment validation failed${NC}"
        cd .. 2>/dev/null || true
    fi
    
    # Test pre-commit
    if pre-commit --version >/dev/null 2>&1; then
        log "${GREEN}✅ Pre-commit validated${NC}"
    else
        log "${RED}❌ Pre-commit validation failed${NC}"
    fi
    
    log "${GREEN}🎉 Full system recovery completed!${NC}"
}

# Health check function
health_check() {
    log "${YELLOW}🏥 Running health check...${NC}"
    
    local issues=0
    
    # Check Python environment
    if [ -d "venv" ] && source venv/bin/activate && python -c "import fastapi" 2>/dev/null; then
        log "${GREEN}✅ Python environment is healthy${NC}"
    else
        log "${RED}❌ Python environment needs attention${NC}"
        issues=$((issues + 1))
    fi
    
    # Check Node.js environment
    if [ -d "ios-app/node_modules" ] && cd ios-app && npm run typecheck >/dev/null 2>&1; then
        log "${GREEN}✅ Node.js environment is healthy${NC}"
        cd ..
    else
        log "${RED}❌ Node.js environment needs attention${NC}"
        cd .. 2>/dev/null || true
        issues=$((issues + 1))
    fi
    
    # Check pre-commit
    if pre-commit --version >/dev/null 2>&1; then
        log "${GREEN}✅ Pre-commit is healthy${NC}"
    else
        log "${RED}❌ Pre-commit needs attention${NC}"
        issues=$((issues + 1))
    fi
    
    # Check Git configuration
    if git config --get user.name >/dev/null && git config --get user.email >/dev/null; then
        log "${GREEN}✅ Git configuration is healthy${NC}"
    else
        log "${YELLOW}⚠️ Git configuration incomplete${NC}"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        log "${GREEN}🎉 All systems healthy!${NC}"
        return 0
    else
        log "${RED}⚠️ Found $issues issues that need attention${NC}"
        return 1
    fi
}

# Interactive recovery menu
interactive_recovery() {
    echo -e "${BLUE}🔧 Interactive Recovery Menu${NC}"
    echo -e "${BLUE}============================${NC}"
    echo
    echo "Select recovery option:"
    echo "1. Health Check"
    echo "2. Recover Python Environment"
    echo "3. Recover Node.js Environment"
    echo "4. Recover Git State"
    echo "5. Recover Pre-commit Hooks"
    echo "6. Recover Database State"
    echo "7. Recover IDE Configuration"
    echo "8. Recover Build State"
    echo "9. Full System Recovery"
    echo "0. Exit"
    echo
    
    read -p "Enter your choice (0-9): " choice
    
    case $choice in
        1) health_check ;;
        2) recover_python_environment ;;
        3) recover_nodejs_environment ;;
        4) recover_git_state ;;
        5) recover_precommit_hooks ;;
        6) recover_database_state ;;
        7) recover_ide_config ;;
        8) recover_build_state ;;
        9) full_recovery ;;
        0) log "${GREEN}👋 Goodbye!${NC}"; exit 0 ;;
        *) log "${RED}Invalid choice. Please try again.${NC}"; interactive_recovery ;;
    esac
}

# Main function
main() {
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    case "${1:-interactive}" in
        "health"|"check")
            health_check
            ;;
        "python")
            recover_python_environment
            ;;
        "nodejs"|"node")
            recover_nodejs_environment
            ;;
        "git")
            recover_git_state
            ;;
        "precommit"|"hooks")
            recover_precommit_hooks
            ;;
        "database"|"db")
            recover_database_state
            ;;
        "ide")
            recover_ide_config
            ;;
        "build")
            recover_build_state
            ;;
        "full")
            full_recovery
            ;;
        "interactive"|"")
            interactive_recovery
            ;;
        *)
            echo "Usage: $0 [health|python|nodejs|git|precommit|database|ide|build|full|interactive]"
            echo
            echo "Options:"
            echo "  health      - Run health check"
            echo "  python      - Recover Python environment"
            echo "  nodejs      - Recover Node.js environment" 
            echo "  git         - Recover Git state"
            echo "  precommit   - Recover pre-commit hooks"
            echo "  database    - Recover database state"
            echo "  ide         - Recover IDE configuration"
            echo "  build       - Recover build state"
            echo "  full        - Full system recovery"
            echo "  interactive - Interactive recovery menu (default)"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"