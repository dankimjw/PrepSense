#!/usr/bin/env bash
# Register MCP servers for current directory

claude mcp add filesystem --scope project "mcp-server-filesystem --root ."
claude mcp add memory --scope project "mcp-server-memory"
claude mcp add sequential-thinking --scope project "mcp-server-sequential-thinking"
claude mcp add context7 --scope project "npx -y @upstash/context7-mcp"

echo "✅ Registered 4 MCP servers for this project"