# Quick Start Guide - VPS Deployment

## 🚀 Fast Track Deployment (5 Minutes)

### Prerequisites
- VPS with Ubuntu 20.04+ or similar
- Root/sudo access
- At least 2GB RAM
- 20GB free disk space

---

## Step 1: Upload Project to VPS

```bash
# On your local machine
scp -r leads-checker-tool root@YOUR_VPS_IP:/var/www/

# Or clone from git
ssh root@YOUR_VPS_IP
cd /var/www
git clone YOUR_REPO_URL leads-checker-tool
```

---

## Step 2: Configure Environment

```bash
cd /var/www/leads-checker-tool

# Copy environment template
cp .env.vps .env

# Edit with your settings
nano .env
```

**CRITICAL: Update these values:**
```env
# Change admin password
ADMIN_PASSWORD=your_secure_password_here

# Change secret key
SECRET_KEY=your_random_secret_key_here

# Add VPS database URLs (REQUIRED for email verification)
VPS2_MONGODB_URL=mongodb://user:pass@vps2.example.com:27017/email_A_G
VPS2_ENABLED=true

VPS3_MONGODB_URL=mongodb://user:pass@vps3.example.com:27017/email_H_N
VPS3_ENABLED=true

# ... configure all VPS databases you want to use

# Update API URL to your VPS IP
VITE_API_URL=http://YOUR_VPS_IP:4005/api
```

Save and exit (Ctrl+X, Y, Enter)

---

## Step 3: Run Deployment Script

```bash
# Make script executable
chmod +x deploy-vps.sh

# Run deployment
sudo bash deploy-vps.sh
```

The script will:
- ✅ Install all dependencies
- ✅ Setup backend and frontend
- ✅ Create systemd services
- ✅ Configure Nginx
- ✅ Start all services

**Wait for completion** (2-3 minutes)

---

## Step 4: Verify Deployment

```bash
# Run status check
bash check-vps-status.sh
```

You should see:
```
✓ MongoDB is running
✓ Redis is running
✓ API Server is running
✓ Celery Worker is running
✓ API is responding
```

---

## Step 5: Check VPS Database Connections

```bash
tail -f backend/logs/vps_connections.log
```

You should see:
```
✓ Successfully connected to VPS2: email_A_G
✓ Successfully connected to VPS3: email_H_N
...
VPS Connection Summary: 7/7 successful
```

**If you see "No VPS databases configured":**
- Go back to Step 2 and configure VPS database URLs
- Restart services: `sudo systemctl restart leads-checker-api leads-checker-worker`

---

## Step 6: Access the Application

Open in browser:
```
http://YOUR_VPS_IP/
```

**Admin Panel:**
```
http://YOUR_VPS_IP/admin
Username: admin
Password: (what you set in .env)
```

---

## ✅ Quick Tests

### Test 1: Copy Device Key
1. Login to admin panel
2. Generate a device key
3. Click copy button
4. Should copy successfully (even on HTTP)

### Test 2: Upload Test File
1. Create test file with emails (one per line)
2. Upload via main interface
3. Monitor progress: `tail -f backend/logs/worker.log`
4. Should see email verification happening

### Test 3: Check Logs
```bash
# View all logs
tail -f backend/logs/*.log

# Should see:
# - VPS connections successful
# - Email checks with routing info
# - Task processing progress
```

---

## 🐛 Troubleshooting

### Issue: Services not starting
```bash
# Check service logs
sudo journalctl -u leads-checker-api -n 50
sudo journalctl -u leads-checker-worker -n 50

# Fix permissions
sudo bash fix-permissions.sh

# Restart services
sudo systemctl restart leads-checker-api leads-checker-worker
```

### Issue: "No VPS databases connected"
```bash
# Edit .env and add VPS database URLs
nano .env

# Restart services
sudo systemctl restart leads-checker-api leads-checker-worker

# Verify connections
tail -f backend/logs/vps_connections.log
```

### Issue: Frontend can't connect to backend
```bash
# Check API is running
curl http://localhost:4005/health

# Check Nginx
sudo nginx -t
sudo systemctl restart nginx

# Verify API URL in .env
grep VITE_API_URL .env
```

### Issue: Clipboard copy not working
**This is now fixed!** The fallback mechanism should work on HTTP.
If still failing, check browser console for errors.

---

## 📊 Monitoring Commands

```bash
# Full status check
bash check-vps-status.sh

# Watch logs in real-time
tail -f backend/logs/*.log

# Check service status
sudo systemctl status leads-checker-api
sudo systemctl status leads-checker-worker

# View recent errors
grep -i error backend/logs/*.log | tail -n 20

# Monitor resource usage
htop
```

---

## 🔄 Common Operations

### Restart Services
```bash
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

### View Logs
```bash
# Application logs
tail -f backend/logs/application.log

# Worker logs (task processing)
tail -f backend/logs/worker.log

# VPS connections
tail -f backend/logs/vps_connections.log

# Email verification
tail -f backend/logs/email_checker.log
```

### Update Code
```bash
cd /var/www/leads-checker-tool

# Pull latest changes
git pull

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart leads-checker-api leads-checker-worker
```

### Clear Old Results
```bash
# Clean up old files
rm -rf backend/uploads/*
rm -rf backend/results/*

# Restart worker
sudo systemctl restart leads-checker-worker
```

---

## 🔒 Security Checklist

- [ ] Changed ADMIN_PASSWORD in .env
- [ ] Changed SECRET_KEY in .env
- [ ] Configured firewall (ufw)
- [ ] Set up HTTPS (optional but recommended)
- [ ] Regular backups configured
- [ ] Monitoring in place

---

## 📚 Additional Resources

- **Full Setup Guide**: `VPS_SETUP_CHECKLIST.md`
- **Troubleshooting**: `VPS_TROUBLESHOOTING.md`
- **Deployment Summary**: `VPS_DEPLOYMENT_SUMMARY.md`

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ All services are running (check with `check-vps-status.sh`)  
✅ VPS databases are connected (check logs)  
✅ Frontend is accessible via browser  
✅ Admin panel login works  
✅ Device keys can be copied  
✅ Test file upload processes successfully  
✅ Email verification is working (check logs)  

---

## 🆘 Need Help?

1. Run status check: `bash check-vps-status.sh`
2. Check logs: `tail -f backend/logs/*.log`
3. Review troubleshooting guide: `VPS_TROUBLESHOOTING.md`
4. Verify .env configuration
5. Check service logs: `sudo journalctl -u leads-checker-api -n 100`

---

**Deployment time: ~5 minutes**  
**First test: ~2 minutes**  
**Total: ~7 minutes to fully operational system** 🚀
