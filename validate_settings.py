#!/usr/bin/env python3
import json
import sys

def validate_json_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            data = json.loads(content)
        print(f"✅ {filepath}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {filepath}: Invalid JSON")
        print(f"   Error: {e}")
        print(f"   Line {e.lineno}, Column {e.colno}")
        
        # Show the problematic line
        lines = content.split('\n')
        if e.lineno <= len(lines):
            print(f"   Problem line: {lines[e.lineno-1]}")
        return False
    except Exception as e:
        print(f"❌ {filepath}: Error reading file - {e}")
        return False

# Check all settings files
settings_files = [
    '.claude/settings.json',
    '.claude/settings.local.json',
    '.claude/settings.json.backup'
]

print("=== Validating Claude Settings Files ===\n")

all_valid = True
for file in settings_files:
    if not validate_json_file(file):
        all_valid = False
    print()

if not all_valid:
    print("⚠️  Some settings files have JSON syntax errors")
    print("This is likely causing the 'invalid settings files' warning")
else:
    print("✅ All settings files have valid JSON syntax")
