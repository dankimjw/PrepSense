# 📋 Prerequisites & Tools Installation

[← Back to Main Guide](../README.md) | [Next: Repository Setup →](./02-repository-setup.md)

## 🎯 What You'll Need

Before we start, let's make sure you have all the necessary tools installed. Don't worry if this seems overwhelming - we'll go through each one step by step!

## 💻 Operating System Requirements

This guide supports:
- **macOS** (recommended for iOS development)
- **Windows** (with some limitations for iOS)
- **Linux** (with some limitations for iOS)

## 🛠️ Required Tools

### 1. Git (Version Control)
Git helps us manage code and collaborate with teammates.

**Check if installed:**
```bash
git --version
```

**Installation:**
- **macOS**: Install via [Homebrew](https://brew.sh/) with `brew install git` or download from [git-scm.com](https://git-scm.com/)
- **Windows**: Download from [git-scm.com](https://git-scm.com/)
- **Linux**: `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (Fedora)

### 2. Python 3.8+
Our backend is built with Python.

**Check if installed:**
```bash
python3 --version
```

**Installation:**
- **All platforms**: Download from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation on Windows!

### 3. Node.js 18+ and npm
Required for our React Native frontend.

**Check if installed:**
```bash
node --version
npm --version
```

**Installation:**
- **Recommended**: Use [Node Version Manager (nvm)](https://github.com/nvm-sh/nvm) for easy version management
- **Direct download**: From [nodejs.org](https://nodejs.org/)

### 4. Expo CLI
Expo makes React Native development easier.

**Installation** (after Node.js is installed):
```bash
npm install -g expo-cli
```

### 5. iOS Simulator (macOS only)
For testing the iOS app without a physical device.

**Installation:**
1. Download [Xcode](https://apps.apple.com/us/app/xcode/id497799835) from Mac App Store (this is large, ~10GB)
2. Open Xcode once to accept licenses
3. Install additional components when prompted

### 6. Android Emulator (Optional)
For testing on Android devices.

**Installation:**
1. Download [Android Studio](https://developer.android.com/studio)
2. Follow the [React Native environment setup](https://reactnative.dev/docs/environment-setup) for Android

### 7. Expo Go App (For Physical Device Testing)
Test on your actual phone!

**Installation:**
- **iOS**: [Download from App Store](https://apps.apple.com/us/app/expo-go/id982107779)
- **Android**: [Download from Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

## 📱 Optional but Helpful Tools

### Visual Studio Code
A great code editor with Python and JavaScript support.

**Download**: [code.visualstudio.com](https://code.visualstudio.com/)

**Recommended Extensions:**
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter

### Postman
For testing API endpoints.

**Download**: [postman.com](https://www.postman.com/downloads/)

## 🔍 Verification Checklist

Run these commands to verify everything is installed:

```bash
# Check Git
git --version

# Check Python
python3 --version

# Check pip (Python package manager)
pip3 --version

# Check Node.js
node --version

# Check npm
npm --version

# Check Expo CLI
expo --version
```

## ❓ Troubleshooting Installation Issues

### "Command not found" errors
- Make sure the tool is added to your PATH
- Try restarting your terminal
- On Windows, you might need to restart your computer

### Permission errors on macOS/Linux
- Use `sudo` for global installations
- Or use a version manager (like nvm for Node.js)

### Python issues
- Make sure you're using `python3` not `python`
- On Windows, you might need to use `py` instead

## ✅ Ready to Continue?

Once you have all the tools installed, you're ready to move on to cloning the repository!

---

[← Back to Main Guide](../README.md) | [Next: Repository Setup →](./02-repository-setup.md)