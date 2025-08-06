# 🚀 Repository Setup

[← Previous: Prerequisites](./01-prerequisites.md) | [Back to Main Guide](../README.md) | [Next: Backend Setup →](./03-backend-setup.md)

## 📥 Cloning the Repository

### Step 1: Open Terminal
- **macOS**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Win + R`, type "cmd", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### Step 2: Navigate to Where You Want the Project
```bash
# Example: Go to your home directory
cd ~

# Or create a dedicated projects folder
mkdir -p ~/projects
cd ~/projects
```

### Step 3: Clone the Repository
```bash
git clone https://github.com/[your-username]/PrepSense.git
cd PrepSense
```

🔄 **Replace `[your-username]` with the actual GitHub username!**

### Step 4: Verify the Clone
```bash
# You should see all the project files
ls -la

# You should see folders like:
# backend_gateway/
# ios-app/
# docs/
# etc.
```

## 🌳 Understanding the Project Structure

Here's what each main folder contains:

```
PrepSense/
├── backend_gateway/    # Python FastAPI backend
│   ├── app.py         # Main application file
│   ├── routers/       # API endpoints
│   ├── services/      # Business logic
│   └── requirements.txt # Python dependencies
├── ios-app/           # React Native Expo frontend
│   ├── app/          # Main app screens
│   ├── components/   # Reusable components
│   └── package.json  # Node.js dependencies
├── docs/             # This documentation!
└── README.md         # Project overview
```

## 🔑 Setting Up Git (First Time Only)

If this is your first time using Git, configure your identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🌿 Creating Your Own Branch

It's good practice to work on your own branch:

```bash
# Create and switch to a new branch
git checkout -b your-name-feature

# Example:
git checkout -b john-pantry-updates
```

## 📂 Environment Variables Setup

### Step 1: Check for Environment File Template
```bash
# Look for example environment files
ls -la | grep -E "\.env|example"
```

### Step 2: Create Your Environment Files
If there's an `.env.example` file:
```bash
# For backend
cp backend_gateway/.env.example backend_gateway/.env

# For frontend (if exists)
cp ios-app/.env.example ios-app/.env
```

### Step 3: Get Required Keys from Team
You'll need to ask your team for:
- API keys
- Database credentials
- Service account files

**⚠️ Never commit `.env` files or credentials to Git!**

## 🔒 Setting Up Google Cloud Credentials

PrepSense uses Google Cloud services. You'll need:

1. **Service Account Key File**
   - Get this from your team lead
   - Save it as `service-account-key.json` in the project root
   - Add to `.gitignore` to keep it private

2. **Set Environment Variable**
   ```bash
   # Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
   export GOOGLE_APPLICATION_CREDENTIALS="$HOME/projects/PrepSense/service-account-key.json"
   
   # Reload your shell
   source ~/.bashrc  # or ~/.zshrc
   ```

## ✅ Verification Checklist

Run these commands to make sure everything is set up:

```bash
# Check you're in the right directory
pwd
# Should show: /path/to/PrepSense

# Check Git is working
git status

# Check project structure
ls -la backend_gateway/
ls -la ios-app/

# Check environment variables (if set)
echo $GOOGLE_APPLICATION_CREDENTIALS
```

## 🆘 Common Issues

### "Permission denied" when cloning
- Make sure you have access to the repository
- If it's private, you might need to set up SSH keys or use HTTPS with credentials

### "Repository not found"
- Double-check the URL
- Make sure you have access to the repository
- Try using HTTPS instead of SSH (or vice versa)

### Missing folders after cloning
- Make sure the clone completed successfully
- Try cloning again in a fresh directory

## 📝 Next Steps

Great! You now have the project on your computer. Next, we'll set up the Python backend environment.

---

[← Previous: Prerequisites](./01-prerequisites.md) | [Back to Main Guide](../README.md) | [Next: Backend Setup →](./03-backend-setup.md)