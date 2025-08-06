# 🚀 Running the Complete App

[← Previous: Frontend Setup](./04-frontend-setup.md) | [Back to Main Guide](../README.md) | [Next: Troubleshooting →](./06-troubleshooting.md)

## 🎯 Overview

Let's put it all together! This guide shows you how to run both backend and frontend simultaneously.

## 📋 Pre-Flight Checklist

Before starting, make sure you have:
- ✅ All tools installed ([Prerequisites](./01-prerequisites.md))
- ✅ Repository cloned ([Repository Setup](./02-repository-setup.md))
- ✅ Virtual environment created ([Backend Setup](./03-backend-setup.md))
- ✅ Node modules installed ([Frontend Setup](./04-frontend-setup.md))

## 🖥️ Terminal Setup

You'll need **at least 2 terminal windows**:
1. **Terminal 1**: Backend (Python/FastAPI)
2. **Terminal 2**: Frontend (React Native/Expo)
3. **Terminal 3** (Optional): For Git commands and general tasks

## 🔥 Step 1: Start the Backend

### In Terminal 1:
```bash
# Navigate to project
cd ~/projects/PrepSense

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Navigate to backend
cd backend_gateway

# Start the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### ✅ Backend is ready when you see:
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 🧪 Quick Backend Test:
Open browser to: `http://localhost:8000/docs`

## 📱 Step 2: Start the Frontend

### In Terminal 2:
```bash
# Navigate to frontend
cd ~/projects/PrepSense/ios-app

# Start Expo
npm start
```

### ✅ Frontend is ready when you see:
```
› Metro waiting on exp://192.168.1.100:8081
› Scan the QR code with Expo Go
```

## 📲 Step 3: Launch on Device/Simulator

### Option A: iOS Simulator (macOS)
1. Press `i` in Terminal 2
2. Wait for simulator to launch
3. App should open automatically

### Option B: Physical Device
1. Open Expo Go app
2. Scan QR code from Terminal 2
3. Wait for app to load

### Option C: Android Emulator
1. Press `a` in Terminal 2
2. Emulator launches automatically

## 🔄 Step 4: Verify Full Stack Connection

### Test the Connection:
1. Open the app
2. Try any feature that needs backend (login, view items, etc.)
3. Check Terminal 1 for API requests

### You should see in Backend terminal:
```
INFO: 127.0.0.1:58392 - "GET /api/pantry/items HTTP/1.1" 200 OK
INFO: 127.0.0.1:58392 - "POST /api/auth/login HTTP/1.1" 200 OK
```

## 🛠️ Development Workflow

### Making Backend Changes:
1. Edit Python files
2. Backend auto-reloads (you'll see in terminal)
3. Test changes via app or API docs

### Making Frontend Changes:
1. Edit React Native files
2. App auto-reloads
3. Press `r` if reload needed

### Making Full Stack Changes:
1. Update backend API
2. Update frontend to use new API
3. Test end-to-end flow

## 📝 Useful Commands Reference

### Backend Commands:
```bash
# Check API docs
open http://localhost:8000/docs

# Check backend logs
# (They appear in Terminal 1)

# Stop backend
Ctrl+C
```

### Frontend Commands:
```bash
# In Expo terminal (Terminal 2):
r - Reload app
m - Toggle menu
j - Open debugger
Ctrl+C - Stop Expo
```

### Git Commands (Terminal 3):
```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Your message"

# Push to your branch
git push origin your-branch-name
```

## 🎯 Complete Startup Script

Save time with this startup script! Create `start-app.sh`:

```bash
#!/bin/bash
# Save this as start-app.sh in project root

echo "🚀 Starting PrepSense..."

# Start backend in new terminal
osascript -e 'tell app "Terminal" to do script "cd ~/projects/PrepSense && source venv/bin/activate && cd backend_gateway && uvicorn app:app --reload"'

# Wait for backend to start
sleep 5

# Start frontend in new terminal
osascript -e 'tell app "Terminal" to do script "cd ~/projects/PrepSense/ios-app && npm start"'

echo "✅ PrepSense is starting up!"
echo "📱 Press 'i' in the Expo terminal to launch iOS simulator"
```

Make it executable:
```bash
chmod +x start-app.sh
./start-app.sh
```

## 🔍 Monitoring Your App

### Backend Monitoring:
- Watch Terminal 1 for API requests
- Check for error messages
- Monitor response times

### Frontend Monitoring:
- Watch Terminal 2 for build status
- Check for JavaScript errors
- Use React Native debugger

### Database Monitoring:
- Connect to the PostgreSQL database to verify data is being saved.

## 🛑 Shutting Down

### Proper Shutdown Order:
1. **Stop Frontend**: Press `Ctrl+C` in Terminal 2
2. **Stop Backend**: Press `Ctrl+C` in Terminal 1
3. **Deactivate venv**: Type `deactivate` in Terminal 1

## ⚡ Performance Tips

### Backend Performance:
- Use `--workers 4` for production
- Enable caching where possible
- Monitor API response times

### Frontend Performance:
- Use production builds for testing
- Enable Hermes for Android
- Profile with React DevTools

## 🎉 Success Checklist

You know everything is working when:
- ✅ Backend API docs load at http://localhost:8000/docs
- ✅ Frontend launches without errors
- ✅ App can make API calls to backend
- ✅ Data persists in database
- ✅ Images upload and process correctly

## 🆘 Quick Fixes

### "Cannot connect to backend"
- Check backend is running
- Verify API URL in frontend code
- Check firewall settings

### "Metro bundler stuck"
```bash
# Kill all node processes
killall node
# Restart
npm start
```

### "Module not found"
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

## 📚 Next Steps

Congratulations! You're now running the full PrepSense stack! 

Check out:
- [Troubleshooting Guide](./06-troubleshooting.md) for common issues
- [Helpful Resources](./07-resources.md) for learning more

---

[← Previous: Frontend Setup](./04-frontend-setup.md) | [Back to Main Guide](../README.md) | [Next: Troubleshooting →](./06-troubleshooting.md)