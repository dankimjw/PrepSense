#!/bin/bash

cd /Users/danielkim/_Capstone/PrepSense

echo "=== Debugging Claude Code Agents ==="
echo ""

# Test 1: Check if Claude recognizes the project
echo "Test 1: Check Claude project status"
claude status 2>&1 || echo "No status command"
echo ""

# Test 2: Try listing agents directly
echo "Test 2: List agents command"
claude agents 2>&1 || echo "No agents command"
echo ""

# Test 3: Check config validation
echo "Test 3: Validate configuration"
claude config 2>&1 || echo "No config command"
echo ""

# Test 4: Start chat and immediately ask about agents
echo "Test 4: Query agents in chat"
echo "What agents are available?" | claude chat 2>&1 | head -30
echo ""

# Test 5: Check if agents directory is correct relative path
echo "Test 5: Directory structure"
echo "Current dir: $(pwd)"
echo "Agents dir exists: $([ -d ".claude/agents" ] && echo "YES" || echo "NO")"
echo "Agents count: $(ls .claude/agents/*.md 2>/dev/null | wc -l)"
echo ""

# Test 6: Try different agent path configurations
echo "Test 6: Testing absolute vs relative paths"
cat > .claude/settings.json.test << 'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "Sonnet",
  "agents": {
    "path": ".claude/agents",
    "enabled": true
  },
  "agentsPath": ".claude/agents",
  "enableAgents": true,
  "permissions": {
    "allow": ["Write", "Edit", "Bash(ls:*)", "Bash(cat:*)"]
  }
}
EOF

echo "Created test configuration with multiple agent path formats"
echo ""

# Test 7: Environment check
echo "Test 7: Environment"
echo "PATH: $PATH"
echo "Claude location: $(which claude)"
echo "Claude version: $(claude --version 2>&1 || echo "Version unknown")"
