# PostgreSQL MCP Server Setup

## Overview
The PostgreSQL MCP (Model Context Protocol) server allows Claude instances to directly query the PrepSense database for read-only operations, enabling better data analysis and verification.

## Configuration
The PostgreSQL MCP server is configured in `.mcp.json`:

```json
"postgres": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://postgres:changeme123!@35.184.61.42:5432/prepsense"],
  "env": {}
}
```

## Setup for All Worktrees
As of 2025-01-27, all worktrees have been updated with the PostgreSQL MCP configuration:

- `/Users/danielkim/_Capstone/PrepSense/.mcp.json` (main)
- `../PrepSense-worktrees/bugfix/.mcp.json`
- `../PrepSense-worktrees/testzone/.mcp.json`
- `../PrepSense-worktrees/testzone_backup/.mcp.json`

## Usage
Claude instances with this configuration can:
- Query database schema
- Perform read-only SELECT queries
- Analyze data patterns
- Verify data integrity

## Important Notes
- **Read-only access**: The MCP server only allows SELECT queries
- **Connection string**: Uses the production PostgreSQL instance on Google Cloud SQL
- **Automatic setup**: The configuration is automatically loaded when Claude Code starts
- **Shared across instances**: All Claude instances in different worktrees can access the same database

## Updating Worktrees
To ensure all worktrees have the latest MCP configuration:

```bash
# From main PrepSense directory
for worktree in ../PrepSense-worktrees/*/; do
    if [ -d "$worktree" ]; then
        cp .mcp.json "$worktree"
    fi
done
```

## Verification
To verify PostgreSQL MCP is configured in all worktrees:

```bash
grep -l "postgres" ../PrepSense-worktrees/*/.mcp.json
```

Last updated: 2025-01-27