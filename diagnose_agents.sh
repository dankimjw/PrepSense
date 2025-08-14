#!/bin/bash
cd /Users/danielkim/_Capstone/PrepSense

# Diagnostic script for Claude Code agents

echo "=== Claude Code Agents Diagnostic ==="
echo ""

# Check current directory
echo "Current directory: $(pwd)"
echo ""

# Check if we're in a Claude project
if [ -d ".claude" ]; then
    echo "✅ Found .claude directory"
else
    echo "❌ No .claude directory found"
    exit 1
fi

# Check for agents directory
if [ -d ".claude/agents" ]; then
    echo "✅ Found .claude/agents directory"
    echo ""
    echo "Available agents:"
    for agent in .claude/agents/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent" .md)
            description=$(grep -m1 "^description:" "$agent" | cut -d'"' -f2 || echo "No description")
            echo "  - $agent_name: $description"
        fi
    done
else
    echo "❌ No .claude/agents directory found"
fi

echo ""
echo "=== Testing Claude Command ==="

# Check if claude command exists
if command -v claude &> /dev/null; then
    echo "✅ Claude command found at: $(which claude)"
    echo ""
    
    # Try to list agents
    echo "Attempting to list agents with 'claude agents list':"
    claude agents list 2>&1 || echo "Command failed"
    
    echo ""
    echo "Attempting to use an agent with 'claude chat --agent hello-world-agent':"
    echo "Hi" | claude chat --agent hello-world-agent 2>&1 | head -20 || echo "Command failed"
    
else
    echo "❌ Claude command not found in PATH"
    echo "PATH: $PATH"
fi

echo ""
echo "=== Checking Configuration ==="

# Check settings files
if [ -f ".claude/settings.json" ]; then
    echo "✅ Found settings.json"
    if grep -q '"agents"' .claude/settings.json; then
        echo "  - Contains agents configuration"
    else
        echo "  - No agents configuration found"
    fi
fi

if [ -f ".claude/settings.local.json" ]; then
    echo "✅ Found settings.local.json"
fi

echo ""
echo "=== Possible Issues ==="

# Check common issues
if ! command -v claude &> /dev/null; then
    echo "1. Claude Code CLI not installed or not in PATH"
    echo "   Solution: Install with 'npm install -g @anthropic/claude-code'"
fi

if [ -d ".claude/agents" ] && ! grep -q '"agents"' .claude/settings.json 2>/dev/null; then
    echo "2. Agents directory exists but not configured in settings.json"
    echo "   Solution: Add agents configuration to settings.json"
fi

echo ""
echo "=== End Diagnostic ==="
