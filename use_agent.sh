#!/bin/bash

# Claude Agent Quick Launcher

cd /Users/danielkim/_Capstone/PrepSense

# Check if agent name provided
if [ -z "$1" ]; then
    echo "Usage: $0 <agent-name> [initial-message]"
    echo ""
    echo "Available agents:"
    ls .claude/agents/*.md | xargs -I {} basename {} .md | sed 's/^/  - /'
    exit 1
fi

AGENT_NAME=$1
AGENT_FILE=".claude/agents/${AGENT_NAME}.md"

# Check if agent exists
if [ ! -f "$AGENT_FILE" ]; then
    echo "Error: Agent '$AGENT_NAME' not found"
    echo ""
    echo "Available agents:"
    ls .claude/agents/*.md | xargs -I {} basename {} .md | sed 's/^/  - /'
    exit 1
fi

# Get agent description
DESCRIPTION=$(grep -m1 "^description:" "$AGENT_FILE" | cut -d'"' -f2 || echo "No description")
echo "Launching agent: $AGENT_NAME"
echo "Description: $DESCRIPTION"
echo ""

# If initial message provided, use it
if [ -n "$2" ]; then
    shift
    MESSAGE="$@"
    echo "Sending message: $MESSAGE"
    echo ""
    
    # Create a prompt that references the agent
    echo "$MESSAGE

Please use the $AGENT_NAME agent to help with this." | claude chat
else
    # Interactive mode - instruct user how to use the agent
    echo "Starting Claude chat..."
    echo "To use the agent, type: 'Use the $AGENT_NAME agent' or reference it in your request"
    echo ""
    claude chat
fi
