#!/bin/bash

# Setup multiple git worktrees for parallel PrepSense development

echo "Setting up PrepSense worktrees for parallel development..."

# Create worktrees directory
mkdir -p ../PrepSense-worktrees

# Add worktrees for different tasks
echo "Creating worktree for feature development..."
git worktree add ../PrepSense-worktrees/feature -b feature-work

echo "Creating worktree for bug fixes..."
git worktree add ../PrepSense-worktrees/bugfix -b bugfix-work

echo "Creating worktree for testing zone..."
git worktree add ../PrepSense-worktrees/testzone -b testzone-work

# Copy .env to each worktree
echo "Copying environment files..."
cp .env ../PrepSense-worktrees/feature/.env
cp .env ../PrepSense-worktrees/bugfix/.env
cp .env ../PrepSense-worktrees/testzone/.env

echo "Worktrees created successfully!"
echo ""
echo "Next steps for each worktree:"
echo "1. cd ../PrepSense-worktrees/[feature|bugfix|testzone]"
echo "2. python -m venv venv && source venv/bin/activate"
echo "3. pip install -r requirements.txt"
echo "4. cd ios-app && npm install"
echo "5. python setup.py"
echo ""
echo "To see all worktrees: git worktree list"
echo "To remove a worktree: git worktree remove ../PrepSense-worktrees/[name]"