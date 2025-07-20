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
