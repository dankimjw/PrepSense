#!/usr/bin/env bash
# MCP Health Check - Quick verification of MCP server status
# This script is designed to be integrated into existing health check workflows

set -euo pipefail

# Colors for output
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
END='\033[0m'

# Required MCP servers
REQUIRED_SERVERS=("filesystem" "memory" "sequential-thinking" "context7" "ios-simulator" "mobile" "postgres")

printf "${BOLD}🔍 MCP Server Health Check${END}\n"
printf "================================\n\n"

# Check if claude mcp command is available
if ! command -v claude >/dev/null 2>&1; then
    printf "${RED}✗ Claude CLI not found${END}\n"
    exit 1
fi

# Get list of registered MCP servers
printf "${BLUE}📡 Checking registered MCP servers...${END}\n"
if ! mcp_output=$(claude mcp list 2>/dev/null); then
    printf "${RED}✗ Failed to get MCP server list${END}\n"
    exit 1
fi

# Check each required server
all_healthy=true
healthy_count=0
total_count=${#REQUIRED_SERVERS[@]}

for server in "${REQUIRED_SERVERS[@]}"; do
    if echo "$mcp_output" | grep -q "$server.*Connected"; then
        printf "${GREEN}✓ $server${END} - Connected\n"
        ((healthy_count++))
    elif echo "$mcp_output" | grep -q "$server"; then
        printf "${YELLOW}⚠ $server${END} - Registered but not connected\n"
        all_healthy=false
    else
        printf "${RED}✗ $server${END} - Not registered\n"
        all_healthy=false
    fi
done

printf "\n"

# Summary
if [ $healthy_count -eq $total_count ] && [ "$all_healthy" = true ]; then
    printf "${GREEN}${BOLD}✅ All MCP servers are healthy ($healthy_count/$total_count)${END}\n"
    printf "${GREEN}🚀 Ready for Claude sessions!${END}\n"
    exit 0
elif [ $healthy_count -gt 0 ]; then
    printf "${YELLOW}${BOLD}⚠️  Partial MCP health ($healthy_count/$total_count healthy)${END}\n"
    printf "${YELLOW}🔧 Run: python scripts/mcp_auto_manager.py --repair${END}\n"
    exit 1
else
    printf "${RED}${BOLD}❌ No MCP servers healthy (0/$total_count)${END}\n"
    printf "${RED}🔧 Run: python scripts/mcp_auto_manager.py --init${END}\n"
    exit 2
fi