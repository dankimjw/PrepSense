# .gitignore Recommendations for Public Repositories

If you plan to make this repository public or create public forks, consider adding these entries to your `.gitignore`:

## Internal Documentation (Recommended for Public Repos)
```
# Internal development documentation 
docs/internal/

# Claude-specific configuration files
docs/internal/claude/
.mcp.json
WORKTREE_NOTES_*.md
```

## Environment and Configuration Files
```
# Environment files
.env
.env.local
.env.development
.env.production

# Database configuration
config/database.yml
config/secrets.yml
```

## Development Files
```
# Development session logs
docs/internal/sessions/
docs/internal/testing/
docs/internal/workflows/

# Claude validation and prompts
docs/internal/claude/CLAUDE_VALIDATION_RULES.md
docs/internal/claude/CLAUDE_TRUTHFUL_PROMPT.md
```

## What to Keep Public

These should remain public in any fork:
- `docs/public/` - All public documentation
- `docs/flows/` - Flow documentation 
- `docs/README.md` - Main documentation index
- Standard project files (README.md, LICENSE, etc.)

## Current Repository Status

This repository currently tracks both public and internal docs. The reorganization makes it easy to selectively ignore internal files for public forks while keeping them available for private development.

## Implementation Options

### Option 1: Keep Current Structure (Recommended)
- Keep everything tracked in the main development repository
- Create public forks that only include `docs/public/` content
- Use branch-specific .gitignore for public releases

### Option 2: Split Repositories  
- Main private repo: All documentation
- Public repo: Only `docs/public/` content
- Sync public-facing changes between repositories

### Option 3: Conditional Gitignore
- Use environment-based gitignore rules
- Different ignore patterns for development vs. production

The current structure supports all these approaches while keeping development workflow intact.