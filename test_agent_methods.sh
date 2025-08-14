#!/bin/bash

# Quick test of different agent invocation methods

cd /Users/danielkim/_Capstone/PrepSense

echo "Testing different Claude agent invocation methods..."
echo ""

# Method 1: Using the Task tool (subagents)
echo "Method 1: Using Task tool (subagent):"
echo "claude chat"
echo "Then type: use the hello-world-agent agent"
echo ""

# Method 2: Direct agent flag
echo "Method 2: Direct agent flag:"
echo "claude chat --agent hello-world-agent"
echo ""

# Method 3: Agent command
echo "Method 3: Agent subcommand:"
echo "claude agent hello-world-agent"
echo ""

# Method 4: With full path
echo "Method 4: Full path:"
echo "claude chat --agent .claude/agents/hello-world-agent.md"
echo ""

# Method 5: Check claude help
echo "Checking Claude help for agent usage:"
echo "---"
claude --help 2>&1 | grep -A5 -i agent || echo "No agent help found"
echo "---"

echo ""
echo "Checking for 'claude chat' help:"
echo "---"
claude chat --help 2>&1 | grep -A5 -i agent || echo "No agent options in chat help"
echo "---"

echo ""
echo "Your agents are properly configured in:"
echo "  Directory: .claude/agents/"
echo "  Settings: .claude/settings.json (agents.path configured)"
echo ""
echo "Try one of the methods above to use your agents!"
