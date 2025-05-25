import subprocess
import os
import sys
import socket
import platform
import signal
from pathlib import Path
from typing import Optional, List

from run_server import DEFAULT_HOST, DEFAULT_PORT, kill_processes_on_port


def _get_local_ip(fallback: str = DEFAULT_HOST) -> str:
    """Best-effort attempt to discover this machine's LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return fallback

def main():
    # Get the project root directory (where this file is located)
    project_root = Path(__file__).parent.absolute()
    ios_app_dir = project_root / "ios-app"
    
    if not ios_app_dir.exists():
        print("Error: ios-app directory not found")
        sys.exit(1)
    
    # Change to the ios-app directory
    os.chdir(ios_app_dir)

    # Determine backend URL from run_server configuration
    host = os.getenv("SERVER_HOST", DEFAULT_HOST)
    port = os.getenv("SERVER_PORT", str(DEFAULT_PORT))

    # If host is not explicitly provided or is a wildcard/localhost,
    # use a best-effort guess for the machine's IP so the mobile
    # simulator/physical device can reach the backend.
    if host in {"0.0.0.0", "127.0.0.1", "localhost"}:
        host_ip = _get_local_ip()
    else:
        host_ip = host

    backend_url = f"http://{host_ip}:{port}/v1"

    print(f"Using backend at {backend_url}")

    # Pass the backend URL to the Expo app via environment variable
    os.environ["EXPO_PUBLIC_API_BASE_URL"] = backend_url

    # Common ports used by Expo/React Native
    expo_ports = [19000, 19001, 19002, 19006, 8081]
    
    print("Checking for existing Expo/metro processes...")
    for port in expo_ports:
        if kill_processes_on_port(port):
            print(f"Successfully terminated processes on port {port}")
    
    print("\nStarting iOS app...")
    print("Press Ctrl+C to stop the app")
    
    try:
        # Run expo start with clear cache and environment variables
        subprocess.run(["npx", "expo", "start", "-c"], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting iOS app: {e}")
        print("Trying to clean up any remaining processes...")
        for port in expo_ports:
            kill_processes_on_port(port)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Cleaning up any remaining processes...")
        for port in expo_ports:
            kill_processes_on_port(port)
        sys.exit(1)

if __name__ == "__main__":
    main()
