# VPS Deployment Guide - Leads Checker Tool

Complete step-by-step guide to deploy the Leads Checker Tool on your VPS.

## Server Information

- **VPS IP**: 138.226.247.175
- **Frontend URL**: http://138.226.247.175/
- **Backend API URL**: http://138.226.247.175/api/

---

## Prerequisites

Before starting deployment, ensure your VPS has:

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- At least 2GB RAM
- 20GB+ disk space

---

## Part 1: Initial VPS Setup

### 1.1 Connect to VPS

```bash
ssh root@138.226.247.175
# or
ssh your_user@138.226.247.175
```

### 1.2 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Install Required Software

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install Git
sudo apt install -y git
```

### 1.4 Start Services

```bash
# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 1.5 Verify Services

```bash
# Check MongoDB
sudo systemctl status mongod

# Check Redis
redis-cli ping
# Should return: PONG

# Check Nginx
sudo systemctl status nginx
```

---

## Part 2: Deploy Application

### 2.1 Create Application Directory

```bash
sudo mkdir -p /var/www/leads-checker
cd /var/www/leads-checker
```

### 2.2 Upload Project Files

**Option A: Using Git (Recommended)**

```bash
# If you have a Git repository
sudo git clone <your-repo-url> .
```

**Option B: Using SCP from Local Machine**

From your local Windows machine (PowerShell):

```powershell
# Navigate to project directory
cd "d:\Patmar Properties\leads-checker-tool"

# Upload to VPS
scp -r backend frontend .env README.md root@138.226.247.175:/var/www/leads-checker/
```

**Option C: Using SFTP**

Use FileZilla or WinSCP to upload files to `/var/www/leads-checker/`

### 2.3 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/leads-checker
sudo chmod -R 755 /var/www/leads-checker
```

---

## Part 3: Backend Setup

### 3.1 Configure Environment Variables

```bash
cd /var/www/leads-checker
sudo nano .env
```

Add the following (replace with your actual values):

```env
# MongoDB Configuration (New VPS Database)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=leads_checker

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# External Database Connections (VPS2-VPS8)
VPS2_MONGODB_URL=mongodb://user:pass@vps2-ip:27017
VPS2_MONGODB_DATABASE=email_ag

VPS3_MONGODB_URL=mongodb://user:pass@vps3-ip:27017
VPS3_MONGODB_DATABASE=email_hn

VPS4_MONGODB_URL=mongodb://user:pass@vps4-ip:27017
VPS4_MONGODB_DATABASE=email_ou

VPS5_MONGODB_URL=mongodb://user:pass@vps5-ip:27017
VPS5_MONGODB_DATABASE=email_vz

VPS6_MONGODB_URL=mongodb://user:pass@vps6-ip:27017
VPS6_MONGODB_DATABASE=email_gmail

VPS7_MONGODB_URL=mongodb://user:pass@vps7-ip:27017
VPS7_MONGODB_DATABASE=email_hotmail

VPS8_MONGODB_URL=mongodb://user:pass@vps8-ip:27017
VPS8_MONGODB_DATABASE=email_yahoo_aol
```

Save and exit (Ctrl+X, Y, Enter)

### 3.2 Install Backend Dependencies

```bash
cd /var/www/leads-checker/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Create Required Directories

```bash
mkdir -p /var/www/leads-checker/backend/uploads
mkdir -p /var/www/leads-checker/backend/results
sudo chown -R www-data:www-data /var/www/leads-checker/backend/uploads
sudo chown -R www-data:www-data /var/www/leads-checker/backend/results
```

### 3.4 Create Systemd Service for Backend

```bash
sudo nano /etc/systemd/system/leads-backend.service
```

Add the following:

```ini
[Unit]
Description=Leads Checker Backend API
After=network.target mongod.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/leads-checker/backend
Environment="PATH=/var/www/leads-checker/backend/venv/bin"
EnvironmentFile=/var/www/leads-checker/.env
ExecStart=/var/www/leads-checker/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 3.5 Create Systemd Service for Celery Worker

```bash
sudo nano /etc/systemd/system/leads-celery.service
```

Add the following:

```ini
[Unit]
Description=Leads Checker Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/leads-checker/backend
Environment="PATH=/var/www/leads-checker/backend/venv/bin"
EnvironmentFile=/var/www/leads-checker/.env
ExecStart=/var/www/leads-checker/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 3.6 Start Backend Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable leads-backend
sudo systemctl enable leads-celery

# Start services
sudo systemctl start leads-backend
sudo systemctl start leads-celery

# Check status
sudo systemctl status leads-backend
sudo systemctl status leads-celery
```

### 3.7 View Backend Logs (if needed)

```bash
# Backend API logs
sudo journalctl -u leads-backend -f

# Celery worker logs
sudo journalctl -u leads-celery -f
```

---

## Part 4: Frontend Setup

### 4.1 Build Frontend

```bash
cd /var/www/leads-checker/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

This creates a `dist` folder with optimized static files.

### 4.2 Move Build Files

```bash
# Create web root directory
sudo mkdir -p /var/www/html/leads-checker

# Copy built files
sudo cp -r dist/* /var/www/html/leads-checker/

# Set permissions
sudo chown -R www-data:www-data /var/www/html/leads-checker
sudo chmod -R 755 /var/www/html/leads-checker
```

---

## Part 5: Nginx Configuration

### 5.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/leads-checker
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name 138.226.247.175;

    # Frontend - Serve static files
    location / {
        root /var/www/html/leads-checker;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API - Proxy to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
        
        # Increase max body size for file uploads
        client_max_body_size 100M;
    }

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

Save and exit.

### 5.2 Enable Site and Restart Nginx

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/leads-checker /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Part 6: Firewall Configuration

### 6.1 Configure UFW Firewall

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (for future SSL setup)
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

---

## Part 7: Verification & Testing

### 7.1 Test Backend API

```bash
# Test from VPS
curl http://127.0.0.1:8000/api/admin/stats

# Test from external
curl http://138.226.247.175/api/admin/stats
```

### 7.2 Test Frontend

Open browser and navigate to:
- **Frontend**: http://138.226.247.175/
- **API Docs**: http://138.226.247.175/docs

### 7.3 Check All Services

```bash
# Check all services status
sudo systemctl status mongod
sudo systemctl status redis-server
sudo systemctl status nginx
sudo systemctl status leads-backend
sudo systemctl status leads-celery
```

---

## Part 8: Maintenance Commands

### 8.1 Restart Services

```bash
# Restart backend
sudo systemctl restart leads-backend

# Restart celery worker
sudo systemctl restart leads-celery

# Restart nginx
sudo systemctl restart nginx
```

### 8.2 View Logs

```bash
# Backend logs
sudo journalctl -u leads-backend -n 100 --no-pager

# Celery logs
sudo journalctl -u leads-celery -n 100 --no-pager

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### 8.3 Update Application

```bash
# Stop services
sudo systemctl stop leads-backend
sudo systemctl stop leads-celery

# Update code (if using git)
cd /var/www/leads-checker
sudo git pull

# Update backend dependencies
cd /var/www/leads-checker/backend
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd /var/www/leads-checker/frontend
npm install
npm run build
sudo cp -r dist/* /var/www/html/leads-checker/

# Start services
sudo systemctl start leads-backend
sudo systemctl start leads-celery
sudo systemctl restart nginx
```

### 8.4 Monitor Resources

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check MongoDB status
sudo systemctl status mongod

# Check Redis status
redis-cli info
```

---

## Part 9: Optional - SSL/HTTPS Setup (Recommended)

### 9.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 9.2 Get SSL Certificate

**Note**: You need a domain name for SSL. If using IP only, skip this section.

```bash
# Replace with your domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically:
- Obtain SSL certificate
- Configure Nginx
- Set up auto-renewal

### 9.3 Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

---

## Part 10: Troubleshooting

### 10.1 Backend Not Starting

```bash
# Check logs
sudo journalctl -u leads-backend -n 50

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Test manually
cd /var/www/leads-checker/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 10.2 Celery Worker Issues

```bash
# Check logs
sudo journalctl -u leads-celery -n 50

# Test manually
cd /var/www/leads-checker/backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### 10.3 Frontend Not Loading

```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify files exist
ls -la /var/www/html/leads-checker/
```

### 10.4 MongoDB Connection Issues

```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh
```

### 10.5 Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli ping
```

### 10.6 Permission Issues

```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/leads-checker
sudo chmod -R 755 /var/www/leads-checker
sudo chown -R www-data:www-data /var/www/html/leads-checker
```

---

## Part 11: Performance Optimization

### 11.1 Increase Celery Workers

Edit `/etc/systemd/system/leads-celery.service`:

```ini
# Change concurrency based on CPU cores
ExecStart=/var/www/leads-checker/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=8
```

Then restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart leads-celery
```

### 11.2 Increase Uvicorn Workers

Edit `/etc/systemd/system/leads-backend.service`:

```ini
# Increase workers (typically 2-4 per CPU core)
ExecStart=/var/www/leads-checker/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 8
```

Then restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart leads-backend
```

### 11.3 Configure MongoDB for Production

```bash
sudo nano /etc/mongod.conf
```

Adjust settings:

```yaml
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1  # Adjust based on available RAM

net:
  maxIncomingConnections: 1000
```

Restart MongoDB:

```bash
sudo systemctl restart mongod
```

---

## Part 12: Backup Strategy

### 12.1 Backup MongoDB

```bash
# Create backup script
sudo nano /usr/local/bin/backup-mongodb.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
mongodump --out=$BACKUP_DIR/backup_$DATE

# Keep only last 7 days
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/backup-mongodb.sh
```

### 12.2 Setup Cron Job for Backups

```bash
sudo crontab -e
```

Add daily backup at 2 AM:

```cron
0 2 * * * /usr/local/bin/backup-mongodb.sh
```

---

## Summary Checklist

- [ ] VPS updated and required software installed
- [ ] MongoDB, Redis, Nginx running
- [ ] Project files uploaded to `/var/www/leads-checker`
- [ ] Environment variables configured in `.env`
- [ ] Backend dependencies installed
- [ ] Frontend built and deployed
- [ ] Systemd services created and running
- [ ] Nginx configured and restarted
- [ ] Firewall configured
- [ ] Application accessible at http://138.226.247.175/
- [ ] API accessible at http://138.226.247.175/api/
- [ ] All services tested and verified

---

## Quick Reference

### Service Management

```bash
# Start all services
sudo systemctl start leads-backend leads-celery nginx mongod redis-server

# Stop all services
sudo systemctl stop leads-backend leads-celery

# Restart all services
sudo systemctl restart leads-backend leads-celery nginx

# Check status
sudo systemctl status leads-backend leads-celery nginx mongod redis-server
```

### Log Files

- Backend: `sudo journalctl -u leads-backend -f`
- Celery: `sudo journalctl -u leads-celery -f`
- Nginx Error: `/var/log/nginx/error.log`
- Nginx Access: `/var/log/nginx/access.log`
- MongoDB: `/var/log/mongodb/mongod.log`

### Important Paths

- Application: `/var/www/leads-checker`
- Frontend Build: `/var/www/html/leads-checker`
- Uploads: `/var/www/leads-checker/backend/uploads`
- Results: `/var/www/leads-checker/backend/results`
- Environment: `/var/www/leads-checker/.env`

---

## Support

For issues or questions, check:
1. Service logs using `journalctl`
2. Nginx error logs
3. MongoDB logs
4. Application README.md

---

**Deployment Date**: _________________  
**Deployed By**: _________________  
**VPS Provider**: _________________
