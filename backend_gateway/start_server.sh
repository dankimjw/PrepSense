#!/bin/bash

# PrepSense Backend Server Startup Script
# This script provides various ways to start the server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

print_color $BLUE "🚀 PrepSense Backend Server Startup Script"
print_color $BLUE "==========================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_color $RED "❌ Python is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_color $GREEN "✅ Python version: $PYTHON_VERSION"

# Check if virtual environment should be used
if [ -d "venv" ]; then
    print_color $YELLOW "🔄 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    print_color $YELLOW "🔄 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set default environment variables if not set
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}
export RELOAD=${RELOAD:-"true"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

print_color $GREEN "🔧 Server Configuration:"
print_color $GREEN "   Host: $HOST"
print_color $GREEN "   Port: $PORT"
print_color $GREEN "   Reload: $RELOAD"
print_color $GREEN "   Log Level: $LOG_LEVEL"

# Check for .env file
if [ -f ".env" ]; then
    print_color $GREEN "✅ .env file found"
else
    print_color $YELLOW "⚠️  .env file not found - using environment variables"
fi

# Parse command line arguments
MODE="dev"
if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    MODE="prod"
    export RELOAD="false"
    export LOG_LEVEL="INFO"
    print_color $BLUE "🏭 Production mode enabled"
elif [ "$1" = "dev" ] || [ "$1" = "development" ]; then
    MODE="dev"
    export RELOAD="true"
    export LOG_LEVEL="DEBUG"
    print_color $BLUE "🛠️  Development mode enabled"
elif [ "$1" = "test" ]; then
    print_color $BLUE "🧪 Running tests before server start..."
    python run_all_crew_ai_tests.py
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ All tests passed!"
    else
        print_color $RED "❌ Some tests failed"
        exit 1
    fi
    MODE="dev"
fi

# Health check before starting
print_color $BLUE "🏥 Running pre-startup health check..."
python -c "
import sys
sys.path.insert(0, '.')
from main import check_system_health
health = check_system_health()
print(f'System health: {health[\"status\"]}')
if health['status'] != 'healthy':
    print('⚠️  System health check failed')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_color $GREEN "✅ System health check passed"
else
    print_color $RED "❌ System health check failed"
    exit 1
fi

# Start the server
print_color $BLUE "🚀 Starting PrepSense Backend Server..."
print_color $BLUE "   Mode: $MODE"
print_color $BLUE "   URL: http://localhost:$PORT"
print_color $BLUE "   Docs: http://localhost:$PORT/docs"
print_color $BLUE "==========================================="

# Trap Ctrl+C
trap 'print_color $YELLOW "\n🛑 Shutting down server..."; exit 0' INT

# Start the server based on mode
if [ "$MODE" = "prod" ]; then
    # Production mode with multiple workers
    export WORKERS=${WORKERS:-"4"}
    python main.py
else
    # Development mode with auto-reload
    python main.py
fi