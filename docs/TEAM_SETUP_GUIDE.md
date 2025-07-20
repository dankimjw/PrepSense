# PrepSense Team Setup Guide

## Prerequisites - Install These First

### 1. Xcode & iOS Simulator

**Required for running the iOS app**

- Download and install Xcode from the Mac App Store (free)
- Link: https://apps.apple.com/us/app/xcode/id497799835
- **Size**: ~15GB, so start this download first!
- After installation, open Xcode once to complete setup and install additional components

### 2. Node.js & npm

**Required for the React Native frontend**

- Download Node.js (LTS version) from: https://nodejs.org/
- This includes npm (Node Package Manager)
- **Verify installation**: Open Terminal and run:

  ```bash
  node --version
  npm --version
  ```

### 3. Python 3.8-3.12

**Required for the FastAPI backend**

- Download from: https://www.python.org/downloads/
- **IMPORTANT**: Use Python 3.8, 3.9, 3.10, 3.11, or 3.12 (Python 3.13 is NOT supported yet)
- Make sure to check "Add Python to PATH" during installation
- **Verify installation**: 

  ```bash
  python3 --version
  pip3 --version
  ```

### 4. Git

**Required for cloning the repository**

- Download from: https://git-scm.com/download/mac
- Or install via Homebrew: `brew install git`

## Getting Started

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/PrepSense.git
cd PrepSense
```

### Step 2: Get Your API Keys

#### OpenAI API Key (REQUIRED)

1. Go to: https://platform.openai.com/api-keys
2. Sign up/login to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. **Important**: Save this key securely - you won't see it again!

#### Spoonacular API Key (REQUIRED)

1. Go to: https://spoonacular.com/food-api
2. Sign up for a free account
3. Go to your dashboard and copy your API key
4. **Free tier**: 150 requests per day (sufficient for testing)

### Step 3: Environment Configuration

1. **Get the `.env` file from the team** (ask Daniel for the complete file)
   - Save it as `.env` in the project root directory
   - This file contains all database credentials pre-configured

2. **Update YOUR personal settings in the `.env` file**:

   ```bash
   # Replace with your actual Spoonacular API key
   SPOONACULAR_API_KEY=your_actual_spoonacular_key_here
   
   # Choose a unique demo user ID (to avoid conflicts with teammates)
   DEMO_USER_ID=john-2  # or jane-3, bob-4, etc.
   ```

3. **Create the OpenAI key file**:

   ```bash
   mkdir -p config
   echo "your_openai_api_key_here" > config/openai_key.txt
   ```

### Step 4: Create Virtual Environment

**IMPORTANT**: Use Python 3.8-3.12 (NOT Python 3.13)

```bash
# Check your Python version first
python3 --version

# If you have Python 3.13, use a specific version instead:
# python3.12 -m venv venv
# python3.11 -m venv venv
# python3.10 -m venv venv
# python3.9 -m venv venv

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows
```

### Step 5: Run Setup Script

```bash
# Make sure your virtual environment is activated first!
python setup.py
```

Choose option 1 to install all dependencies.

This will:
- Create config/ and logs/ directories
- Install Python dependencies from requirements.txt
- Install Node.js dependencies for the iOS app
- Show you the manual setup instructions

### Step 6: Run the Application

```bash
# Make sure your virtual environment is still activated
python run_app.py
```

This will:
- Start the FastAPI backend server on port 8001
- Automatically launch the iOS Simulator
- Open the PrepSense app in the simulator

## What Each Script Does

### `setup.py`

- **Purpose**: One-time installation of dependencies
- **What it does**:
  - Creates config/ and logs/ directories
  - Installs Python dependencies from `requirements.txt`
  - Installs frontend dependencies (`npm install` in `ios-app/`)
  - Shows manual setup instructions for environment configuration

### `run_app.py`

- **Purpose**: Daily development workflow - starts the complete app
- **What it does**:
  - Activates Python virtual environment
  - Starts FastAPI backend server on port 8001
  - Detects your computer's IP address
  - Configures iOS app to connect to your local backend
  - Launches iOS Simulator
  - Starts the React Native app in the simulator

## Troubleshooting

### Python Version Issues

- **"greenlet" installation fails**: You're using Python 3.13 which isn't supported yet
  - Solution: Use Python 3.8-3.12 instead
  - Check version: `python3 --version`
  - Create venv with specific version: `python3.12 -m venv venv`

### Virtual Environment Issues

- **"Not in a virtual environment" error**: 
  - Activate your venv first: `source venv/bin/activate`
  - Check if activated: Your terminal prompt should show `(venv)`

### Database Connection Issues

- **Connection refused**: Check your `.env` file has the correct database credentials
- **Authentication failed**: Make sure you're using the password from the team's `.env` template

### iOS Simulator Issues

- **Simulator won't open**: Make sure Xcode is installed and opened at least once
- **App won't load**: Check that the backend is running (you should see logs in Terminal)
- **Network errors**: Verify your computer's IP address in the Terminal output

### Backend Issues

- **Port 8001 in use**: Kill existing processes: `sudo lsof -ti:8001 | xargs kill -9`
- **Import errors**: Make sure virtual environment is activated: `source venv/bin/activate`

### API Key Issues

- **OpenAI errors**: Verify your key is in `config/openai_key.txt` and has billing enabled
- **Spoonacular errors**: Check your API key in `.env` file and that you haven't exceeded daily limit

### Environment Variables Check

**Make sure your `.env` file includes:**
- `SPOONACULAR_API_KEY` - Your personal API key
- `DEMO_USER_ID` - Your unique ID (e.g., john-2, jane-3)
- Database credentials (should be pre-filled in the template)

**Make sure `config/openai_key.txt` contains:**
- Your OpenAI API key (starts with `sk-`)

## Demo User IDs

To avoid conflicts when multiple people are testing:

- `samantha-1` (default)
- `john-2`
- `jane-3` 
- `bob-4`
- `mike-5`
- `sarah-6`

Each person should use a different DEMO_USER_ID in their `.env` file.

## What You'll See

Once everything is running:

1. **Terminal**: Backend server logs showing API requests
2. **iOS Simulator**: PrepSense app with pantry management interface
3. **Features to test**:
   - Add items to pantry
   - Scan receipts (use sample images in `tests/test_images/`)
   - Get recipe recommendations
   - Chat with AI about recipes
   - View nutrition information
   - Quick Complete recipes

## Quick Start Summary

1. **Clone the repo**
2. **Get `.env` file from Daniel** (has database credentials)
3. **Add your API keys**:
   - Spoonacular key in `.env`
   - OpenAI key in `config/openai_key.txt`
   - Choose unique `DEMO_USER_ID` in `.env`
4. **Create & activate virtual environment** (Python 3.8-3.12 only!):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. **Run setup**: `python setup.py` (choose option 1)
6. **Run app**: `python run_app.py`

## Getting Help

- **Setup issues**: Make sure you're using Python 3.8-3.12 and have activated your venv
- **Missing `.env` file**: Ask Daniel for the complete template with database credentials
- **API key issues**: Make sure you've added your personal keys as instructed
- **General questions**: Check the main `README.md`

## Important Security Notes

- **Never commit credentials**: The `.env` file and `config/` folder are gitignored
- **Don't share API keys**: Keep your OpenAI and Spoonacular keys private
- **API Costs**: OpenAI charges per request - be mindful during testing
- **Database**: Shared instance - use your unique DEMO_USER_ID to avoid conflicts

## Daily Workflow

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. **Start the app**:
   ```bash
   python run_app.py
   ```

3. **Before committing**: 
   - Don't commit `.env` or `config/` files
   - Check `git status` to ensure no sensitive files

---

Last updated: January 20, 2025
Contact: Daniel Kim for `.env` template and project access
