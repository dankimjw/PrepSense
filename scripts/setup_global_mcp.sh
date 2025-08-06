#!/bin/bash

# Global MCP Setup Script
# Makes MCP servers available globally across all Claude Code instances

set -e

GLOBAL_MCP_DIR="$HOME/.claude"
GLOBAL_MCP_CONFIG="$GLOBAL_MCP_DIR/mcp.global.json"

# Create global Claude directory if it doesn't exist
mkdir -p "$GLOBAL_MCP_DIR"

echo "🔧 Setting up global MCP configuration..."

# Create global MCP configuration
cat > "$GLOBAL_MCP_CONFIG" << 'EOF'
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

echo "✅ Created global MCP config: $GLOBAL_MCP_CONFIG"

# Install npm packages globally to avoid first-time download delays
echo "📦 Pre-installing npm MCP packages..."
npm install -g @upstash/context7-mcp ios-simulator-mcp @mobilenext/mobile-mcp@latest

# Create symlink function for projects
create_mcp_link() {
    local project_dir="$1"
    local mcp_file="$project_dir/.mcp.json"
    
    if [ -f "$mcp_file" ] && [ ! -L "$mcp_file" ]; then
        echo "⚠️  Backing up existing .mcp.json to .mcp.json.backup"
        mv "$mcp_file" "$mcp_file.backup"
    fi
    
    ln -sf "$GLOBAL_MCP_CONFIG" "$mcp_file"
    echo "🔗 Linked $mcp_file to global config"
}

# Link current project
if [ -d "$(pwd)" ]; then
    create_mcp_link "$(pwd)"
fi

# Create helper script for linking new projects
cat > "$GLOBAL_MCP_DIR/link_project_mcp.sh" << 'EOF'
#!/bin/bash
# Helper script to link project MCP config to global config

GLOBAL_CONFIG="$HOME/.claude/mcp.global.json"
PROJECT_CONFIG="$(pwd)/.mcp.json"

if [ -f "$PROJECT_CONFIG" ] && [ ! -L "$PROJECT_CONFIG" ]; then
    echo "⚠️  Backing up existing .mcp.json"
    mv "$PROJECT_CONFIG" "$PROJECT_CONFIG.backup"
fi

ln -sf "$GLOBAL_CONFIG" "$PROJECT_CONFIG"
echo "✅ Project linked to global MCP config"
EOF

chmod +x "$GLOBAL_MCP_DIR/link_project_mcp.sh"

echo ""
echo "🎉 Global MCP setup complete!"
echo ""
echo "📋 What was configured:"
echo "  ✅ Global MCP config: $GLOBAL_MCP_CONFIG"
echo "  ✅ Current project linked to global config"
echo "  ✅ npm packages pre-installed globally"
echo "  ✅ Helper script: ~/.claude/link_project_mcp.sh"
echo ""
echo "🚀 Usage:"
echo "  • MCP servers are now available in all Claude Code instances"
echo "  • For new projects: run ~/.claude/link_project_mcp.sh"
echo "  • Check status: ./scripts/start_mcp_services.sh status"
echo ""