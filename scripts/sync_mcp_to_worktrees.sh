#!/usr/bin/env bash
# Sync MCP configuration to all git worktrees
# This ensures all parallel development environments have the same MCP setup

set -euo pipefail

# Colors for output
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
END='\033[0m'

printf "${BOLD}🔄 Syncing MCP Configuration to Worktrees${END}\n"
printf "==========================================\n\n"

# Get main repo path
MAIN_REPO=$(git rev-parse --show-toplevel 2>/dev/null || echo "/Users/danielkim/_Capstone/PrepSense")

if [ ! -f "$MAIN_REPO/.mcp.json" ]; then
    printf "${RED}✗ Main .mcp.json not found in $MAIN_REPO${END}\n"
    printf "${YELLOW}💡 Run: python scripts/mcp_auto_manager.py --init${END}\n"
    exit 1
fi

printf "${BLUE}📁 Found main .mcp.json configuration${END}\n"

# Count synced worktrees
synced_count=0
total_count=0

# Check and sync worktrees
if command -v git >/dev/null 2>&1 && git worktree list >/dev/null 2>&1; then
    printf "${BLUE}🌳 Syncing to worktrees...${END}\n\n"
    
    # Process each worktree (skip the main repo line)
    git worktree list | tail -n +2 | while read -r line; do
        worktree_path=$(echo "$line" | awk '{print $1}')
        worktree_name=$(basename "$worktree_path")
        total_count=$((total_count + 1))
        
        printf "  📂 $worktree_name ($worktree_path)\n"
        
        if [ -d "$worktree_path" ]; then
            # Copy .mcp.json
            if cp "$MAIN_REPO/.mcp.json" "$worktree_path/.mcp.json" 2>/dev/null; then
                printf "    ${GREEN}✓ .mcp.json synced${END}\n"
                synced_count=$((synced_count + 1))
            else
                printf "    ${RED}✗ Failed to copy .mcp.json${END}\n"
            fi
            
            # Also copy the MCP auto-manager script if it doesn't exist
            if [ -f "$MAIN_REPO/scripts/mcp_auto_manager.py" ] && [ ! -f "$worktree_path/scripts/mcp_auto_manager.py" ]; then
                mkdir -p "$worktree_path/scripts"
                if cp "$MAIN_REPO/scripts/mcp_auto_manager.py" "$worktree_path/scripts/mcp_auto_manager.py" 2>/dev/null; then
                    printf "    ${GREEN}✓ MCP auto-manager synced${END}\n"
                fi
            fi
        else
            printf "    ${RED}✗ Worktree directory not found${END}\n"
        fi
        printf "\n"
    done
else
    printf "${YELLOW}ℹ️  No git worktrees found${END}\n"
fi

printf "${BOLD}📊 Sync Summary${END}\n"
printf "================\n"
printf "Worktrees synced: ${GREEN}$synced_count${END}/$total_count\n"

if [ $synced_count -gt 0 ]; then
    printf "${GREEN}✅ MCP configuration synced successfully!${END}\n"
    printf "${BLUE}💡 Each worktree can now use: python scripts/mcp_auto_manager.py --check${END}\n"
else
    printf "${YELLOW}⚠️  No worktrees were synced${END}\n"
fi