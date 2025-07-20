#!/bin/bash

# Script to fix MCP filesystem server configuration across all worktrees

echo "🔧 Fixing MCP filesystem server configuration across all worktrees..."

# Get the main repository path
MAIN_REPO="/Users/danielkim/_Capstone/PrepSense"
WORKTREES_DIR="/Users/danielkim/_Capstone/PrepSense-worktrees"

# Create a proper .mcp.json configuration
cat > "$MAIN_REPO/.mcp.json.fixed" << 'EOF'
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
    "sequential-thinking": {
      "type": "stdio",
      "command": "mcp-server-sequential-thinking",
      "args": [],
      "env": {}
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {}
    },
    "ios-simulator": {
      "type": "stdio",
      "command": "npx",
      "args": ["ios-simulator-mcp"],
      "env": {}
    },
    "mobile": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@mobilenext/mobile-mcp@latest"],
      "env": {}
    }
  }
}
EOF

# Function to update MCP config in a directory
update_mcp_config() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        echo "  📁 Updating $name: $dir"
        cp "$MAIN_REPO/.mcp.json.fixed" "$dir/.mcp.json"
        echo "     ✅ Updated .mcp.json"
    else
        echo "  ❌ Directory not found: $dir"
    fi
}

# Update main repository
echo "📍 Main repository:"
update_mcp_config "$MAIN_REPO" "main"

# Update all worktrees
echo -e "\n📍 Worktrees:"
for worktree in "$WORKTREES_DIR"/*; do
    if [ -d "$worktree" ] && [ "$worktree" != "$WORKTREES_DIR/PrepSense-worktrees" ]; then
        worktree_name=$(basename "$worktree")
        update_mcp_config "$worktree" "$worktree_name"
    fi
done

# Clean up temporary file
rm -f "$MAIN_REPO/.mcp.json.fixed"

echo -e "\n✅ MCP filesystem configuration fixed!"
echo -e "\n⚠️  IMPORTANT: You need to restart Claude Code in each directory for the changes to take effect:"
echo "   1. Close Claude Code in each worktree"
echo "   2. Run 'claude' again in each directory"

# Show current Claude processes
echo -e "\n🔍 Current Claude processes that need to be restarted:"
ps aux | grep -E "claude" | grep -v grep | awk '{print "   PID:", $2, "Directory:", $NF}'