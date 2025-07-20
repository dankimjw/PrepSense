#!/bin/bash

echo "🔍 Debugging Testzone MCP Configuration"
echo "======================================="

TESTZONE="/Users/danielkim/_Capstone/PrepSense-worktrees/testzone"

echo -e "\n1. Current directory:"
pwd

echo -e "\n2. MCP configuration file:"
if [ -f "$TESTZONE/.mcp.json" ]; then
    echo "✅ .mcp.json exists"
    echo "Size: $(wc -c < "$TESTZONE/.mcp.json") bytes"
    echo "Modified: $(ls -la "$TESTZONE/.mcp.json" | awk '{print $6, $7, $8}')"
else
    echo "❌ .mcp.json NOT found"
fi

echo -e "\n3. Claude MCP status:"
cd "$TESTZONE" && claude mcp list 2>&1

echo -e "\n4. Check for hidden characters or encoding issues:"
file "$TESTZONE/.mcp.json"
echo "First line hex dump:"
head -1 "$TESTZONE/.mcp.json" | xxd | head -1

echo -e "\n5. Try to force reload MCP configuration:"
echo "Removing and re-adding servers..."

# Remove existing servers if any
cd "$TESTZONE"
for server in filesystem memory sequential-thinking context7 ios-simulator mobile; do
    claude mcp remove $server 2>/dev/null
done

# Re-add from the existing .mcp.json manually
echo -e "\n6. Re-adding servers manually..."
claude mcp add filesystem mcp-server-filesystem -- --root .
claude mcp add memory mcp-server-memory
claude mcp add sequential-thinking mcp-server-sequential-thinking
claude mcp add context7 npx -- -y @upstash/context7-mcp
claude mcp add ios-simulator npx -- ios-simulator-mcp
claude mcp add mobile npx -- -y @mobilenext/mobile-mcp@latest

echo -e "\n7. Final MCP list:"
claude mcp list 2>&1

echo -e "\n8. Check if .mcp.json was updated:"
ls -la "$TESTZONE/.mcp.json"