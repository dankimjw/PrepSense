#!/bin/bash

# Setup collaborative notes system for Claude instances across worktrees

echo "Setting up Claude instance collaboration system..."

# Define paths
MAIN_REPO="/Users/danielkim/_Capstone/PrepSense"
WORKTREES=(
    "/Users/danielkim/_Capstone/PrepSense-worktrees/bugfix"
    "/Users/danielkim/_Capstone/PrepSense-worktrees/testzone"
)

# Ensure notes files exist in main repo
touch "$MAIN_REPO/WORKTREE_NOTES_MAIN.md"
touch "$MAIN_REPO/WORKTREE_NOTES_BUGFIX.md"
touch "$MAIN_REPO/WORKTREE_NOTES_TESTZONE.md"
touch "$MAIN_REPO/CLAUDE_COLLABORATION_GUIDE.md"

# Create symlinks in each worktree
for worktree in "${WORKTREES[@]}"; do
    if [ -d "$worktree" ]; then
        echo "Setting up collaboration in $worktree..."
        
        # Create symlinks to all notes files
        ln -sf "$MAIN_REPO/WORKTREE_NOTES_MAIN.md" "$worktree/"
        ln -sf "$MAIN_REPO/WORKTREE_NOTES_BUGFIX.md" "$worktree/"
        ln -sf "$MAIN_REPO/WORKTREE_NOTES_TESTZONE.md" "$worktree/"
        ln -sf "$MAIN_REPO/CLAUDE_COLLABORATION_GUIDE.md" "$worktree/"
        
        echo "✓ Symlinks created in $worktree"
    else
        echo "⚠️  Worktree not found: $worktree"
    fi
done

# Add to .gitignore if not already present
if ! grep -q "WORKTREE_NOTES_" "$MAIN_REPO/.gitignore"; then
    echo "" >> "$MAIN_REPO/.gitignore"
    echo "# Claude collaboration notes" >> "$MAIN_REPO/.gitignore"
    echo "WORKTREE_NOTES_*.md" >> "$MAIN_REPO/.gitignore"
    echo "CLAUDE_COLLABORATION_GUIDE.md" >> "$MAIN_REPO/.gitignore"
    echo "✓ Added collaboration files to .gitignore"
fi

# Create a quick status script
cat > "$MAIN_REPO/check_collaboration_status.sh" << 'EOF'
#!/bin/bash
echo "=== Claude Collaboration Status ==="
echo ""
echo "📝 Notes Files Status:"
for file in WORKTREE_NOTES_*.md; do
    if [ -f "$file" ]; then
        last_modified=$(date -r "$file" "+%Y-%m-%d %H:%M")
        lines=$(wc -l < "$file")
        echo "✓ $file - Last modified: $last_modified, Lines: $lines"
    fi
done
echo ""
echo "🔍 Recent Updates (last 20 lines from each):"
for file in WORKTREE_NOTES_*.md; do
    if [ -f "$file" ]; then
        echo ""
        echo "=== $file ==="
        tail -n 20 "$file" | grep -E "^(##|###|\*\*|❓|⚠️|✅|🔄)" || echo "No recent headers found"
    fi
done
EOF

chmod +x "$MAIN_REPO/check_collaboration_status.sh"

echo ""
echo "✅ Collaboration system setup complete!"
echo ""
echo "📋 Instructions for each Claude instance:"
echo ""
echo "1. MAIN instance (current directory):"
echo "   - Write to: WORKTREE_NOTES_MAIN.md"
echo "   - Read: WORKTREE_NOTES_BUGFIX.md, WORKTREE_NOTES_TESTZONE.md"
echo ""
echo "2. BUGFIX instance (../PrepSense-worktrees/bugfix):"
echo "   - Write to: WORKTREE_NOTES_BUGFIX.md"
echo "   - Read: WORKTREE_NOTES_MAIN.md, WORKTREE_NOTES_TESTZONE.md"
echo ""
echo "3. TESTZONE instance (../PrepSense-worktrees/testzone):"
echo "   - Write to: WORKTREE_NOTES_TESTZONE.md"
echo "   - Read: WORKTREE_NOTES_MAIN.md, WORKTREE_NOTES_BUGFIX.md"
echo ""
echo "📊 To check collaboration status:"
echo "   ./check_collaboration_status.sh"
echo ""
echo "📚 Read the guide:"
echo "   cat CLAUDE_COLLABORATION_GUIDE.md"