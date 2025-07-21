#!/bin/bash
# Script to check if Claude instance should sync with other instances

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Claude Collaboration Sync Check ===${NC}"

# Check for reminder file
if [ -f ".claude_collaboration_reminder" ]; then
    echo -e "${RED}📢 SYNC REQUIRED: Found collaboration reminder${NC}"
    cat .claude_collaboration_reminder
    rm .claude_collaboration_reminder
    echo ""
fi

# Check for recent commits from other worktrees
CURRENT_BRANCH=$(git branch --show-current)
RECENT_COMMITS=$(git log --all --oneline --since="30 minutes ago" --pretty=format:"%h %s [%an]" | head -10)

if [ -n "$RECENT_COMMITS" ]; then
    echo -e "${YELLOW}Recent commits detected (last 30 minutes):${NC}"
    echo "$RECENT_COMMITS"
    echo ""
    echo -e "${GREEN}ACTION: Run 'cat WORKTREE_NOTES_*.md' to sync knowledge${NC}"
else
    echo -e "${GREEN}✓ No recent commits detected${NC}"
fi

# Check modification times of notes files
echo ""
echo -e "${YELLOW}Notes file status:${NC}"
for notes in WORKTREE_NOTES_*.md; do
    if [ -f "$notes" ]; then
        MOD_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$notes" 2>/dev/null || stat -c "%y" "$notes" 2>/dev/null | cut -d' ' -f1-2)
        echo "  $notes - Last modified: $MOD_TIME"
    fi
done

echo ""
echo -e "${GREEN}Sync command: cat WORKTREE_NOTES_*.md${NC}"