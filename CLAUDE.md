# Claude AI Assistant Guidelines for PrepSense

## Important: Commit Message Policy

**DO NOT include any Claude/AI references in commit messages**

The following are explicitly forbidden in commit messages:
- ❌ "Claude" or "claude" 
- ❌ "🤖 Generated with [Claude Code]"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Any AI/automated generation references

## Git Configuration

This repository has automated safeguards:
1. **Git Hook**: `.git/hooks/prepare-commit-msg` automatically removes Claude references
2. **Global Template**: `~/.gitmessage` provides clean commit template
3. **Config File**: `.claude-config` documents these requirements

## Commit Message Format

Use this format for all commits:
```
<type>: <description>

[optional body]

[optional footer]
```

Example:
```
feat: add ingredient availability checking to recipes

- Show green checkmarks for available ingredients
- Red X for missing ingredients
- Add shopping list integration
```

## Development Guidelines

1. Follow existing code conventions
2. Test changes before committing
3. Write clear, descriptive commit messages
4. Focus on what changed and why
5. Keep commits atomic and focused

## When Creating Commits

Simply use standard git commands:
```bash
git add .
git commit -m "type: clear description of changes"
git push
```

The git hook will automatically clean any accidental Claude references.