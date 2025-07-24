# 🚨 VERIFICATION BEFORE ACTION - CRITICAL REMINDER 🚨

**THIS FILE EXISTS TO PREVENT ASSUMPTION-BASED MISTAKES**

## The Incident (2025-01-22)
Main instance told user to "add your OpenAI API key" without verifying if it was actually missing. The key existed in `config/openai.json` but Main only checked `config/openai_key.txt`.

## MANDATORY PROTOCOL

### Before Claiming Anything Is Missing:
```bash
# 1. Search EVERYWHERE
find . -name "*.json" -o -name "*.txt" -o -name "*.env" | xargs grep -l "api_key\|API_KEY"

# 2. Check how the code loads it
grep -r "openai.*key" backend_gateway/**/*.py

# 3. Look for alternative locations
ls -la config/
cat config/*.json | grep -i key
```

### Before Suggesting Any Fix:
1. ✅ Verify the actual problem exists
2. ✅ Show evidence of what you found
3. ✅ Test your proposed solution
4. ❌ Never say "Add X" without confirming X is missing

### Examples:
**❌ WRONG**: "Add your API key to config/openai_key.txt"
**✅ RIGHT**: "Let me check where API keys are configured... [runs commands]... I found the key in config/openai.json"

## Why This Matters
- Users trust us to be thorough
- Incorrect assumptions waste everyone's time
- Verification builds confidence
- Evidence-based responses prevent errors

## Quick Verification Commands
```bash
# Config search
find config/ -type f -exec grep -l "key\|KEY\|secret\|SECRET" {} \;

# Code usage search
grep -r "getenv\|environ\|config" --include="*.py" | grep -i "key"

# JSON config dump
for f in config/*.json; do echo "=== $f ==="; cat "$f" | python -m json.tool | grep -A2 -B2 -i "key"; done
```

**REMEMBER**: When in doubt, verify. Always verify. Then verify again.