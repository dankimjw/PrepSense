#!/bin/bash
# Set git author configuration for PrepSense repository

echo "Setting up git author configuration for PrepSense..."

# Set local git config for this repository
cd /Users/danielkim/_Capstone/PrepSense

# Set author name and email locally for this repo
git config --local user.name "dankimjw"
git config --local user.email "dankimjw@example.com"

# Optional: Set up commit template to ensure consistency
git config --local commit.template .gitmessage

echo "✅ Git author configuration complete!"
echo "All future commits will be authored by: dankimjw"

# Display current configuration
echo -e "\nCurrent git configuration:"
git config --local user.name
git config --local user.email