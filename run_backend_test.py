#!/usr/bin/env python3
"""
Quick backend test runner for Claude instances.
Automatically finds available port and runs backend only.
"""

import subprocess
import socket
import sys
import requests
import time

def find_available_port(start_port=8002):
    """Find next available port."""
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return None

def wait_for_backend(port, timeout=30):
    """Wait for backend to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/api/v1/health")
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    if sys.prefix == sys.base_prefix:
        print("❌ Not in virtual environment. Run: source venv/bin/activate")
        sys.exit(1)
    
    # Find available port
    port = find_available_port()
    if not port:
        print("❌ No available ports found")
        sys.exit(1)
    
    print(f"🧪 Starting test backend on port {port}")
    print("📝 Your main instance remains unaffected")
    
    # Start backend with mock data enabled
    cmd = [
        sys.executable,
        "run_app.py",
        "--backend",
        "--port", str(port),
        "-mock"  # Enable mock data for testing
    ]
    
    # Add any additional arguments
    cmd.extend(sys.argv[1:])
    
    print(f"\n💻 Command: {' '.join(cmd)}")
    print(f"🔗 Backend URL: http://127.0.0.1:{port}/api/v1")
    print(f"📚 Swagger UI: http://127.0.0.1:{port}/docs")
    print("-" * 50)
    
    try:
        # Start the backend
        process = subprocess.Popen(cmd)
        
        # Wait for it to be ready
        print("\n⏳ Waiting for backend to start...")
        if wait_for_backend(port):
            print("✅ Backend is ready!")
            print(f"\n🧪 Test endpoints:")
            print(f"   curl http://127.0.0.1:{port}/api/v1/health")
            print(f"   curl http://127.0.0.1:{port}/api/v1/pantry/items")
            print(f"\n📊 Mock data is enabled for testing")
            print("\nPress Ctrl+C to stop the test backend")
            
            # Keep running
            process.wait()
        else:
            print("❌ Backend failed to start")
            process.terminate()
            
    except KeyboardInterrupt:
        print("\n🛑 Test backend stopped")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main()