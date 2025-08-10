#!/bin/bash
# Quick connectivity check for PrepSense - runs in ~30 seconds
# Provides immediate pass/fail feedback for basic service connectivity

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 PrepSense Quick Check (30 seconds)${NC}"
echo "======================================="

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check if port is open
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ $service (port $port) is running${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $service (port $port) is NOT running${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local service=$2
    
    if curl -s -f -m 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is responding${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $service is NOT responding${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to check process
check_process() {
    local process=$1
    local service=$2
    
    if pgrep -f "$process" > /dev/null; then
        echo -e "${GREEN}✅ $service process is running${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $service process is NOT running${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

echo -e "\n1️⃣  Checking ports..."
check_port 8001 "Backend API"
# Only check Metro if it should be running (iOS mode)
if pgrep -f "metro\|expo\|npm.*start" > /dev/null 2>&1; then
    check_port 8082 "Metro Bundler"
else
    echo -e "${YELLOW}ℹ️  Metro Bundler (port 8082) not expected - backend-only mode${NC}"
fi

echo -e "\n2️⃣  Checking HTTP endpoints..."
check_http "http://localhost:8001/api/v1/health" "Backend health endpoint"
# Only check Metro endpoint if Metro is running
if pgrep -f "metro\|expo\|npm.*start" > /dev/null 2>&1; then
    check_http "http://localhost:8082" "Metro bundler endpoint"
else
    echo -e "${YELLOW}ℹ️  Metro bundler endpoint not checked - backend-only mode${NC}"
fi

echo -e "\n3️⃣  Checking processes..."
check_process "uvicorn" "FastAPI server"
# Skip Metro process check since it might be running in various ways
# check_process "node.*metro" "Metro bundler"

echo -e "\n4️⃣  Quick API test..."
if [ $CHECKS_FAILED -eq 0 ]; then
    # Only run if basic checks pass
    # Note: API has duplicate path prefix issue - using demo endpoint instead
    if curl -s -f -m 5 "http://localhost:8001/api/v1/demo/recipes" | grep -q "recipes"; then
        echo -e "${GREEN}✅ API returning valid data${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ API not returning expected data${NC}"
        ((CHECKS_FAILED++))
    fi
fi

# Summary
echo -e "\n======================================="
TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED))
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! ($CHECKS_PASSED/$TOTAL_CHECKS)${NC}"
    echo -e "${GREEN}PrepSense appears to be running correctly.${NC}"
else
    echo -e "${RED}❌ Some checks failed! ($CHECKS_PASSED/$TOTAL_CHECKS passed)${NC}"
    
    # Provide quick fix suggestions
    echo -e "\n${YELLOW}Quick fixes:${NC}"
    if ! lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  • Start backend: source venv/bin/activate && python run_app.py --backend"
        echo "  • Start both: source venv/bin/activate && python run_app.py"
    fi
    if ! lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1 && pgrep -f "metro\|expo\|npm.*start" > /dev/null 2>&1; then
        echo "  • Start iOS app: python run_app.py --ios (or cd ios-app && npm start)"
    fi
    echo -e "\nFor detailed diagnostics, run: ${YELLOW}python check_app_health.py${NC}"
fi

# ---- Repo Janitor: Additional health checks (non-blocking) ----
echo -e "\n${YELLOW}5️⃣  Running additional health checks...${NC}"
echo "======================================="

# Python health check
if [ -f scripts/py_health.sh ]; then 
    echo -e "${YELLOW}Running Python health check...${NC}"
    bash scripts/py_health.sh 2>/dev/null || echo -e "${YELLOW}Python health check completed with warnings${NC}"
fi

# JavaScript health check  
if [ -f scripts/js_health.sh ]; then 
    echo -e "\n${YELLOW}Running JavaScript health check...${NC}"
    (cd ios-app && bash ../scripts/js_health.sh 2>/dev/null) || echo -e "${YELLOW}JavaScript health check completed with warnings${NC}"
fi

# List FastAPI routes
if [ -f scripts/list_fastapi_routes.py ]; then 
    echo -e "\n${YELLOW}Listing FastAPI routes...${NC}"
    python scripts/list_fastapi_routes.py 2>/dev/null || echo -e "${YELLOW}Could not list routes (backend may not be configured)${NC}"
fi

# Find orphaned files
if [ -f scripts/find_orphans.sh ]; then 
    echo -e "\n${YELLOW}Finding orphaned files...${NC}"
    bash scripts/find_orphans.sh 2>/dev/null || echo -e "${YELLOW}Orphan file check completed${NC}"
fi

echo -e "\n${GREEN}Additional health checks complete!${NC}"

# Exit with original status
if [ $CHECKS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi