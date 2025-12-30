# 🔐 File Encryption Integration Guide

## Overview

Your file encryption system is now **fully integrated** with the Hospital Management System's IAM and MFA services. This document explains the architecture and how everything works together.

---

## 🏗️ Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React + TypeScript)                                    │
│ - FileEncryption Component (port 5173)                           │
│ - Calls /api/files/encrypt and /api/files/decrypt               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼ (authenticated request with JWT)
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND API (Express.js, port 3000)                              │
│ - Routes: POST /api/files/encrypt                               │
│ -         POST /api/files/decrypt                               │
│ -         GET  /api/files/status/:fileId                        │
│ - Uses: authenticate middleware (validates JWT)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────────┐      ┌──────────────────┐
    │ Encryption  │      │ IAM Integration  │
    │ Service     │      │ (port 4000)      │
    │             │      │                  │
    │ - Encrypt   │      │ - Verify JWT     │
    │ - Decrypt   │      │ - Check MFA      │
    │ - KMS       │      │ - Get user info  │
    │ - Storage   │      │ - Validate role  │
    └─────────────┘      └──────────────────┘
         │
         ▼
    ┌─────────────┐
    │ PostgreSQL  │
    │ Database    │
    └─────────────┘
```

---

## 📁 File Structure

```
HealthCareCenter/
├── Hospital-Backend/
│   └── src/index.js          ← UPDATED: Added /api/files/* endpoints
│
├── Hospital-Frontend/
│   ├── src/components/
│   │   └── FileEncryption.tsx ← UPDATED: Real API calls instead of demo
│   └── server/
│       └── index.js          ← IAM Service (already running)
│
├── Encryption/
│   ├── iamIntegration.js     ← NEW: Bridges to IAM service
│   ├── encryptionService.js  ← NEW: High-level encryption API
│   ├── decryptionGateway.js  ← Existing decryption logic
│   ├── encryption.js         ← Existing AES-256-GCM encryption
│   ├── kms.js                ← Key management system
│   ├── storageManager.js     ← File storage paths
│   └── server.js             ← Standalone encryption server
│
└── test_encryption_integration.js ← NEW: Integration tests
```

---

## 🔄 How It Works

### **Scenario 1: User Decrypts a Patient File**

```
1. FRONTEND
   └─ User clicks "Decrypt" on FileEncryption component
   └─ Component reads JWT from localStorage
   └─ Sends: POST /api/files/decrypt
      {
        "fileId": "patient123.txt",
        "mfaToken": "123456" (optional)
      }
      Header: Authorization: Bearer {JWT}

2. BACKEND (/api/files/decrypt)
   └─ Validates JWT with authenticate middleware
   └─ Extracts user info from JWT
   └─ Calls: encryptionService.decryptFileWithIAM()

3. ENCRYPTION SERVICE
   └─ Calls: iamIntegration.verifyUserAccess()

4. IAM INTEGRATION
   └─ Calls IAM service (/api/me) to verify JWT
   └─ Returns user object with role + permissions
   └─ If MFA enabled: verifies MFA token with IAM
   └─ Checks permissions: canViewPatients, canViewRecords, canManageUsers
   └─ Returns user object if all checks pass

5. ENCRYPTION SERVICE (continued)
   └─ Gets DEK from KMS (key management system)
   └─ Decrypts file with AES-256-GCM
   └─ Creates temp file with plaintext
   └─ Returns content to Backend
   └─ Schedules auto-delete (5 minutes)

6. BACKEND
   └─ Returns decrypted content to Frontend
   └─ Response:
      {
        "success": true,
        "fileId": "patient123.txt",
        "content": "...",
        "user": { "id": "...", "name": "...", "role": "..." },
        "decryptedAt": "2025-11-28T10:30:00Z",
        "autoDeleteIn": "5 minutes"
      }

7. FRONTEND
   └─ Displays decrypted content in Modal
   └─ Auto-cleanup after 5 minutes
```

---

## 🛡️ Security Features

### **1. JWT Authentication**
- Every request to `/api/files/*` requires valid JWT
- JWT validated by backend `authenticate` middleware
- JWT verified again by IAM service for extra security

### **2. MFA (Multi-Factor Authentication)**
- If user has MFA enabled, MFA token required
- OTP/TOTP code must match
- Prevents unauthorized access even with stolen password

### **3. Role-Based Access Control (RBAC)**
```javascript
// Users can decrypt if they have:
- canViewPatients (Doctor, Nurse)
- canViewRecords (Doctor for medical records)
- canManageUsers (Admin for all data)
```

### **4. Encryption & Key Management**
- AES-256-GCM encryption (authenticated encryption)
- Data Encryption Keys (DEK) wrapped with Master Encryption Key (MEK)
- Keys stored securely in KMS

### **5. Audit Logging**
- All access attempts logged with timestamp
- User ID, file ID, action (decrypt, encrypt) recorded
- HIPAA compliance ready

### **6. Automatic Cleanup**
- Decrypted temp files auto-deleted after 5 minutes
- Prevents accidental data exposure
- Configurable timeout

---

## 🚀 How to Use

### **1. Ensure All Services Running**

```powershell
# Terminal 1: Backend API (port 3000)
cd Hospital-Backend
npm start

# Terminal 2: IAM Service (port 4000)
cd Hospital-Frontend/server
node index.js

# Terminal 3: Frontend (port 5173)
cd Hospital-Frontend
npm run dev
```

### **2. Test Via Frontend**

1. Go to http://localhost:5173
2. Login with credentials:
   - Email: `admin@hospital.com`
   - Password: `Admin@123`
   - MFA Code: (if enabled) Generate from authenticator app using secret: `JBSWY3DPEHPK3PXP`

3. Navigate to user profile or patient records
4. Find "File Encryption" section
5. Click "Decrypt" on a file

### **3. Test Via API (curl)**

```bash
# 1. Login to get JWT
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.com","password":"Admin@123"}'

# Returns: { "token": "eyJhbGc...", "userId": "1", ... }

# 2. Copy the token and decrypt a file
curl -X POST http://localhost:3000/api/files/decrypt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{"fileId":"sample.txt"}'

# Returns: { "success": true, "content": "...", ... }
```

### **4. Test Via Integration Test Suite**

```bash
# Run comprehensive tests (all 3 services must be running)
cd HealthCareCenter
node test_encryption_integration.js
```

---

## 📊 API Endpoints

### **POST /api/files/decrypt**

**Purpose:** Decrypt a file with IAM/MFA verification

**Request:**
```json
{
  "fileId": "patient123.txt",
  "mfaToken": "123456"  // optional, required if user has MFA
}
```

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**Response (Success):**
```json
{
  "success": true,
  "fileId": "patient123.txt",
  "content": "...",
  "user": {
    "id": "user1",
    "name": "Dr. Harini",
    "role": "admin"
  },
  "decryptedAt": "2025-11-28T10:30:00Z",
  "autoDeleteIn": "5 minutes"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid MFA token - MFA verification failed"
}
```

**Status Codes:**
- `200`: Success
- `400`: Missing fileId
- `401`: Invalid JWT or MFA required
- `403`: User lacks permission
- `503`: Encryption service not available
- `500`: Server error

---

### **POST /api/files/encrypt**

**Purpose:** Encrypt a file and store in KMS

**Request:**
```json
{
  "fileId": "patient123.txt",
  "filePath": "/path/to/temp/file"
}
```

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**Response:**
```json
{
  "success": true,
  "fileId": "patient123.txt",
  "encryptedPath": "storage/encrypted/patient123.txt.enc",
  "metadataPath": "storage/metadata/patient123.txt.meta.json",
  "algorithm": "AES-256-GCM",
  "encryptedAt": "2025-11-28T10:30:00Z",
  "user": {
    "id": "user1",
    "role": "admin"
  }
}
```

---

### **GET /api/files/status/:fileId**

**Purpose:** Check if file exists and get metadata

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Response:**
```json
{
  "success": true,
  "fileId": "patient123.txt",
  "exists": true,
  "algorithm": "AES-256-GCM",
  "encryptedSize": 1024,
  "meta": { ... }
}
```

---

## 🧪 Testing

### **Integration Test Suite**

```bash
node test_encryption_integration.js
```

**Tests:**
1. ✓ User Login
2. ✓ Encryption Service Available
3. ✓ IAM Integration Working
4. ✓ Decrypt with IAM Verification
5. ✓ Authentication Required

### **Expected Output:**

```
╔══════════════════════════════════════════════════════════════╗
║          ENCRYPTION INTEGRATION TEST SUITE                   ║
║          IAM + MFA + File Encryption                         ║
╚══════════════════════════════════════════════════════════════╝

📝 TEST 1: User Login
──────────────────────────────────────────────────────────────
✓ Login successful
  User ID: 1
  Token: eyJhbGciOiJIUzI1NiIs...

📝 TEST 2: Check Encryption Service Available
──────────────────────────────────────────────────────────────
✓ Encryption service is available

📝 TEST 3: Verify IAM Integration
──────────────────────────────────────────────────────────────
✓ IAM Service Integration working
  User: Dr. Sarah Admin (admin)
  MFA Enabled: true
  Permissions: canViewPatients, canEditPatients, ...

...

╔══════════════════════════════════════════════════════════════╗
║                     TEST SUMMARY                             ║
╠══════════════════════════════════════════════════════════════╣
║ Login                                              ✓ PASS    ║
║ Encryption Service Available                       ✓ PASS    ║
║ IAM Integration                                    ✓ PASS    ║
║ Decrypt with IAM                                  ✓ PASS    ║
║ Authentication Required                           ✓ PASS    ║
╠══════════════════════════════════════════════════════════════╣
║ TOTAL: 5/5 tests passed                                      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🔧 Configuration

### **Environment Variables**

In `Hospital-Backend/.env`:
```
IAM_HOST=localhost
IAM_PORT=4000
```

In `Encryption/.env`:
```
DEMO_MEK_BASE64=<your-master-key-base64>
PORT=3000
```

---

## 🚨 Troubleshooting

### **"Encryption service not available" (503)**
- Check if Encryption module is properly initialized
- Ensure storageManager has created directories
- Verify KMS and encryption modules are loaded

### **"Invalid JWT token" (401)**
- Check if JWT is valid and not expired (15 min expiry)
- Refresh token using IAM service
- Verify Authorization header format: `Bearer {token}`

### **"MFA verification failed" (401)**
- Enter correct OTP code
- Check if user has MFA enabled in users.json
- Verify TOTP secret is correct

### **"User does not have permission" (403)**
- Check user role and permissions
- Admin has all permissions by default
- Doctor/Nurse need `canViewPatients` or `canViewRecords`

### **"File not found"**
- Ensure file was encrypted first
- Check storage directories exist
- Verify fileId matches exactly (case-sensitive)

---

## 📝 Audit Logs

All encryption operations are logged to console:

```
[AUDIT] DECRYPT_SUCCESS user=admin file=patient123.txt timestamp=2025-11-28T10:30:00Z
[AUDIT] ENCRYPT_SUCCESS user=admin role=admin file=patient123.txt timestamp=2025-11-28T10:30:00Z
[AUDIT] IAM_DENIED user=doctor file=patient123.txt (insufficient permissions)
[AUDIT] MFA_DENIED user=admin file=patient123.txt (invalid OTP)
```

---

## ✅ Checklist for Production

- [ ] All 3 services running (Backend, IAM, Frontend)
- [ ] MFA enabled for all admin users
- [ ] JWT expiry set appropriately (15 min)
- [ ] Encryption keys backed up securely
- [ ] Audit logs monitored and archived
- [ ] Rate limiting configured
- [ ] HTTPS/SSL enabled
- [ ] Database encrypted and backed up
- [ ] Monitoring and alerting set up
- [ ] User training completed

---

## 🎯 Next Steps

1. **Frontend Integration**: Update FileEncryption component with file upload UI (optional)
2. **Bulk Encryption**: Add endpoints for bulk file encryption/decryption
3. **Key Rotation**: Implement automatic key rotation schedule
4. **Backup**: Set up encrypted backup of KMS and encrypted files
5. **Monitoring**: Add dashboards for encryption audit logs
6. **Reporting**: Generate HIPAA compliance reports

---

## 📞 Support

For integration issues:
1. Check console logs on all 3 services
2. Verify JWT token is valid (use `/api/me` to check)
3. Test each service independently
4. Run `test_encryption_integration.js` for comprehensive diagnosis
5. Check `Encryption/` folder for setup issues

---

**Integration Status**: ✅ **COMPLETE**

Your encryption system is now fully integrated with the Hospital Management System's IAM and MFA services!
