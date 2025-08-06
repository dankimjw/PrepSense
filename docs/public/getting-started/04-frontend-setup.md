# 📱 Frontend Setup (Node.js & Expo)

[← Previous: Backend Setup](./03-backend-setup.md) | [Back to Main Guide](../README.md) | [Next: Running the App →](./05-running-app.md)

## 🎯 Overview

Now we'll set up the React Native frontend using Expo. This is what users see on their phones!

**⚠️ Important:** Keep your backend running in its terminal. Open a **new terminal** for the frontend.

## 🆕 Step 1: Open a New Terminal

1. Keep your backend terminal running
2. Open a new terminal window/tab
3. Navigate to the project:
   ```bash
   cd ~/projects/PrepSense
   ```

## 📱 Step 2: Navigate to Frontend Directory

```bash
cd ios-app
```

## 📦 Step 3: Install Frontend Dependencies

### Clean Install (Recommended for First Time)
```bash
# Remove any existing installations
rm -rf node_modules package-lock.json

# Install all dependencies
npm install
```

This installs:
- **React Native**: Mobile app framework
- **Expo**: Development platform
- **React Navigation**: Screen navigation
- **And many more!**

### Verify Installation
```bash
# Check node modules were created
ls node_modules

# See all installed packages
npm list --depth=0
```

## 🔧 Step 4: Frontend Configuration

### Check for Environment Configuration
```bash
# Look for config files
ls -la | grep -E "config|env"
```

### API Endpoint Configuration
Check if there's an API configuration file:
```bash
# Look in services or config directories
cat services/api.ts 2>/dev/null || cat config/api.js 2>/dev/null
```

You might need to update the API endpoint to point to your backend:
- Development: `http://localhost:8000`
- Production: Your deployed backend URL

## 📲 Step 5: Set Up iOS Simulator (macOS Only)

### Start iOS Simulator
```bash
# Open Simulator app
open -a Simulator
```

### Choose a Device
1. In Simulator menu: Device → iOS → iPhone 15 (or any model)
2. Wait for it to boot completely

### Troubleshooting Simulator
If Simulator won't open:
1. Open Xcode first
2. Go to Xcode → Settings → Platforms
3. Make sure iOS is installed

## 📱 Step 6: Install Expo Go on Physical Device (Alternative)

If you prefer testing on your actual phone:

1. **iPhone**: [App Store - Expo Go](https://apps.apple.com/us/app/expo-go/id982107779)
2. **Android**: [Google Play - Expo Go](https://play.google.com/store/apps/details?id=host.exp.exponent)

Make sure your phone and computer are on the **same Wi-Fi network**!

## 🚀 Step 7: Start the Expo Development Server

### Run Expo
```bash
# Make sure you're in ios-app directory
npm start

# Or use Expo directly
npx expo start
```

### What You'll See
```
› Metro waiting on exp://192.168.1.100:8081
› Scan the QR code with Expo Go (Android) or Camera (iOS)

› Press a │ open Android
› Press i │ open iOS simulator
› Press w │ open web

› Press j │ open debugger
› Press r │ reload app
› Press m │ toggle menu
```

## 📱 Step 8: Launch the App

### Option A: iOS Simulator (macOS)
- Press `i` in the terminal
- Wait for the app to build and launch

### Option B: Physical Device
1. Open Expo Go app on your phone
2. Scan the QR code shown in terminal
3. Wait for the app to load

### Option C: Android Emulator
- Press `a` in the terminal
- (Requires Android Studio setup)

## ✅ Step 9: Verify Everything Works

You should see:
1. The PrepSense app loading screen
2. A login or home screen
3. No red error screens!

### Test Basic Functionality
1. Try navigating between screens
2. Check if images load
3. Verify connection to backend (if login exists, try logging in)

## 🔄 Development Workflow

### Making Changes
1. Edit code in your editor
2. Save the file
3. The app automatically reloads!

### Useful Expo Commands
- `r` - Reload the app
- `m` - Toggle developer menu
- `j` - Open Chrome debugger
- `Ctrl+C` - Stop Expo

## 🛠️ Common Frontend Issues

### "Unable to resolve module"
```bash
# Clear cache and reinstall
npm start -- --clear
rm -rf node_modules
npm install
```

### "Network request failed"
- Check backend is running
- Verify API endpoint in code
- Check if on same network (physical device)

### Build Errors
```bash
# Clear all caches
npx expo start -c

# Or reset everything
rm -rf node_modules .expo
npm install
npx expo start
```

### Metro bundler issues
```bash
# Kill any existing Metro processes
killall node

# Restart
npm start
```

## 📁 Understanding Frontend Structure

```
ios-app/
├── app/               # Screen components
│   ├── (tabs)/       # Tab navigation screens
│   ├── (auth)/       # Authentication screens
│   └── index.tsx     # Entry point
├── components/        # Reusable UI components
├── services/         # API calls
├── context/          # Global state management
├── assets/           # Images, fonts
└── package.json      # Dependencies
```

## 💡 Development Tips

### Hot Reloading
- Changes appear instantly
- If not working, press `r` to reload

### Developer Menu
- Shake device or press `m` in terminal
- Access debugging tools

### Console Logs
- View in terminal
- Or Chrome debugger (press `j`)

## ✅ Frontend Setup Complete!

Congratulations! You now have:
- ✅ Backend running (previous terminal)
- ✅ Frontend running (this terminal)
- ✅ App loaded on simulator/device

**Next: Learn how to run everything together efficiently!**

---

[← Previous: Backend Setup](./03-backend-setup.md) | [Back to Main Guide](../README.md) | [Next: Running the App →](./05-running-app.md)