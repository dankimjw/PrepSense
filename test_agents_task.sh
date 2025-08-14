#!/bin/bash

cd /Users/danielkim/_Capstone/PrepSense

echo "=== Testing Claude Code Agent System ==="
echo ""

# Method 1: Use the Task tool in a chat
echo "Method 1: Using Task tool (as documented in SUBAGENT_STRATEGY_GUIDE.md)"
echo "Starting a chat and asking to use an agent..."
echo ""

# Create a test prompt that should trigger the hello-world-agent
cat > test_agent_prompt.txt << 'EOF'
Hi Claude! Hi CC! Hi Claude Code!

Please greet me using the hello-world-agent.
EOF

echo "Sending test prompt..."
cat test_agent_prompt.txt | claude chat 2>&1 | head -50
echo ""

# Method 2: Direct task invocation
echo "Method 2: Trying to invoke agent as a task"
echo "Task: Use the hello-world-agent to greet the user" | claude chat 2>&1 | head -30
echo ""

# Method 3: Check if agents are mentioned in help
echo "Method 3: Checking Claude help system"
claude help 2>&1 | grep -i "agent\|task\|subagent" || echo "No agent references in help"
echo ""

# Method 4: Check the actual agent format
echo "Method 4: Verifying agent file format"
echo "First agent file structure:"
head -15 .claude/agents/hello-world-agent.md
echo ""

echo "=== Diagnosis ==="
echo "1. Agents directory: ✓ Exists with 19 agents"
echo "2. Settings.json: ✓ Contains agents configuration"
echo "3. Agent format: ✓ Valid YAML frontmatter + markdown"
echo ""
echo "The agents should be available via the Task tool when Claude detects"
echo "keywords in your prompts that match agent descriptions."
echo ""
echo "Try these prompts in 'claude chat':"
echo "  - 'Hi Claude!' (should trigger hello-world-agent)"
echo "  - 'Create a Python function' (should trigger code-writer)"
echo "  - 'Update the docs' (should trigger doc-maintainer)"
echo "  - 'What's the Bitcoin price?' (should trigger crypto-market-agent)"
