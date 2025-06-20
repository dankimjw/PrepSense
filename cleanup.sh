#!/bin/bash
# Simple shell version of cleanup script

echo "🧹 PrepSense Cleanup Script (Shell Version)"
echo "=========================================="

# Function to kill processes on a port
kill_port() {
    local port=$1
    echo "🔍 Checking port $port..."
    
    pids=$(lsof -t -i:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "Killing processes on port $port: $pids"
        echo $pids | xargs kill -TERM 2>/dev/null
        sleep 1
        # Force kill any remaining
        echo $pids | xargs kill -KILL 2>/dev/null
    else
        echo "No processes found on port $port"
    fi
}

# Kill processes on key ports
kill_port 8001  # Backend
kill_port 8082  # iOS app
kill_port 8083  # iOS app alternate
kill_port 19000 # Expo
kill_port 19001 # Expo
kill_port 19002 # Expo
kill_port 19006 # Expo

echo ""
echo "🔍 Killing expo/metro processes..."
pkill -f "expo start" 2>/dev/null || echo "No expo processes found"
pkill -f "metro" 2>/dev/null || echo "No metro processes found"

echo ""
echo "🔍 Killing python backend processes..."
pkill -f "start.py" 2>/dev/null || echo "No start.py processes found"
pkill -f "run_app.py" 2>/dev/null || echo "No run_app.py processes found"
pkill -f "uvicorn" 2>/dev/null || echo "No uvicorn processes found"

echo ""
echo "✅ Cleanup complete!"
echo "All PrepSense processes should now be stopped."
