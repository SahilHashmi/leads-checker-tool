# ⚠️ CRITICAL: Configure VPS Database Connections

## Problem

Your system is showing all emails as "fresh" because the VPS database URLs in `.env` are pointing to `localhost` instead of the actual external VPS servers where the leaked email data is stored.

**Current (WRONG) configuration:**
```env
VPS2_MONGODB_URL=mongodb://localhost:27017
VPS3_MONGODB_URL=mongodb://localhost:27017
# ... all pointing to localhost
```

This means the system is checking empty local databases instead of your actual VPS databases with the leaked email data.

---

## Solution

You need to update the `.env` file with the **actual external VPS database connection strings**.

### Step 1: Find Your Actual VPS Database URLs

You mentioned you have existing VPS databases from `privatedatachecker`. You need to get the connection strings from there.

**Option A: If you have privatedatachecker `.env` file:**
```bash
# On your privatedatachecker server
cat /path/to/privatedatachecker/backend/.env | grep MONGO
```

Look for variables like:
- `EMAIL_AG_MONGO_URI`
- `EMAIL_HN_MONGO_URI`
- `EMAIL_OU_MONGO_URI`
- `EMAIL_VZ_MONGO_URI`
- `EMAIL_GMAIL_MONGO_URI`
- `EMAIL_HOTMAIL_MONGO_URI`
- `EMAIL_YAHOO_AOL_MONGO_URI`

**Option B: If you know the VPS IPs/hostnames:**

Your connection strings should look like:
```
mongodb://username:password@VPS_IP_OR_HOSTNAME:27017/database_name
```

Example:
```
mongodb://admin:SecurePass123@192.168.1.100:27017/email_A_G
mongodb://dbuser:MyPass456@vps2.example.com:27017/email_H_N
```

---

### Step 2: Update `.env` File on Your VPS

**On your VPS server:**

```bash
cd /var/www/leads-checker-tool
nano .env
```

**Replace the localhost URLs with actual VPS URLs:**

```env
# VPS2: Mail Data 1 (domains A-G) - aicardi.org goes here
VPS2_MONGODB_URL=mongodb://username:password@YOUR_VPS2_IP:27017/email_A_G
VPS2_MONGODB_DATABASE=email_A_G
VPS2_ENABLED=true

# VPS3: Mail Data 2 (domains H-N)
VPS3_MONGODB_URL=mongodb://username:password@YOUR_VPS3_IP:27017/email_H_N
VPS3_MONGODB_DATABASE=email_H_N
VPS3_ENABLED=true

# VPS4: Mail Data 3 (domains O-U)
VPS4_MONGODB_URL=mongodb://username:password@YOUR_VPS4_IP:27017/email_O_U
VPS4_MONGODB_DATABASE=email_O_U
VPS4_ENABLED=true

# VPS5: Mail Data 4 (domains V-Z, Extra, yahoo.fr, comcast.net)
VPS5_MONGODB_URL=mongodb://username:password@YOUR_VPS5_IP:27017/email_V_Z
VPS5_MONGODB_DATABASE=email_V_Z
VPS5_ENABLED=true

# VPS6: Mail Data 5 (gmail.com) - All your gmail emails go here
VPS6_MONGODB_URL=mongodb://username:password@YOUR_VPS6_IP:27017/email_gmail
VPS6_MONGODB_DATABASE=email_gmail
VPS6_ENABLED=true

# VPS7: Mail Data 6 (hotmail.com, hotmail.fr, mail.ru)
VPS7_MONGODB_URL=mongodb://username:password@YOUR_VPS7_IP:27017/email_hotmail
VPS7_MONGODB_DATABASE=email_hotmail
VPS7_ENABLED=true

# VPS8: Mail Data 7 (yahoo.com, aol.com)
VPS8_MONGODB_URL=mongodb://username:password@YOUR_VPS8_IP:27017/email_yahoo_aol
VPS8_MONGODB_DATABASE=email_yahoo_aol
VPS8_ENABLED=true
```

**Important Notes:**
- Replace `username:password` with actual MongoDB credentials
- Replace `YOUR_VPSX_IP` with actual IP addresses or hostnames
- Replace database names if they're different in your setup
- If you don't have all 7 VPS databases, set `ENABLED=false` for the ones you don't have

---

### Step 3: Restart Services

After updating `.env`:

```bash
sudo systemctl restart leads-checker-api
sudo systemctl restart leads-checker-worker
```

---

### Step 4: Verify Connections

Check if VPS databases are now connected:

```bash
tail -f /var/www/leads-checker-tool/backend/logs/vps_connections.log
```

You should see:
```
✓ Successfully connected to VPS2: email_A_G
✓ Successfully connected to VPS3: email_H_N
✓ Successfully connected to VPS6: email_gmail
...
VPS Connection Summary: 7/7 successful
```

**If you see connection errors:**
- Check credentials are correct
- Verify VPS IP addresses are reachable
- Check firewall rules allow connections from your app server
- Test connection manually: `mongo "mongodb://user:pass@vps_ip:27017/database" --eval "db.runCommand({ping: 1})"`

---

### Step 5: Test Email Verification

Upload a test file with known leaked emails:

```bash
tail -f /var/www/leads-checker-tool/backend/logs/email_checker.log
```

You should now see:
```
Email check: 1marco@aicardi.org -> VPS2/Email_Aa_Ag -> LEAKED
Email check: likeforyou2026@gmail.com -> VPS6/Email_GCh_GCn -> LEAKED
```

---

## Email Routing Reference

To understand which VPS each email goes to:

### By Domain First Letter:
- **VPS2**: Domains starting with A-G (aicardi.org, atxg.com, e-mail.ua, aa-fm.com)
- **VPS3**: Domains starting with H-N
- **VPS4**: Domains starting with O-U
- **VPS5**: Domains starting with V-Z

### Special Domains (by email username):
- **VPS6**: gmail.com (all your likef* emails)
- **VPS7**: hotmail.com, hotmail.fr, mail.ru
- **VPS8**: yahoo.com, aol.com

---

## Example for Your Test Emails

Based on your test file:

```
1marco@aicardi.org          -> VPS2 (domain starts with 'a')
likeforyou2026@gmail.com    -> VPS6 (gmail.com special domain)
likef.mailbox@gmail.com     -> VPS6 (gmail.com special domain)
vanessa19912009@e-mail.ua   -> VPS2 (domain starts with 'e')
aa-fm.com                   -> VPS2 (domain starts with 'a')
agordon@atxg.com            -> VPS2 (domain starts with 'a')
```

All of these should be detected as LEAKED once you configure the correct VPS database URLs.

---

## Security Notes

1. **Keep credentials secure** - Don't commit `.env` to git
2. **Use strong passwords** for MongoDB connections
3. **Firewall rules** - Only allow connections from your app server IP
4. **Read-only access** - The app only needs READ permissions on VPS databases
5. **Backup `.env`** - Keep a secure backup of your configuration

---

## Troubleshooting

### All emails still showing as fresh after configuration:

1. **Check logs for connection errors:**
   ```bash
   tail -f backend/logs/vps_connections.log
   ```

2. **Verify database names match:**
   ```bash
   mongo "mongodb://user:pass@vps_ip:27017" --eval "show dbs"
   ```

3. **Test connection manually:**
   ```bash
   mongo "mongodb://user:pass@vps_ip:27017/email_A_G" --eval "db.getCollectionNames()"
   ```

4. **Check if collections exist:**
   Should see collections like: `Email_Aa_Ag`, `Email_Ah_An`, `Email_Ao_Au`, etc.

5. **Verify _email_hash field exists:**
   ```bash
   mongo "mongodb://user:pass@vps_ip:27017/email_A_G" --eval "db.Email_Aa_Ag.findOne()"
   ```
   Should show documents with `_email_hash` field.

---

## Quick Test Command

After configuration, test a known leaked email:

```bash
# Check logs while uploading
tail -f backend/logs/email_checker.log backend/logs/worker.log

# Upload file with: 1marco@aicardi.org
# Should see: Email check: 1marco@aicardi.org -> VPS2/Email_Aa_Ag -> LEAKED
```

---

**Without correct VPS database URLs, email verification CANNOT work!**

This is the most critical configuration for the entire system.
