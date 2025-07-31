#!/bin/bash
# Script to fix all .claude directories and replace them with symlinks

MAIN_CLAUDE_DIR="/Users/danielkim/_Capstone/PrepSense/.claude"

echo "Fixing all .claude directories..."
echo "Main .claude directory: $MAIN_CLAUDE_DIR"
echo ""

# Find all .claude directories (excluding the main one)
find /Users/danielkim/_Capstone -name ".claude" -type d 2>/dev/null | grep -v "PrepSense/.claude$" | while read dir; do
    parent_dir=$(dirname "$dir")
    echo "Found .claude directory at: $dir"
    
    # Backup any unique logs
    if [ -d "$dir/hooks/logs" ]; then
        echo "  - Backing up logs..."
        mkdir -p "$MAIN_CLAUDE_DIR/hooks/logs/backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$dir/hooks/logs/"* "$MAIN_CLAUDE_DIR/hooks/logs/backup_$(date +%Y%m%d_%H%M%S)/" 2>/dev/null || true
    fi
    
    # Remove the directory
    echo "  - Removing directory..."
    rm -rf "$dir"
    
    # Create symlink
    echo "  - Creating symlink..."
    cd "$parent_dir"
    ln -s "$MAIN_CLAUDE_DIR" .claude
    echo "  ✓ Fixed: $parent_dir/.claude -> $MAIN_CLAUDE_DIR"
    echo ""
done

echo "✅ All .claude directories have been replaced with symlinks!"
echo ""
echo "Note: Each worktree still needs its own virtual environment with 'uv' installed."