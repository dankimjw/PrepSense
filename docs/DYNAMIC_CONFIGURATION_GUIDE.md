# Dynamic Configuration Guide for PrepSense Team Development

## Overview

PrepSense is designed to work across different team members' machines without hardcoding IP addresses, ports, or credentials. This guide explains how the dynamic configuration works and what needs to be customized per team member.

## What Should Be Dynamic (Not Hardcoded)

### 1. **IP Addresses** 🌐
- **Problem**: Your computer's IP changes when you switch networks
- **Solution**: `run_app.py` automatically detects your current IP
- **Never**: Hardcode IPs like `192.168.1.196` in code

### 2. **Ports** 🔌
- **Backend Port**: Configurable (default: 8001)
- **iOS Port**: Configurable (default: 8082)
- **Override**: Use `--port` and `--ios-port` flags

### 3. **Database Credentials** 🔐
- **Per Team Member**: Each person may have different database passwords
- **Location**: `.env` file (never commit this!)
- **Required**:
  - `POSTGRES_HOST`: GCP SQL instance IP
  - `POSTGRES_DATABASE`: Database name
  - `POSTGRES_USER`: Your database user
  - `POSTGRES_PASSWORD`: Your password (get from team lead)

### 4. **API Keys** 🔑
- **Per Developer**: Each person should use their own API keys
- **Required**:
  - `OPENAI_API_KEY`: Your OpenAI key
  - `SPOONACULAR_API_KEY`: Your Spoonacular key
- **Optional**:
  - `UNSPLASH_ACCESS_KEY`: For image features
  - `GOOGLE_APPLICATION_CREDENTIALS`: For GCP services

## How Dynamic Configuration Works

### Automatic IP Detection

```python
# run_app.py automatically does this:
1. Detects your current LAN IP address
2. Sets EXPO_PUBLIC_API_BASE_URL environment variable
3. iOS app reads this to connect to backend
```

### The Flow

```
┌─────────────────┐
│   run_app.py    │
│                 │
│ 1. Detect IP    │──────► Your IP: 192.168.x.x
│ 2. Start backend│
│ 3. Start iOS    │──────► Sets EXPO_PUBLIC_API_BASE_URL
└─────────────────┘                    │
                                      ▼
                              ┌──────────────┐
                              │   iOS App    │
                              │              │
                              │ Reads env var│
                              │ Connects to  │
                              │   backend    │
                              └──────────────┘
```

## Common Issues & Solutions

### Issue 1: "Network request timed out"
**Cause**: Your IP address changed (switched WiFi, etc.)
**Fix**: 
1. Stop the app (Ctrl+C)
2. Run `python run_app.py` again

### Issue 2: "Cannot connect to backend"
**Cause**: Backend not running or wrong port
**Fix**:
1. Check if backend is running: `ps aux | grep uvicorn`
2. Check port 8001 is free: `lsof -i :8001`
3. Restart with: `python run_app.py`

### Issue 3: "Database connection failed"
**Cause**: Wrong credentials in .env
**Fix**:
1. Check `.env` file exists
2. Verify `POSTGRES_PASSWORD` is correct (not placeholder)
3. Ask team lead for correct password

## Team Development Setup

### For Each Team Member:

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd PrepSense
   ```

2. **Create your `.env` file**
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

3. **Never commit `.env`**
   - It's in `.gitignore` for a reason
   - Contains personal API keys and passwords

4. **Always start with `run_app.py`**
   ```bash
   source venv/bin/activate
   python run_app.py
   ```

## Configuration Files

### 1. `.env` (Personal - Don't Commit!)
```env
# Database (same for all team members)
POSTGRES_HOST=<your-cloud-sql-ip>
POSTGRES_DATABASE=prepsense
POSTGRES_USER=<your-database-user>
POSTGRES_PASSWORD=<your-password-here>  # Get from team lead

# API Keys (use your own)
OPENAI_API_KEY=sk-your-key-here
SPOONACULAR_API_KEY=your-key-here
```

### 2. `ios-app/config.ts` (Shared - Commit)
```typescript
// Never hardcode IPs here!
const DEV_API_CONFIG = {
  baseURL: ENV_API_URL || 'http://127.0.0.1:8001/api/v1',
  timeout: 10000,
};
```

### 3. `run_app.py` (Shared - Commit)
- Handles all dynamic configuration
- Detects IPs automatically
- Sets up environment for iOS app

## Best Practices

### ✅ DO:
- Use `run_app.py` to start the app
- Keep your `.env` file updated
- Use your own API keys
- Report issues if IP detection fails

### ❌ DON'T:
- Hardcode IP addresses anywhere
- Commit `.env` files
- Share API keys
- Manually set `EXPO_PUBLIC_API_BASE_URL`

## Debugging Dynamic Configuration

### Check Current Configuration:
```bash
# See your current IP
python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0])"

# Check if backend is running
curl http://localhost:8001/api/v1/health

# Check environment variables
echo $EXPO_PUBLIC_API_BASE_URL
```

### iOS App Console:
Look for these messages:
```
✅ OK - API URL: http://192.168.x.x:8001/api/v1
⚠️  WARNING - EXPO_PUBLIC_API_BASE_URL not set
❌ ERROR - Backend not reachable
```

## Advanced Configuration

### Custom Ports:
```bash
# Use different backend port
python run_app.py --port 9000

# Use different iOS port
python run_app.py --ios-port 8090

# Both
python run_app.py --port 9000 --ios-port 8090
```

### Backend Only:
```bash
python run_app.py --backend
```

### iOS Only (with custom backend):
```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8001/api/v1
python run_app.py --ios
```

## Summary

The key principle: **Nothing specific to your machine should be hardcoded**. Everything that changes between team members or network environments must be:
1. Read from environment variables
2. Detected automatically at runtime
3. Configurable via command-line options

This ensures the same codebase works for everyone without modifications!