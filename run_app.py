#!/usr/bin/env python3
"""
Unified launcher for PrepSense backend server and iOS app.
This script ensures both the backend and frontend use the same IP configuration.

Usage:
    python3 run_app.py            # Start both backend and iOS app (default)
    python3 run_app.py --backend  # Start backend server only
    python3 run_app.py --ios      # Start iOS app only
    python3 run_app.py --help     # Show help
"""

import uvicorn
import os

# --- Start of environment variable cleanup ---
# List of environment variables to unset to prevent conflicts with .env file
VARIABLES_TO_UNSET = [
    'BIGQUERY_PROJECT',  # Should come from .env or pydantic settings
    'PORT',              # Should be set by the script or use default
    # Add other variables here if needed
]

for var in VARIABLES_TO_UNSET:
    if var in os.environ:
        print(f"run_app.py: Found {var} in shell environment: {os.getenv(var)}")
        print(f"run_app.py: Unsetting {var} to prioritize .env or default config values.")
        del os.environ[var]
        # On Unix-like systems, also remove from os.environ.mapping
        if hasattr(os.environ, 'mapping') and var in os.environ.mapping:
            del os.environ.mapping[var]
# --- End of environment variable cleanup ---
import sys
import signal
import platform
import time
import subprocess
import threading
import atexit
import argparse
from pathlib import Path
from typing import Optional, List
import socket
from dotenv import load_dotenv

# Default configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_BACKEND_PORT = 8001
DEFAULT_IOS_PORT = 8082

class ProcessManager:
    """Manages both backend and frontend processes"""
    
    def __init__(self):
        self.backend_process = None
        self.ios_process = None
        self.cleanup_registered = False
        
    def register_cleanup(self):
        """Register cleanup functions for graceful shutdown"""
        if not self.cleanup_registered:
            atexit.register(self.cleanup_all)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            self.cleanup_registered = True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.cleanup_all()
        sys.exit(0)
    
    def cleanup_all(self):
        """Clean up all processes"""
        print("Cleaning up processes...")
        
        # Stop iOS process
        if self.ios_process and self.ios_process.poll() is None:
            try:
                self.ios_process.terminate()
                self.ios_process.wait(timeout=5)
                print("iOS app stopped")
            except subprocess.TimeoutExpired:
                self.ios_process.kill()
                print("iOS app force killed")
            except Exception as e:
                print(f"Error stopping iOS app: {e}")
        
        # Clean up expo ports
        expo_ports = [19000, 19001, 19002, 19006, 8081, DEFAULT_IOS_PORT]
        for port in expo_ports:
            kill_processes_on_port(port)

def kill_processes_on_port(port: int, host: str = '0.0.0.0') -> bool:
    """Kill processes running on the specified port.
    
    Args:
        port: The port number to check
        host: The host to check (default: 0.0.0.0)
        
    Returns:
        bool: True if any processes were killed, False otherwise
    """
    killed_any = False
    max_attempts = 2
    
    for attempt in range(1, max_attempts + 1):
        try:
            if platform.system() == 'Windows':
                # Windows implementation
                result = subprocess.run(
                    ['netstat', '-ano', '-p', 'tcp'], 
                    capture_output=True, 
                    text=True
                )
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port} " in line and (f"{host}:" in line or '0.0.0.0' in line):
                        parts = line.split()
                        pid = parts[-1]
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], 
                                         check=True, 
                                         stderr=subprocess.PIPE)
                            print(f"Killed process with PID {pid} on port {port}")
                            killed_any = True
                            time.sleep(1)
                        except subprocess.CalledProcessError:
                            pass
            else:
                # Unix/Linux/macOS implementation
                try:
                    # Find processes using lsof
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'], 
                        capture_output=True, 
                        text=True,
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid.strip():
                                try:
                                    # Try SIGTERM first
                                    subprocess.run(['kill', '-TERM', pid.strip()], 
                                                 check=True, 
                                                 stderr=subprocess.PIPE)
                                    print(f"Terminated process with PID {pid.strip()} on port {port}")
                                    killed_any = True
                                except subprocess.CalledProcessError:
                                    try:
                                        # If SIGTERM fails, use SIGKILL
                                        subprocess.run(['kill', '-KILL', pid.strip()], 
                                                     check=True, 
                                                     stderr=subprocess.PIPE)
                                        print(f"Force killed process with PID {pid.strip()} on port {port}")
                                        killed_any = True
                                    except subprocess.CalledProcessError:
                                        pass
                        
                        if killed_any:
                            time.sleep(1.5)
                except FileNotFoundError:
                    # lsof not available, try alternative
                    pass
                    
        except Exception as e:
            print(f"Error in attempt {attempt} to kill processes on port {port}: {e}")
        
        if not killed_any:
            break
    
    return killed_any

def get_local_ip(fallback: str = DEFAULT_HOST) -> str:
    """Best-effort attempt to discover this machine's LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return fallback

def check_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((host, port))
        test_socket.close()
        return True
    except OSError:
        return False

def start_backend_server(host: str, port: int, reload: bool = True):
    """Start the backend server using uvicorn"""
    print(f"Starting backend server on {host}:{port}")
    try:
        from backend_gateway.app import app
        uvicorn.run(
            "backend_gateway.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        print(f"Backend server error: {e}")
        raise

def start_ios_app_subprocess(backend_url: str, ios_port: int, project_root: Path):
    """Start the iOS app as a subprocess"""
    ios_app_dir = project_root / "ios-app"
    
    if not ios_app_dir.exists():
        raise FileNotFoundError("ios-app directory not found")
    
    try:
        # Set environment variables for the iOS app
        env = os.environ.copy()
        env["EXPO_PUBLIC_API_BASE_URL"] = backend_url
        
        print(f"Starting iOS app on port {ios_port} with backend: {backend_url}")
        
        # Start the iOS app as subprocess
        process = subprocess.Popen([
            "npm", "start", "--", "--port", str(ios_port)
        ], cwd=ios_app_dir, env=env)
        
        return process
        
    except Exception as e:
        print(f"Error starting iOS app: {e}")
        raise

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PrepSense App Launcher - Launch backend and/or iOS app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 run_app.py                # Start both services (default)
    python3 run_app.py --backend      # Backend server only
    python3 run_app.py --ios          # iOS app only
    python3 run_app.py --backend --port 8002  # Backend on custom port
        
Environment Variables:
    LAUNCH_MODE     Launch mode: both, backend, ios (default: both)
    HOST           Backend host (default: 0.0.0.0)
    PORT           Backend port (default: 8001)  
    IOS_PORT       iOS app port (default: 8082)
        """
    )
    
    parser.add_argument(
        '--backend', 
        action='store_true',
        help='Start backend server only'
    )
    
    parser.add_argument(
        '--ios', 
        action='store_true',
        help='Start iOS app only'
    )
    
    parser.add_argument(
        '--port', 
        type=int,
        help='Override backend port (same as PORT env var)'
    )
    
    parser.add_argument(
        '--host', 
        type=str,
        help='Override backend host (same as HOST env var)'
    )
    
    parser.add_argument(
        '--ios-port', 
        type=int,
        help='Override iOS app port (same as IOS_PORT env var)'
    )
    
    return parser.parse_args()

def main():
    """Main function to coordinate backend and frontend startup"""
    print("🚀 PrepSense Unified App Launcher")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Add the project root to Python path if needed
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Load environment variables from .env FIRST
    load_dotenv()
    
    # Set up Google Cloud credentials path if not already set or if the current path doesn't exist
    current_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    credentials_path = project_root / "config" / "adsp-34002-on02-prep-sense-ef1111b0833b.json"
    
    if not current_creds or not Path(current_creds).exists():
        if credentials_path.exists():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
            print(f"📋 Set Google credentials path: {credentials_path}")
        else:
            print("⚠️  Google credentials file not found, running in development mode")
    else:
        print(f"📋 Using existing Google credentials path: {current_creds}")
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("⚠️  Warning: Not running in a virtual environment. It's recommended to use one.")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Configuration from environment variables and command line arguments
    backend_host = args.host or os.getenv("HOST", DEFAULT_HOST)
    backend_port = args.port or int(os.getenv("PORT", DEFAULT_BACKEND_PORT))
    ios_port = args.ios_port or int(os.getenv("IOS_PORT", DEFAULT_IOS_PORT))
    
    # Determine launch mode from command line args or environment variable
    if args.backend and args.ios:
        mode = "both"
    elif args.backend:
        mode = "backend"
    elif args.ios:
        mode = "ios"
    else:
        # Fall back to environment variable or default to "both"
        mode = os.getenv("LAUNCH_MODE", "both")  # both, backend, ios
    
    # Determine the IP to use
    if backend_host in {"0.0.0.0", "127.0.0.1", "localhost"}:
        host_ip = get_local_ip()
        print(f"📡 Detected local IP: {host_ip}")
    else:
        host_ip = backend_host
    
    backend_url = f"http://{host_ip}:{backend_port}/api/v1"
    
    if mode in ["both", "backend"]:
        print(f"📊 Backend will run on: {backend_host}:{backend_port}")
    if mode in ["both", "ios"]:
        print(f"📱 iOS app will run on: http://localhost:{ios_port}")
        print(f"🔗 iOS app will connect to backend: {backend_url}")
    print()
    
    # Initialize process manager
    process_manager = ProcessManager()
    process_manager.register_cleanup()
    
    # Clean up any existing processes
    print("🧹 Cleaning up existing processes...")
    
    # Backend port
    if mode in ["both", "backend"]:
        if kill_processes_on_port(backend_port, backend_host):
            print(f"✅ Cleaned up backend port {backend_port}")
            time.sleep(2)
    
    # iOS/Expo ports
    if mode in ["both", "ios"]:
        expo_ports = [19000, 19001, 19002, 19006, 8081, ios_port]
        for port in expo_ports:
            if kill_processes_on_port(port):
                print(f"✅ Cleaned up port {port}")
    
    # Verify ports are available
    if mode in ["both", "backend"]:
        if not check_port_available(backend_host, backend_port):
            print(f"❌ Backend port {backend_port} is still in use. Please check for remaining processes.")
            sys.exit(1)
    
    print("✅ All ports cleaned up successfully")
    print()
    
    try:
        if mode == "ios":
            # iOS only mode
            print("📱 Starting iOS app only...")
            ios_process = start_ios_app_subprocess(backend_url, ios_port, project_root)
            process_manager.ios_process = ios_process
            ios_process.wait()
            
        elif mode == "backend":
            # Backend only mode
            print("🔧 Starting backend server only...")
            start_backend_server(backend_host, backend_port, True)
            
        else:
            # Both services (default)
            print("📱 Starting iOS app...")
            ios_process = start_ios_app_subprocess(backend_url, ios_port, project_root)
            process_manager.ios_process = ios_process
            
            # Give iOS app time to start
            print("⏳ Waiting for iOS app to initialize...")
            time.sleep(3)
            
            print("🔧 Starting backend server...")
            # Backend runs in main thread to avoid signal issues
            start_backend_server(backend_host, backend_port, True)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        process_manager.cleanup_all()
        print("👋 PrepSense app launcher stopped")

if __name__ == "__main__":
    main()
