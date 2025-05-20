import subprocess
import os
import sys
from pathlib import Path

from run_server import DEFAULT_HOST, DEFAULT_PORT

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
    backend_url = f"http://{host}:{port}/v1"

    # Pass the backend URL to the Expo app via environment variable
    os.environ["EXPO_PUBLIC_API_BASE_URL"] = backend_url

    print("Starting iOS app...")
    print("Press Ctrl+C to stop the app")
    
    try:
        # Run expo start with clear cache and environment variables
        subprocess.run(["npx", "expo", "start", "-c"], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting iOS app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
