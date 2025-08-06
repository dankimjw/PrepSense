# 🔧 Troubleshooting Guide

[← Previous: Running the App](./05-running-app.md) | [Back to Main Guide](../README.md) | [Next: Helpful Resources →](./07-resources.md)

## 🎯 Overview

Don't panic! This guide covers the most common issues and their solutions. We've all been there!

## 🐍 Python/Backend Issues

### Issue: "Python command not found"
```bash
# Try these alternatives:
python3 --version
py --version  # Windows
python --version
```

**Solution:**
- Make sure Python is installed
- Add Python to your PATH
- Restart your terminal

### Issue: "No module named 'fastapi'"
**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Symptoms:**
```
ERROR: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Find what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux

# Or use a different port
uvicorn app:app --port 8001
```

### Issue: "Google Cloud credentials not found"
**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError
```

**Solutions:**
1. Get service account key from team
2. Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```
3. Add to `.env` file

## 📱 React Native/Frontend Issues

### Issue: "Metro bundler can't find module"
**Symptoms:**
```
Unable to resolve module 'x' from 'y'
```

**Solutions:**
```bash
# Clear everything and reinstall
rm -rf node_modules
rm package-lock.json
npm install

# Clear Metro cache
npx expo start -c
```

### Issue: "Invariant Violation: Module AppRegistry is not registered"
**Solutions:**
```bash
# Kill all Node processes
killall node  # macOS/Linux
taskkill /f /im node.exe  # Windows

# Restart Expo
npm start
```

### Issue: "Network request failed"
**Symptoms:**
- App can't connect to backend
- API calls fail

**Solutions:**
1. Check backend is running
2. Verify API URL in frontend code:
```javascript
// Should be for local development:
const API_URL = 'http://localhost:8000'
// or
const API_URL = 'http://192.168.1.x:8000' // Your IP
```
3. For physical devices, use your computer's IP, not localhost

### Issue: "Expo Go keeps crashing"
**Solutions:**
1. Update Expo Go app
2. Clear Expo cache:
```bash
expo start -c
```
3. Check for incompatible packages:
```bash
expo doctor
```

## 🔗 Git Issues

### Issue: "Permission denied (publickey)"
**Solutions:**
1. Set up SSH keys:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub
# Add this key to GitHub settings
```

2. Or use HTTPS instead:
```bash
git remote set-url origin https://github.com/username/repo.git
```

### Issue: "Failed to push some refs"
**Solutions:**
```bash
# Pull latest changes first
git pull origin main

# If conflicts, resolve them, then:
git add .
git commit -m "Resolved conflicts"
git push
```

## 💻 Platform-Specific Issues

### macOS Issues

#### "xcrun: error: invalid active developer path"
**Solution:**
```bash
xcode-select --install
```

#### Simulator won't open
**Solutions:**
1. Open Xcode first
2. Accept license agreements
3. Download iOS simulators in Xcode settings

### Windows Issues

#### "Scripts cannot be executed on this system"
**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Path issues with backslashes
**Solution:**
- Use forward slashes in code: `path/to/file`
- Or use `path.join()` in Node.js

### Linux Issues

#### Permission denied errors
**Solutions:**
```bash
# For global npm packages
sudo npm install -g expo-cli

# Or use a Node version manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

## 🔍 Debugging Techniques

### Backend Debugging

1. **Check logs in terminal**
2. **Use FastAPI docs**: http://localhost:8000/docs
3. **Add print statements**:
```python
print(f"Debug: variable = {variable}")
```
4. **Check error responses**:
```python
import traceback
try:
    # code
except Exception as e:
    print(f"Error: {str(e)}")
    print(traceback.format_exc())
```

### Frontend Debugging

1. **Console logs**:
```javascript
console.log('Debug:', variable);
```

2. **React Native Debugger**:
   - Press `j` in Expo terminal
   - Opens Chrome DevTools

3. **Check network requests**:
```javascript
fetch(url)
  .then(res => {
    console.log('Response:', res);
    return res.json();
  })
  .catch(err => console.error('Error:', err));
```

## 🚨 Emergency Fixes

### "Everything is broken!"

1. **Stop everything**:
```bash
# Kill all processes
killall node python uvicorn
```

2. **Clean everything**:
```bash
# Backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ios-app
rm -rf node_modules .expo
npm install
```

3. **Start fresh**:
```bash
# Terminal 1: Backend
cd backend_gateway
uvicorn app:app --reload

# Terminal 2: Frontend
cd ios-app
expo start -c
```

### Still not working?

1. **Check versions**:
```bash
python3 --version  # Should be 3.8+
node --version     # Should be 18+
npm --version      # Should be 8+
```

2. **Check network**:
   - Are you connected to internet?
   - Is firewall blocking connections?
   - Are backend and frontend on same network?

3. **Ask for help**:
   - Screenshot the error
   - Share terminal output
   - Check if others had same issue

## 📋 Troubleshooting Checklist

When something goes wrong:

1. ✅ Is the error message clear? Read it carefully
2. ✅ Did you save all files?
3. ✅ Is virtual environment activated? (backend)
4. ✅ Are all dependencies installed?
5. ✅ Are both backend and frontend running?
6. ✅ Did you check the logs in both terminals?
7. ✅ Did you try restarting everything?
8. ✅ Is your code up to date with git?

## 💡 Prevention Tips

1. **Always activate venv** before working on backend
2. **Keep dependencies updated** but test after updates
3. **Commit working code** before major changes
4. **Read error messages** completely
5. **Check logs** in both terminals
6. **Test incrementally** after each change

## 🆘 Getting More Help

If you're still stuck:

1. **Search the error message** on Google
2. **Check Stack Overflow**
3. **Look at GitHub issues** for the libraries
4. **Ask your team** with:
   - Clear error description
   - What you tried
   - Screenshots/logs
   - Your environment details

Remember: Every developer faces these issues. You're not alone!

---

[← Previous: Running the App](./05-running-app.md) | [Back to Main Guide](../README.md) | [Next: Helpful Resources →](./07-resources.md)