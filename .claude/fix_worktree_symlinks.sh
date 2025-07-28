#!/bin/bash
# Fix symlinks in worktrees after moving files to .claude

MAIN_DIR="/Users/danielkim/_Capstone/PrepSense"
CLAUDE_DIR="$MAIN_DIR/.claude"

# Remove old broken symlinks and create new ones
for worktree in ../PrepSense-worktrees/*; do
    if [ -d "$worktree" ]; then
        echo "Fixing symlinks in $worktree..."
        
        # Remove old symlinks
        rm -f "$worktree"/WORKTREE_NOTES_*.md
        rm -f "$worktree"/CLAUDE_*.md
        rm -f "$worktree"/START_HERE_CLAUDE.md
        rm -f "$worktree"/SUBAGENT_*.md
        rm -f "$worktree"/VERIFICATION_*.md
        rm -f "$worktree"/COMPREHENSIVE_*.md
        rm -f "$worktree"/check_collaboration_status.sh
        rm -f "$worktree"/setup_*.sh
        
        # Create new symlinks to .claude directory
        ln -s "$CLAUDE_DIR/WORKTREE_NOTES_MAIN.md" "$worktree/"
        ln -s "$CLAUDE_DIR/WORKTREE_NOTES_BUGFIX.md" "$worktree/"
        ln -s "$CLAUDE_DIR/WORKTREE_NOTES_TESTZONE.md" "$worktree/"
        ln -s "$CLAUDE_DIR/CLAUDE_COLLABORATION_GUIDE.md" "$worktree/"
        ln -s "$CLAUDE_DIR/CLAUDE_INSTANCE_ROLES.md" "$worktree/"
        ln -s "$CLAUDE_DIR/START_HERE_CLAUDE.md" "$worktree/"
        ln -s "$CLAUDE_DIR/check_collaboration_status.sh" "$worktree/"
        
        echo "✓ Fixed symlinks in $(basename $worktree)"
    fi
done

echo "All symlinks updated!"