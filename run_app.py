#!/usr/bin/env python3
"""
PrepSense Backend Runner
Convenient script to start the backend server or run tests
"""

import argparse
import subprocess
import sys
import os
import time
import signal
import threading

def start_backend_server(port=8000, reload=True):
    """Start the FastAPI backend server"""
    print(f"🚀 Starting PrepSense backend on port {port}...")
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "backend_gateway.app:app",
        f"--port={port}",
        "--host=0.0.0.0"
    ]
    if reload:
        cmd.append("--reload")
    
    try:
        # Ensure we run from the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n✋ Server stopped by user")

def run_ingredient_subtraction_tests():
    """Run the ingredient subtraction test suite"""
    print("🧪 Running ingredient subtraction tests...")
    
    # Start backend server in background
    server_process = None
    try:
        # Start server in a subprocess
        print("Starting backend server for tests...")
        server_cmd = [
            sys.executable, "-m", "uvicorn", 
            "backend_gateway.app:app",
            "--port=8000"
        ]
        # Get project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        server_process = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is running
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running")
            else:
                print("⚠️  Server returned status:", response.status_code)
        except:
            print("⚠️  Could not connect to server, but continuing with tests...")
        
        # Run tests - try simple test first (no external dependencies)
        test_script = os.path.join(
            os.path.dirname(__file__),
            "tests/ingredient-subtraction/simple_test.py"
        )
        
        # Fall back to full test suite if simple test doesn't exist
        if not os.path.exists(test_script):
            test_script = os.path.join(
                os.path.dirname(__file__),
                "tests/ingredient-subtraction/run_tests.py"
            )
        
        if not os.path.exists(test_script):
            print(f"❌ Test script not found at: {test_script}")
            return
        
        print("\n" + "="*80)
        print("Running test suite...")
        print("="*80 + "\n")
        
        result = subprocess.run([sys.executable, test_script])
        
        if result.returncode == 0:
            print("\n✅ Tests completed successfully!")
        else:
            print("\n❌ Tests failed with exit code:", result.returncode)
            
    except KeyboardInterrupt:
        print("\n✋ Tests interrupted by user")
    except Exception as e:
        print(f"❌ Error running tests: {e}")
    finally:
        # Stop the server
        if server_process:
            print("\nStopping test server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Test server stopped")

def reset_test_data():
    """Reset test data to initial state"""
    print("🔄 Resetting test data...")
    
    script_path = os.path.join(
        os.path.dirname(__file__),
        "backend_gateway/scripts/setup_demo_data.py"
    )
    
    if not os.path.exists(script_path):
        print(f"❌ Setup script not found at: {script_path}")
        return
    
    result = subprocess.run([sys.executable, script_path])
    
    if result.returncode == 0:
        print("✅ Test data reset successfully!")
    else:
        print("❌ Failed to reset test data")

def main():
    parser = argparse.ArgumentParser(
        description="PrepSense Backend Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_app.py                    # Start backend server
  python run_app.py --port 8080        # Start on different port
  python run_app.py --test-sub         # Run ingredient subtraction tests
  python run_app.py --reset-data       # Reset test data
        """
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    
    parser.add_argument(
        "--test-sub",
        action="store_true",
        help="Run ingredient subtraction tests"
    )
    
    parser.add_argument(
        "--reset-data",
        action="store_true",
        help="Reset test data to initial state"
    )
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.test_sub:
        # First check if requests is available
        try:
            import requests
        except ImportError:
            print("❌ 'requests' module not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--user"])
            print("✅ Installed requests module. Please run the command again.")
            return
        
        run_ingredient_subtraction_tests()
    elif args.reset_data:
        reset_test_data()
    else:
        # Default: start server
        start_backend_server(port=args.port, reload=not args.no_reload)

if __name__ == "__main__":
    main()