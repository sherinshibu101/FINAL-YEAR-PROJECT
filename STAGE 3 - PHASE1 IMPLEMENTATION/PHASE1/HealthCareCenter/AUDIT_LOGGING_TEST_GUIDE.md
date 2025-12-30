# Quick Test Guide - Audit Logging

## Step 1: Restart Backend Server

```bash
# In Terminal: Hospital-Backend
npm start
# or
npm run dev
```

Watch for confirmation:
```
Hospital Backend listening on http://localhost:3000
Database: localhost:5432/hospital_db
```

---

## Step 2: Make API Requests (with auth token)

### Option A: Using Frontend Login
1. Open http://localhost:5173 (or port shown by frontend)
2. Login with: `doctor@hospital.com` / `Doctor@123`
3. Enter MFA code from authenticator app
4. Backend will log your access

### Option B: Using curl

Get token first:
```bash
# 1. Login
curl -X POST http://localhost:4000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hospital.com","password":"Doctor@123"}'

# Response:
# {"success":true,"mfaRequired":true}

# 2. Get MFA code from authenticator app (6 digits)
# Example: 123456

# 3. Verify MFA
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hospital.com","code":"123456"}'

# Response:
# {
#   "success": true,
#   "token": "eyJhbGc...",
#   "refreshToken": "..."
# }

# 4. Use token for API requests
TOKEN="eyJhbGc..."

# Request patients
curl -X GET http://localhost:3000/api/patients \
  -H "Authorization: Bearer $TOKEN"

# Request appointments
curl -X GET http://localhost:3000/api/appointments \
  -H "Authorization: Bearer $TOKEN"

# Request audit logs (admin only)
curl -X GET "http://localhost:3000/api/audit-logs?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Step 3: Verify Logs in Database

### Using psql
```bash
# Connect to database
psql -h localhost -U postgres -d hospital_db

# View recent audit logs
SELECT id, actor_id, action, resource_type, created_at 
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 20;

# View specific action
SELECT * FROM audit_logs 
WHERE action = 'PATIENT_LIST_VIEWED' 
ORDER BY created_at DESC 
LIMIT 5;

# View details
SELECT id, action, details, created_at 
FROM audit_logs 
WHERE action LIKE '%PATIENT%' 
ORDER BY created_at DESC 
LIMIT 1;
```

### Using API
```bash
curl -X GET "http://localhost:3000/api/audit-logs?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

Response format:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "actor_id": "user-uuid",
      "action": "PATIENT_LIST_VIEWED",
      "resource_type": "patients",
      "resource_id": null,
      "remote_addr": "192.168.1.100",
      "details": {
        "count": 45,
        "email": "doctor@hospital.com",
        "role": "doctor"
      },
      "status": "success",
      "created_at": "2024-12-01T13:30:45.000Z",
      "actor_name": "Dr. John Smith",
      "actor_email": "doctor@hospital.com"
    }
  ],
  "pagination": {
    "total": 125,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

---

## Step 4: Check Log Files

### View audit.log
```bash
tail -f Hospital-Backend/logs/audit.log
```

Output (newest entries):
```json
{"timestamp":"2024-12-01T13:30:45.123Z","level":"info","service":"audit","eventType":"PATIENT_LIST_VIEWED","userId":"abc-123","email":"doctor@hospital.com","role":"doctor","count":45}
```

### View error.log
```bash
tail -f Hospital-Backend/logs/error.log
```

---

## Expected Audit Log Entries

After making requests, you should see:

| Action | When | Details |
|--------|------|---------|
| `LOGIN_SUCCESS` | User logs in | email, role, ip |
| `MFA_SUCCESS` | MFA verified | email, mfaMethod |
| `PATIENT_LIST_VIEWED` | GET /api/patients | count: 45 |
| `APPOINTMENTS_LIST_VIEWED` | GET /api/appointments | count: 12 |
| `AUDIT_LOGS_VIEWED` | GET /api/audit-logs | admin access |
| `PATIENT_RECORD_VIEWED` | GET /api/patients/:id | patientId |
| `[ERROR_TYPE]` | Any error | error message |

---

## Troubleshooting

### No logs appearing?

**Check 1: Is backend running?**
```bash
curl http://localhost:3000/api/patients
# Should get 401 (auth required) - backend is up
```

**Check 2: Is database connected?**
```bash
psql -h localhost -U postgres -d hospital_db
# If this fails, database is down
```

**Check 3: Are you authenticated?**
```bash
# Missing Authorization header?
curl -X GET http://localhost:3000/api/patients
# Should get 401 Unauthorized

# With valid token?
curl -X GET http://localhost:3000/api/patients \
  -H "Authorization: Bearer $TOKEN"
# Should work
```

**Check 4: Is MFA enabled?**
```bash
# Check users.json
cat Hospital-Frontend/server/users.json | grep mfaEnabled

# Should show: "mfaEnabled": true
```

---

## Sample Workflow

### Complete Test Sequence

```bash
# Terminal 1: Start Backend
cd Hospital-Backend
npm start

# Terminal 2: Start Frontend Server (IAM)
cd Hospital-Frontend/server
node index.js

# Terminal 3: Test API
TOKEN=$(curl -s -X POST http://localhost:4000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@hospital.com","password":"Doctor@123"}' \
  | jq -r .token)

# (User enters MFA code when prompted)

# Make requests
curl -X GET http://localhost:3000/api/patients \
  -H "Authorization: Bearer $TOKEN"

# Check logs
curl -X GET "http://localhost:3000/api/audit-logs?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Terminal 4: Monitor files
tail -f Hospital-Backend/logs/audit.log
```

---

## What to Look For

✅ **Success Indicators:**
- API returns 200 status (not 401/403)
- Audit logs table has new entries
- Log files update when requests made
- Details include count, email, IP address

❌ **Problems:**
- No database entries after requests
- Log files not updating
- 401 errors (auth issues)
- 403 errors (permission issues)

---

## Common Tests

### 1. List all patients
```bash
curl -X GET http://localhost:3000/api/patients \
  -H "Authorization: Bearer $TOKEN"

# Check logs:
SELECT COUNT(*) FROM audit_logs WHERE action = 'PATIENT_LIST_VIEWED';
```

### 2. View audit logs (admin)
```bash
curl -X GET "http://localhost:3000/api/audit-logs?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Should see entry for AUDIT_LOGS_VIEWED
```

### 3. Test with different roles
```bash
# Nurse account
curl -X POST http://localhost:4000/api/login \
  -d '{"email":"nurse@hospital.com","password":"Nurse@123"}'

# Lab Technician
curl -X POST http://localhost:4000/api/login \
  -d '{"email":"labtech@hospital.com","password":"LabTech@123"}'

# Each should create audit logs
```

### 4. Force an error
```bash
# Non-existent patient
curl -X GET http://localhost:3000/api/patients/invalid-id \
  -H "Authorization: Bearer $TOKEN"

# Check error log
SELECT * FROM audit_logs WHERE action LIKE '%ERROR%' LIMIT 1;
```

---

## Performance Check

Monitor log file sizes:
```bash
ls -lh Hospital-Backend/logs/
```

Expected:
```
-rw-r--r-- 1 user user 2.3M audit.log
-rw-r--r-- 1 user user 856K error.log
-rw-r--r-- 1 user user 1.5M security.log
-rw-r--r-- 1 user user 3.1M api.log
```

---

## Next Steps

1. ✅ Start backend server
2. ✅ Login and make API requests
3. ✅ Check audit_logs table
4. ✅ View log files
5. ✅ Verify data persists correctly

**All logs should now be generated and stored!**

