# Claude Configuration for Git Worktrees

## Problem
The `.claude/` directory is gitignored, so each worktree needs access to the Claude configuration and hooks.

## Solution: Symlinks
All worktrees share the same `.claude` directory via symlinks to the main repository.

## Quick Setup
From any worktree directory, run:
```bash
/path/to/main/repo/setup_worktree_claude.sh
```

This will:
- Create a symlink to the main repo's `.claude` directory
- Set up a virtual environment with `uv` installed
- Install all Python and Node dependencies

## Manual Setup
If you prefer to set up manually:

1. **Create symlink to .claude directory:**
   ```bash
   ln -s /path/to/main/repo/.claude .claude
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install uv
   pip install -r requirements.txt
   ```

3. **Install Node dependencies:**
   ```bash
   cd ios-app && npm install && cd ..
   ```

## Important Notes

- **Always activate the virtual environment** before running Claude Code in a worktree:
  ```bash
  source venv/bin/activate
  ```

- All worktrees share the same `.claude` configuration
- The hooks use `uv run --script` which expects `uv` to be available in PATH
- Hook logs are shared across all worktrees in `.claude/hooks/logs/`

## Troubleshooting

If you see errors like:
- `uv: command not found` - Activate the virtual environment
- `.claude/hooks/run_hook.sh: No such file or directory` - Create the symlink to .claude
- Hook errors with status code 127 - Ensure `uv` is installed in the virtual environment