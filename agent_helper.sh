#!/bin/bash

# Claude Code Agent Helper Script

cd /Users/danielkim/_Capstone/PrepSense

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Claude Code Agent Launcher ===${NC}"
echo ""

# Function to list agents
list_agents() {
    echo -e "${YELLOW}Available agents:${NC}"
    echo ""
    for agent in .claude/agents/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent" .md)
            description=$(grep -m1 "^description:" "$agent" | cut -d'"' -f2 || echo "No description")
            echo -e "  ${GREEN}${agent_name}${NC}"
            echo "    ${description}"
            echo ""
        fi
    done
}

# Function to launch agent
launch_agent() {
    agent_name=$1
    shift
    message="$@"
    
    if [ -f ".claude/agents/${agent_name}.md" ]; then
        echo -e "${GREEN}Launching agent: ${agent_name}${NC}"
        echo ""
        
        # Try different command variations
        echo "Attempting: claude chat --agent ${agent_name}"
        if [ -n "$message" ]; then
            echo "$message" | claude chat --agent "${agent_name}" 2>&1
        else
            claude chat --agent "${agent_name}" 2>&1
        fi
        
        # If that fails, try without --agent flag
        if [ $? -ne 0 ]; then
            echo ""
            echo "Attempting: claude agent ${agent_name}"
            if [ -n "$message" ]; then
                echo "$message" | claude agent "${agent_name}" 2>&1
            else
                claude agent "${agent_name}" 2>&1
            fi
        fi
        
        # If that fails too, try with full path
        if [ $? -ne 0 ]; then
            echo ""
            echo "Attempting: claude chat --agent .claude/agents/${agent_name}.md"
            if [ -n "$message" ]; then
                echo "$message" | claude chat --agent ".claude/agents/${agent_name}.md" 2>&1
            else
                claude chat --agent ".claude/agents/${agent_name}.md" 2>&1
            fi
        fi
    else
        echo -e "${YELLOW}Agent not found: ${agent_name}${NC}"
        echo "Use 'list' to see available agents"
    fi
}

# Main logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 [command] [agent-name] [message]"
    echo ""
    echo "Commands:"
    echo "  list              - List all available agents"
    echo "  run <agent>       - Run an agent interactively"
    echo "  msg <agent> <msg> - Send a message to an agent"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 run hello-world-agent"
    echo "  $0 msg code-writer \"Create a Python function to sort a list\""
    exit 1
fi

case "$1" in
    list)
        list_agents
        ;;
    run)
        if [ -z "$2" ]; then
            echo "Please specify an agent name"
            exit 1
        fi
        launch_agent "$2"
        ;;
    msg)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Please specify an agent name and message"
            exit 1
        fi
        agent=$2
        shift 2
        launch_agent "$agent" "$@"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use 'list', 'run', or 'msg'"
        exit 1
        ;;
esac
