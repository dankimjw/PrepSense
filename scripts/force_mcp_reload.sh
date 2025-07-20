#!/usr/bin/env bash
# Force Claude to reload MCP configuration from .mcp.json

# First, remove ALL existing registrations
echo "🧹 Cleaning all MCP registrations..."
for scope in user project local; do
  for server in filesystem memory sequential-thinking context7; do
    claude mcp remove "$server" --scope "$scope" 2>/dev/null || true
  done
done

# Give it a moment
sleep 1

# If .mcp.json exists, register each server from it
if [ -f ".mcp.json" ]; then
  echo "📄 Found .mcp.json, registering servers..."
  
  # Parse .mcp.json and register each server
  # Using jq if available, otherwise manual registration
  if command -v jq >/dev/null 2>&1; then
    servers=$(jq -r '.mcpServers | keys[]' .mcp.json 2>/dev/null)
    for server in $servers; do
      cmd=$(jq -r ".mcpServers[\"$server\"].command" .mcp.json)
      echo "  ✓ Registering $server"
      claude mcp add "$server" --scope project "$cmd"
    done
  else
    # Manual registration based on standard .mcp.json
    claude mcp add filesystem --scope project "mcp-server-filesystem --root ."
    claude mcp add memory --scope project "mcp-server-memory"
    claude mcp add sequential-thinking --scope project "mcp-server-sequential-thinking"
    claude mcp add context7 --scope project "npx -y @upstash/context7-mcp"
  fi
else
  echo "❌ No .mcp.json found in current directory"
fi

echo ""
echo "✅ Done! Restart Claude to see changes:"
echo "   exit"
echo "   claude --dangerously-skip-permissions"