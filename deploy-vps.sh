#!/bin/bash

# ============================================
# VPS Deployment Script for Leads Checker Tool
# ============================================

set -e  # Exit on error

echo "=========================================="
echo "Leads Checker Tool - VPS Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/leads-checker-tool"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Step 1: Check system dependencies
print_info "Checking system dependencies..."

command -v python3.11 >/dev/null 2>&1 || {
    print_error "Python 3.11 is not installed. Please install it first."
    exit 1
}
print_success "Python 3.11 found"

command -v node >/dev/null 2>&1 || {
    print_error "Node.js is not installed. Please install it first."
    exit 1
}
print_success "Node.js found"

command -v mongod >/dev/null 2>&1 || {
    print_error "MongoDB is not installed. Please install it first."
    exit 1
}
print_success "MongoDB found"

command -v redis-cli >/dev/null 2>&1 || {
    print_error "Redis is not installed. Please install it first."
    exit 1
}
print_success "Redis found"

# Step 2: Check .env file
print_info "Checking environment configuration..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_warning ".env file not found. Copying from .env.vps template..."
    cp "$PROJECT_DIR/.env.vps" "$PROJECT_DIR/.env"
    print_warning "IMPORTANT: Edit $PROJECT_DIR/.env with your actual VPS database URLs!"
    print_warning "Press Enter to continue after editing .env file..."
    read
fi

# Verify critical env vars
if grep -q "VPS2_MONGODB_URL=$" "$PROJECT_DIR/.env"; then
    print_warning "VPS database URLs are not configured in .env file!"
    print_warning "Email verification will NOT work without VPS database connections."
fi

print_success "Environment file exists"

# Step 3: Setup backend
print_info "Setting up backend..."

cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating Python virtual environment..."
    python3.11 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

# Activate virtual environment and install dependencies
print_info "Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create necessary directories
mkdir -p logs uploads results
print_success "Created necessary directories"

# Step 4: Setup frontend
print_info "Setting up frontend..."

cd "$FRONTEND_DIR"

# Install dependencies
print_info "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Build frontend
print_info "Building frontend for production..."
npm run build
print_success "Frontend built successfully"

# Step 5: Setup systemd services
print_info "Setting up systemd services..."

# Backend API service
cat > /etc/systemd/system/leads-checker-api.service <<EOF
[Unit]
Description=Leads Checker Tool API
After=network.target mongod.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 4005
Restart=always
RestartSec=10
StandardOutput=append:$BACKEND_DIR/logs/api.log
StandardError=append:$BACKEND_DIR/logs/api-error.log

[Install]
WantedBy=multi-user.target
EOF

print_success "Created API service file"

# Celery worker service
cat > /etc/systemd/system/leads-checker-worker.service <<EOF
[Unit]
Description=Leads Checker Tool Celery Worker
After=network.target mongod.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10
StandardOutput=append:$BACKEND_DIR/logs/worker.log
StandardError=append:$BACKEND_DIR/logs/worker-error.log

[Install]
WantedBy=multi-user.target
EOF

print_success "Created Worker service file"

# Step 6: Set permissions
print_info "Setting file permissions..."
chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod -R 777 "$BACKEND_DIR/logs"
chmod -R 777 "$BACKEND_DIR/uploads"
chmod -R 777 "$BACKEND_DIR/results"
print_success "Permissions set"

# Step 7: Reload systemd and start services
print_info "Starting services..."

systemctl daemon-reload
systemctl enable leads-checker-api
systemctl enable leads-checker-worker

systemctl restart leads-checker-api
systemctl restart leads-checker-worker

sleep 2

# Check service status
if systemctl is-active --quiet leads-checker-api; then
    print_success "API service is running"
else
    print_error "API service failed to start. Check logs: journalctl -u leads-checker-api -n 50"
    exit 1
fi

if systemctl is-active --quiet leads-checker-worker; then
    print_success "Worker service is running"
else
    print_error "Worker service failed to start. Check logs: journalctl -u leads-checker-worker -n 50"
    exit 1
fi

# Step 8: Configure Nginx (if installed)
if command -v nginx >/dev/null 2>&1; then
    print_info "Configuring Nginx..."
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > /etc/nginx/sites-available/leads-checker <<EOF
server {
    listen 80;
    server_name $SERVER_IP;

    # Frontend
    location / {
        root $FRONTEND_DIR/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:4005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/leads-checker /etc/nginx/sites-enabled/
    
    # Test nginx config
    if nginx -t 2>/dev/null; then
        systemctl restart nginx
        print_success "Nginx configured and restarted"
    else
        print_error "Nginx configuration test failed"
    fi
else
    print_warning "Nginx not installed. Skipping web server configuration."
fi

# Step 9: Final checks
print_info "Running final checks..."

# Check MongoDB
if systemctl is-active --quiet mongod; then
    print_success "MongoDB is running"
else
    print_warning "MongoDB is not running. Starting it..."
    systemctl start mongod
fi

# Check Redis
if systemctl is-active --quiet redis; then
    print_success "Redis is running"
else
    print_warning "Redis is not running. Starting it..."
    systemctl start redis
fi

# Test API endpoint
sleep 2
if curl -s http://localhost:4005/health | grep -q "healthy"; then
    print_success "API health check passed"
else
    print_warning "API health check failed. Check logs."
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
print_success "Frontend: http://$SERVER_IP/"
print_success "Backend API: http://$SERVER_IP:4005/"
echo ""
print_info "Next steps:"
echo "1. Verify VPS database connections in logs:"
echo "   tail -f $BACKEND_DIR/logs/vps_connections.log"
echo ""
echo "2. Monitor worker logs:"
echo "   tail -f $BACKEND_DIR/logs/worker.log"
echo ""
echo "3. Check service status:"
echo "   systemctl status leads-checker-api"
echo "   systemctl status leads-checker-worker"
echo ""
print_warning "IMPORTANT: Make sure to configure VPS database URLs in .env file!"
echo ""
