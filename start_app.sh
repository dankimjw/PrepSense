#!/bin/bash

start_backend() {
    echo "Starting FastAPI backend server..."
    uvicorn backend_gateway.app:app --reload
}
start_ios() {
    echo "Starting iOS app..."
    cd ios-app
    npx expo start -c
}

if [ $# -eq 0 ]; then
    echo "Please specify which app to start:"
    echo "Usage: ./start_app.sh [backend|ios]"
    exit 1
fi

case "$1" in
    "backend")
        start_backend
        ;;
    "ios")
        start_ios
        ;;
    *)
        echo "Invalid parameter. Use 'backend' or 'ios'"
        exit 1
        ;;
esac