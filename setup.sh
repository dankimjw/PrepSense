#!/bin/bash

# PrepSense Setup Script for macOS/Linux
# This script automates the setup process for the PrepSense application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print functions
print_header() {
    echo -e "\n${BLUE}${BOLD}============================================================${NC}"
    echo -e "${BLUE}${BOLD}                    $1${NC}"
    echo -e "${BLUE}${BOLD}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup
print_header "PrepSense Automated Setup"

# Check prerequisites
print_header "Checking Prerequisites"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python installed: $PYTHON_VERSION"
    
    # Check Python version is 3.8+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js installed: $NODE_VERSION"
else
    print_error "Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm installed: $NPM_VERSION"
else
    print_error "npm is not installed"
    exit 1
fi

# Check Git
if command_exists git; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git installed: $GIT_VERSION"
else
    print_error "Git is not installed"
    exit 1
fi

# Create directories
print_header "Creating Required Directories"
mkdir -p config logs data
print_success "Created config/, logs/, and data/ directories"

# Setup Python environment
print_header "Setting Up Python Environment"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip >/dev/null 2>&1

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Setup iOS app
print_header "Setting Up iOS App"

# Change to ios-app directory
cd ios-app

# Install npm dependencies
echo "Installing npm dependencies..."
npm install
print_success "npm dependencies installed"

# Check for Expo CLI
if ! command_exists expo; then
    print_warning "Expo CLI not found"
    echo "You can use 'npx expo' to run Expo commands"
else
    print_success "Expo CLI is installed"
fi

# Return to root directory
cd ..

# Setup environment file
print_header "Setting Up Environment Variables"

if [ -f ".env.template" ]; then
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_success "Keeping existing .env file"
        else
            cp .env.template .env
            print_success ".env file created from template"
        fi
    else
        cp .env.template .env
        print_success ".env file created from template"
    fi
    
    # Create placeholder OpenAI key file
    if [ ! -f "config/openai_key.txt" ]; then
        echo "your_openai_api_key_here" > config/openai_key.txt
        print_success "Created config/openai_key.txt placeholder"
    fi
    
    echo -e "\n${YELLOW}Please configure your API keys:${NC}"
    echo "  1. Edit config/openai_key.txt and add your OpenAI API key"
    echo "  2. Ensure your Google Cloud credentials are in config/"
    echo "  3. The .env file is already configured to use these files"
else
    print_error ".env.template not found"
fi

# Print completion message
print_header "Setup Complete! 🎉"

echo -e "${BOLD}Next Steps:${NC}"
echo -e "\n1. Configure your environment variables:"
echo -e "   ${BLUE}Edit .env file with your API keys${NC}"

echo -e "\n2. Add Google Cloud credentials:"
echo -e "   ${BLUE}Place your service account JSON file in the config/ directory${NC}"
echo -e "   ${BLUE}Update GOOGLE_APPLICATION_CREDENTIALS path in .env${NC}"

echo -e "\n3. Start the application:"
echo -e "   ${GREEN}Backend:${NC} python run_app.py"
echo -e "   ${GREEN}iOS App:${NC} python run_ios.py"

echo -e "\n4. Access the services:"
echo -e "   ${BLUE}API Documentation:${NC} http://localhost:8001/docs"
echo -e "   ${BLUE}iOS App:${NC} Scan QR code with Expo Go"

echo -e "\n${BOLD}For more help, see the documentation in docs/${NC}"

# Make the Python setup script executable
chmod +x setup.py run_app.py run_ios.py 2>/dev/null || true