#!/usr/bin/env python3
"""
Start the PrepSense backend server
"""

import subprocess
import sys
import os
import time

def start_backend():
    """Start the backend server with proper environment"""
    
    print("🚀 Starting PrepSense Backend Server...")
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        print("❌ Virtual environment not found. Please run setup.py first.")
        return
    
    # Prepare the command
    cmd = [
        sys.executable,  # Use current Python interpreter
        "-m", "uvicorn",
        "backend_gateway.app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ]
    
    print(f"📍 Running: {' '.join(cmd)}")
    print("📱 Backend will be available at: http://localhost:8000")
    print("📊 API docs available at: http://localhost:8000/docs")
    print("\n✋ Press Ctrl+C to stop the server\n")
    
    try:
        # Start the server
        process = subprocess.Popen(cmd, env=os.environ.copy())
        process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping backend server...")
        process.terminate()
        time.sleep(1)
        if process.poll() is None:
            process.kill()
        print("✅ Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

if __name__ == "__main__":
    start_backend()