#!/bin/bash
# One-click script to remove Claude from git history

echo "🚀 Starting Claude removal process..."
echo ""

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "📦 Installing git-filter-repo..."
    brew install git-filter-repo
    
    # Check if installation succeeded
    if ! command -v git-filter-repo &> /dev/null; then
        echo "❌ Failed to install git-filter-repo"
        echo "Please install manually: brew install git-filter-repo"
        exit 1
    fi
fi

# Create backup
echo "💾 Creating backup..."
git branch backup-before-claude-removal-$(date +%Y%m%d-%H%M%S)

# Run the filter
echo "🔄 Rewriting history..."
git filter-repo --force --mailmap <(echo "dankimjw <dankimjw@users.noreply.github.com> Claude <noreply@anthropic.com>")

# Check if Claude is still in history
echo ""
echo "🔍 Checking results..."
if git log --all --format='%an <%ae>' | grep -i claude > /dev/null; then
    echo "⚠️  Warning: Claude still found in some commits"
else
    echo "✅ Claude successfully removed from all commits!"
fi

echo ""
echo "📤 Ready to push changes to GitHub"
echo "Run this command to update GitHub:"
echo ""
echo "  git push --force origin --all && git push --force origin --tags"
echo ""
echo "⚠️  This will overwrite the remote repository!"