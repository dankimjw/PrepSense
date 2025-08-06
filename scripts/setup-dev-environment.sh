#!/usr/bin/env bash
# PrepSense Developer Environment Setup Script
# Automatically sets up development tools, hooks, and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.9"
NODE_VERSION="20"
PROJECT_NAME="PrepSense"

echo -e "${BLUE}🚀 ${PROJECT_NAME} Developer Environment Setup${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if running from project root
if [ ! -f "pyproject.toml" ] || [ ! -d "backend_gateway" ] || [ ! -d "ios-app" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package managers
setup_package_managers() {
    echo -e "${YELLOW}📦 Setting up package managers...${NC}"
    
    # Check for Homebrew on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command_exists brew; then
            echo -e "${YELLOW}🍺 Installing Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        else
            echo -e "${GREEN}✅ Homebrew is already installed${NC}"
        fi
    fi
    
    # Update package managers
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew update
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
    fi
}

# Function to setup Python environment
setup_python() {
    echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
    
    # Check Python version
    if command_exists python3; then
        CURRENT_PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        echo -e "${BLUE}Current Python version: ${CURRENT_PYTHON_VERSION}${NC}"
        
        if [ "$CURRENT_PYTHON_VERSION" != "$PYTHON_VERSION" ]; then
            echo -e "${YELLOW}⚠️ Python ${PYTHON_VERSION} recommended. Current: ${CURRENT_PYTHON_VERSION}${NC}"
        fi
    else
        echo -e "${RED}❌ Python 3 not found. Please install Python ${PYTHON_VERSION}+${NC}"
        exit 1
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}🔧 Creating Python virtual environment...${NC}"
        python3 -m venv venv
    else
        echo -e "${GREEN}✅ Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    echo -e "${YELLOW}📦 Upgrading pip...${NC}"
    pip install --upgrade pip
    
    # Install dependencies
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    
    # Install development tools
    echo -e "${YELLOW}🔧 Installing Python development tools...${NC}"
    pip install pre-commit black ruff mypy isort flake8 bandit safety pip-audit pytest pytest-cov
    
    echo -e "${GREEN}✅ Python environment setup complete${NC}"
}

# Function to setup Node.js environment
setup_nodejs() {
    echo -e "${YELLOW}📱 Setting up Node.js environment...${NC}"
    
    # Check Node.js version
    if command_exists node; then
        CURRENT_NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        echo -e "${BLUE}Current Node.js version: ${CURRENT_NODE_VERSION}${NC}"
        
        if [ "$CURRENT_NODE_VERSION" -lt "$NODE_VERSION" ]; then
            echo -e "${YELLOW}⚠️ Node.js ${NODE_VERSION}+ recommended. Current: ${CURRENT_NODE_VERSION}${NC}"
        fi
    else
        echo -e "${RED}❌ Node.js not found. Installing...${NC}"
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install node
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
    fi
    
    # Install React Native dependencies
    echo -e "${YELLOW}📱 Setting up React Native environment...${NC}"
    cd ios-app
    
    # Install npm dependencies
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm ci
    
    # Install development tools globally
    echo -e "${YELLOW}🔧 Installing global development tools...${NC}"
    npm install -g @expo/cli @react-native-community/cli
    
    cd ..
    
    echo -e "${GREEN}✅ Node.js environment setup complete${NC}"
}

# Function to setup development tools
setup_dev_tools() {
    echo -e "${YELLOW}🛠️ Setting up development tools...${NC}"
    
    # Install additional tools based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS specific tools
        if ! command_exists watchman; then
            echo -e "${YELLOW}👀 Installing Watchman...${NC}"
            brew install watchman
        fi
        
        if ! command_exists cocoapods; then
            echo -e "${YELLOW}🥥 Installing CocoaPods...${NC}"
            sudo gem install cocoapods
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux specific tools
        sudo apt-get install -y git curl wget build-essential
    fi
    
    # Install Spectral for API linting
    if ! command_exists spectral; then
        echo -e "${YELLOW}🔍 Installing Spectral CLI...${NC}"
        npm install -g @stoplight/spectral-cli
    fi
    
    echo -e "${GREEN}✅ Development tools setup complete${NC}"
}

# Function to setup Git hooks
setup_git_hooks() {
    echo -e "${YELLOW}🪝 Setting up Git hooks...${NC}"
    
    # Install pre-commit
    if ! command_exists pre-commit; then
        echo -e "${YELLOW}📋 Installing pre-commit...${NC}"
        pip install pre-commit
    fi
    
    # Install pre-commit hooks
    echo -e "${YELLOW}🔧 Installing pre-commit hooks...${NC}"
    pre-commit install --install-hooks
    pre-commit install --hook-type pre-push
    pre-commit install --hook-type commit-msg
    pre-commit install --hook-type prepare-commit-msg
    
    # Set up custom Git hooks
    echo -e "${YELLOW}⚙️ Setting up custom Git hooks...${NC}"
    
    # Configure Git hooks directory
    git config core.hooksPath .githooks
    
    # Make hook files executable
    chmod +x .githooks/*
    
    echo -e "${GREEN}✅ Git hooks setup complete${NC}"
}

# Function to setup IDE configuration
setup_ide_config() {
    echo -e "${YELLOW}💻 Setting up IDE configuration...${NC}"
    
    # Create .vscode directory if it doesn't exist
    mkdir -p .vscode
    
    # VS Code settings
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
  "prettier.configPath": "ios-app/.prettierrc",
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.git": false,
    "**/venv": true,
    "**/.env": false
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/venv": true,
    "**/.git": true
  }
}
EOF

    # VS Code extensions recommendations
    cat > .vscode/extensions.json << 'EOF'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-python.isort",
    "charliermarsh.ruff",
    "ms-vscode.vscode-typescript-next",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "expo.vscode-expo-tools",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-python.pytest",
    "ms-python.debugpy",
    "github.copilot",
    "github.copilot-chat",
    "eamodio.gitlens",
    "ms-vscode.remote-containers"
  ]
}
EOF

    # VS Code launch configuration for debugging
    cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/venv/bin/uvicorn",
      "args": ["backend_gateway.app:app", "--reload", "--port", "8001"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": false
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${workspaceFolder}/backend_gateway/tests", "-v"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
EOF

    echo -e "${GREEN}✅ IDE configuration setup complete${NC}"
}

# Function to validate environment
validate_environment() {
    echo -e "${YELLOW}✅ Validating environment setup...${NC}"
    
    local errors=0
    
    # Check Python environment
    echo -e "${BLUE}🐍 Checking Python environment...${NC}"
    if source venv/bin/activate && python -c "import fastapi, pytest, black, ruff" 2>/dev/null; then
        echo -e "${GREEN}✅ Python environment is working${NC}"
    else
        echo -e "${RED}❌ Python environment has issues${NC}"
        errors=$((errors + 1))
    fi
    
    # Check Node.js environment
    echo -e "${BLUE}📱 Checking Node.js environment...${NC}"
    if cd ios-app && npm run typecheck 2>/dev/null; then
        echo -e "${GREEN}✅ React Native environment is working${NC}"
        cd ..
    else
        echo -e "${RED}❌ React Native environment has issues${NC}"
        cd ..
        errors=$((errors + 1))
    fi
    
    # Check pre-commit
    echo -e "${BLUE}🪝 Checking pre-commit hooks...${NC}"
    if pre-commit --version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Pre-commit hooks are installed${NC}"
    else
        echo -e "${RED}❌ Pre-commit hooks are not working${NC}"
        errors=$((errors + 1))
    fi
    
    # Check Git configuration
    echo -e "${BLUE}📝 Checking Git configuration...${NC}"
    if [ -d ".git" ] && git config --get user.name >/dev/null && git config --get user.email >/dev/null; then
        echo -e "${GREEN}✅ Git is configured${NC}"
    else
        echo -e "${YELLOW}⚠️ Git user configuration needed${NC}"
        read -p "Enter your Git username: " git_username
        read -p "Enter your Git email: " git_email
        git config --global user.name "$git_username"
        git config --global user.email "$git_email"
        echo -e "${GREEN}✅ Git configuration updated${NC}"
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}🎉 Environment validation passed!${NC}"
    else
        echo -e "${RED}❌ Environment validation failed with $errors errors${NC}"
        return 1
    fi
}

# Function to create helpful scripts
create_helper_scripts() {
    echo -e "${YELLOW}📝 Creating helper scripts...${NC}"
    
    # Create start development script
    cat > scripts/start-dev.sh << 'EOF'
#!/usr/bin/env bash
# Start development environment

echo "🚀 Starting PrepSense development environment..."

# Activate Python virtual environment
source venv/bin/activate

# Start backend in background
echo "🐍 Starting FastAPI backend..."
cd backend_gateway
python -m uvicorn app:app --reload --port 8001 &
BACKEND_PID=$!
cd ..

# Start React Native
echo "📱 Starting React Native..."
cd ios-app
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Development environment started!"
echo "📝 Backend: http://localhost:8001"
echo "📝 Frontend: Check Expo CLI output"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
EOF

    # Create test script
    cat > scripts/run-all-tests.sh << 'EOF'
#!/usr/bin/env bash
# Run all tests for the project

set -e

echo "🧪 Running all PrepSense tests..."

# Activate Python environment
source venv/bin/activate

# Backend tests
echo "🐍 Running backend tests..."
cd backend_gateway
python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term
cd ..

# Frontend tests
echo "📱 Running frontend tests..."
cd ios-app
npm run test:ci
cd ..

echo "✅ All tests completed!"
EOF

    # Create quality check script
    cat > scripts/quality-check.sh << 'EOF'
#!/usr/bin/env bash
# Run quality checks for the project

set -e

echo "📊 Running PrepSense quality checks..."

# Activate Python environment
source venv/bin/activate

# Pre-commit checks
echo "🪝 Running pre-commit checks..."
pre-commit run --all-files

# Backend quality
echo "🐍 Backend quality checks..."
cd backend_gateway
black --check .
ruff check .
mypy .
cd ..

# Frontend quality
echo "📱 Frontend quality checks..."
cd ios-app
npm run lint:strict
npm run typecheck
cd ..

echo "✅ Quality checks completed!"
EOF

    # Make scripts executable
    chmod +x scripts/*.sh
    
    echo -e "${GREEN}✅ Helper scripts created${NC}"
}

# Function to display setup summary
display_summary() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🎉 PrepSense Development Environment Setup Complete!"
    echo "=================================================="
    echo -e "${NC}"
    
    echo -e "${GREEN}✅ What was set up:${NC}"
    echo "   🐍 Python virtual environment with dependencies"
    echo "   📱 React Native development environment"
    echo "   🪝 Git hooks and pre-commit configuration"
    echo "   💻 IDE configuration (VS Code)"
    echo "   🔧 Development tools and utilities"
    echo "   📝 Helper scripts"
    
    echo ""
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo "   1. Copy .env.example to .env and configure your environment variables"
    echo "   2. Run 'scripts/start-dev.sh' to start the development environment"
    echo "   3. Run 'scripts/quality-check.sh' to validate your setup"
    echo "   4. Open the project in VS Code for optimal development experience"
    
    echo ""
    echo -e "${BLUE}💡 Useful commands:${NC}"
    echo "   🚀 Start dev environment: ./scripts/start-dev.sh"
    echo "   🧪 Run all tests: ./scripts/run-all-tests.sh"
    echo "   📊 Quality checks: ./scripts/quality-check.sh"
    echo "   🪝 Pre-commit check: pre-commit run --all-files"
    echo "   🔧 Health check: python check_app_health.py"
    
    echo ""
    echo -e "${GREEN}🎯 You're ready to start developing!${NC}"
}

# Main setup process
main() {
    echo -e "${YELLOW}Starting development environment setup...${NC}"
    
    # Check for required commands
    local required_commands=("git" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            echo -e "${RED}❌ Required command '$cmd' not found${NC}"
            exit 1
        fi
    done
    
    # Run setup functions
    setup_package_managers
    setup_python
    setup_nodejs
    setup_dev_tools
    setup_git_hooks
    setup_ide_config
    create_helper_scripts
    validate_environment
    display_summary
}

# Run main function
main "$@"