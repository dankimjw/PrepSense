#!/usr/bin/env bash
set -euo pipefail

echo "======================================"
echo "Finding Orphaned Files"
echo "======================================"

# Create temp files
ALL_FILES="/tmp/allfiles_$$.txt"
REFERENCED_FILES="/tmp/referenced_$$.txt"

# Find all files (excluding common build artifacts and node_modules)
echo "Scanning all files..."
find . -type f \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/venv/*" \
    -not -path "*/.venv/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -not -path "*/.expo/*" \
    -not -path "*/coverage/*" \
    -not -name "*.pyc" \
    -not -name "*.pyo" \
    -not -name ".DS_Store" \
    | sort > "$ALL_FILES"

# Find referenced files by looking for imports and references
echo "Finding referenced files..."
{
    # Python imports
    grep -r --include="*.py" -h -o "from [a-zA-Z0-9_.]* import\|import [a-zA-Z0-9_.]*" . 2>/dev/null | \
        sed 's/from //g; s/import //g; s/ .*//g' | \
        sed 's/\./\//g' | \
        awk '{print "./" $0 ".py"; print "./backend_gateway/" $0 ".py"}'
    
    # JavaScript/TypeScript imports
    grep -r --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" \
        -h -o "from ['\"][^'\"]*['\"]\\|require(['\"][^'\"]*['\"])" . 2>/dev/null | \
        sed "s/from ['\"]//g; s/['\"]//g; s/require(//g; s/)//g"
    
    # Direct file references in various files
    grep -r --include="*.py" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" \
        --include="*.json" --include="*.md" --include="*.sh" \
        -h -o "['\"][./a-zA-Z0-9_-]*\.[a-zA-Z0-9]*['\"]" . 2>/dev/null | \
        sed "s/['\"]//g"
} | sort -u > "$REFERENCED_FILES"

# Find orphaned files
echo ""
echo "Potentially orphaned files (not directly referenced):"
echo "------------------------------------------------------"
comm -23 "$ALL_FILES" "$REFERENCED_FILES" | \
    grep -v -E "(README|LICENSE|\.gitignore|\.md$|\.txt$|\.json$|\.yaml$|\.yml$|test_|_test\.|\.test\.|conftest)" | \
    head -20

# Cleanup
rm -f "$ALL_FILES" "$REFERENCED_FILES"

echo ""
echo "Note: This is a heuristic check. Some files may be:"
echo "  - Referenced dynamically"
echo "  - Entry points or config files"
echo "  - Documentation or test files"
echo "Always verify before deleting!"