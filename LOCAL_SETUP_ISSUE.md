# Local Setup Issue - Empty VPS Databases

## Problem Identified

Your local system is showing all emails as fresh because **your local VPS databases are empty or have incomplete data**.

### Evidence:

**Debug test results:**

1. **`rodriguesantonio@aeplegua.pt`** (VPS2/Email_Aa_Ag):
   - ✅ Collection has 1,532,401 documents
   - ✅ Email found → LEAKED

2. **`likeforyou2026@gmail.com`** (VPS6/Email_GCh_GCn):
   - ❌ Collection has 0 documents
   - ❌ Email not found → FRESH

## Root Cause

Your local MongoDB has the VPS database structure (collections exist) but **no actual leaked email data**.

---

## Solution Options

### Option 1: Import Data to Local MongoDB (Recommended for Development)

If you have the leaked email data files, import them:

```bash
# For each VPS database, import the data
mongoimport --db email_A_G --collection Email_Aa_Ag --file path/to/Email_Aa_Ag.json
mongoimport --db email_gmail --collection Email_GCh_GCn --file path/to/Email_GCh_GCn.json
# ... repeat for all collections
```

Or if you have a MongoDB dump:

```bash
mongorestore --db email_A_G path/to/dump/email_A_G
mongorestore --db email_gmail path/to/dump/email_gmail
# ... repeat for all databases
```

---

### Option 2: Connect to External VPS Databases (Recommended for Testing)

Instead of using localhost, connect to your actual VPS databases where the data exists.

**Edit `.env`:**

```env
ENV_MODE=local

# Point to your actual VPS databases (not localhost)
VPS2_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS3_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS4_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS5_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS6_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS7_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
VPS8_MONGODB_URL=mongodb://username:password@YOUR_VPS_IP:27017
```

**Restart services:**

```bash
# Stop current services (Ctrl+C on backend and worker terminals)

# Restart backend
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# Restart worker (in new terminal)
cd backend
.\venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

---

### Option 3: Use Sample Data for Testing

Create a small test dataset:

```javascript
// test-data.js
use email_A_G
db.Email_Aa_Ag.insertMany([
  {
    "_email_hash": "59a6ff4a92aa3b8be7125ca7a13f4ec8357689a6aaded826431db124130c5826",
    "email": "rodriguesantonio@aeplegua.pt"
  }
])

use email_gmail
db.Email_GCh_GCn.insertMany([
  {
    "_email_hash": "c27367941b6f180efb16c4b7d95ea1ff56bed8a9fed6e3f4a26803ca7e6a0b75",
    "email": "likeforyou2026@gmail.com"
  }
])
```

Run:
```bash
mongo < test-data.js
```

---

## Quick Verification

After setting up data, test:

```bash
# Test specific email
curl -X POST "http://localhost:8000/api/debug/test-email?email=likeforyou2026@gmail.com"

# Should show:
# "document_found": true
# "is_leaked": true
```

---

## Why This Happened

1. **Local development** typically uses localhost MongoDB
2. **VPS databases** with leaked data are on external servers
3. Your `.env` was configured for localhost (empty databases)
4. You need either:
   - Import data to local MongoDB, OR
   - Connect to external VPS databases

---

## Recommended Approach

**For local development:**
- Use **Option 2** - Connect to external VPS databases
- This way you don't need to maintain duplicate data locally
- Just update the VPS URLs in `.env` to point to your actual VPS servers

**For production:**
- Use `ENV_MODE=server` with `SERVER_VPS*_MONGODB_URL` variables
- Already configured in your `.env` file

---

## Current Status

✅ Code is working correctly
✅ VPS connections are working
✅ Email verification logic is correct
❌ Local VPS databases are empty

**Fix:** Import data OR connect to external VPS databases with actual leaked email data.

---

## Next Steps

1. Choose one of the options above
2. Update `.env` if using Option 2
3. Restart backend and worker
4. Test with debug endpoint
5. Upload file and verify leaked emails are detected

**Time to fix: 2-5 minutes** (depending on which option you choose)
