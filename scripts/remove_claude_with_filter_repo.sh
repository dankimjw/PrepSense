#!/bin/bash
# Clean solution using git-filter-repo to remove Claude from history

echo "=== Remove Claude from Git History ==="
echo ""

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "git-filter-repo not found. Install with:"
    echo "  brew install git-filter-repo"
    echo "  OR"
    echo "  pip install git-filter-repo"
    exit 1
fi

# Create backup
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
echo "Creating backup branch: $BACKUP_BRANCH"
git branch $BACKUP_BRANCH

echo ""
echo "Rewriting history to replace Claude with dankimjw..."

# Use git-filter-repo with mailmap
git filter-repo --force --mailmap <(echo "
dankimjw <dankimjw@users.noreply.github.com> Claude <noreply@anthropic.com>
")

echo ""
echo "✅ History rewritten successfully!"
echo ""
echo "Next steps:"
echo "1. Review changes: git log --oneline -20"
echo "2. Force push: git push --force origin $(git branch --show-current)"
echo ""
echo "To restore backup: git reset --hard $BACKUP_BRANCH"