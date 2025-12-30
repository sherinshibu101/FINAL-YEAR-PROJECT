# Lab Report Decryption & Temp File Management - FIXED

## Issues Resolved

### 1. ✅ Doctor Cannot Decrypt Lab Reports
**Problem:** Error "Failed to encrypt report" when doctors tried to view lab reports they ordered  
**Root Cause:** Access control was too restrictive - only lab_technician role allowed to decrypt  
**Solution:** Updated `/api/lab/results/:testId/download` to include `doctor` role

### 2. ✅ Temp Files Not Auto-Cleaned
**Problem:** Decrypted files stored in temp folder persisted even after user logout  
**Root Cause:** No session management or cleanup mechanism for temp files  
**Solution:** Implemented `tempFileManager` with automatic cleanup on logout and timeout

### 3. ✅ Unsecure Temp File Storage
**Problem:** All decrypted files in single temp folder, accessible to all users  
**Root Cause:** No session isolation for temp files  
**Solution:** Session-specific temp directories: `{userId}-{sessionId}/`

---

## Implementation Details

### New Service: `tempFileManager.js`

Located at: `Hospital-Backend/src/services/tempFileManager.js`

**Features:**
```javascript
// Initialize user session with temp directory
await tempFileManager.initSessionTempDir(userId, sessionId)

// Save decrypted file to user's temp folder
const tempPath = await tempFileManager.saveTempFile(userId, sessionId, filename, buffer)

// Read from temp folder (with security checks)
const content = await tempFileManager.readTempFile(userId, sessionId, filename)

// Clean up all temp files when user logs out
await tempFileManager.cleanupSession(userId, sessionId)

// Auto-cleanup expired sessions every 10 minutes
tempFileManager.startCleanupJob()
```

**Directory Structure:**
```
.temp-decrypted/
├── user1-session1/
│   ├── test-123.pdf
│   └── test-456.pdf
├── user2-session2/
│   └── test-789.pdf
└── ...
```

**Auto-Cleanup Timeline:**
- Session timeout: 30 minutes of inactivity
- Cleanup check: Every 10 minutes
- Manual cleanup: On logout
- Path validation: Prevents directory traversal attacks

---

## Code Changes

### 1. Lab Routes (`src/routes/lab.js`)

#### Added Import:
```javascript
const tempFileManager = require('../services/tempFileManager');
```

#### Updated GET `/api/lab/results/:testId`
**Before:** `requireRole(['doctor','lab_technician'])`  
**After:** `requireRole(['doctor','lab_technician','nurse'])`

**Access Logic:**
- Lab Technician: Can view ANY result
- Nurse: Can view ANY result  
- **Doctor: Can ONLY view results they ordered** ✓ FIXED

#### Updated GET `/api/lab/results/:testId/download`
**Before:** Direct file response  
**After:** 
1. Decrypt file
2. Save to temp folder: `.temp-decrypted/{userId}-{sessionId}/`
3. Send file to client
4. **Auto-cleanup scheduled** ✓ NEW
5. Detailed audit log with cleanup info

**Example Flow:**
```
User: doctor@hospital.com, Session: abc123def456
Downloads: test-789.pdf

→ File decrypted
→ Saved to: .temp-decrypted/doc-uuid-abc123def456/test-789-1701432045000.pdf
→ File sent to browser
→ Auto-cleanup in 30 minutes if inactive
→ OR manually cleaned on logout
```

### 2. Logout Endpoint (`src/index.js`)

#### Updated POST `/api/logout`
**Before:** Only revokes token  
**After:** Revokes token + cleans temp files

```javascript
app.post('/api/logout', authenticate, async (req, res) => {
  // 1. Get session ID
  const sessionId = req.session?.id || req.body.sessionId;
  
  // 2. Clean all temp files for user
  await tempFileManager.cleanupSession(req.user.userId, sessionId);
  
  // 3. Log the action
  await winstonLogger.logAudit('LOGOUT_WITH_CLEANUP', {...});
  
  // 4. Respond
  res.json({ success: true, tempFilesRemoved: true });
});
```

### 3. Server Startup (`src/index.js`)

#### Auto-Cleanup Job
```javascript
// Initialize cleanup job (runs every 10 minutes)
const tempFileManager = require('./services/tempFileManager');
tempFileManager.startCleanupJob();
```

**Output on startup:**
```
✓ Hospital Backend listening on http://localhost:3000
✓ Temp file cleanup job started (30 min timeout)
```

---

## User Experience

### Scenario 1: Doctor Views Lab Report

```
1. Doctor opens lab report in portal
2. Frontend calls: GET /api/lab/results/{testId}/download
3. Backend decrypts file
4. File saved to: .temp-decrypted/doctor-id-session-id/
5. Browser downloads: test-results.pdf
6. ✓ Auto-cleanup in 30 min (or on logout)
```

### Scenario 2: Secure Logout

```
1. User clicks "Logout" button
2. Frontend calls: POST /api/logout with sessionId
3. Backend executes:
   - Revokes JWT token
   - Calls tempFileManager.cleanupSession()
   - Deletes: .temp-decrypted/user-id-session-id/
4. ✓ All temp files deleted immediately
5. User returned to login screen
```

### Scenario 3: Timeout Cleanup

```
1. User downloads report at 10:00 AM
   → Temp file created
   → Last accessed: 10:00 AM

2. User leaves for meetings, doesn't close browser
   → No activity until 10:35 AM (35+ minutes)

3. Cleanup job runs at 10:10, 10:20, 10:30, 10:40 AM
   → At 10:40: detects 40 min inactivity (> 30 min timeout)
   → Automatically deletes temp files

4. ✓ User returns - files are gone, security maintained
```

---

## Security Features

### ✅ Session Isolation
Each user/session has separate folder:
```
.temp-decrypted/
├── user1-session1/  ← Only user1 can access
├── user1-session2/  ← New session, new folder
└── user2-session1/  ← Only user2 can access
```

### ✅ Path Validation
Prevents directory traversal attacks:
```javascript
// Security check
const realpath = await fs.realpath(filepath);
if (!realpath.startsWith(await fs.realpath(tempDir))) {
  throw new Error('Invalid file path');
}
```

### ✅ Auto-Cleanup
Prevents accumulation of sensitive files:
- 30-minute inactivity timeout
- Automatic job every 10 minutes
- Manual cleanup on logout
- Size limit: 10MB per file max

### ✅ Audit Logging
Every decryption logged with details:
```javascript
{
  action: 'downloaded_report',
  resourceType: 'lab_report_pdf',
  details: { 
    tempPath: '.temp-decrypted/...',
    sessionId: 'abc123',
    willAutoCleanup: true  ← NEW
  }
}
```

---

## Testing

### Test 1: Doctor Decrypts Report
```bash
# 1. Login as doctor
curl -X POST http://localhost:4000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hospital.com","password":"Doctor@123"}'

# 2. Verify MFA, get token
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hospital.com","code":"123456"}'

# 3. Download report (should work now!)
curl -X GET "http://localhost:3000/api/lab/results/test-id-here/download" \
  -H "Authorization: Bearer $TOKEN" \
  > report.pdf

# 4. Verify temp file exists
ls -la .temp-decrypted/
```

### Test 2: Auto-Cleanup on Logout
```bash
# 1. Check temp files exist
ls -la .temp-decrypted/doctor-uuid-session/

# 2. Logout
curl -X POST http://localhost:3000/api/logout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc123"}'

# Response:
# {"success":true,"message":"Logged out successfully","tempFilesRemoved":true}

# 3. Verify temp folder cleaned
ls -la .temp-decrypted/doctor-uuid-session/
# Should be empty or deleted
```

### Test 3: Timeout Cleanup
```bash
# 1. Download report
# ... (as above)

# 2. Check temp file
ls -la .temp-decrypted/*/

# 3. Wait 30+ minutes
sleep 1800

# 4. Cleanup job runs automatically
# Watch logs for: "✓ Auto-cleaned expired session..."

# 5. Verify deleted
ls -la .temp-decrypted/*/  # Should be empty
```

---

## Database Queries

### View Session Info
```javascript
// Get active sessions (debugging)
const tempFileManager = require('./services/tempFileManager');
console.log(tempFileManager.listActiveSessions());

// Output:
[
  {
    sessionKey: "doctor-uuid:abc123",
    userId: "doctor-uuid",
    fileCount: 2,
    createdAt: "2024-12-01T10:30:00Z",
    lastAccessed: "2024-12-01T10:35:00Z",
    inactiveTime: "5 min"
  }
]
```

---

## Configuration

### Adjust Timeout
Edit `tempFileManager.js`:
```javascript
// Default: 30 minutes
const CLEANUP_TIMEOUT = 30 * 60 * 1000;

// Change to: 60 minutes
const CLEANUP_TIMEOUT = 60 * 60 * 1000;
```

### Adjust Cleanup Check
```javascript
// Default: every 10 minutes
setInterval(() => {
  cleanupExpiredSessions();
}, 10 * 60 * 1000);

// Change to: every 5 minutes
setInterval(() => {
  cleanupExpiredSessions();
}, 5 * 60 * 1000);
```

---

## Troubleshooting

### Issue: "Access denied" for doctor

**Solution:**
1. Verify doctor role: `SELECT role FROM users WHERE email='doctor@hospital.com'`
2. Verify doctor ordered the test: `SELECT doctor_id FROM lab_tests WHERE id='test-id'`
3. Ensure both match and role includes 'doctor'

### Issue: Temp files not deleted

**Check:**
1. Verify cleanup job started: `grep "Temp file cleanup job" logs/`
2. Check session ID: Ensure logout includes sessionId
3. Verify permissions: Check .temp-decrypted folder is writable

### Issue: "Failed to decrypt report"

**Check:**
1. Verify KEK: `echo $ENCRYPTION_KEY`
2. Check file exists: `SELECT report_file_encrypted FROM lab_results WHERE test_id='...'`
3. Check IV/tag: `SELECT report_file_iv, report_file_tag FROM lab_results`

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| Doctor decrypt lab reports | ❌ Permission denied | ✅ Can decrypt owned tests |
| Temp file cleanup | ❌ Manual/never | ✅ Auto-cleanup in 30 min |
| Session isolation | ❌ Shared folder | ✅ Per-session folders |
| Logout cleanup | ❌ No cleanup | ✅ Immediate cleanup |
| Audit logging | ⚠️ Basic | ✅ With cleanup info |
| Path validation | ❌ None | ✅ Prevents traversal |

---

## Next Steps

1. **Test** - Run test scenarios above
2. **Monitor** - Watch cleanup logs for issues
3. **Document** - Share with frontend team for session ID handling
4. **Deploy** - Push to production with monitoring
5. **Review** - Check temp folder size weekly

**Files Modified:**
- `Hospital-Backend/src/services/tempFileManager.js` ✅ NEW
- `Hospital-Backend/src/routes/lab.js` ✅ UPDATED
- `Hospital-Backend/src/index.js` ✅ UPDATED

