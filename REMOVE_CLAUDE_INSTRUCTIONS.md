# Instructions to Remove Claude from Git History

## Step 1: Install git-filter-repo

```bash
# Option A: Using Homebrew (recommended for Mac)
brew install git-filter-repo

# Option B: Using pip
pip install git-filter-repo
```

## Step 2: Create a backup

```bash
cd /Users/danielkim/_Capstone/PrepSense

# Create backup branch
git branch backup-before-claude-removal

# Also create a backup tag
git tag backup-$(date +%Y%m%d-%H%M%S)
```

## Step 3: Run the filter

```bash
# This command will rewrite all commits where Claude is the author
git filter-repo --force --mailmap <(echo "dankimjw <dankimjw@users.noreply.github.com> Claude <noreply@anthropic.com>")
```

## Step 4: Verify the changes

```bash
# Check that Claude is no longer in the history
git log --all --format='%an <%ae>' | sort | uniq | grep -i claude

# If the above returns nothing, Claude has been removed successfully
```

## Step 5: Force push to GitHub

```bash
# Push all branches with force
git push --force-with-lease origin --all

# Push all tags
git push --force-with-lease origin --tags
```

## If something goes wrong

```bash
# To restore from backup:
git reset --hard backup-before-claude-removal
```

## Important Notes

1. This will rewrite ALL commits where Claude is the author
2. All commit hashes will change
3. If anyone else has cloned this repo, they'll need to re-clone
4. Old PR and issue links to commits will break

## Alternative: Just the current branch

If you only want to clean the current branch:

```bash
git filter-repo --refs HEAD --force --mailmap <(echo "dankimjw <dankimjw@users.noreply.github.com> Claude <noreply@anthropic.com>")
```