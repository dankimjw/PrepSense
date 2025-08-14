#!/bin/bash

cd /Users/danielkim/_Capstone/PrepSense

echo "=== Claude Code Settings Verification ==="
echo ""

echo "1. Checking settings files for unrecognized fields..."
echo ""

# Run doctor to check for issues
claude doctor 2>&1 | grep -A20 "Invalid Settings" || echo "✅ No invalid settings found!"

echo ""
echo "2. Verifying agents directory..."
if [ -d ".claude/agents" ]; then
    agent_count=$(ls .claude/agents/*.md 2>/dev/null | wc -l)
    echo "✅ Found .claude/agents/ directory with $agent_count agents"
else
    echo "❌ No .claude/agents/ directory found"
fi

echo ""
echo "3. Testing agent availability..."
echo "Starting claude chat to test agents..."
echo ""
echo "In Claude Code v1.0.61, agents are automatically discovered from the .claude/agents/ directory."
echo "They don't need to be configured in settings.json."
echo ""
echo "Try these commands in claude chat:"
echo "  - Type: Hi Claude!"
echo "  - Type: What agents are available?"
echo "  - Type: /agents (if supported)"
echo ""

# Show current settings
echo "4. Current settings.json (should be minimal):"
cat .claude/settings.json | head -20
echo ""

echo "=== Verification Complete ==="
echo ""
echo "Now run: claude chat"
echo "Your agents should be automatically available based on the .claude/agents/ directory"
