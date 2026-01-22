# Debug Server Email Detection Issues

## Problem
Emails that are detected as LEAKED on local are showing as FRESH on server.

## Root Cause Analysis

The most common reasons:

1. **VPS Database URLs pointing to localhost** (most likely)
2. **ENV_MODE not set correctly**
3. **VPS databases not accessible from server**
4. **Different database content between local and server**

---

## Quick Diagnostic Steps

### Step 1: Check Environment Mode

```bash
# On server
curl http://localhost:4005/api/debug/environment

# Should show:
# {
#   "env_mode": "server",  # Should be "server" not "local"
#   "debug": true,
#   "mongodb_url": "***",
#   "mongodb_database": "leads_checker"
# }
```

**If `env_mode` is "local"**: Update `.env` and set `ENV_MODE=server`

---

### Step 2: Check VPS Configuration

```bash
curl http://localhost:4005/api/debug/vps-config

# Should show all 7 VPS databases with their URLs
```

**If URLs show `localhost`**: You need to configure SERVER_VPS URLs in `.env`

---

### Step 3: Test VPS Connections

```bash
curl http://localhost:4005/api/debug/vps-connections

# Should show:
# {
#   "total_configured": 7,
#   "total_connected": 7,  # Should match configured
#   "status": "success",
#   "connections": [...]
# }
```

**If `total_connected` is 0**: VPS databases are not accessible

---

### Step 4: Test Specific Email

```bash
# Test a known leaked email
curl -X POST "http://localhost:4005/api/debug/test-email?email=1marco@aicardi.org"

# Should show:
# {
#   "email": "1marco@aicardi.org",
#   "routing": {"vps": "VPS2", "collection": "Email_Aa_Ag"},
#   "vps_connection": {"status": "connected"},
#   "is_leaked": true  # Should be true for leaked emails
# }
```

**If `is_leaked` is false**: Email not found in VPS database

---

### Step 5: Check Recent Logs

```bash
curl http://localhost:4005/api/debug/logs/recent?lines=100

# Shows recent logs from all log files
```

---

## Fix Instructions

### Fix 1: Configure ENV_MODE and Server VPS URLs

**Edit `.env` on server:**

```bash
nano .env
```

**Set ENV_MODE:**
```env
ENV_MODE=server
```

**Configure SERVER_VPS URLs:**
```env
# Uncomment and add your actual VPS IPs/hostnames
SERVER_VPS2_MONGODB_URL=mongodb://username:password@192.168.1.100:27017/email_A_G
SERVER_VPS3_MONGODB_URL=mongodb://username:password@192.168.1.101:27017/email_H_N
SERVER_VPS4_MONGODB_URL=mongodb://username:password@192.168.1.102:27017/email_O_U
SERVER_VPS5_MONGODB_URL=mongodb://username:password@192.168.1.103:27017/email_V_Z
SERVER_VPS6_MONGODB_URL=mongodb://username:password@192.168.1.104:27017/email_gmail
SERVER_VPS7_MONGODB_URL=mongodb://username:password@192.168.1.105:27017/email_hotmail
SERVER_VPS8_MONGODB_URL=mongodb://username:password@192.168.1.106:27017/email_yahoo_aol
```

**Restart services:**
```bash
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

---

### Fix 2: If VPS Databases Are on Same Server

If your VPS databases are running on the same server as the app, but you're getting connection errors:

**Check MongoDB is listening on all interfaces:**
```bash
sudo nano /etc/mongod.conf

# Find bindIp and set to:
net:
  bindIp: 0.0.0.0
  port: 27017

# Restart MongoDB
sudo systemctl restart mongod
```

**Or use localhost in SERVER_VPS URLs:**
```env
SERVER_VPS2_MONGODB_URL=mongodb://localhost:27017/email_A_G
SERVER_VPS3_MONGODB_URL=mongodb://localhost:27017/email_H_N
# etc...
```

---

### Fix 3: Test Connection from Server

**Test if server can reach VPS databases:**
```bash
# Test connection
mongo "mongodb://username:password@VPS_IP:27017/email_A_G" --eval "db.runCommand({ping: 1})"

# Should return: { "ok" : 1 }
```

**If connection fails:**
- Check firewall rules
- Verify VPS IP is correct
- Verify credentials are correct
- Check if MongoDB is running on VPS

---

## Detailed Health Check

```bash
curl http://localhost:4005/api/debug/health-detailed

# Shows comprehensive system status with issues and solutions
```

---

## Test Email Batch

```bash
curl -X POST "http://localhost:4005/api/debug/test-batch" \
  -H "Content-Type: application/json" \
  -d '["1marco@aicardi.org", "likeforyou2026@gmail.com", "test@example.com"]'

# Shows results for multiple emails at once
```

---

## Understanding the Flow

### Local (Working)
```
ENV_MODE=local
↓
Uses VPS2_MONGODB_URL=mongodb://localhost:27017
↓
Connects to local MongoDB with leaked data
↓
Finds email → LEAKED ✓
```

### Server (Not Working - Before Fix)
```
ENV_MODE=local (WRONG!)
↓
Uses VPS2_MONGODB_URL=mongodb://localhost:27017
↓
Connects to local MongoDB (empty or different data)
↓
Email not found → FRESH ✗
```

### Server (Fixed)
```
ENV_MODE=server
↓
Uses SERVER_VPS2_MONGODB_URL=mongodb://user:pass@VPS_IP:27017
↓
Connects to external VPS MongoDB with leaked data
↓
Finds email → LEAKED ✓
```

---

## Common Scenarios

### Scenario 1: Same MongoDB for Local and Server
If you're running the same MongoDB instance for both:

```env
# .env
ENV_MODE=local
VPS2_MONGODB_URL=mongodb://localhost:27017/email_A_G
# No need for SERVER_VPS URLs
```

### Scenario 2: Different VPS Databases
If local uses localhost and server uses external VPS:

```env
# .env
ENV_MODE=server  # Set to "server" on production

# Local URLs (used when ENV_MODE=local)
VPS2_MONGODB_URL=mongodb://localhost:27017/email_A_G

# Server URLs (used when ENV_MODE=server)
SERVER_VPS2_MONGODB_URL=mongodb://user:pass@external-vps:27017/email_A_G
```

### Scenario 3: All Databases on Same Server
If all VPS databases are on the same server as the app:

```env
# .env
ENV_MODE=server

# Can use localhost since databases are local
SERVER_VPS2_MONGODB_URL=mongodb://localhost:27017/email_A_G
SERVER_VPS3_MONGODB_URL=mongodb://localhost:27017/email_H_N
# etc...
```

---

## Verification Checklist

After configuration:

- [ ] `ENV_MODE` is set correctly in `.env`
- [ ] SERVER_VPS URLs are configured (if ENV_MODE=server)
- [ ] Services restarted
- [ ] `/api/debug/environment` shows correct env_mode
- [ ] `/api/debug/vps-connections` shows all databases connected
- [ ] `/api/debug/test-email` shows leaked emails as `is_leaked: true`
- [ ] Upload test file and check results

---

## Monitoring

### Watch logs during upload:
```bash
# Terminal 1: VPS connections
tail -f backend/logs/vps_connections.log

# Terminal 2: Email verification
tail -f backend/logs/email_checker.log

# Terminal 3: Worker processing
tail -f backend/logs/worker.log
```

### Expected log output:
```
[vps_connections.log]
✓ Successfully connected to VPS2: email_A_G
✓ Successfully connected to VPS6: email_gmail
VPS Connection Summary: 7/7 successful

[email_checker.log]
Email check: 1marco@aicardi.org -> VPS2/Email_Aa_Ag -> LEAKED
Email check: likeforyou2026@gmail.com -> VPS6/Email_GCh_GCn -> LEAKED

[worker.log]
Task abc123: Processing 23 emails
Task abc123: Batch 1 complete. Progress: 23/23 (15 leaked, 8 fresh)
```

---

## Quick Fix Summary

**Most likely fix:**

1. Edit `.env` on server
2. Set `ENV_MODE=server`
3. Add `SERVER_VPS2_MONGODB_URL` through `SERVER_VPS8_MONGODB_URL` with actual VPS IPs
4. Restart services
5. Test with debug endpoints

**Time to fix: 2-5 minutes**

---

## API Endpoints Reference

All debug endpoints are available at `/api/debug/`:

- `GET /api/debug/environment` - Current environment info
- `GET /api/debug/vps-config` - VPS configuration
- `GET /api/debug/vps-connections` - Test all VPS connections
- `POST /api/debug/test-email?email=xxx` - Test single email
- `POST /api/debug/test-batch` - Test multiple emails
- `GET /api/debug/logs/recent?lines=50` - Recent logs
- `GET /api/debug/health-detailed` - Comprehensive health check

---

## Need More Help?

1. Run all diagnostic endpoints
2. Check logs for errors
3. Verify VPS database accessibility
4. Ensure database content matches between local and server
5. Check firewall rules if using external VPS databases
