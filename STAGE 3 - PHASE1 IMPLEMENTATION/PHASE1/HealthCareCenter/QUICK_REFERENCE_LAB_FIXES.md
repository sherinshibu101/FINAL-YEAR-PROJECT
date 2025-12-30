# Quick Reference: Lab Encryption & Temp File Cleanup

## Problem Summary
❌ **Before:** Lab encryption endpoint returned 500 error + temp files never deleted  
✅ **After:** Lab encryption works + temp files auto-cleanup on logout

---

## What Was Fixed

| Issue | Solution |
|-------|----------|
| Missing `encryption_status` column | Added via migration 20251201_add_encryption_status.js |
| Missing `sample_id` and `technician_id` | Fixed INSERT query to create lab_samples record |
| Temp files not deleted | Implemented tempFileManager with cleanup on logout |
| No session isolation for temp files | Per-session temp directories `.temp-decrypted/{userId}-{sessionId}/` |

---

## Testing Quick Steps

### Prerequisites
- Backend running on http://localhost:3000
- PostgreSQL database configured
- Lab test records exist in database

### Test Flow

**Step 1: Login**
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "labtech@hospital.com",
    "password": "SecurePass123!",
    "mfaCode": "000000"
  }'

# Save the token from response
```

**Step 2: Get Lab Test ID**
```bash
curl -X GET http://localhost:3000/api/lab-tests \
  -H "Authorization: Bearer TOKEN_FROM_STEP_1"

# Save test_id from response
```

**Step 3: Encrypt Lab Report** ✅ THIS SHOULD NOW WORK
```bash
curl -X POST http://localhost:3000/api/lab/results/TEST_ID/encrypt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "filename": "lab-report.pdf",
    "fileContent": "UERGIHRlc3QgY29udGVudA=="
  }'

# Should return: 200 OK with "success": true
```

**Step 4: Check Temp Folder**
```bash
ls -la .temp-decrypted/
# Should see: labtech-id-session-id/ folder
ls -la .temp-decrypted/labtech-id-session-id/
# Should see: lab-report.pdf file
```

**Step 5: Logout (Triggers Cleanup)**
```bash
curl -X POST http://localhost:3000/api/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"sessionId": "your-session-id"}'

# Should return: 200 OK with "tempFilesRemoved": true
```

**Step 6: Verify Cleanup**
```bash
ls -la .temp-decrypted/
# Should be empty or folder should not exist
```

---

## Key Files Changed

```
✏️  Hospital-Backend/src/index.js
   - POST /logout: Added tempFileManager.cleanupSession()
   - POST /api/lab/results/:testId/encrypt: Fixed INSERT query

✨ Hospital-Backend/src/services/tempFileManager.js [NEW]
   - Complete temp file lifecycle management

📋 Hospital-Backend/src/migrations/20251201_add_encryption_status.js [NEW]
   - Added encryption_status, encrypted_at, encrypted_by, etc.

🔧 Hospital-Backend/src/migrations/20251130_comprehensive_update.js
   - Fixed to check column existence before adding
```

---

## Expected Behavior

### Encryption Endpoint
| Before | After |
|--------|-------|
| ❌ 500 error | ✅ 200 success |
| ❌ "column does not exist" | ✅ Report encrypted in DB |
| ❌ No tracking of encryption | ✅ encryption_status = 'encrypted' |

### Temp Files
| Before | After |
|--------|-------|
| ❌ No temp folder created | ✅ `.temp-decrypted/{userId}-{sessionId}/` created |
| ❌ Files persist indefinitely | ✅ Deleted on logout |
| ❌ All files in one folder | ✅ Session-isolated directories |
| ❌ No cleanup mechanism | ✅ Auto-cleanup every 10 min + timeout |

---

## Troubleshooting

### Encryption Returns 500
**Check:**
```bash
# Verify migrations ran
npx knex migrate:status

# Output should show:
# 20251130_comprehensive_update.js - Batch 2, run on ...
# 20251201_add_encryption_status.js - Batch 2, run on ...
```

**If migrations missing:**
```bash
npx knex migrate:latest
```

### Temp Files Not Deleted After Logout
**Check 1: Verify cleanup job started**
```bash
# Look for this in server logs at startup:
# ✓ Temp file cleanup job started (checks every 10 min, timeout: 30 min)
```

**Check 2: Manual cleanup**
```bash
# Cleanup manually (for testing)
rm -rf .temp-decrypted/
```

**Check 3: Change timeout for faster testing**
```env
# Add to .env file in Hospital-Backend/
TEMP_CLEANUP_TIMEOUT=1
TEMP_CLEANUP_INTERVAL=1
```

### Server Won't Start
**Error: "Database: not configured"**
```bash
# Verify .env file in Hospital-Backend/ has:
DATABASE_URL=postgres://hospital_user:password@localhost:5432/hospital_db

# Or check Encryption/.env for ENCRYPTION_KEY
```

---

## Environment Variables

### For Production
```env
NODE_ENV=production
TEMP_CLEANUP_TIMEOUT=5          # 5 minutes
TEMP_CLEANUP_INTERVAL=2         # Check every 2 minutes
```

### For Testing/Development
```env
NODE_ENV=development
TEMP_CLEANUP_TIMEOUT=2          # 2 minutes (fast cleanup)
TEMP_CLEANUP_INTERVAL=1         # Check every 1 minute
```

### For Immediate Testing
```env
TEMP_CLEANUP_TIMEOUT=0.1        # 6 seconds (testing only!)
TEMP_CLEANUP_INTERVAL=0.05      # Check every 3 seconds
```

---

## Verification Commands

### 1. Check Database Schema
```bash
# Connect to database
psql -h localhost -U hospital_user -d hospital_db

# Check lab_results table has new columns
\d lab_results

# Should show:
# encryption_status | text
# encrypted_at      | timestamp without time zone
# encrypted_by      | uuid
# decrypted_at      | timestamp without time zone
# decrypted_by      | uuid
```

### 2. Check Migrations Applied
```bash
cd Hospital-Backend
npx knex migrate:status
```

**Expected output:**
```
Using environment: development
✓ 20251127_init.js
✓ 20251128_add_billing_pharmacy.js
✓ 20251128_add_password_hash.js
✓ 20251129_lab_tests.js
✓ 20251130_comprehensive_update.js
✓ 20251201_add_encryption_status.js
```

### 3. Check Server Startup Logs
```bash
npm start

# Should show:
# ✓ Encryption service loaded
# ✓ Hospital Backend listening on http://localhost:3000
# ✓ Temp file cleanup job started (checks every 10 min, timeout: 30 min)
```

### 4. Monitor Temp Folder
```bash
# Watch in real-time
watch 'ls -la .temp-decrypted/ 2>/dev/null || echo "Temp folder cleaned up"'

# Or one-time check
find .temp-decrypted -type f 2>/dev/null | wc -l
# Should be 0 after logout
```

---

## Summary

✅ **Lab encryption working** - No more 500 errors  
✅ **Temp files created** - Per-session isolation  
✅ **Cleanup working** - On logout + timeout-based  
✅ **Database fixed** - All required columns added  
✅ **Migrations applied** - Ready for production  

**Next: Run full integration tests and monitor logs!**
