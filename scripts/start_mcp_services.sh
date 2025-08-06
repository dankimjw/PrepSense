#!/bin/bash

# MCP Services Startup Script
# This script ensures all MCP servers are running and available

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/mcp"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if a process is running
is_running() {
    local name="$1"
    pgrep -f "$name" > /dev/null 2>&1
}

# Function to start MCP server if not running
start_mcp_server() {
    local name="$1"
    local command="$2"
    local log_file="$LOG_DIR/${name}.log"
    
    if is_running "$name"; then
        echo "✅ $name is already running"
        return 0
    fi
    
    echo "🚀 Starting $name..."
    nohup $command > "$log_file" 2>&1 &
    sleep 2
    
    if is_running "$name"; then
        echo "✅ $name started successfully"
    else
        echo "❌ Failed to start $name (check $log_file)"
        return 1
    fi
}

# Function to stop MCP servers
stop_mcp_servers() {
    echo "🛑 Stopping MCP servers..."
    
    # Stop each server type
    pkill -f "mcp-server-filesystem" || true
    pkill -f "mcp-server-memory" || true
    pkill -f "mcp-server-sequential-thinking" || true
    pkill -f "context7-mcp" || true
    pkill -f "ios-simulator-mcp" || true
    pkill -f "mobile-mcp" || true
    
    echo "✅ MCP servers stopped"
}

# Function to check status of all servers
check_status() {
    echo "📊 MCP Server Status:"
    echo "-------------------"
    
    local servers=(
        "mcp-server-filesystem:Filesystem"
        "mcp-server-memory:Memory" 
        "mcp-server-sequential-thinking:Sequential Thinking"
        "context7-mcp:Context7"
        "ios-simulator-mcp:iOS Simulator"
        "mobile-mcp:Mobile"
    )
    
    for server in "${servers[@]}"; do
        IFS=':' read -ra ADDR <<< "$server"
        local process="${ADDR[0]}"
        local display="${ADDR[1]}"
        
        if is_running "$process"; then
            echo "✅ $display: Running"
        else
            echo "❌ $display: Not running"
        fi
    done
}

# Function to create launchd service (macOS)
create_launchd_service() {
    local plist_file="$HOME/Library/LaunchAgents/com.prepsense.mcp.plist"
    
    cat > "$plist_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.prepsense.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_ROOT/scripts/start_mcp_services.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/launchd.out</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/launchd.err</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>
</dict>
</plist>
EOF
    
    echo "📄 Created launchd plist: $plist_file"
    echo "🔧 To enable auto-start: launchctl load $plist_file"
    echo "🔧 To disable auto-start: launchctl unload $plist_file" 
}

# Main command handling
case "${1:-start}" in
    "start")
        echo "🚀 Starting MCP Services..."
        
        # Note: MCP servers are started by Claude Code automatically
        # when configured in .mcp.json, but we can check they're available
        
        # Verify npm packages are available
        echo "📦 Verifying npm packages..."
        npx -y @upstash/context7-mcp --help > /dev/null 2>&1 || echo "⚠️  context7-mcp may need first-time download"
        npx ios-simulator-mcp --help > /dev/null 2>&1 || echo "⚠️  ios-simulator-mcp may need first-time download"
        npx -y @mobilenext/mobile-mcp@latest --help > /dev/null 2>&1 || echo "⚠️  mobile-mcp may need first-time download"
        
        echo "✅ MCP services configuration verified"
        echo "ℹ️  MCP servers will start automatically when Claude Code connects"
        ;;
    
    "stop")
        stop_mcp_servers
        ;;
    
    "status"|"check")
        check_status
        ;;
    
    "install-service")
        create_launchd_service
        ;;
    
    "enable-service")
        launchctl load "$HOME/Library/LaunchAgents/com.prepsense.mcp.plist"
        echo "✅ MCP service enabled for auto-start"
        ;;
    
    "disable-service")
        launchctl unload "$HOME/Library/LaunchAgents/com.prepsense.mcp.plist"
        echo "✅ MCP service disabled"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|install-service|enable-service|disable-service}"
        echo ""
        echo "Commands:"
        echo "  start           - Verify MCP configuration (default)"
        echo "  stop            - Stop all MCP servers"  
        echo "  status          - Check status of MCP servers"
        echo "  install-service - Create launchd service file"
        echo "  enable-service  - Enable auto-start service"
        echo "  disable-service - Disable auto-start service"
        exit 1
        ;;
esac