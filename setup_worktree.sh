#!/bin/bash
# Setup script for PrepSense worktree

echo "🔧 Setting up PrepSense worktree..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Not in a PrepSense directory. Run this from the worktree root."
    exit 1
fi

# Create Python virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup iOS dependencies
echo "📱 Setting up iOS dependencies..."
cd ios-app
npm install
cd ..

# Copy environment files from main worktree
echo "📋 Copying environment configuration..."
if [ ! -f ".env" ]; then
    echo "📁 Copying .env file from main worktree..."
    cp ../../../PrepSense/.env .
fi

if [ ! -d "config" ]; then
    echo "📁 Copying config folder from main worktree..."
    cp -r ../../../PrepSense/config .
fi

echo "✅ Worktree setup complete!"
echo ""
echo "To use this worktree:"
echo "  source venv/bin/activate"
echo "  python run_app_smart.py"
echo ""
echo "Configuration files copied:"
echo "  ✅ .env file"
echo "  ✅ config/ folder"
echo ""
echo "The smart launcher will automatically use available ports to avoid conflicts."