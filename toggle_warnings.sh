#!/bin/bash

# Toggle iOS simulator warnings on/off

if [ "$1" = "on" ]; then
    echo "Enabling warnings in iOS simulator..."
    sed -i.bak 's/EXPO_PUBLIC_SUPPRESS_WARNINGS=true/EXPO_PUBLIC_SUPPRESS_WARNINGS=false/' .env
    echo "✓ Warnings enabled"
elif [ "$1" = "off" ]; then
    echo "Disabling warnings in iOS simulator..."
    sed -i.bak 's/EXPO_PUBLIC_SUPPRESS_WARNINGS=false/EXPO_PUBLIC_SUPPRESS_WARNINGS=true/' .env
    echo "✓ Warnings disabled"
else
    # Check current status
    if grep -q "EXPO_PUBLIC_SUPPRESS_WARNINGS=true" .env; then
        echo "Warnings are currently: DISABLED"
    else
        echo "Warnings are currently: ENABLED"
    fi
    echo ""
    echo "Usage: ./toggle_warnings.sh [on|off]"
    echo "  on  - Show warnings in iOS simulator"
    echo "  off - Hide warnings in iOS simulator"
fi