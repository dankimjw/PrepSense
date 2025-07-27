#!/usr/bin/env python3
"""
Smart app launcher that automatically finds available ports.
Perfect for Claude instances to avoid interrupting the main development instance.
"""

import subprocess
import socket
import sys
import time
from pathlib import Path

def find_available_port(start_port=8001, max_attempts=10):
    """Find the next available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return None

def check_main_instance_running(port=8001):
    """Check if the main instance is running on default port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('127.0.0.1', port))
            return True
        except (ConnectionRefusedError, OSError):
            return False

def main():
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("❌ Not running inside a virtual environment. Activate it first:")
        print("   source venv/bin/activate && python3 run_app_smart.py")
        sys.exit(1)
    
    # Check if main instance is running
    if check_main_instance_running():
        print("✅ Main instance detected on port 8001")
        print("🔍 Finding available ports for Claude instance...")
        
        # Find available backend port
        backend_port = find_available_port(8002)
        if not backend_port:
            print("❌ No available backend ports found (8002-8011)")
            sys.exit(1)
        
        # Find available iOS port
        ios_port = find_available_port(8083)
        if not ios_port:
            print("❌ No available iOS ports found")
            sys.exit(1)
        
        print(f"🚀 Starting Claude instance on ports: backend={backend_port}, ios={ios_port}")
        print("📝 This won't interrupt the main development instance")
        
        # Add a delay to make it clear this is a secondary instance
        time.sleep(2)
        
        # Run with found ports and backend-only mode by default
        cmd = [
            sys.executable,
            "run_app.py",
            "--backend",  # Backend only for testing
            "--port", str(backend_port),
            "--ios-port", str(ios_port)
        ]
        
        # Pass through any additional arguments
        if len(sys.argv) > 1:
            # Remove --backend if user explicitly wants both or ios
            if "--ios" in sys.argv or "--both" in sys.argv:
                cmd.remove("--backend")
            cmd.extend(sys.argv[1:])
        
        print(f"💻 Running command: {' '.join(cmd)}")
        print("-" * 50)
        
    else:
        print("ℹ️  No main instance detected, using default ports")
        cmd = [sys.executable, "run_app.py"] + sys.argv[1:]
    
    # Execute the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Claude instance stopped")

if __name__ == "__main__":
    main()