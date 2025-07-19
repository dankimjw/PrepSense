#!/bin/bash
# Quick health check for PrepSense app

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 PrepSense Quick Health Check${NC}"
echo "==============================="

# Check backend
echo -n "Backend (port 8001): "
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

# Check iOS Metro
echo -n "iOS Metro (port 8082): "
if curl -s http://localhost:8082 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

# Check processes
echo -n "Backend process: "
if pgrep -f "run_app.py\|uvicorn.*app:app" > /dev/null; then
    echo -e "${GREEN}✅ Active${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
fi

echo -n "Metro process: "
if pgrep -f "expo.*start\|metro" > /dev/null; then
    echo -e "${GREEN}✅ Active${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
fi

echo ""
echo -e "${BLUE}Quick commands:${NC}"
echo "Start backend: source venv/bin/activate && python run_app.py"
echo "Start iOS: cd ios-app && npx expo start --ios"
echo "Full check: python check_app_health.py"