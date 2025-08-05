#!/bin/bash
# Script to set up Claude configuration for worktrees using symlinks

echo "Setting up Claude configuration for worktree..."

# Get the main repository path (assuming this script is in the main repo)
MAIN_REPO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if .claude already exists
if [ -e ".claude" ]; then
    if [ -L ".claude" ]; then
        echo "✓ .claude symlink already exists"
    else
        echo "❌ Error: .claude exists but is not a symlink. Please remove it first."
        exit 1
    fi
else
    # Create symlink to main repo's .claude directory
    if [ -d "$MAIN_REPO_PATH/.claude" ]; then
        echo "Creating symlink to .claude directory..."
        ln -s "$MAIN_REPO_PATH/.claude" .claude
        echo "✓ .claude symlink created"
    else
        echo "❌ Error: .claude directory not found in main repository at $MAIN_REPO_PATH"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment and install uv
echo "Installing uv in virtual environment..."
source venv/bin/activate
pip install uv
echo "✓ uv installed"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✓ Python dependencies installed"
fi

# Install Node dependencies for ios-app
if [ -d "ios-app" ] && [ -f "ios-app/package.json" ]; then
    echo "Installing Node dependencies for ios-app..."
    cd ios-app
    npm install
    cd ..
    echo "✓ Node dependencies installed"
fi

echo ""
echo "✅ Worktree Claude setup complete!"
echo ""
echo "To use Claude in this worktree:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run Claude Code as normal"
echo ""
echo "All worktrees share the same .claude configuration via symlink."