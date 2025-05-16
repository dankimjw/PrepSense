import uvicorn
import os
import sys
from pathlib import Path

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
    host = "0.0.0.0"  # Allow external connections
    port = 8001       # Use port 8001
    reload = True     # Enable auto-reload for development
    
    print(f"Starting server on {host}:{port}")
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