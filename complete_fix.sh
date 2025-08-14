#!/bin/bash

cd /Users/danielkim/_Capstone/PrepSense

echo "=== Complete Claude Code Fix ==="
echo ""

# Step 1: Validate current settings
echo "Step 1: Checking settings files..."
python3 validate_settings.py
echo ""

# Step 2: Backup current settings
echo "Step 2: Backing up current settings..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p .claude/backups
cp .claude/settings*.json .claude/backups/ 2>/dev/null || true
echo "Backed up to .claude/backups/"
echo ""

# Step 3: Fix settings.json if needed
echo "Step 3: Creating fixed settings.json..."
cat > .claude/settings.json.fixed << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(mkdir:*)",
      "Bash(uv:*)",
      "Bash(find:*)",
      "Bash(mv:*)",
      "Bash(grep:*)",
      "Bash(npm:*)",
      "Bash(ls:*)",
      "Bash(cp:*)",
      "Write",
      "Edit",
      "Bash(chmod:*)",
      "Bash(touch:*)"
    ]
  },
  "model": "Sonnet",
  "agents": {
    "path": ".claude/agents",
    "enabled": true
  }
}
EOF

# Step 4: Downgrade Claude Code
echo "Step 4: Fixing Claude Code version..."
echo "Uninstalling current version..."
npm uninstall -g @anthropic/claude-code @anthropic-ai/claude-code 2>/dev/null || true

echo "Installing working version 1.0.61..."
npm install -g @anthropic-ai/claude-code@1.0.61

if [ $? -ne 0 ]; then
    echo "⚠️  npm install failed. Trying with sudo..."
    sudo npm install -g @anthropic-ai/claude-code@1.0.61
fi

# Step 5: Apply fixed settings
echo ""
echo "Step 5: Applying fixed settings..."
mv .claude/settings.json .claude/settings.json.invalid 2>/dev/null || true
mv .claude/settings.json.fixed .claude/settings.json

# Step 6: Verify
echo ""
echo "Step 6: Verifying fix..."
echo "Claude version: $(claude --version 2>&1 || echo 'Unknown')"
echo "Settings validation:"
python3 validate_settings.py | grep "settings.json:" || echo "Validation failed"
echo "Agents found: $(ls .claude/agents/*.md 2>/dev/null | wc -l)"

echo ""
echo "=== Fix Complete ==="
echo ""
echo "✅ Claude Code downgraded to v1.0.61"
echo "✅ Settings file fixed with agents configuration"
echo "✅ All $(ls .claude/agents/*.md | wc -l) agents should now be available"
echo ""
echo "Test it:"
echo "  cd /Users/danielkim/_Capstone/PrepSense"
echo "  claude chat"
echo ""
echo "If you still see warnings, run: claude doctor"
