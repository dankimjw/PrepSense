#!/bin/bash

# Ensure MCP Always Available Script
# This script can be added to your shell profile or run at system startup

set -e

echo "🔧 Ensuring MCP servers are always available..."

# Check if global MCP config exists
if [ ! -f "$HOME/.claude/mcp.global.json" ]; then
    echo "⚠️  Global MCP config not found. Run ./scripts/setup_global_mcp.sh first"
    exit 1
fi

# Ensure current directory has MCP config linked
if [ ! -L ".mcp.json" ]; then
    echo "🔗 Linking current directory to global MCP config..."
    ln -sf "$HOME/.claude/mcp.global.json" ".mcp.json"
fi

# Pre-warm npm packages (download if needed)
echo "📦 Pre-warming npm MCP packages..."
npx -y @upstash/context7-mcp --help > /dev/null 2>&1 &
npx ios-simulator-mcp --help > /dev/null 2>&1 &
npx -y @mobilenext/mobile-mcp@latest --help > /dev/null 2>&1 &

# Wait for background processes
wait

echo "✅ MCP servers are ready and available!"

# Add to shell profile if not already there
SHELL_PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
fi

if [ -n "$SHELL_PROFILE" ] && ! grep -q "MCP_SETUP" "$SHELL_PROFILE"; then
    echo ""
    echo "🔧 Would you like to add MCP auto-setup to your shell profile?"
    echo "This will ensure MCP is available whenever you open a terminal."
    echo ""
    echo "Add this to $SHELL_PROFILE:"
    echo ""
    echo "# MCP_SETUP - Auto-link MCP config in new directories"
    echo "claude_mcp_link() {"
    echo "    if [ -f \"\$HOME/.claude/mcp.global.json\" ] && [ ! -f \".mcp.json\" ]; then"
    echo "        ln -sf \"\$HOME/.claude/mcp.global.json\" \".mcp.json\""
    echo "        echo \"✅ MCP linked for \$(basename \$(pwd))\""
    echo "    fi"
    echo "}"
    echo "alias mcp-link='claude_mcp_link'"
    echo ""
fi