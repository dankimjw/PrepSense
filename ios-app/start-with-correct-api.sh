#!/bin/bash

# Clear Metro cache and start with correct API URL
echo "🧹 Clearing Metro cache..."
npx expo start --clear

echo "🚀 Starting with correct API URL..."
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.196:8000/api/v1 npx expo start --ios