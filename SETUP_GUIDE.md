# Setup Guide - Local vs Server Configuration

## Quick Setup

### For Local Development

**1. Edit `.env`:**
```env
ENV_MODE=local
```

**2. Make sure local VPS databases are running:**
```bash
# Your local MongoDB should have these databases:
# - email_A_G
# - email_H_N
# - email_O_U
# - email_V_Z
# - email_gmail
# - email_hotmail
# - email_yahoo_aol
```

**3. Start services:**
```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Worker
celery -A app.workers.celery_app worker --loglevel=info

# Frontend
cd frontend
npm run dev
```

---

### For Server/Production

**1. Edit `.env` on server:**
```env
ENV_MODE=server

# Configure external VPS database URLs
SERVER_VPS2_MONGODB_URL=mongodb://user:pass@VPS2_IP:27017/email_A_G
SERVER_VPS3_MONGODB_URL=mongodb://user:pass@VPS3_IP:27017/email_H_N
SERVER_VPS4_MONGODB_URL=mongodb://user:pass@VPS4_IP:27017/email_O_U
SERVER_VPS5_MONGODB_URL=mongodb://user:pass@VPS5_IP:27017/email_V_Z
SERVER_VPS6_MONGODB_URL=mongodb://user:pass@VPS6_IP:27017/email_gmail
SERVER_VPS7_MONGODB_URL=mongodb://user:pass@VPS7_IP:27017/email_hotmail
SERVER_VPS8_MONGODB_URL=mongodb://user:pass@VPS8_IP:27017/email_yahoo_aol
```

**2. Deploy and restart:**
```bash
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

**3. Verify:**
```bash
curl http://localhost:4005/api/debug/health-detailed
```

---

## Troubleshooting on Server

### Issue: All emails showing as fresh

**Quick diagnosis:**
```bash
# 1. Check environment mode
curl http://localhost:4005/api/debug/environment

# 2. Check VPS connections
curl http://localhost:4005/api/debug/vps-connections

# 3. Test specific email
curl -X POST "http://localhost:4005/api/debug/test-email?email=1marco@aicardi.org"
```

**Most common fix:**
- Set `ENV_MODE=server` in `.env`
- Configure `SERVER_VPS*_MONGODB_URL` variables
- Restart services

---

## Debug Endpoints

Access these at `http://YOUR_SERVER:4005/api/debug/`:

| Endpoint | Purpose |
|----------|---------|
| `/environment` | Check ENV_MODE and config |
| `/vps-config` | See VPS database configuration |
| `/vps-connections` | Test all VPS connections |
| `/test-email?email=xxx` | Test single email verification |
| `/test-batch` | Test multiple emails |
| `/logs/recent?lines=50` | View recent logs |
| `/health-detailed` | Full system health check |

---

## Configuration Files

**Single `.env` file for both local and server:**
- `ENV_MODE=local` - Uses `VPS*_MONGODB_URL` variables
- `ENV_MODE=server` - Uses `SERVER_VPS*_MONGODB_URL` variables

**No more `.env.vps` file needed!**

---

## Email Routing Reference

| Email Domain | VPS Database | Example |
|--------------|--------------|---------|
| Domains A-G | VPS2 | aicardi.org, atxg.com |
| Domains H-N | VPS3 | hotmail.com (if not special) |
| Domains O-U | VPS4 | outlook.com |
| Domains V-Z | VPS5 | yahoo.fr |
| gmail.com | VPS6 | likeforyou2026@gmail.com |
| hotmail.com/fr, mail.ru | VPS7 | hotmail.com |
| yahoo.com, aol.com | VPS8 | yahoo.com |

---

## Logs Location

```
backend/logs/
├── application.log       # Main app events
├── database.log         # MongoDB operations
├── vps_connections.log  # VPS database connections
├── email_checker.log    # Email verification details
└── worker.log           # Task processing
```

**Monitor during upload:**
```bash
tail -f backend/logs/email_checker.log backend/logs/worker.log
```

---

## Common Commands

### Check service status:
```bash
sudo systemctl status leads-checker-api
sudo systemctl status leads-checker-worker
```

### View logs:
```bash
# Application logs
tail -f backend/logs/application.log

# Email verification
tail -f backend/logs/email_checker.log

# All logs
tail -f backend/logs/*.log
```

### Restart services:
```bash
sudo systemctl restart leads-checker-api leads-checker-worker
```

### Test API:
```bash
curl http://localhost:4005/health
curl http://localhost:4005/api/debug/health-detailed
```

---

## Success Indicators

### Local Working:
- ✅ ENV_MODE=local
- ✅ VPS databases on localhost
- ✅ Emails detected as leaked
- ✅ Logs show "LEAKED" for known emails

### Server Working:
- ✅ ENV_MODE=server
- ✅ SERVER_VPS URLs configured
- ✅ `/api/debug/vps-connections` shows all connected
- ✅ `/api/debug/test-email` returns `is_leaked: true` for leaked emails
- ✅ Upload shows correct leaked count
- ✅ Logs show "LEAKED" for known emails

---

## Quick Reference

**Local works, server doesn't?**
→ Set `ENV_MODE=server` and configure `SERVER_VPS*_MONGODB_URL`

**Need to debug?**
→ Use `/api/debug/*` endpoints

**Check logs?**
→ `tail -f backend/logs/*.log`

**Restart everything?**
→ `sudo systemctl restart leads-checker-api leads-checker-worker`

---

For detailed troubleshooting, see: **`DEBUG_SERVER_ISSUES.md`**
