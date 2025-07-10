#!/bin/bash
# Script to remove Claude as a contributor from git history
# WARNING: This rewrites history and requires force pushing

echo "=== Git History Rewrite Script ==="
echo "This will remove Claude as a contributor from all commits"
echo ""

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Create backup tag before rewriting
BACKUP_TAG="backup-before-claude-removal-$(date +%Y%m%d-%H%M%S)"
echo "Creating backup tag: $BACKUP_TAG"
git tag $BACKUP_TAG

echo ""
echo "Starting history rewrite..."
echo "This will change all commits where Claude is the author to use 'dankimjw' instead"
echo ""

# Use git filter-branch to rewrite history
git filter-branch -f --env-filter '
OLD_EMAIL="noreply@anthropic.com"
CORRECT_NAME="dankimjw"
CORRECT_EMAIL="dankimjw@users.noreply.github.com"

if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

echo ""
echo "History rewrite complete!"
echo ""
echo "To finish the process:"
echo "1. Review the changes with: git log --oneline -10"
echo "2. Force push to remote: git push --force-with-lease origin $CURRENT_BRANCH"
echo "3. If working with others, they need to:"
echo "   git fetch origin"
echo "   git reset --hard origin/$CURRENT_BRANCH"
echo ""
echo "To undo this operation:"
echo "git reset --hard $BACKUP_TAG"
echo ""
echo "WARNING: Force pushing will overwrite remote history!"