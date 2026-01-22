# VPS Setup Checklist for Leads Checker Tool

## Critical Issues Fixed

### 1. ✅ Clipboard Copy Issue (HTTP vs HTTPS)
**Problem**: Device keys couldn't be copied on VPS (HTTP environment)
**Solution**: Implemented fallback clipboard mechanism using `document.execCommand('copy')` for HTTP environments
- Modern Clipboard API works on HTTPS only
- Fallback method now handles HTTP environments (VPS)
- Better error messages when copy fails

### 2. ✅ VPS Database Connection Issues
**Problem**: System not checking data from external VPS databases
**Solution**: 
- Added comprehensive connection retry logic (3 attempts with 2s delay)
- Proper timeout handling (10 seconds per connection)
- Connection validation with ping command
- Detailed logging for each connection attempt

### 3. ✅ Missing Error Handling & Logging
**Problem**: No clear error messages when things fail
**Solution**: Added comprehensive logging system
- Application logs: `logs/application.log`
- Database logs: `logs/database.log`
- VPS connection logs: `logs/vps_connections.log`
- Email checker logs: `logs/email_checker.log`
- Worker logs: `logs/worker.log`

### 4. ✅ Email Verification Not Working
**Problem**: Emails treated as fresh every time, not checking against VPS databases
**Solution**:
- Validates VPS connections before processing
- Fails task if no VPS databases are connected
- Logs each email check with routing information
- Treats connection errors gracefully (marks as fresh to avoid data loss)

## VPS Deployment Steps

### Step 1: Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install mongodb-org -y
sudo systemctl start mongod
sudo systemctl enable mongod

# Install Redis
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis
```

### Step 2: Configure Environment Variables
```bash
cd /path/to/leads-checker-tool

# Copy VPS environment template
cp .env.vps .env

# Edit with your actual values
nano .env
```

**CRITICAL**: Update these values in `.env`:
1. `SECRET_KEY` - Generate a secure random string
2. `ADMIN_PASSWORD` - Change from default
3. `VPS2_MONGODB_URL` through `VPS8_MONGODB_URL` - Add your actual VPS database URLs
4. Set `VPS*_ENABLED=true` for each VPS you want to use
5. `VITE_API_URL` - Update to your VPS IP/domain

### Step 3: Setup Backend
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs uploads results

# Test database connection
python -c "from app.core.config import settings; print(f'MongoDB URL: {settings.MONGODB_URL}')"
```

### Step 4: Setup Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

# The build output will be in 'dist' folder
```

### Step 5: Configure Systemd Services

**Backend API Service** (`/etc/systemd/system/leads-checker-api.service`):
```ini
[Unit]
Description=Leads Checker Tool API
After=network.target mongod.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/leads-checker-tool/backend
Environment="PATH=/path/to/leads-checker-tool/backend/venv/bin"
ExecStart=/path/to/leads-checker-tool/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4005
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/leads-checker-worker.service`):
```ini
[Unit]
Description=Leads Checker Tool Celery Worker
After=network.target mongod.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/leads-checker-tool/backend
Environment="PATH=/path/to/leads-checker-tool/backend/venv/bin"
ExecStart=/path/to/leads-checker-tool/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start Services**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable leads-checker-api
sudo systemctl enable leads-checker-worker
sudo systemctl start leads-checker-api
sudo systemctl start leads-checker-worker
```

### Step 6: Configure Nginx for Frontend
```nginx
server {
    listen 80;
    server_name 138.226.247.175;  # Your VPS IP

    # Frontend
    location / {
        root /path/to/leads-checker-tool/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:4005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable and restart Nginx**:
```bash
sudo ln -s /etc/nginx/sites-available/leads-checker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Verification Steps

### 1. Check Logs for VPS Connections
```bash
# Backend logs
tail -f /path/to/leads-checker-tool/backend/logs/vps_connections.log

# Should show:
# ✓ Successfully connected to VPS2: email_A_G
# ✓ Successfully connected to VPS3: email_H_N
# etc.
```

### 2. Test API Health
```bash
curl http://127.0.0.1:8000/health
# Should return: {"status":"healthy"}
```

### 3. Check Service Status
```bash
sudo systemctl status leads-checker-api
sudo systemctl status leads-checker-worker
sudo systemctl status mongod
sudo systemctl status redis
```

### 4. Monitor Worker Logs
```bash
tail -f /path/to/leads-checker-tool/backend/logs/worker.log

# When processing emails, you should see:
# Task {task_id}: Connecting to main database
# Task {task_id}: Successfully connected to main database
# Task {task_id}: Initializing VPS connections
# VPS Connection Summary: 7/7 successful
# Task {task_id}: Processing batch 1/X
```

### 5. Test Email Verification
Upload a test file with known emails and check logs:
```bash
tail -f /path/to/leads-checker-tool/backend/logs/email_checker.log

# Should show routing and verification:
# Email check: test@gmail.com -> VPS6/Email_GCa_GCg -> LEAKED
# Email check: fresh@example.com -> VPS2/Email_Ea_Eg -> FRESH
```

## Troubleshooting

### Issue: "No VPS databases configured!"
**Solution**: 
1. Check `.env` file has VPS URLs configured
2. Ensure `VPS*_ENABLED=true` for databases you want to use
3. Restart services: `sudo systemctl restart leads-checker-api leads-checker-worker`

### Issue: "Failed to connect to VPS"
**Solution**:
1. Check VPS database URLs are correct
2. Verify network connectivity: `telnet vps-ip 27017`
3. Check MongoDB authentication credentials
4. Review logs: `tail -f logs/vps_connections.log`

### Issue: "Clipboard copy not working"
**Solution**:
1. This is normal on HTTP - the fallback method should work
2. Check browser console for errors
3. If still failing, manually select and copy the key
4. Consider setting up HTTPS for better clipboard support

### Issue: "All emails marked as fresh"
**Solution**:
1. Check VPS connections in logs
2. Verify email routing is correct
3. Ensure VPS databases have the `_email_hash` field indexed
4. Check worker logs for connection errors

## Monitoring Commands

```bash
# Watch all logs in real-time
tail -f logs/*.log

# Check disk space
df -h

# Check memory usage
free -h

# Monitor MongoDB
mongo --eval "db.serverStatus()"

# Monitor Redis
redis-cli INFO

# Check active connections
netstat -an | grep :4005
netstat -an | grep :27017
```

## Security Recommendations

1. **Change default credentials** in `.env`
2. **Use strong SECRET_KEY** (generate with: `openssl rand -hex 32`)
3. **Configure firewall** to restrict access
4. **Set up HTTPS** with Let's Encrypt for production
5. **Regular backups** of MongoDB data
6. **Monitor logs** for suspicious activity
7. **Keep system updated**: `sudo apt update && sudo apt upgrade`

## Performance Tuning

1. **Increase Celery workers** if processing is slow: `CELERY_WORKER_CONCURRENCY=8`
2. **Add MongoDB indexes** for faster queries
3. **Configure Redis persistence** for task queue reliability
4. **Set up log rotation** to prevent disk space issues
5. **Monitor resource usage** and scale as needed
