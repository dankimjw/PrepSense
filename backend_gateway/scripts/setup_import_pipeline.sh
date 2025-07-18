#!/bin/bash
# Setup script for Food Database Import Pipeline

echo "🚀 Setting up Food Database Import Pipeline"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create necessary directories
echo "📁 Creating import directories..."
mkdir -p food_data_imports
mkdir -p logs/imports

# Install required packages
echo "📦 Installing required packages..."
pip install aiohttp aiofiles schedule

# Check environment variables
echo "🔑 Checking API keys..."
if [ -z "$USDA_API_KEY" ]; then
    echo "  ⚠️  USDA_API_KEY not set - USDA imports will be skipped"
    echo "  ℹ️  Get a free API key at: https://fdc.nal.usda.gov/api-key-signup.html"
else
    echo "  ✓ USDA API key configured"
fi

# Create systemd service file (optional)
if command -v systemctl &> /dev/null; then
    echo "📋 Creating systemd service file..."
    cat > /tmp/prepsense-food-import.service << EOF
[Unit]
Description=PrepSense Food Database Import Service
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 $(pwd)/food_database_import_pipeline.py --schedule
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
    
    echo "  ℹ️  To install as system service, run:"
    echo "     sudo cp /tmp/prepsense-food-import.service /etc/systemd/system/"
    echo "     sudo systemctl enable prepsense-food-import"
    echo "     sudo systemctl start prepsense-food-import"
fi

# Create cron job alternative
echo "📅 Setting up cron jobs (alternative to systemd)..."
cron_file="/tmp/prepsense-food-import-cron"
cat > $cron_file << EOF
# PrepSense Food Database Import Jobs
# Daily USDA import at 2 AM
0 2 * * * cd $(pwd) && /usr/bin/python3 food_database_import_pipeline.py --sources usda >> logs/imports/usda.log 2>&1
# Weekly Open Food Facts import on Sunday at 3 AM
0 3 * * 0 cd $(pwd) && /usr/bin/python3 food_database_import_pipeline.py --sources openfoodfacts >> logs/imports/off.log 2>&1
# Monthly full import on 1st at 4 AM
0 4 1 * * cd $(pwd) && /usr/bin/python3 food_database_import_pipeline.py >> logs/imports/full.log 2>&1
EOF

echo "  ℹ️  To install cron jobs, run:"
echo "     crontab -l > /tmp/current_cron"
echo "     cat $cron_file >> /tmp/current_cron"
echo "     crontab /tmp/current_cron"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Usage:"
echo "  # Run one-time import from all sources"
echo "  python3 food_database_import_pipeline.py"
echo ""
echo "  # Import only from USDA"
echo "  python3 food_database_import_pipeline.py --sources usda"
echo ""
echo "  # Import only from Open Food Facts"
echo "  python3 food_database_import_pipeline.py --sources openfoodfacts"
echo ""
echo "  # Run as scheduled service (runs indefinitely)"
echo "  python3 food_database_import_pipeline.py --schedule"
echo ""
echo "  # Test import with limited data"
echo "  python3 food_database_import_pipeline.py --test"