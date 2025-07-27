#!/bin/bash
# Script to run MCP mobile automation tests

# Ensure test results directory exists
mkdir -p /Users/danielkim/_Capstone/PrepSense/test_results

# Start the backend if not running
echo "Checking backend status..."
if ! curl -s http://localhost:8006/api/v1/health > /dev/null; then
    echo "Starting backend..."
    cd /Users/danielkim/_Capstone/PrepSense
    source venv/bin/activate
    python run_app.py &
    sleep 5
fi

# Example of running tests with Claude Code
echo "Running MCP mobile automation tests..."
echo "Use these commands in Claude Code to execute tests:"
echo ""
echo "# Basic navigation test"
echo "mcp__mobile__mobile_use_default_device"
echo "mcp__mobile__mobile_launch_app packageName='host.exp.Exponent'"
echo "mcp__mobile__mobile_take_screenshot"
echo ""
echo "# Test quick actions"
echo "mcp__mobile__mobile_click_on_screen_at_coordinates x=67 y=343  # Scan Items"
echo "mcp__mobile__mobile_take_screenshot"
echo "mcp__mobile__mobile_click_on_screen_at_coordinates x=36 y=170  # Back"
echo ""
echo "# Test search"
echo "mcp__mobile__mobile_click_on_screen_at_coordinates x=220 y=142  # Search field"
echo "mcp__mobile__mobile_type_keys text='apple' submit=false"
echo ""
echo "# Save results"
echo "mcp__mobile__mobile_save_screenshot saveTo='/Users/danielkim/_Capstone/PrepSense/test_results/test_screenshot.png'"