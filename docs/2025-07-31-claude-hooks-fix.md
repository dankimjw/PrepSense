# Claude Hooks Configuration Fix - July 31, 2025

## Problem Summary
Claude instances were getting hook errors like:
```
PreToolUse:Read [.claude/hooks/run_hook.sh .claude/hooks/pre_tool_use.py] failed 
with non-blocking status code 127: /bin/sh: .claude/hooks/run_hook.sh: No such file 
or directory
```

## Root Cause
1. Hooks were configured with relative paths in `.claude/settings.json`
2. Claude instances running from different directories couldn't find the hook scripts
3. `uv` command wasn't available in PATH when Claude instances didn't have venv activated

## Solution Implemented

### 1. Updated Hook Commands
Changed all hooks in `.claude/settings.json` to use:
```json
"command": "uv run --script .claude/hooks/[hook_name].py"
```

This matches the shebang line in the hook scripts:
```python
#!/usr/bin/env -S uv run --script
```

### 2. Worktree Setup with Symlinks
Created `setup_worktree_claude.sh` that:
- Creates a **symlink** to the main repo's `.claude` directory (not a copy)
- Sets up virtual environment with `uv` installed
- Installs all dependencies

All worktrees now share the same `.claude` configuration via symlinks.

### 3. Key Requirements
- **Always activate venv** before running Claude Code: `source venv/bin/activate`
- This ensures `uv` is available in PATH
- All paths in settings.json are project-relative

## Files Created/Modified
1. `/Users/danielkim/_Capstone/PrepSense/.claude/settings.json` - Updated hook commands
2. `/Users/danielkim/_Capstone/PrepSense/setup_worktree_claude.sh` - Worktree setup script
3. `/Users/danielkim/_Capstone/PrepSense/WORKTREE_CLAUDE_SETUP.md` - Documentation

## Important Notes
- `.claude/` is gitignored, so it's not tracked in version control
- Each worktree needs to run the setup script once
- All worktrees share the same hooks and configuration
- Hook logs are centralized in `.claude/hooks/logs/`

## For Future Reference
If hooks fail with "command not found" or "No such file" errors:
1. Check if virtual environment is activated
2. Verify `.claude` exists (as directory or symlink)
3. Ensure `uv` is installed: `pip install uv`