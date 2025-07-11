#!/bin/bash

# Safe script to fix commit authors and remove Claude co-author

echo "Starting safe commit fix process..."

# Create backup
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
echo "Creating backup branch: $BACKUP_BRANCH"
git branch $BACKUP_BRANCH

# Export warning suppression
export FILTER_BRANCH_SQUELCH_WARNING=1

# Fix all commits in one pass
echo "Fixing commits..."
git filter-branch -f \
  --msg-filter 'sed "/Co-authored-by: Claude <noreply@anthropic.com>/d"' \
  --env-filter '
    # Fix PrepSense Team commits
    if [ "$GIT_AUTHOR_NAME" = "PrepSense Team" ]; then
        export GIT_AUTHOR_NAME="Daniel Kim"
        export GIT_AUTHOR_EMAIL="16387112+dankimjw@users.noreply.github.com"
        export GIT_COMMITTER_NAME="Daniel Kim"
        export GIT_COMMITTER_EMAIL="16387112+dankimjw@users.noreply.github.com"
    fi
' HEAD

echo "Process complete!"
echo ""
echo "To verify the changes:"
echo "1. Check recent commits: git log --oneline --format='%h %an %s' -20"
echo "2. Check specific commits for Claude co-author:"
echo "   git show 53534372f0b7bccc2657b59c224b4ce20b4044fb"
echo "   git show 5ac9aeee9b740c4e99b4588a9c1367202df6b64c" 
echo "   git show ebdb003264cbb91429d6ccc458cf3a2e55bcb213"
echo "3. Check for PrepSense Team: git log --author='PrepSense Team' --oneline"
echo ""
echo "If everything looks good:"
echo "  git push --force-with-lease origin $(git branch --show-current)"
echo ""
echo "To restore from backup if needed:"
echo "  git reset --hard $BACKUP_BRANCH"