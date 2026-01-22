# VPS Troubleshooting Guide

## Common Issues and Solutions

### 1. Clipboard Copy Not Working on VPS

**Symptom**: Device keys don't copy to clipboard when clicking the copy button.

**Root Cause**: Modern Clipboard API (`navigator.clipboard`) only works in secure contexts (HTTPS). VPS is running on HTTP.

**Solution Applied**: ✅ Fixed
- Implemented fallback clipboard mechanism using `document.execCommand('copy')`
- Works in both HTTP and HTTPS environments
- Better error messages when copy fails
- Manual copy option displayed if all methods fail

**Verification**:
```javascript
// Check browser console for:
[API] Clipboard API failed, trying fallback: [error details]
// Or on success:
✓ Key copied successfully
```

**Manual Workaround**: If copy still fails, manually select and copy the displayed key.

---

### 2. VPS Database Not Connected

**Symptom**: 
- Emails are all marked as "fresh" even when they should be leaked
- Error message: "No VPS databases connected!"
- Worker logs show: "WARNING: No VPS databases configured!"

**Root Cause**: VPS database connection strings not configured in `.env` file.

**Solution**:

1. **Check current configuration**:
```bash
cd /var/www/leads-checker-tool
cat .env | grep VPS
```

2. **Configure VPS databases**:
```bash
nano .env
```

Add your actual VPS database URLs:
```env
# Example configuration
VPS2_MONGODB_URL=mongodb://username:password@vps2.example.com:27017/email_A_G
VPS2_MONGODB_DATABASE=email_A_G
VPS2_ENABLED=true

VPS3_MONGODB_URL=mongodb://username:password@vps3.example.com:27017/email_H_N
VPS3_MONGODB_DATABASE=email_H_N
VPS3_ENABLED=true

# ... configure all VPS2-VPS8
```

3. **Restart services**:
```bash
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

4. **Verify connections**:
```bash
tail -f /var/www/leads-checker-tool/backend/logs/vps_connections.log
```

You should see:
```
✓ Successfully connected to VPS2: email_A_G
✓ Successfully connected to VPS3: email_H_N
...
VPS Connection Summary: 7/7 successful
```

---

### 3. Connection Timeout to VPS Databases

**Symptom**: 
```
VPS2: Connection timeout on attempt 1/3
✗ Failed to connect to VPS2 after 3 attempts
```

**Possible Causes**:
1. VPS database server is down
2. Network connectivity issues
3. Firewall blocking connections
4. Incorrect connection string

**Solutions**:

**A. Test network connectivity**:
```bash
# Test if port is reachable
telnet vps2.example.com 27017

# Or using nc
nc -zv vps2.example.com 27017
```

**B. Check MongoDB authentication**:
```bash
# Test connection manually
mongo "mongodb://username:password@vps2.example.com:27017/email_A_G" --eval "db.runCommand({ping: 1})"
```

**C. Check firewall rules**:
```bash
# On VPS database server, allow incoming connections
sudo ufw allow from YOUR_APP_SERVER_IP to any port 27017
```

**D. Verify connection string format**:
```
Correct: mongodb://username:password@host:port/database
Wrong:   mongodb://host:port/database (missing auth)
Wrong:   mongodb://username@host:port/database (missing password)
```

---

### 4. Email Verification Not Working

**Symptom**: All emails marked as fresh, even known leaked emails.

**Diagnostic Steps**:

1. **Check VPS connections**:
```bash
tail -f /var/www/leads-checker-tool/backend/logs/vps_connections.log
```

2. **Check email routing**:
```bash
tail -f /var/www/leads-checker-tool/backend/logs/email_checker.log
```

Look for:
```
Email check: test@gmail.com -> VPS6/Email_GCa_GCg -> LEAKED
```

3. **Verify database collections exist**:
```bash
mongo "mongodb://user:pass@vps6.example.com:27017/email_gmail" --eval "db.getCollectionNames()"
```

Should show collections like: `Email_GCa_GCg`, `Email_GCh_GCn`, etc.

4. **Check _email_hash index**:
```bash
mongo "mongodb://user:pass@vps6.example.com:27017/email_gmail" --eval "db.Email_GCa_GCg.getIndexes()"
```

Should include an index on `_email_hash` field.

**Solutions**:

**A. If collections don't exist**: Database is empty or wrong database name
```bash
# Check actual database name on VPS
mongo --host vps6.example.com -u username -p password --eval "show dbs"
```

**B. If _email_hash index missing**: Create index
```bash
mongo "mongodb://user:pass@vps6.example.com:27017/email_gmail" --eval "
  db.getCollectionNames().forEach(function(col) {
    db[col].createIndex({'_email_hash': 1});
  });
"
```

---

### 5. Worker Not Processing Tasks

**Symptom**: 
- Files uploaded but status stays "pending"
- No worker logs being generated

**Diagnostic**:
```bash
# Check worker service status
sudo systemctl status leads-checker-worker

# Check worker logs
tail -f /var/www/leads-checker-tool/backend/logs/worker.log

# Check Redis connection
redis-cli ping
# Should return: PONG
```

**Solutions**:

**A. Worker service not running**:
```bash
sudo systemctl start leads-checker-worker
sudo systemctl enable leads-checker-worker
```

**B. Redis not running**:
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

**C. Check Celery configuration**:
```bash
cd /var/www/leads-checker-tool/backend
source venv/bin/activate
celery -A app.workers.celery_app inspect active
```

---

### 6. High Memory Usage

**Symptom**: Server running out of memory during processing.

**Diagnostic**:
```bash
free -h
top -o %MEM
```

**Solutions**:

**A. Reduce Celery worker concurrency**:
Edit `.env`:
```env
CELERY_WORKER_CONCURRENCY=2  # Reduce from 4 to 2
```

**B. Reduce batch size**:
Edit `backend/app/workers/tasks.py`:
```python
batch_size = 25  # Reduce from 50 to 25
```

**C. Add swap space**:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### 7. API Returns 500 Internal Server Error

**Symptom**: Frontend shows "Internal server error" messages.

**Diagnostic**:
```bash
# Check API logs
tail -f /var/www/leads-checker-tool/backend/logs/application.log

# Check API service logs
sudo journalctl -u leads-checker-api -n 100
```

**Common Causes**:

**A. Database connection failed**:
```bash
# Check MongoDB status
sudo systemctl status mongod

# Test connection
mongo --eval "db.runCommand({ping: 1})"
```

**B. Missing dependencies**:
```bash
cd /var/www/leads-checker-tool/backend
source venv/bin/activate
pip install -r requirements.txt
```

**C. Permission issues**:
```bash
sudo chown -R www-data:www-data /var/www/leads-checker-tool
sudo chmod -R 755 /var/www/leads-checker-tool
sudo chmod -R 777 /var/www/leads-checker-tool/backend/logs
sudo chmod -R 777 /var/www/leads-checker-tool/backend/uploads
sudo chmod -R 777 /var/www/leads-checker-tool/backend/results
```

---

### 8. Frontend Can't Connect to Backend

**Symptom**: 
- Browser console shows: "Network error. Cannot reach the server."
- Frontend displays connection errors

**Diagnostic**:
```bash
# Check if API is running
curl http://localhost:4005/health

# Check if port is listening
netstat -tlnp | grep 4005

# Check Nginx configuration
sudo nginx -t
```

**Solutions**:

**A. API not running**:
```bash
sudo systemctl start leads-checker-api
```

**B. Wrong API URL in frontend**:
Check `.env`:
```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Rebuild frontend:
```bash
cd /var/www/leads-checker-tool/frontend
npm run build
```

**C. Nginx not configured**:
```bash
sudo ln -s /etc/nginx/sites-available/leads-checker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### 9. Logs Not Being Created

**Symptom**: Log files don't exist or aren't being updated.

**Solution**:
```bash
# Create logs directory
mkdir -p /var/www/leads-checker-tool/backend/logs

# Set permissions
sudo chmod -R 777 /var/www/leads-checker-tool/backend/logs

# Restart services
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

---

### 10. Task Marked as Failed

**Symptom**: Upload completes but task shows "Failed" status.

**Diagnostic**:
Check worker logs for the specific task ID:
```bash
grep "task_id_here" /var/www/leads-checker-tool/backend/logs/worker.log
```

**Common Causes**:

**A. No VPS databases connected**:
See issue #2 above.

**B. Database write error**:
Check MongoDB logs:
```bash
sudo tail -f /var/log/mongodb/mongod.log
```

**C. File system full**:
```bash
df -h
# Clean up old results if needed
rm -rf /var/www/leads-checker-tool/backend/results/*
```

---

## Quick Diagnostic Commands

```bash
# Full system check
/var/www/leads-checker-tool/check-vps-status.sh

# View all logs in real-time
tail -f /var/www/leads-checker-tool/backend/logs/*.log

# Restart all services
sudo systemctl restart leads-checker-api leads-checker-worker mongod redis nginx

# Check service status
sudo systemctl status leads-checker-api leads-checker-worker mongod redis

# View recent errors
grep -i error /var/www/leads-checker-tool/backend/logs/*.log | tail -n 20

# Test API health
curl http://localhost:4005/health

# Test VPS database connection
mongo "mongodb://user:pass@vps.example.com:27017/database" --eval "db.runCommand({ping: 1})"
```

---

## Getting Help

If issues persist after trying these solutions:

1. **Collect diagnostic information**:
```bash
# Run status check
/var/www/leads-checker-tool/check-vps-status.sh > diagnostic.txt

# Collect recent logs
tail -n 100 /var/www/leads-checker-tool/backend/logs/*.log >> diagnostic.txt

# System information
uname -a >> diagnostic.txt
free -h >> diagnostic.txt
df -h >> diagnostic.txt
```

2. **Check the logs** for specific error messages
3. **Review the VPS_SETUP_CHECKLIST.md** for configuration steps
4. **Verify all environment variables** are correctly set in `.env`

---

## Performance Optimization

### For Large Email Lists (100k+ emails)

1. **Increase batch size**:
```python
# In backend/app/workers/tasks.py
batch_size = 100  # Increase from 50
```

2. **Increase worker concurrency**:
```env
# In .env
CELERY_WORKER_CONCURRENCY=8
```

3. **Add connection pooling**:
```python
# In MongoDB connection
AsyncIOMotorClient(
    url,
    maxPoolSize=50,
    minPoolSize=10
)
```

4. **Enable MongoDB query caching**
5. **Use SSD storage** for database and results
6. **Monitor resource usage** and scale as needed
