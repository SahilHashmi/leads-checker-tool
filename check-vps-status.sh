#!/bin/bash

# ============================================
# VPS Status Check Script
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/leads-checker-tool"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=========================================="
echo "Leads Checker Tool - Status Check"
echo "=========================================="
echo ""

# Function to check service status
check_service() {
    local service=$1
    local name=$2
    
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT running"
        return 1
    fi
}

# Check system services
echo -e "${BLUE}System Services:${NC}"
check_service mongod "MongoDB"
check_service redis "Redis"
check_service leads-checker-api "API Server"
check_service leads-checker-worker "Celery Worker"
echo ""

# Check API health
echo -e "${BLUE}API Health Check:${NC}"
if curl -s http://localhost:4005/health | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} API is responding"
else
    echo -e "${RED}✗${NC} API is not responding"
fi
echo ""

# Check VPS database connections
echo -e "${BLUE}VPS Database Connections:${NC}"
if [ -f "$BACKEND_DIR/logs/vps_connections.log" ]; then
    # Get the last connection summary
    echo "Last connection attempt:"
    tail -n 20 "$BACKEND_DIR/logs/vps_connections.log" | grep -E "(Successfully connected|Failed to connect|Connection Summary)" | tail -n 10
else
    echo -e "${YELLOW}⚠${NC} No VPS connection logs found"
fi
echo ""

# Check recent errors
echo -e "${BLUE}Recent Errors (last 10):${NC}"
if [ -f "$BACKEND_DIR/logs/application.log" ]; then
    grep -i "error" "$BACKEND_DIR/logs/application.log" | tail -n 10 || echo "No recent errors"
else
    echo "No application logs found"
fi
echo ""

# Check disk space
echo -e "${BLUE}Disk Space:${NC}"
df -h / | tail -n 1
echo ""

# Check memory usage
echo -e "${BLUE}Memory Usage:${NC}"
free -h | grep Mem
echo ""

# Check active connections
echo -e "${BLUE}Active Connections:${NC}"
echo "API (port 4005): $(netstat -an | grep :4005 | grep ESTABLISHED | wc -l) connections"
echo "MongoDB (port 27017): $(netstat -an | grep :27017 | grep ESTABLISHED | wc -l) connections"
echo ""

# Check recent tasks
echo -e "${BLUE}Recent Processing Tasks:${NC}"
if [ -f "$BACKEND_DIR/logs/worker.log" ]; then
    grep "Starting task" "$BACKEND_DIR/logs/worker.log" | tail -n 5 || echo "No recent tasks"
else
    echo "No worker logs found"
fi
echo ""

# Check .env configuration
echo -e "${BLUE}Environment Configuration:${NC}"
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "VPS databases configured:"
    grep "VPS.*_ENABLED=true" "$PROJECT_DIR/.env" | wc -l
    echo ""
    echo "Configured VPS databases:"
    grep "VPS.*_ENABLED=true" "$PROJECT_DIR/.env" | cut -d'_' -f1 | sort -u
else
    echo -e "${RED}✗${NC} .env file not found!"
fi
echo ""

echo "=========================================="
echo "Quick Commands:"
echo "=========================================="
echo "View API logs:        tail -f $BACKEND_DIR/logs/application.log"
echo "View worker logs:     tail -f $BACKEND_DIR/logs/worker.log"
echo "View VPS logs:        tail -f $BACKEND_DIR/logs/vps_connections.log"
echo "Restart API:          sudo systemctl restart leads-checker-api"
echo "Restart worker:       sudo systemctl restart leads-checker-worker"
echo "View API status:      sudo systemctl status leads-checker-api"
echo "View worker status:   sudo systemctl status leads-checker-worker"
echo ""
