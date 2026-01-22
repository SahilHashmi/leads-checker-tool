#!/bin/bash

# ============================================
# Fix Permissions Script for VPS Deployment
# ============================================

set -e

echo "=========================================="
echo "Fixing Permissions for Leads Checker Tool"
echo "=========================================="

PROJECT_DIR="/var/www/leads-checker-tool"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Setting ownership to www-data..."
chown -R www-data:www-data "$PROJECT_DIR"

echo "Setting directory permissions (755)..."
find "$PROJECT_DIR" -type d -exec chmod 755 {} \;

echo "Setting file permissions (644)..."
find "$PROJECT_DIR" -type f -exec chmod 644 {} \;

echo "Setting script permissions (755)..."
chmod 755 "$PROJECT_DIR"/*.sh 2>/dev/null || true

echo "Setting special permissions for writable directories..."
chmod -R 777 "$BACKEND_DIR/logs" 2>/dev/null || mkdir -p "$BACKEND_DIR/logs" && chmod -R 777 "$BACKEND_DIR/logs"
chmod -R 777 "$BACKEND_DIR/uploads" 2>/dev/null || mkdir -p "$BACKEND_DIR/uploads" && chmod -R 777 "$BACKEND_DIR/uploads"
chmod -R 777 "$BACKEND_DIR/results" 2>/dev/null || mkdir -p "$BACKEND_DIR/results" && chmod -R 777 "$BACKEND_DIR/results"

echo "Setting Python virtual environment permissions..."
if [ -d "$BACKEND_DIR/venv" ]; then
    chmod -R 755 "$BACKEND_DIR/venv"
    chmod +x "$BACKEND_DIR/venv/bin/"* 2>/dev/null || true
fi

echo "Setting .env file permissions (600 for security)..."
if [ -f "$PROJECT_DIR/.env" ]; then
    chmod 600 "$PROJECT_DIR/.env"
    chown www-data:www-data "$PROJECT_DIR/.env"
fi

echo ""
echo "✓ Permissions fixed successfully!"
echo ""
echo "Directory structure:"
ls -la "$BACKEND_DIR" | grep -E "(logs|uploads|results|venv|.env)" || true
echo ""
