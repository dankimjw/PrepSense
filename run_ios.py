import subprocess
import os
import sys
from pathlib import Path

def main():
    # Get the project root directory (where this file is located)
    project_root = Path(__file__).parent.absolute()
    ios_app_dir = project_root / "ios-app"
    
    if not ios_app_dir.exists():
        print("Error: ios-app directory not found")
        sys.exit(1)
    
    # Change to the ios-app directory
    os.chdir(ios_app_dir)
    
    print("Starting iOS app...")
    print("Press Ctrl+C to stop the app")
    
    try:
        # Run expo start with clear cache
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