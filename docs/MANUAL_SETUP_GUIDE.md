# Manual Setup Guide for PrepSense

This guide helps you set up PrepSense manually when automated scripts don't work.

## Prerequisites Check

First, verify you have the required tools installed:

```bash
# Check Python (need 3.9+)
python --version

# Check Node.js and npm
node --version
npm --version

# Check if Xcode is installed (macOS only)
xcodebuild -version

# Check if Expo is installed
expo --version
```

## Step 1: Clone the Repository

```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense
```

## Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

## Step 3: Install Backend Dependencies

```bash
# Make sure you're in the project root with venv activated
pip install -r requirements.txt
```

## Step 4: Create Environment Configuration

```bash
# Copy the template
cp .env.template .env

# Edit the file with your credentials
nano .env  # or use any text editor
```

Required values in .env:
```env
# Database Configuration (ask team lead for password)
POSTGRES_HOST=your-cloud-sql-ip-here
POSTGRES_PORT=5432
POSTGRES_DATABASE=prepsense
POSTGRES_USER=your-database-user-here
POSTGRES_PASSWORD=your-password-here

# API Keys (get your own)
OPENAI_API_KEY=sk-your-openai-key-here
SPOONACULAR_API_KEY=your-spoonacular-key-here
```

## Step 5: Install Frontend Dependencies

```bash
cd ios-app
npm install
cd ..
```

## Step 6: Start the Backend Server

```bash
# From project root with venv activated
cd backend_gateway
python main.py
```

You should see:
- Server starting on http://0.0.0.0:8001
- API docs at http://localhost:8001/docs

If you get configuration errors, double-check your .env file.

## Step 7: Start the iOS App (New Terminal)

```bash
# Open a new terminal window/tab
cd PrepSense/ios-app
npm start
```

When Expo starts:
- Press `i` to open iOS simulator
- Or scan the QR code with Expo Go app on your phone

## Common Issues and Solutions

### Issue: "Module not found" errors
```bash
# For backend
pip install -r requirements.txt

# For frontend
cd ios-app && npm install
```

### Issue: "OPENAI_API_KEY is required" error
- Make sure .env file is in project root (not in backend_gateway/)
- Check that .env contains valid API keys
- Try: `cat .env` to verify contents

### Issue: "Cannot connect to database"
- Verify you have the correct database password
- Check your internet connection (database is on Google Cloud)
- Ask team lead for current password

### Issue: iOS simulator won't start
```bash
# Kill any existing processes
killall Simulator
killall Expo

# Try starting manually
open -a Simulator
cd ios-app && npm start
```

### Issue: Port already in use
```bash
# Find what's using port 8001
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or use a different port
cd backend_gateway
python main.py --port 8002
```

## Getting Your API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to your .env file

### Spoonacular API Key
1. Go to https://spoonacular.com/food-api
2. Click "Start Now" (free tier available)
3. Sign up for an account
4. Go to your dashboard
5. Copy your API key
6. Add to your .env file

## Verifying Everything Works

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```
   Should return JSON with status "healthy"

2. **Frontend Running**:
   - iOS Simulator should open
   - App should load without errors
   - Try logging in with test credentials

## Need More Help?

If manual setup still isn't working:

1. **Double-check prerequisites** - all tools must be installed
2. **Check error messages** - they usually tell you what's wrong
3. **Ask for help** with:
   - Your operating system and version
   - The exact command you ran
   - The complete error message
   - What you've already tried

Remember: Everyone struggles with setup sometimes. It's part of learning!

Last updated: 2025-01-19