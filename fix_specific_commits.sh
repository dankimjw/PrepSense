#!/bin/bash

# Script to remove Claude co-author from specific commits and fix PrepSense Team author

echo "Creating backup branch..."
git branch backup-$(date +%Y%m%d-%H%M%S)

# First, let's handle the Claude co-author removal for specific commits
echo "Removing Claude co-author from specific commits..."

# We'll use interactive rebase to edit these specific commits
# Find the parent of the oldest commit we need to fix
OLDEST_COMMIT="53534372f0b7bccc2657b59c224b4ce20b4044fb"
PARENT=$(git rev-parse ${OLDEST_COMMIT}^)

# Create a script for the rebase
cat > /tmp/remove_claude.sh << 'EOF'
#!/bin/bash
# Remove Claude co-author line from commit message
git log -1 --format=%B | sed '/Co-authored-by: Claude <noreply@anthropic.com>/d' | git commit --amend -F -
EOF
chmod +x /tmp/remove_claude.sh

# Set up git to use our script for specific commits
export GIT_SEQUENCE_EDITOR="sed -i '' 's/pick 5353437/edit 5353437/; s/pick 5ac9aee/edit 5ac9aee/; s/pick ebdb003/edit ebdb003/'"

# Start the rebase
git rebase -i $PARENT --exec "/tmp/remove_claude.sh"

# Clean up
rm /tmp/remove_claude.sh

echo "Claude co-author removal complete!"

# Now fix PrepSense Team commits
echo "Fixing PrepSense Team author commits..."

git filter-branch -f --env-filter '
    if [ "$GIT_AUTHOR_NAME" = "PrepSense Team" ]; then
        export GIT_AUTHOR_NAME="Daniel Kim"
        export GIT_AUTHOR_EMAIL="16387112+dankimjw@users.noreply.github.com"
    fi
    if [ "$GIT_COMMITTER_NAME" = "PrepSense Team" ]; then
        export GIT_COMMITTER_NAME="Daniel Kim"
        export GIT_COMMITTER_EMAIL="16387112+dankimjw@users.noreply.github.com"
    fi
' -- --all

echo "All fixes complete!"
echo "Review changes with: git log --oneline --format='%h %an <%ae> %s' | head -20"
echo "Check specific commits:"
echo "  git show --format=fuller 53534372f0b7bccc2657b59c224b4ce20b4044fb"
echo "  git show --format=fuller 5ac9aeee9b740c4e99b4588a9c1367202df6b64c"
echo "  git show --format=fuller ebdb003264cbb91429d6ccc458cf3a2e55bcb213"