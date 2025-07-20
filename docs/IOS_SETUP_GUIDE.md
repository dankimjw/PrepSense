# iOS Setup Guide for PrepSense

This guide helps you set up your development environment to run the PrepSense iOS app.

## Prerequisites

Before you can run the iOS app, you need to install the following tools:

### 1. Xcode (macOS only)
- **Required for**: iOS Simulator
- **Download**: Mac App Store (free, ~8GB)
- **Setup**:
  ```bash
  # Install Xcode Command Line Tools
  xcode-select --install
  
  # Verify installation
  xcodebuild -version
  ```
- **Important**: Open Xcode at least once to accept the license agreement

### 2. Node.js and npm
- **Required for**: JavaScript package management
- **Download**: https://nodejs.org/ (LTS version recommended)
- **Alternative installation** (using Homebrew):
  ```bash
  brew install node
  ```
- **Verify installation**:
  ```bash
  node --version
  npm --version
  ```

### 3. Expo CLI
- **Required for**: Running the React Native app
- **Installation**:
  ```bash
  npm install -g expo-cli
  ```
- **Verify installation**:
  ```bash
  expo --version
  ```

### 4. Watchman (Recommended)
- **Purpose**: File watching for hot reload
- **Installation**:
  ```bash
  brew install watchman
  ```

### 5. Expo Go App (for physical device testing)
- **iOS**: https://apps.apple.com/app/expo-go/id982107779
- **Android**: https://play.google.com/store/apps/details?id=host.exp.exponent

## Setting Up Environment Variables

Before running the app, you need to create a `.env` file:

```bash
# From project root
cp .env.template .env
```

Then edit the `.env` file with your API keys and database credentials:
```bash
# Open in your preferred editor
nano .env  # or vim .env, or open in VS Code
```

## Running the iOS App

### Option 1: Using run_app.py (Recommended)
```bash
# From project root
source venv/bin/activate
python run_app.py  # Runs both backend and iOS app
```

### Option 2: Manual Setup (if run_app.py doesn't work)
```bash
# Terminal 1: Start backend
cd backend_gateway
source ../venv/bin/activate  # Activate virtual environment
python main.py

# Terminal 2: Start iOS app
cd ios-app
npm install  # First time only
npm start

# When Expo starts, press 'i' to open iOS simulator
```

## Common Issues and Solutions

### Issue: "xcrun: error: unable to find utility"
**Solution**: Install Xcode Command Line Tools
```bash
xcode-select --install
sudo xcode-select --switch /Applications/Xcode.app
```

### Issue: "Metro bundler can't find module"
**Solution**: Clear cache and reinstall
```bash
cd ios-app
rm -rf node_modules
npm cache clean --force
npm install
npx expo start -c  # Clear cache
```

### Issue: Simulator not starting
**Solution**: 
1. Open Xcode > Preferences > Locations
2. Ensure Command Line Tools is set
3. Try opening Simulator manually first: `open -a Simulator`

### Issue: "Network response timed out"
**Solution**: Your backend isn't running or IP is wrong
1. Check backend is running: `curl http://localhost:8001/api/v1/health`
2. Update API_URL in ios-app/.env with your machine's IP

## Troubleshooting Checklist

Before asking for help, please verify:

- [ ] Xcode is installed and opened at least once
- [ ] Command Line Tools are installed (`xcode-select -p` shows a path)
- [ ] Node.js and npm are installed (`node -v` and `npm -v` work)
- [ ] You've run `npm install` in the ios-app directory
- [ ] Backend is running (`curl http://localhost:8001/api/v1/health` returns data)
- [ ] You've checked the error message on Google/StackOverflow
- [ ] You've tried the relevant solution from Common Issues above

## Learning Resources

### Official Documentation
- **Expo**: https://docs.expo.dev/
- **React Native**: https://reactnative.dev/docs/getting-started
- **Xcode**: https://developer.apple.com/xcode/

### Troubleshooting Guides
- **Expo Troubleshooting**: https://docs.expo.dev/troubleshooting/overview/
- **React Native Troubleshooting**: https://reactnative.dev/docs/troubleshooting

### Video Tutorials
- **React Native Crash Course**: https://www.youtube.com/watch?v=0-S5a0eXPoc
- **Expo Basics**: https://www.youtube.com/watch?v=0-S5a0eXPoc

## Getting Help with Setup

### Self-Help Resources (Try These First!)

1. **Error Messages**: Copy and paste the exact error into Google
2. **Video Tutorials**: Sometimes seeing it done helps more than reading
3. **AI Assistants**: ChatGPT and Claude are excellent for setup help
4. **This Guide**: Most common issues are covered above

### When to Ask for Help

It's totally fine to ask for help! Here's how to do it effectively:

**Good timing**: After you've tried the common solutions above

**Include these details**:
- What step you're on
- The exact error message
- What you've already tried
- Your operating system version

**Example of a good help request**:
> "I'm trying to install Expo CLI on macOS 13.2. When I run `npm install -g expo-cli`, I get 'EACCES permission denied'. I tried using sudo but got the same error. I also tried the npx method from the Expo docs. Any ideas?"

### Building Skills Together

Remember, everyone starts somewhere! The setup process is a great opportunity to:
- Practice troubleshooting
- Learn to read documentation
- Get comfortable with developer tools

Don't be discouraged if it takes longer than expected. Once you're set up, you'll have learned valuable skills that apply to any development project.

### Manual Environment Setup

If automated setup isn't working, here's how to do it manually:

1. **Create .env file**:
   ```bash
   cd /Users/danielkim/_Capstone/PrepSense
   cp .env.template .env
   ```

2. **Edit .env file** with your credentials:
   - Database password: Ask your team lead
   - OpenAI API key: https://platform.openai.com/api-keys
   - Spoonacular API key: https://spoonacular.com/food-api

3. **Verify .env location**:
   - Must be in project root: `/Users/danielkim/_Capstone/PrepSense/.env`
   - NOT in backend_gateway folder

### Team Support

We're all here to help each other succeed. If you're stuck:
1. Check if someone else had the same issue in the team chat
2. Share what you've tried so others can learn too
3. Once you solve it, help the next person with the same issue

Together, we can make sure everyone gets their development environment working!

## Quick Commands Reference

```bash
# Check all prerequisites
which xcodebuild && which npm && which expo && echo "✅ All prerequisites installed!"

# Start everything
python run_app.py

# Start only iOS (if backend is already running)
python run_app.py --ios

# Clean restart
cd ios-app && rm -rf node_modules && npm install && cd .. && python run_app.py

# Check backend health
curl http://localhost:8001/api/v1/health
```

Last updated: 2025-01-19