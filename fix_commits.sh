#!/bin/bash

# Script to fix commit authors and remove Claude co-author

echo "Starting commit fixing process..."

# First, let's create a backup branch
git branch backup-before-fix-$(date +%Y%m%d-%H%M%S)

# Create environment variables for the filter
export FILTER_BRANCH_SQUELCH_WARNING=1

# Use git filter-repo or filter-branch to fix commits
# We'll use filter-branch for this task

git filter-branch -f --msg-filter '
    # Remove Co-authored-by: Claude lines
    sed "/Co-authored-by: Claude <noreply@anthropic.com>/d"
' --env-filter '
    # Fix PrepSense Team commits
    if [ "$GIT_AUTHOR_NAME" = "PrepSense Team" ]; then
        export GIT_AUTHOR_NAME="Daniel Kim"
        export GIT_AUTHOR_EMAIL="16387112+dankimjw@users.noreply.github.com"
    fi
    if [ "$GIT_COMMITTER_NAME" = "PrepSense Team" ]; then
        export GIT_COMMITTER_NAME="Daniel Kim"
        export GIT_COMMITTER_EMAIL="16387112+dankimjw@users.noreply.github.com"
    fi
' -- --all

echo "Commit fixing complete!"
echo "Review the changes with: git log --oneline -20"
echo "If everything looks good, force push with: git push --force-with-lease origin main"