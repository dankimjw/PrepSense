# Git Author Configuration for PrepSense

## Setup Instructions

To ensure all commits are authored by "dankimjw", run these commands in your terminal:

```bash
# Navigate to the PrepSense repository
cd /Users/danielkim/_Capstone/PrepSense

# Set local git configuration (only affects this repository)
git config --local user.name "dankimjw"
git config --local user.email "dankimjw@example.com"

# Optional: Set global configuration (affects all repositories)
# git config --global user.name "dankimjw"
# git config --global user.email "dankimjw@example.com"
```

## Verify Configuration

To verify your configuration is set correctly:

```bash
# Check local configuration
git config --local user.name
git config --local user.email

# Check what will be used for commits
git config user.name
git config user.email
```

## Existing Safeguards

This repository already has the following safeguards in place:

1. **Git Hook** (`.git/hooks/prepare-commit-msg`): Automatically removes any Claude/AI references from commit messages
2. **Configuration File** (`.claude-config`): Documents commit message requirements
3. **CLAUDE.md**: Contains instructions for AI assistants to avoid Claude references

## Making Commits

After configuration, all commits will automatically use "dankimjw" as the author:

```bash
git add .
git commit -m "feat: your commit message here"
git push origin feature/recipe-ingredient-quantity-subtraction
```

## Important Notes

- The git hook will automatically clean any accidental Claude references
- All commits will show "dankimjw" as the author
- Replace "dankimjw@example.com" with your actual email if needed