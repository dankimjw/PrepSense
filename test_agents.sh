#!/bin/bash

cd /Users/danielkim/_Capstone/PrepSense

echo "Testing Claude Code agents..."
echo ""

# List available agents
echo "Available agents in .claude/agents/:"
ls .claude/agents/*.md | xargs -I {} basename {} .md | sed 's/^/  - /'

echo ""
echo "Agent configuration in settings.json:"
cat .claude/settings.json | jq '.agents' 2>/dev/null || echo "No jq installed, showing raw:"
grep -A3 '"agents"' .claude/settings.json

echo ""
echo "To use an agent, run:"
echo "  cd /Users/danielkim/_Capstone/PrepSense"
echo "  claude chat --agent hello-world-agent"
echo ""
echo "Or for a specific task:"
echo "  claude chat --agent code-writer"
echo "  claude chat --agent unit-tester"
echo "  claude chat --agent doc-writer"
