# PrepSense Unified App Launcher

This unified launcher simplifies running both the backend server and iOS app with synchronized IP configuration.

## What's New

The `run_app.py` script replaces the separate `run_server.py` and `run_ios.py` files by:

- **Unified IP Management**: Both backend and frontend use the same IP configuration
- **Automatic Process Cleanup**: Cleans up existing processes on required ports
- **Coordinated Startup**: Backend starts first, then iOS app connects to it
- **Graceful Shutdown**: Properly handles Ctrl+C and cleans up all processes
- **Environment Variable Support**: Configurable via environment variables

## Quick Start

### Option 1: Simple Script (Recommended)
```bash
./start.sh
```

### Option 2: Direct Python
```bash
python3 run_app.py
```

## Configuration

You can customize the setup using environment variables:

```bash
# Backend configuration
export SERVER_HOST="0.0.0.0"        # Default: 127.0.0.1
export SERVER_PORT="8001"            # Default: 8001

# iOS app configuration  
export IOS_PORT="8082"               # Default: 8082

# Then run the launcher
python3 run_app.py
```

## How It Works

1. **🧹 Cleanup Phase**:
   - Terminates any existing processes on backend and iOS ports
   - Cleans up common Expo/Metro bundler ports (19000, 19001, 19002, 19006, 8081)
   - Verifies all ports are available

2. **🔧 Backend Startup**:
   - Starts the FastAPI backend server using uvicorn
   - Uses the configured host and port
   - Enables auto-reload for development

3. **📱 iOS App Startup**:
   - Automatically detects the local IP address
   - Sets `EXPO_PUBLIC_API_BASE_URL` to point to the backend
   - Starts the Expo development server on the configured port
   - iOS app connects to backend using the same IP

4. **🔗 IP Synchronization**:
   - If backend host is `127.0.0.1`, `localhost`, or `0.0.0.0`, the script auto-detects your local IP
   - iOS app is configured to use this same IP to connect to the backend
   - No more IP mismatches between frontend and backend!

## Default Configuration

- **Backend**: `127.0.0.1:8001`
- **iOS App**: `localhost:8082` 
- **Backend URL for iOS**: `http://{local_ip}:8001/api/v1`

## Stopping the App

Press `Ctrl+C` to stop both services. The script will:
- Gracefully shut down the backend server
- Stop the iOS development server
- Clean up all spawned processes
- Release all used ports

## Troubleshooting

### Port Already in Use
The launcher automatically handles port conflicts by terminating existing processes. If you see persistent port issues:

```bash
# Manual cleanup
lsof -ti :8001 | xargs kill -9  # Backend port
lsof -ti :8082 | xargs kill -9  # iOS port
```

### Backend Not Starting
Check that you're in a Python virtual environment with the required dependencies:

```bash
# Activate your virtual environment first
source venv/bin/activate  # or your venv path

# Install dependencies
pip install -r requirements.txt

# Then run the launcher
python3 run_app.py
```

### iOS App Can't Connect to Backend
The launcher automatically configures the iOS app with the correct backend URL. If connection issues persist:

1. Check that both services are running
2. Verify the IP address shown in the launcher output
3. Check firewall settings if using a physical device

## Migration from Old Scripts

If you were using the separate scripts before:

- **Instead of**: `python3 run_server.py` → **Use**: `python3 run_app.py`
- **Instead of**: `python3 run_ios.py` → **Use**: The new launcher handles both
- **Environment variables**: Same as before, just use the unified launcher

## Features

✅ **Automatic IP Detection**: No manual IP configuration needed  
✅ **Process Management**: Handles cleanup and startup automatically  
✅ **Environment Support**: Configurable via environment variables  
✅ **Graceful Shutdown**: Proper cleanup on exit  
✅ **Development Ready**: Auto-reload and development features enabled  
✅ **Cross-Platform**: Works on macOS, Linux, and Windows  

## Example Output

```
🚀 PrepSense Unified App Launcher
==================================================
📡 Detected local IP: 192.168.1.100
📊 Backend will run on: 127.0.0.1:8001
📱 iOS app will run on: http://localhost:8082
🔗 iOS app will connect to backend: http://192.168.1.100:8001/api/v1

🧹 Cleaning up existing processes...
✅ All ports cleaned up successfully

🔧 Starting backend server...
⏳ Waiting for backend to initialize...
✅ Backend server is running

📱 Starting iOS app...
```

This unified approach ensures your backend and frontend always use compatible IP configurations for seamless development!
