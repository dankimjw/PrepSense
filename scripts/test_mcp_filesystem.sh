#!/bin/bash

# Script to test MCP filesystem functionality across all instances

echo "🧪 Testing MCP Filesystem Server Functionality"
echo "============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_mcp_in_directory() {
    local dir=$1
    local name=$2
    
    echo -e "\n📍 Testing in $name: $dir"
    
    if [ ! -f "$dir/.mcp.json" ]; then
        echo -e "  ${RED}❌ No .mcp.json found${NC}"
        return
    fi
    
    # Check if filesystem server is configured
    if grep -q "filesystem" "$dir/.mcp.json"; then
        echo -e "  ${GREEN}✅ Filesystem server configured in .mcp.json${NC}"
        
        # Check the configuration details
        echo "  📋 Configuration:"
        jq '.mcpServers.filesystem' "$dir/.mcp.json" 2>/dev/null | sed 's/^/     /'
    else
        echo -e "  ${RED}❌ Filesystem server NOT configured${NC}"
    fi
}

# Main execution
MAIN_REPO="/Users/danielkim/_Capstone/PrepSense"
WORKTREES_DIR="/Users/danielkim/_Capstone/PrepSense-worktrees"

# Test main repository
test_mcp_in_directory "$MAIN_REPO" "Main repository"

# Test worktrees
for worktree in "$WORKTREES_DIR"/*; do
    if [ -d "$worktree" ] && [ "$worktree" != "$WORKTREES_DIR/PrepSense-worktrees" ]; then
        worktree_name=$(basename "$worktree")
        test_mcp_in_directory "$worktree" "Worktree: $worktree_name"
    fi
done

# Check running MCP processes
echo -e "\n🔍 Currently running MCP filesystem processes:"
ps aux | grep -E "mcp-server-filesystem" | grep -v grep | while read line; do
    pid=$(echo $line | awk '{print $2}')
    args=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
    echo -e "  ${YELLOW}PID $pid:${NC} $args"
done

echo -e "\n⚠️  ${YELLOW}Important Notes:${NC}"
echo "  1. The filesystem server should use '--root .' to work in the current directory"
echo "  2. If you see '--root /Users/...' it's using an absolute path (incorrect)"
echo "  3. After fixing .mcp.json, restart Claude Code in each directory"
echo "  4. Each Claude instance needs its own filesystem server process"