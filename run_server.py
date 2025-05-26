"""Starts the FastAPI dev server with optional port cleanup."""

import uvicorn
import os
import sys
import signal
import platform
import time
from pathlib import Path
import subprocess
from typing import Optional, List
import socket

# Default host and port for the development server
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001

def kill_processes_on_port(port: int, host: str = '0.0.0.0') -> bool:
    """Kill processes running on the specified port.
    
    Args:
        port: The port number to check
        host: The host to check (default: 0.0.0.0)
        
    Returns:
        bool: True if any processes were killed, False otherwise
    """
    killed_any = False
    max_attempts = 2  # Number of times to try killing processes
    
    for attempt in range(1, max_attempts + 1):
        try:
            if platform.system() == 'Windows':
                # Find process using the port on Windows
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
                            # First try normal termination
                            subprocess.run(['taskkill', '/F', '/PID', pid], 
                                         check=True, 
                                         stderr=subprocess.PIPE)
                            print(f"Killed process with PID {pid} on port {port}")
                            killed_any = True
                            # Add small delay to allow OS to release the port
                            time.sleep(1)
                        except subprocess.CalledProcessError as e:
                            if attempt == max_attempts:
                                print(f"Failed to kill process {pid} on attempt {attempt}: {e}")
                            continue
            else:
                # Find process using the port on Unix-like systems
                try:
                    # Try lsof first
                    result = subprocess.run(
                        ['lsof', '-i', f'tcp:{port}'], 
                        capture_output=True, 
                        text=True
                    )
                except FileNotFoundError:
                    # If lsof is not available, try ss
                    try:
                        result = subprocess.run(
                            ['ss', '-tulpn'],
                            capture_output=True,
                            text=True
                        )
                    except FileNotFoundError:
                        print("Neither lsof nor ss is available. Cannot check for processes.")
                        return False
                
                lines = result.stdout.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and f":{port} " in line:
                        parts = line.split()
                        if len(parts) > 1:
                            # Get PID differently based on command
                            if 'lsof' in result.args[0]:
                                pid = parts[1]
                            else:  # ss command
                                pid = parts[6].split('=')[-1].rstrip(')')
                            
                            try:
                                # First try graceful termination
                                os.kill(int(pid), signal.SIGTERM)
                                # Give it a moment to shut down
                                time.sleep(1)
                                # Then force kill if still running
                                try:
                                    os.kill(int(pid), 0)  # Check if process exists
                                    os.kill(int(pid), signal.SIGKILL)
                                    print(f"Force killed process with PID {pid}")
                                except (ProcessLookupError, OSError):
                                    pass  # Process already terminated
                                
                                print(f"Killed process with PID {pid} on port {port}")
                                killed_any = True
                                # Add small delay to allow OS to release the port
                                time.sleep(1)
                            except (ProcessLookupError, OSError) as e:
                                if attempt == max_attempts:
                                    print(f"Failed to kill process {pid}: {e}")
                                continue
                
                # Additional check using lsof for any remaining processes
                try:
                    subprocess.run(
                        ['lsof', '-ti', f'tcp:{port}'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                except FileNotFoundError:
                    pass
        except Exception as e:
            if attempt == max_attempts:
                print(f"Error checking for processes on port {port}: {e}")
            continue
        
        # If we killed something, try one more time to catch any child processes
        if killed_any and attempt < max_attempts:
            time.sleep(2)  # Give some time for the OS to clean up
            continue
            
    return killed_any

def main():
    # Get the project root directory (where this file is located)
    project_root = Path(__file__).parent.absolute()
    
    # Add the project root to Python path if needed
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("Warning: Not running in a virtual environment. It's recommended to use one.")
    
    # Configuration
    # Allow overriding the host and port via environment variables, but
    # default to the values defined above for local development.
    host = os.getenv("SERVER_HOST", DEFAULT_HOST)
    port = int(os.getenv("SERVER_PORT", DEFAULT_PORT))
    reload = True  # Enable auto-reload for development
    
    print(f"Checking for processes on {host}:{port}...")
    if kill_processes_on_port(port, host):
        print("Successfully terminated existing processes")
        # Give the OS a moment to clean up
        time.sleep(2)
    else:
        print("No conflicting processes found")
    
    # Final check to ensure port is available
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((host, port))
        test_socket.close()
    except OSError as e:
        print(f"Port {port} is still in use. Please check for any remaining processes.")
        sys.exit(1)
    
    print(f"\nStarting server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            "backend_gateway.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
