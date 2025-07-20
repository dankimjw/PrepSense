# Sunday Meeting App Setup Guide

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

### 3. Python 3.9+
**Required for the FastAPI backend**
- Download from: https://www.python.org/downloads/
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
1. Copy the template file:
   ```bash
   cp .env.template .env
   ```

2. Edit the `.env` file and replace the following:
   ```bash
   # Replace YOUR_SPOONACULAR_API_KEY_HERE with your actual key
   SPOONACULAR_API_KEY=your_actual_spoonacular_key_here
   
   # Choose a unique demo user ID (to avoid conflicts with teammates)
   DEMO_USER_ID=john-2  # or jane-3, bob-4, etc.
   ```

3. Create the OpenAI key file:
   ```bash
   mkdir -p config
   echo "your_openai_api_key_here" > config/openai_key.txt
   ```

### Step 4: Run Setup Script
```bash
python setup.py
```
This will:
- Create Python virtual environment
- Install Python dependencies
- Install Node.js dependencies for iOS app
- Set up database connections
- Verify all configurations

### Step 5: Run the Application
```bash
python run_app.py
```
This will:
- Start the FastAPI backend server
- Automatically launch the iOS Simulator
- Open the PrepSense app in the simulator

## What Each Script Does

### `setup.py`
- **Purpose**: One-time setup of the development environment
- **What it does**:
  - Creates Python virtual environment (`venv/`)
  - Installs backend dependencies from `requirements.txt`
  - Installs frontend dependencies (`npm install` in `ios-app/`)
  - Validates environment configuration
  - Tests database connectivity
  - Verifies API keys are working

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

### iOS Simulator Issues
- **Simulator won't open**: Make sure Xcode is installed and opened at least once
- **App won't load**: Check that the backend is running (you should see logs in Terminal)
- **Network errors**: Verify your computer's IP address in the Terminal output

### Backend Issues
- **Port 8001 in use**: Kill existing processes: `sudo lsof -ti:8001 | xargs kill -9`
- **Database connection failed**: Check your internet connection (database is hosted on Google Cloud)
- **Import errors**: Make sure virtual environment is activated: `source venv/bin/activate`

### API Key Issues
- **OpenAI errors**: Verify your key is in `config/openai_key.txt` and has billing enabled
- **Spoonacular errors**: Check your API key in `.env` file and that you haven't exceeded daily limit

### Quick Health Check
Run this command to verify everything is working:
```bash
python check_app_health.py
```

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

## Getting Help
- **Setup issues**: Check `docs/troubleshooting.md`
- **App not working**: Run `python check_app_health.py` for diagnostics
- **General questions**: Ask Daniel or check the `README.md`

## Important Notes
- **Database**: Shared Google Cloud SQL instance - all data is persistent across team members
- **API Costs**: OpenAI charges per request - be mindful of usage during testing
- **Git**: Don't commit your `.env` file - it contains your API keys!
- **Performance**: First app launch may be slow as it downloads dependencies

---

Last updated: January 20, 2025