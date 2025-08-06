# MCP Auto-Initialization System

## Overview

The MCP (Model Context Protocol) auto-initialization system ensures that all required MCP servers are automatically set up, configured, and available for every Claude Code session in the PrepSense project.

## 🚀 Key Features

- **Automatic Session Initialization**: MCP servers are initialized when starting new Claude sessions
- **Health Monitoring**: Continuous monitoring of MCP server health and connectivity
- **Self-Healing**: Automatic repair of broken or missing server configurations
- **Worktree Synchronization**: MCP configuration syncs across all git worktrees
- **Zero Manual Intervention**: Complete automation of MCP server management

## 📁 System Components

### 1. Core Manager Script
**File**: `scripts/mcp_auto_manager.py`

The central MCP management system with these capabilities:
- Install all required MCP servers and packages
- Generate and maintain `.mcp.json` configuration
- Register servers with `claude mcp`
- Perform health checks and diagnostics
- Repair broken server configurations

**Usage**:
```bash
python scripts/mcp_auto_manager.py --session    # Full session initialization
python scripts/mcp_auto_manager.py --check     # Health check only
python scripts/mcp_auto_manager.py --repair    # Fix broken servers
python scripts/mcp_auto_manager.py --init      # Install and register only
```

### 2. Session Start Hook
**File**: `.claude/hooks/session_start.py`

Enhanced to automatically initialize MCP servers for new sessions:
- Detects session type (startup, resume, clear)
- Calls MCP auto-manager for new sessions
- Provides status feedback in session context
- Includes `--no-mcp` flag to skip initialization if needed

### 3. Health Check Script
**File**: `scripts/mcp_health_check.sh`

Quick health verification for integration into existing workflows:
- Checks connectivity status of all required servers
- Provides colored output and status codes
- Integrates with existing health check systems
- Returns appropriate exit codes for automation

### 4. Configuration Management
**Files**: 
- `.mcp.json` - Main MCP server configuration
- `.claude/settings.json` - Session start hook configuration
- `.claude/settings.local.json` - Local MCP server settings

### 5. Worktree Synchronization
**File**: `scripts/sync_mcp_to_worktrees.sh`

Ensures all parallel development environments have the same MCP configuration:
- Syncs `.mcp.json` to all worktrees
- Copies MCP manager scripts
- Provides sync status and reporting

## 🔧 Required MCP Servers

The system manages these MCP servers automatically:

| Server | Package | Description | Status |
|--------|---------|-------------|---------|
| **filesystem** | `@modelcontextprotocol/server-filesystem` | File operations with proper permissions | 🟢 Auto-configured |
| **memory** | `@modelcontextprotocol/server-memory` | Persistent memory across conversations | 🟢 Auto-configured |
| **sequential-thinking** | `@modelcontextprotocol/server-sequential-thinking` | Step-by-step reasoning | 🟢 Auto-configured |
| **context7** | `@upstash/context7-mcp` | Up-to-date library documentation | 🟢 Auto-configured |
| **ios-simulator** | `ios-simulator-mcp` | iOS Simulator control and automation | 🟢 Working |
| **mobile** | `@mobilenext/mobile-mcp` | Mobile device control and automation | 🟢 Working |
| **postgres** | `@modelcontextprotocol/server-postgres` | PostgreSQL/Cloud SQL database access | 🟡 Needs environment variables |

## ⚙️ Configuration Details

### .mcp.json Structure
```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "mcp-server-filesystem",
      "args": ["--root", "."],
      "env": {}
    },
    "memory": {
      "type": "stdio", 
      "command": "mcp-server-memory",
      "args": [],
      "env": {}
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@host:port/db"
      }
    }
  }
}
```

### Session Hook Configuration
The session start hook is configured in `.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
                     "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session_start.py --load-context" } ] }
    ]
  }
}
```

## 🚀 Automatic Initialization Workflow

When a Claude Code session starts:

1. **Session Hook Triggers** - `.claude/hooks/session_start.py --load-context`
2. **Source Detection** - Identifies session type (startup, resume, clear)
3. **MCP Initialization** - For new sessions, calls `mcp_auto_manager.py --session`
4. **Package Installation** - Ensures all required npm packages are installed globally
5. **Configuration Generation** - Creates/updates `.mcp.json` with current environment
6. **Server Registration** - Registers all servers with `claude mcp add`
7. **Health Verification** - Tests connectivity and reports status
8. **Context Integration** - Provides MCP status in session development context

## 🔧 Manual Operations

### Initial Setup
```bash
# One-time setup of the entire MCP system
python scripts/mcp_auto_manager.py --session

# Traditional setup script (now includes MCP auto-manager)
./scripts/setup_mcp_servers.sh
```

### Health Monitoring
```bash
# Quick health check
./scripts/mcp_health_check.sh

# Detailed health check
python scripts/mcp_auto_manager.py --check

# Native claude mcp status
claude mcp list
```

### Troubleshooting
```bash
# Fix broken servers
python scripts/mcp_auto_manager.py --repair

# Reset and reinitialize everything
python scripts/mcp_auto_manager.py --init

# Skip MCP in session start
python .claude/hooks/session_start.py --load-context --no-mcp
```

### Worktree Management
```bash
# Sync MCP config to all worktrees
./scripts/sync_mcp_to_worktrees.sh

# Manual sync to specific worktree
cp .mcp.json /path/to/worktree/.mcp.json
cp scripts/mcp_auto_manager.py /path/to/worktree/scripts/
```

## 🔍 Monitoring and Debugging

### Status Indicators
- ✅ **Green**: Server is connected and healthy
- ⚠️ **Yellow**: Server is registered but may need configuration
- ❌ **Red**: Server is missing or broken

### Log Files
- `logs/session_start.json` - Session initialization events
- MCP manager provides real-time colored output
- Claude mcp list shows current server status

### Common Issues and Solutions

**Issue**: Some servers show as "unhealthy" but are registered
- **Cause**: stdio-based servers don't respond to simple connectivity tests
- **Solution**: This is normal - they'll work when Claude tries to use them

**Issue**: postgres server not connecting
- **Cause**: Missing environment variables for database connection
- **Solution**: Ensure .env file has correct DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

**Issue**: MCP initialization times out during session start
- **Cause**: Network issues or npm package downloads
- **Solution**: Use `--no-mcp` flag or run manual initialization separately

## 🎯 Integration Points

### With Existing Health Checks
The MCP health check integrates with:
- `quick_check.sh` - Can include MCP status
- `check_app_health.py` - Can verify MCP availability
- CI/CD pipelines - Exit codes indicate health status

### With Development Workflow
- **Session Start**: Automatic MCP initialization
- **Worktree Creation**: Automatic config synchronization
- **Development**: All MCP servers ready without manual setup
- **Testing**: MCP functionality available immediately

## 📊 Performance Characteristics

- **Cold Start**: ~60 seconds for complete initialization
- **Health Check**: ~10 seconds for all servers
- **Session Start**: +5-10 seconds with MCP initialization
- **Memory Usage**: Minimal - servers start on-demand
- **Network**: Downloads packages only on first install

## 🔒 Security Considerations

- MCP servers run with project-level scope (not user-level)
- Database credentials read from environment variables only
- No sensitive information stored in configuration files
- All MCP communication uses stdio (no network exposure)

## 🚀 Future Enhancements

- **Smart Health Checks**: More sophisticated server testing
- **Performance Monitoring**: Track MCP server response times
- **Auto-Updates**: Keep MCP servers updated automatically
- **Custom Server Support**: Easy integration of project-specific MCP servers
- **Cloud Integration**: Direct GCP service integration via MCP

---

## Quick Reference Commands

```bash
# Session initialization (automatic)
# Happens when starting Claude Code sessions

# Manual management
python scripts/mcp_auto_manager.py --help
./scripts/mcp_health_check.sh
./scripts/sync_mcp_to_worktrees.sh

# Status and debugging  
claude mcp list
python test_mcp_integration.py
```

This MCP auto-initialization system ensures that every Claude Code session in PrepSense has immediate access to all required MCP capabilities without any manual setup or configuration.