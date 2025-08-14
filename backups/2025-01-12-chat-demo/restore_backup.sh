#!/bin/bash
# Restore script for chat demo implementation
# Date: January 12, 2025

echo "🔄 Restoring chat demo implementation backup..."
echo "================================================"

# Get the backup directory path
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="/Users/danielkim/_Capstone/PrepSense"

echo "Backup directory: $BACKUP_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Ask for confirmation
read -p "⚠️  This will overwrite current files. Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled."
    exit 1
fi

echo ""
echo "📁 Restoring files..."

# Restore main service files
echo "  - Restoring openai_chat_service.py..."
cp "$BACKUP_DIR/openai_chat_service.py.backup" "$PROJECT_ROOT/backend_gateway/services/openai_chat_service.py"

echo "  - Restoring chat_router.py..."
cp "$BACKUP_DIR/chat_router.py.backup" "$PROJECT_ROOT/backend_gateway/routers/chat_router.py"

# Restore utility scripts
echo "  - Restoring utility scripts..."
cp "$BACKUP_DIR/update_pantry_quantities.py" "$PROJECT_ROOT/"
cp "$BACKUP_DIR/add_new_pantry_items.py" "$PROJECT_ROOT/"
cp "$BACKUP_DIR/check_pantry.py" "$PROJECT_ROOT/"

echo ""
echo "✅ Files restored successfully!"
echo ""
echo "📝 Next steps:"
echo "  1. Restart the backend: python run_app_smart.py --backend"
echo "  2. Test chat functionality with user 111"
echo "  3. Chat should only show saved recipes from 'My Recipes'"
echo ""
echo "⚠️  Note: This backup includes:"
echo "  - Chat service showing only saved recipes (demo mode)"
echo "  - Router using OpenAI service for all requests"
echo "  - Pantry with 19 items (all whole numbers)"
echo ""
echo "✨ Restore complete!"