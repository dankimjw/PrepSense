#\!/bin/bash

# Script to create CLAUDE.md symlinks in all worktrees

# Path to the main CLAUDE.md file
MAIN_CLAUDE_MD="/Users/danielkim/_Capstone/PrepSense/CLAUDE.md"

# Array of worktree paths
WORKTREES=(
    "/Users/danielkim/_Capstone/PrepSense-worktrees/feature"
    "/Users/danielkim/_Capstone/PrepSense-worktrees/bugfix"
    "/Users/danielkim/_Capstone/PrepSense-worktrees/testzone"
)

# Create symlinks in each worktree
for worktree in "${WORKTREES[@]}"; do
    if [ -d "$worktree" ]; then
        # Remove existing CLAUDE.md if it exists
        if [ -f "$worktree/CLAUDE.md" ]; then
            echo "Removing existing CLAUDE.md in $worktree"
            rm "$worktree/CLAUDE.md"
        fi
        
        # Create symlink
        echo "Creating symlink in $worktree"
        ln -s "$MAIN_CLAUDE_MD" "$worktree/CLAUDE.md"
        
        # Verify symlink
        if [ -L "$worktree/CLAUDE.md" ]; then
            echo "✓ Symlink created successfully in $worktree"
        else
            echo "✗ Failed to create symlink in $worktree"
        fi
    else
        echo "Worktree not found: $worktree"
    fi
done

echo ""
echo "All worktrees now share the same CLAUDE.md file\!"
echo "Any changes made to CLAUDE.md in any worktree will be reflected everywhere."
