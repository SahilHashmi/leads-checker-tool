#!/bin/bash

# ============================================
# Rebuild Frontend and Deploy to VPS
# ============================================

set -e

echo "=========================================="
echo "Rebuilding Frontend for VPS"
echo "=========================================="

FRONTEND_DIR="/var/www/leads-checker-tool/frontend"

cd "$FRONTEND_DIR"

echo "→ Installing dependencies..."
npm install

echo "→ Building production bundle..."
npm run build

echo ""
echo "✓ Frontend rebuilt successfully!"
echo ""
echo "Build output: $FRONTEND_DIR/dist"
echo ""
echo "If using Nginx, restart it:"
echo "  sudo systemctl restart nginx"
echo ""
