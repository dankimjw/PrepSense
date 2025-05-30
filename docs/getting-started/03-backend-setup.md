# 🐍 Backend Setup (Python & FastAPI)

[← Previous: Repository Setup](./02-repository-setup.md) | [Back to Main Guide](../README.md) | [Next: Frontend Setup →](./04-frontend-setup.md)

## 🎯 Overview

We'll set up the Python backend that powers PrepSense. This includes:
- Creating a virtual environment
- Installing dependencies
- Understanding the backend structure
- Running the FastAPI server

## 🌍 Step 1: Create a Virtual Environment

A virtual environment keeps our project dependencies separate from other Python projects.

### Navigate to the Project
```bash
cd ~/projects/PrepSense  # Or wherever you cloned it
```

### Create the Virtual Environment
```bash
# Create a new virtual environment named 'venv'
python3 -m venv venv
```

### Activate the Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
# Command Prompt
venv\Scripts\activate.bat

# PowerShell
venv\Scripts\Activate.ps1
```

**🎉 Success indicator:** You should see `(venv)` at the beginning of your terminal prompt!

## 📦 Step 2: Install Backend Dependencies

### Navigate to Backend Directory
```bash
cd backend_gateway
```

### Upgrade pip (Python Package Manager)
```bash
pip install --upgrade pip
```

### Install All Requirements
```bash
pip install -r requirements.txt
```

This installs:
- **FastAPI**: Our web framework
- **Uvicorn**: Server to run FastAPI
- **Google Cloud libraries**: For BigQuery and Vision API
- **And more!**

### Verify Installation
```bash
# Check FastAPI is installed
pip show fastapi

# Check all installed packages
pip list
```

## 🔧 Step 3: Backend Configuration

### Check for Required Files
```bash
# From backend_gateway directory
ls -la
```

You should see:
- `app.py` - Main application file
- `requirements.txt` - Dependencies
- `routers/` - API endpoints
- `services/` - Business logic

### Environment Variables
Create a `.env` file if it doesn't exist:

```bash
# Create .env file
touch .env

# Open in text editor (or use your preferred editor)
nano .env
```

Add these variables (get actual values from your team):
```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=../service-account-key.json
GCP_PROJECT_ID=your-project-id

# API Keys
OPENAI_API_KEY=your-openai-key

# Database
DATABASE_URL=your-database-url

# Other settings
DEBUG=True
```

**Press `Ctrl+X`, then `Y`, then `Enter` to save and exit nano**

## 🏃 Step 4: Test the Backend

### Run the FastAPI Server
```bash
# Make sure you're in backend_gateway directory
cd ~/projects/PrepSense/backend_gateway

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### What the Command Means:
- `uvicorn`: The server program
- `app:app`: Run the `app` object from `app.py`
- `--reload`: Auto-restart when code changes
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Use port 8000

### Success Indicators
You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🧪 Step 5: Verify It's Working

### Open API Documentation
Open your web browser and go to:
```
http://localhost:8000/docs
```

You should see the **FastAPI Swagger UI** with all available endpoints!

### Test a Simple Endpoint
In another terminal (keep the server running):
```bash
# Test health check
curl http://localhost:8000/

# Or use a browser to visit http://localhost:8000/
```

## 📚 Understanding the Backend Structure

```
backend_gateway/
├── app.py              # Main FastAPI application
├── routers/            # API endpoint definitions
│   ├── auth.py        # Authentication endpoints
│   ├── pantry_router.py # Pantry management
│   ├── recipes_router.py # Recipe suggestions
│   └── ...
├── services/           # Business logic
│   ├── vision_service.py # Image recognition
│   ├── pantry_service.py # Pantry operations
│   └── ...
├── models/             # Data models
└── core/               # Core utilities
```

## 🛑 How to Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## 🔄 Daily Workflow

Every time you work on the backend:

1. **Navigate to project**
   ```bash
   cd ~/projects/PrepSense
   ```

2. **Activate virtual environment**
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Start the backend**
   ```bash
   cd backend_gateway
   uvicorn app:app --reload
   ```

## ❗ Common Issues & Solutions

### "Module not found" errors
- Make sure virtual environment is activated
- Re-run `pip install -r requirements.txt`

### "Port already in use"
- Another process is using port 8000
- Find and stop it: `lsof -i :8000` (macOS/Linux)
- Or use a different port: `--port 8001`

### "Permission denied" errors
- Make sure you have write permissions
- Try with `sudo` (carefully!)

### Virtual environment not activating
- Make sure you created it correctly
- Try recreating: `rm -rf venv && python3 -m venv venv`

## ✅ Backend Setup Complete!

Your Python backend is now running! Keep this terminal open while working on the project.

**Next, we'll set up the frontend in a new terminal window.**

---

[← Previous: Repository Setup](./02-repository-setup.md) | [Back to Main Guide](../README.md) | [Next: Frontend Setup →](./04-frontend-setup.md)