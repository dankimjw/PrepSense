#!/bin/bash
# Fix watchman recrawl warning

echo "Fixing watchman recrawl warning..."

# Delete the current watch
watchman watch-del '/Users/danielkim/_Capstone/PrepSense' 2>/dev/null

# Re-add the watch
watchman watch-project '/Users/danielkim/_Capstone/PrepSense'

echo "Watchman fix applied. The warning should be resolved."