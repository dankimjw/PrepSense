#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Git Worktrees for PrepSense ===${NC}"
echo ""

# Get the main repository path
MAIN_REPO=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$MAIN_REPO" ]; then
    echo -e "${YELLOW}Error: Not in a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}Main Repository:${NC}"
echo "  $MAIN_REPO"
echo ""

# List all worktrees
echo -e "${GREEN}Worktrees:${NC}"
CURRENT_DIR=$(pwd)

# Use git worktree list and process output
git worktree list | while IFS= read -r line; do
    # Extract path (first word in the line)
    WORKTREE_PATH=$(echo "$line" | cut -d' ' -f1)
    
    # Check if this is the current directory
    if [ "$WORKTREE_PATH" = "$CURRENT_DIR" ]; then
        echo -e "  ${YELLOW}→ $line${NC} ${YELLOW}(current)${NC}"
    else
        echo "  $line"
    fi
done

echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "  cd ../PrepSense-worktrees/feature     # Go to feature worktree"
echo "  cd ../PrepSense-worktrees/bugfix      # Go to bugfix worktree"
echo "  cd ../PrepSense-worktrees/testzone    # Go to testzone worktree"
echo ""
echo -e "${BLUE}To start Claude in a worktree:${NC}"
echo "  cd <worktree-path> && claude"